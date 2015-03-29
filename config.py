import os

from ConfigParser import SafeConfigParser
from updatemanager import DummyLogger

BUILT_IN_CONFIG = {
	"Update" : {
	    "interval" : "7",
	    }
	}


class WxfcConfig(SafeConfigParser):
    """extends ConfigParser with default options"""

    def __init__(self, filename="wxfalsecolor.cfg", logger=None):
	self._log = logger if logger else DummyLogger()
	self.filename = filename
	SafeConfigParser.__init__(self)
	self.set_defaults(BUILT_IN_CONFIG)
	
	## read config file if it exists
	configfile = self.get_filepath()
	if os.path.isfile(configfile):
	    self._log.info("reading config file '%s'" % configfile)
	    self.read(configfile)
	
	## set this after defaults and existing file have been loaded
	self._changed = False


    def get(self, section, option, default=None):
        """add default value to return if not found in config"""
        if default and not self.has_option(section, option):
            if not self.has_section(section):
                self.add_section(section)
            self.set(section, option, str(default))
        return SafeConfigParser.get(self, section, option)

    def getfloat(self, section, option, default=None):
        return float(self.get(section, option, default))

    def getint(self, section, option, default=None):
        return int(self.get(section, option, default))


    def get_filepath(self):
	"""return path to config file in $APPDATA or $HOME"""
	if os.name == 'nt':
	    appdata = os.path.join(os.environ['APPDATA'], "falsecolor2")
	else:
	    appdata = os.path.join(os.environ['HOME'], ".falsecolor2")
	return os.path.join(appdata, self.filename)


    def save_changes(self, filename=""):
	"""save only if contents have changed"""
	if self._changed == True:
	    if not filename:
		filename = self.get_filepath()
	    self.write(filename)


    def set(self, section, option, value, logging=True):
	"""set _changed flag with each change to config"""
	if logging:
	    self._log.debug("new value for [%s] %s: '%s'" % (section, option, value))
	SafeConfigParser.set(self, section, option, value)
	self._changed = True


    def set_defaults(self, defaults):
	"""add sections and default values"""
	self._log.debug("loading default values")
	for s,pairs in defaults.items():
	    if not self.has_section(s):
		self.add_section(s)
	    for k,v in pairs.items():
		self.set(s,k,v,False)


    def set_filename(self, filename):
	"""change default filename"""
	self._log.info("new filename for config file: '%s'" % filename)
	self.filename = filename


    def write(self, path=None):
	"""write config file to <path> or default path"""
	if not path:
	    path = self.get_filepath()

	## create directories if necessary
	dirname = os.path.dirname(path)
	if not os.path.isdir(dirname):
	    self._log.info("creating directory for config file: '%s'" % dirname)
	    try:
		os.makedirs(dirname)
	    except Exception, err:
		self._log.exception(err)
		return False

	## now try to write the file
	self._log.info("saving config file '%s' ..." % path)
	try:
	    f = file(path, "wb")
	    SafeConfigParser.write(self, f)
	    f.close()
	    return True
	except Exception, err:
	    self._log.exception(err)

    


if __name__ == '__main__':
    wc = WxfcConfig()
    for s in wc.sections():
	print s
	for k,v in wc.items(s):
	    print "   %-20s : %s" % (k,v)

