import unittest
import mock
import json

from requests.exceptions import RequestException
from updatemanager import *

import requests_mock

GITHUB_URL = "https://api.github.com/repos/tbleicher/wxfalsecolor/releases"

TEST_RELEASES = [
    {'assets': [{'browser_download_url': 'https://github.com/tbleicher/wxfalsecolor/releases/download/v0.51/wxfalsecolor_v0.51.exe',
               'created_at': '2015-05-09T15:40:44Z',
               'label': None,
               'name': 'wxfalsecolor_v0.51.exe',
               'size': 5741460,
               'updated_at': '2015-05-09T15:42:16Z',
               'uploader': {},
               'url': 'https://api.github.com/repos/tbleicher/wxfalsecolor/releases/assets/571667'}],
    'assets_url': 'https://api.github.com/repos/tbleicher/wxfalsecolor/releases/1278186/assets',
    'author': {},
    'body': 'This is the old code from code.google.com. Minor typos and transfer bugs fixed, no new features.\r\n\r\nThis release is provided as a migration aid to offer a download location for the latest working version of the code and binary. The Windows binary was built on Windows XP using versions of Python and wxPython that were current at the time (December 2012). ',
    'created_at': '2015-03-29T16:22:00Z',
    'draft': False,
    'html_url': 'https://github.com/tbleicher/wxfalsecolor/releases/tag/v0.51',
    'name': 'wxfalsecolor version 0.51 [December 2012]',
    'prerelease': False,
    'published_at': '2015-05-09T15:42:29Z',
    'tag_name': 'v0.51',
    'url': 'https://api.github.com/repos/tbleicher/wxfalsecolor/releases/1278186',
    'zipball_url': 'https://api.github.com/repos/tbleicher/wxfalsecolor/zipball/v0.51'},

    {'assets': [{'browser_download_url': 'https://github.com/tbleicher/wxfalsecolor/releases/download/v0.52/wxfalsecolor_v0.52.exe',
               'created_at': '2015-06-09T15:40:44Z',
               'label': None,
               'name': 'wxfalsecolor_v0.52.exe',
               'size': 5741460,
               'updated_at': '2015-06-09T15:42:16Z',
               'uploader': {},
               'url': 'https://api.github.com/repos/tbleicher/wxfalsecolor/releases/assets/571667'}],
    'assets_url': 'https://api.github.com/repos/tbleicher/wxfalsecolor/releases/1278186/assets',
    'author': {},
    'body': 'Future release. ',
    'created_at': '2015-05-29T16:22:00Z',
    'draft': False,
    'html_url': 'https://github.com/tbleicher/wxfalsecolor/releases/tag/v0.52',
    'name': 'wxfalsecolor version 0.52 [June 2015]',
    'prerelease': False,
    'published_at': '2015-06-09T15:42:29Z',
    'tag_name': 'v0.52',
    'url': 'https://api.github.com/repos/tbleicher/wxfalsecolor/releases/1278186',
    'zipball_url': 'https://api.github.com/repos/tbleicher/wxfalsecolor/zipball/v0.52'},

    {'assets': [{'foo': 'bar'}],
    'body': 'ignored because draft status',
    'name': 'wxfalsecolor version 0.52a1 (prerelease)',
    'tag_name': 'v0.52a1',
    'prerelease': False,
    'draft': True},

    {'assets': [{'foo': 'bar'}],
    'body': 'ignored because prerelease status',
    'name': 'wxfalsecolor version 0.52a2 (prerelease)',
    'tag_name': 'v0.52a2',
    'prerelease': True,
    'draft': False},

    {'assets': [{'foo': 'bar'}],
    'body': 'ignored because old version',
    'name': 'wxfalsecolor version 0.50',
    'tag_name': 'v0.50',
    'prerelease': False,
    'draft': False}
]


class TestRelease(unittest.TestCase):

    def test_draft(self):
        r = Release({"draft": False})
        self.assertFalse(r.draft)
        r = Release({"draft": True})
        self.assertTrue(r.draft)

    def test_prerelease(self):
        r = Release({"prerelease": False})
        self.assertFalse(r.prerelease)
        r = Release({"prerelease": True})
        self.assertTrue(r.prerelease)

    def test_equal(self):
        r1 = Release({"tag_name": "1.1"})
        r2 = Release({"tag_name": "1.1.0"})
        self.assertEqual(r1, r2)
    
    def test_less_than(self):
        r1 = Release({"tag_name": "1.1"})
        r2 = Release({"tag_name": "1.1.1"})
        self.assertTrue(r1 < r2)

    def test_less_than_alpha(self):
        r1 = Release({"tag_name": "1.1a1"})
        r2 = Release({"tag_name": "1.1"})
        self.assertTrue(r1 < r2)

    def test_greater_than(self):
        r1 = Release({"tag_name": "1.1.1"})
        r2 = Release({"tag_name": "1.1.0"})
        self.assertTrue(r1 > r2)

    def test_greater_than_alpha(self):
        r1 = Release({"tag_name": "1.1a1"})
        r2 = Release({"tag_name": "1.2"})
        self.assertTrue(r1 < r2)



class TestUpdateManager(unittest.TestCase):

    def setUp(self):
        self.um = UpdateManager()
        self.um.releases = TEST_RELEASES

    @requests_mock.Mocker()
    def test_get_releases(self, m):
        m.get(GITHUB_URL, text=json.dumps(['a','b']), status_code=200)
        self.um.get_releases(GITHUB_URL)
        self.assertEqual(self.um.releases, ['a','b'])
        self.assertEqual(self.um.url, GITHUB_URL)

    @requests_mock.Mocker()
    def test_get_releases_with_wrong_http_status(self, m):
        m.get(GITHUB_URL, text=json.dumps({'message': 'Not Found'}), status_code=404)
        self.um.get_releases(GITHUB_URL)
        self.assertEqual(self.um.releases, [])
        self.assertEqual(self.um.url, "")

    @mock.patch('requests.get', mock.Mock(side_effect=RequestException))
    def test_get_releases_with_exception(self):
        self.um.get_releases(GITHUB_URL)
        self.assertTrue(self.um.error)
        self.assertEqual(self.um.releases, [])
        self.assertEqual(self.um.url, "")

    def test_version(self):
        self.assertEqual(self.um._version("v0.51"), "0.51")
        self.assertEqual(self.um._version("0.51"), "0.51")

    def test_number_of_releases(self):
        self.assertEqual(len(self.um.releases), 5)

    def test_find_updates(self):
        self.um.find_updates("v0.0")
        self.assertEqual(len(self.um._updates), 3)
        self.um.find_updates("v0.50")
        self.assertEqual(len(self.um._updates), 2)

    def test_find_updates_include_prerelease(self):
        self.um.find_updates("v0.0", include_prerelease=True)
        self.assertEqual(len(self.um._updates), 4)

    def test_updates_sorted(self):
        self.um.find_updates("v0.0")
        self.assertEqual(len(self.um._updates), 3)
        self.assertEqual( StrictVersion("0.50"), self.um._updates[0].version)
        self.assertEqual( StrictVersion("0.52"), self.um._updates[2].version)

    def test_update_available(self):
        self.um.find_updates("v0.0")
        self.assertTrue(self.um.updateAvailable())
        self.um.find_updates("v0.52")
        self.assertFalse(self.um.updateAvailable())
        self.um.error = "test error"
        self.assertFalse(self.um.updateAvailable())



if __name__ == '__main__':
  unittest.main()



