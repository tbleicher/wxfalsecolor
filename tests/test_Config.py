import os
import mock
from config import WxfcConfig


class TestWxfcConfig(object):
    
    def setUp(self):
	self.config = WxfcConfig()
        
    @mock.patch("os.name", 'nt')
    @mock.patch("os.environ", {"APPDATA": "C:/Users/doe"}) 
    def test_default_path_nt(self):
	path = os.path.join(os.environ["APPDATA"], "falsecolor2", "wxfalsecolor.cfg")
	print "path=", path
	print "dflt=", self.config.get_filepath()
	assert self.config.get_filepath() == path
    
    def test_default_path_unix(self):
	path = os.path.join(os.environ["HOME"], ".falsecolor2", "wxfalsecolor.cfg")
	print "path=", path
	print "dflt=", self.config.get_filepath()
	assert self.config.get_filepath() == path

    def test_builtin_section(self):
	assert self.config.has_section("Update") == True

    def test_set_filename(self):
	alt_name = "nosetesting.tmp"
	self.config.set_filename(alt_name)
	assert self.config.get_filepath().endswith(alt_name)

    def test_changed_state(self):
	self.config.set("Update", "nosetesting", "some value")
	assert self.config._changed == True


class TestAlternateConfig(object):
    
    def setUp(self):
	self.filename = "nosetesting.tmp"
	self.config = WxfcConfig(self.filename)

    def tearDown(self):
	path = self.config.get_filepath()
	if os.path.isfile(path):
	    os.remove(path)

    def test_alternate_default_path(self):
	assert self.config.get_filepath().endswith(self.filename)

    def test_write(self):
	self.config.write()
	assert os.path.isfile(self.config.get_filepath())


