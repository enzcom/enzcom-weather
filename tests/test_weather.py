"""Isolated tests with the actual HA runtime; no devices or production config."""
import asyncio
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from types import SimpleNamespace, MappingProxyType
import unittest
from unittest.mock import AsyncMock, Mock, patch

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry, ConfigEntryState, ConfigEntries
from homeassistant.exceptions import ConfigEntryNotReady
from custom_components.enzcom_weather import async_setup_entry, async_unload_entry
from custom_components.enzcom_weather.api import WeatherClient, WeatherError, RateLimited
from custom_components.enzcom_weather import model, sensor, weather
from custom_components.enzcom_weather.config_flow import EnzcomWeatherConfigFlow

NOW = datetime(2026, 11, 18, 12, tzinfo=timezone.utc)
LOCATION = 'geonames:2830953'


def fixture():
    data = {'schema_version':1,'place':{'id':LOCATION,'name':'Sorge-Settendorf','timezone':'Europe/Berlin'},
            'provider':'DWD / Bright Sky','units':{'temperature':'°C','humidity':'%','pressure':'hPa','wind_speed':'km/h','wind_gust':'km/h','precipitation':'mm','visibility':'m'},
            'fetched_at':datetime.now(timezone.utc).isoformat(),'expires_at':(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(),'stale':False,
            'current':{'temperature':12,'humidity':70,'pressure':1010,'wind_speed':20,'wind_gust':30,'wind_direction':270,'precipitation':0.2,'precipitation_minutes':10,'kind':'observation','icon':'cloudy','time':NOW.isoformat()},
            'daily':[{'date':'2026-11-18','partial':True,'precipitation':4},{'date':'2026-11-19','partial':False,'precipitation':6}],
            'temperature_daily':[{'date':'2026-11-18','complete':True,'temperature_max':14,'temperature_min':8,'icon':'cloudy'},{'date':'2026-11-19','complete':False,'temperature_max':15,'temperature_min':9}], 'hourly':[]}
    for i in range(5):
        data['hourly'].append({'kind':'forecast','time':(NOW+timedelta(hours=i)).isoformat(),'interval_start':(NOW+timedelta(hours=i-1)).isoformat(),'precipitation_minutes':60,'temperature':10+i,'wind_speed':20+i,'wind_gust':30+i,'wind_direction':270,'precipitation':i,'precipitation_probability':i*20,'icon':'cloudy'})
    return data


class Conversion(unittest.TestCase):
    def test_hourly_precipitation_matches_following_interval(self):
        rows=model.hourly(fixture(),NOW)
        self.assertEqual(rows[0]['native_temperature'],10)
        self.assertEqual(rows[0]['native_precipitation'],1)
        self.assertEqual(rows[0]['precipitation_probability'],20)
        self.assertIsNone(rows[-1]['native_precipitation'])

    def test_met_instant_time_and_rain_same_hour(self):
        data=fixture()
        for row in data['hourly']:
            row['instant_time']=row['interval_start']
        rows=model.hourly(data,NOW)
        self.assertEqual(rows[0]['native_temperature'],11)
        self.assertEqual(rows[0]['native_precipitation'],1)

    def test_daily_partial_totals_and_incomplete_extrema_not_invented(self):
        rows=model.daily(fixture())
        self.assertIsNone(rows[0]['native_precipitation'])
        self.assertEqual(rows[0]['native_temperature'],14)
        self.assertEqual(rows[1]['native_precipitation'],6)
        self.assertIsNone(rows[1]['native_temperature'])
        self.assertEqual(rows[0]['datetime'],'2026-11-17T23:00:00+00:00')

    def test_daily_dst(self):
        data=fixture();data['daily']=[{'date':'2026-10-25'},{'date':'2026-10-26'}]
        rows=model.daily(data)
        self.assertEqual(rows[0]['datetime'],'2026-10-24T22:00:00+00:00')
        self.assertEqual(rows[1]['datetime'],'2026-10-25T23:00:00+00:00')

    def test_missing_and_zero(self):
        data=fixture();data['hourly'][1]['wind_speed']=0;data['hourly'][1]['precipitation']=0
        rows=model.hourly(data,NOW)
        self.assertEqual(rows[0]['native_precipitation'],0)
        self.assertEqual(rows[1]['native_wind_speed'],0)
        self.assertIsNone(rows[1]['wind_bearing'])
        for bad in [None,True,'3',float('nan'),float('inf'),-1]:
            self.assertIsNone(model.value({'x':bad},'x',0))

    def test_duplicate_and_outside_window(self):
        data=fixture();data['hourly'].append(copy.deepcopy(data['hourly'][0]));rows=model.hourly(data,NOW)
        self.assertEqual(len(rows),4)
        self.assertEqual(model.hourly(data,NOW+timedelta(days=4)),[])

    def test_conditions_and_directions(self):
        for a,b in [('clear-night','clear-night'),('clearsky_day','sunny'),('fair_night','partlycloudy'),('rainandthunder','lightning-rainy'),('sleet','snowy-rainy'),('unknown',None)]:self.assertEqual(model.condition(a),b)
        self.assertEqual(model.bearing({'wind_speed':1,'wind_direction':360}),0)
        self.assertIsNone(model.bearing({'wind_speed':0,'wind_direction':90}))

    def test_stale(self):
        data=fixture();self.assertTrue(model.fresh(data));data['stale']=True;self.assertFalse(model.fresh(data));data['stale']=False;data['expires_at']=NOW.isoformat();self.assertFalse(model.fresh(data,NOW))


class Response:
    def __init__(self,data,status=200):self.status=status;self.data=data;self.content=self
    async def __aenter__(self):return self
    async def __aexit__(self,*args):return None
    async def iter_chunked(self,size):yield json.dumps(self.data).encode()


class ClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_schema_units_place_and_redirect_guard(self):
        session=Mock();session.get.return_value=Response(fixture());client=WeatherClient(session)
        self.assertEqual((await client.weather(LOCATION))['schema_version'],1)
        self.assertFalse(session.get.call_args.kwargs['allow_redirects'])
        for data in [dict(fixture(),schema_version=2),dict(fixture(),units={}),dict(fixture(),place={'id':'geonames:1'}),dict(fixture(),hourly={}),dict(fixture(),fetched_at='invalid')]:
            session.get.return_value=Response(data)
            with self.assertRaises(WeatherError):await client.weather(LOCATION)
        for status in [302,503,404]:
            session.get.return_value=Response({},status)
            with self.assertRaises(WeatherError):await client.weather(LOCATION)
        session.get.return_value=Response({},429)
        with self.assertRaises(RateLimited):await client.weather(LOCATION)

    async def test_search_and_no_arbitrary_url(self):
        session=Mock();session.get.return_value=Response({'places':[{'id':LOCATION,'name':'Sorge-Settendorf'},{'id':'../../x','name':'bad'}]});client=WeatherClient(session)
        self.assertEqual(len(await client.search('Sorge')),1)
        self.assertEqual(await client.search('a'),[])
        with self.assertRaises(WeatherError):await client.weather('https://example.org')

    async def test_timeout_and_response_limit(self):
        session=Mock();session.get.side_effect=TimeoutError()
        with self.assertRaises(WeatherError):await WeatherClient(session).weather(LOCATION)
        session.get.side_effect=None;session.get.return_value=Response({'large':'x'*2_000_001})
        with self.assertRaises(WeatherError):await WeatherClient(session).weather(LOCATION)


class Lifecycle(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.hass=HomeAssistant('/tmp/enzcom-weather-isolated')
        for module in ['coordinator','config_flow']:
            patcher=patch('custom_components.enzcom_weather.'+module+'.async_get_clientsession',return_value=Mock());patcher.start();self.addCleanup(patcher.stop)
        self.hass.config_entries=SimpleNamespace(async_forward_entry_setups=AsyncMock(),async_unload_platforms=AsyncMock(return_value=True))
        self.entry=ConfigEntry(data={'place_id':LOCATION},discovery_keys=MappingProxyType({}),domain='enzcom_weather',minor_version=1,options={},source='user',title='Sorge-Settendorf',unique_id=LOCATION,version=1,subentries_data=[],state=ConfigEntryState.SETUP_IN_PROGRESS)

    async def asyncTearDown(self):
        if hasattr(self.entry,'runtime_data'):await self.entry.runtime_data.async_shutdown()
        await self.hass.async_stop(force=True)

    async def test_initial_failure_and_recovery(self):
        with patch.object(WeatherClient,'weather',side_effect=[WeatherError('offline'),fixture()]) as call:
            with self.assertRaises(ConfigEntryNotReady):await async_setup_entry(self.hass,self.entry)
            self.hass.config_entries.async_forward_entry_setups.assert_not_awaited()
            self.assertTrue(await async_setup_entry(self.hass,self.entry));self.assertEqual(call.await_count,2)
        added=Mock();await sensor.async_setup_entry(self.hass,self.entry,added);sensors=added.call_args.args[0]
        self.assertEqual(len(sensors),11);self.assertTrue(all(s.coordinator is self.entry.runtime_data for s in sensors))
        self.assertEqual(self.entry.runtime_data.update_interval,timedelta(minutes=10))
        self.assertEqual(next(s for s in sensors if s.entity_description.key=='precipitation').native_value,0.2)

    async def test_runtime_failure_stale_and_recovery(self):
        with patch.object(WeatherClient,'weather',return_value=fixture()):await async_setup_entry(self.hass,self.entry)
        entity=weather.EnzcomWeather(self.entry.runtime_data)
        status=sensor.EnzcomSensor(self.entry.runtime_data,sensor.DESCRIPTIONS[-1])
        self.assertTrue(entity.available);self.assertEqual(status.native_value,'current')
        with patch.object(WeatherClient,'weather',side_effect=WeatherError('offline')):await self.entry.runtime_data.async_refresh()
        self.assertFalse(entity.available);self.assertTrue(status.available);self.assertEqual(status.native_value,'unavailable')
        data=fixture();data['stale']=True
        with patch.object(WeatherClient,'weather',return_value=data):await self.entry.runtime_data.async_refresh()
        self.assertFalse(entity.available);self.assertEqual(status.native_value,'stale');self.assertIsNone(await entity.async_forecast_hourly())
        with patch.object(WeatherClient,'weather',return_value=fixture()):await self.entry.runtime_data.async_refresh()
        self.assertTrue(entity.available);self.assertEqual(status.native_value,'current')
        self.assertTrue(await async_unload_entry(self.hass,self.entry))

    async def test_forecast_listener_notified(self):
        with patch.object(WeatherClient,'weather',return_value=fixture()):await async_setup_entry(self.hass,self.entry)
        e=weather.EnzcomWeather(self.entry.runtime_data);e.hass=self.hass;e.async_write_ha_state=Mock();e.async_update_listeners=AsyncMock()
        e._handle_coordinator_update();await self.hass.async_block_till_done();e.async_update_listeners.assert_awaited_once_with(None)

    async def test_config_search_errors_selection_and_unique_id(self):
        f=EnzcomWeatherConfigFlow();f.hass=self.hass;f.context={'source':'user'};f.flow_id='isolated'
        self.hass.config_entries=ConfigEntries(self.hass,{})
        with patch.object(WeatherClient,'search',return_value=[]):result=await f.async_step_user({'query':'no'});self.assertEqual(result['errors']['base'],'no_places')
        with patch.object(WeatherClient,'search',side_effect=RateLimited('wait')):result=await f.async_step_user({'query':'no'});self.assertEqual(result['errors']['base'],'rate_limited')
        with patch.object(WeatherClient,'search',return_value=[fixture()['place']]):result=await f.async_step_user({'query':'Sorge'});self.assertEqual(result['step_id'],'place')
        result=await f.async_step_place({'place_id':'geonames:1'});self.assertEqual(result['errors']['base'],'invalid_place')
        with patch.object(WeatherClient,'weather',return_value=fixture()):result=await f.async_step_place({'place_id':LOCATION})
        self.assertEqual(result['type'],'create_entry');self.assertEqual(result['data'],{'place_id':LOCATION});self.assertEqual(f.unique_id,LOCATION)

if __name__=='__main__':unittest.main(verbosity=2)
