#!/usr/bin/env python3
"""Resolve approved assets explicitly; check source, bundle, HTML and live bytes."""
import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import shutil
import urllib.request


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = {}
        self.reconstructed = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            require(attrs['id'] not in self.ids, 'Duplicate HTML ID')
            self.ids[attrs['id']] = (tag, attrs)
        if 'wordmark' in attrs.get('class', '').split() and tag != 'img':
            self.reconstructed = True


def inspect_html(html, lock):
    parsed = Elements()
    parsed.feed(html)
    require(not parsed.reconstructed, 'Reconstructed HTML wordmark is forbidden')
    for binding in lock['htmlBindings']:
        require(binding['id'] in parsed.ids, 'Missing brand surface: ' + binding['id'])
        tag, attrs = parsed.ids[binding['id']]
        asset = lock['assets'][binding['asset']]
        require(tag == binding['tag'] and attrs.get(binding['attribute']) == asset['url'],
                'Wrong asset or stale cache reference: ' + binding['id'])


def check_bundle(root):
    lock = json.loads((root / 'branding-lock.json').read_text())
    require(lock['schemaVersion'] == 1, 'Unsupported branding lock')
    for asset in lock['assets'].values():
        path = root / asset['target']
        require(root.resolve() in path.resolve().parents, 'Asset path escapes bundle')
        require(digest(path.read_bytes()) == asset['sha256'], 'Asset hash mismatch: ' + asset['target'])
        require(asset['url'] == '/' + asset['target'] + '?v=' + asset['sha256'], 'Missing content version')
    if lock.get('surfaceKind') == 'none':
        require(not lock['assets'] and not lock['htmlBindings'], 'Nonvisual extension has brand surfaces')
        require(not any(p.suffix.lower() in {'.html', '.css', '.svg', '.png', '.jpg', '.ico'}
                        for p in root.rglob('*') if p.is_file()),
                'Nonvisual extension contains visual assets; register actual surfaces')
    elif lock.get('surfaceKind') == 'native':
        bindings = lock.get('nativeBindings', [])
        require(bindings and {b['asset'] for b in bindings} == set(lock['assets']), 'Unbound native assets')
        for binding in bindings:
            path = root / binding['path']
            require(root.resolve() in path.resolve().parents, 'Native binding escapes bundle')
            target = lock['assets'][binding['asset']]['target']
            if binding.get('kind') == 'nextcloud-navigation-icon':
                import xml.etree.ElementTree as ET
                require(path.name == 'info.xml', 'Nextcloud navigation must bind appinfo/info.xml')
                info = ET.fromstring(path.read_text())
                icons = [node.text for node in info.findall('./navigations/navigation/icon')]
                require(target.startswith('img/') and target[4:] in icons,
                        'Nextcloud navigation does not resolve to approved icon')
            else:
                require(target in path.read_text(), 'Native UI does not reference approved asset')
    else:
        inspect_html((root / 'static/index.html').read_text(), lock)
    return lock


def registry(root):
    base = root / 'branding/canonical'
    data = json.loads((base / 'ASSETS.json').read_text())
    for key, asset in data['assets'].items():
        require(digest((base / asset['source']).read_bytes()) == asset['sha256'], 'Canonical asset changed: ' + key)
        if asset['role'] == 'app-icon':
            require(not any(asset['source'].startswith(p + '/') for p in data['legacyIconDirectories']),
                    'Legacy app icon: ' + key)
    return data


def expected_lock(data, consumer):
    result = {'schemaVersion': 1, 'consumer': consumer, 'assets': {},
              'htmlBindings': data['consumers'][consumer]['htmlBindings']}
    if data['consumers'][consumer].get('surfaceKind') == 'none':
        result['surfaceKind'] = 'none'
    if data['consumers'][consumer].get('surfaceKind') == 'native':
        result['surfaceKind'] = 'native'
        result['nativeBindings'] = data['consumers'][consumer]['nativeBindings']
    for key, target in data['consumers'][consumer]['assets'].items():
        asset = data['assets'][key]
        result['assets'][key] = {**asset, 'target': target, 'url': '/' + target + '?v=' + asset['sha256']}
    return result


def check_consumer(root, consumer):
    data = registry(root)
    directory = root / data['consumers'][consumer]['root']
    actual = check_bundle(directory)
    require(actual == expected_lock(data, consumer), 'Bundle differs from current approval registry')
    require((directory / 'branding-check.py').read_bytes() == Path(__file__).read_bytes(), 'Stale branding checker')
    return actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['registry', 'sync', 'check', 'bundle', 'live'])
    parser.add_argument('root', type=Path)
    parser.add_argument('--consumer', default='drive-service')
    parser.add_argument('--url')
    args = parser.parse_args()
    if args.action == 'bundle':
        check_bundle(args.root)
    elif args.action == 'registry':
        data = registry(args.root)
        print('Approved product/role bindings:', len(data['assets']))
    elif args.action == 'sync':
        data = registry(args.root)
        directory = args.root / data['consumers'][args.consumer]['root']
        lock = expected_lock(data, args.consumer)
        for asset in lock['assets'].values():
            target = directory / asset['target']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(args.root / 'branding/canonical' / asset['source'], target)
        (directory / 'branding-lock.json').write_text(json.dumps(lock, indent=2) + '\n')
        shutil.copy2(__file__, directory / 'branding-check.py')
        print('Assets synchronized; HTML bindings must use URLs in branding-lock.json')
    else:
        lock = check_consumer(args.root, args.consumer)
        if args.action == 'live':
            require(args.url and args.url.startswith('https://'), 'HTTPS URL required')
            with urllib.request.urlopen(args.url.rstrip('/') + '/', timeout=30) as response:
                inspect_html(response.read().decode(), lock)
            for asset in lock['assets'].values():
                with urllib.request.urlopen(args.url.rstrip('/') + asset['url'], timeout=30) as response:
                    require(digest(response.read()) == asset['sha256'], 'Live asset differs: ' + asset['target'])
    print('Brand asset check: PASS')


if __name__ == '__main__':
    main()
