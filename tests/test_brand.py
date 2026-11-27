"""Check the files Home Assistant receives in the integration branding directory."""
from pathlib import Path
import struct
import unittest

BRAND = Path(__file__).resolve().parents[1] / 'custom_components/enzcom_weather/brand'
EXPECTED_SIZES = {'icon.png': 256, 'icon@2x.png': 512}


class BrandImages(unittest.TestCase):
    def test_brand_contains_only_supported_pngs_at_required_sizes(self):
        self.assertEqual({p.name for p in BRAND.iterdir()}, set(EXPECTED_SIZES))
        for name, size in EXPECTED_SIZES.items():
            with self.subTest(name=name):
                with (BRAND / name).open('rb') as image:
                    header = image.read(24)
                self.assertEqual(header[:16], b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')
                self.assertEqual(struct.unpack('!II', header[16:24]), (size, size))
