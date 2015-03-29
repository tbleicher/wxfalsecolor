from updatemanager import *
import mock
import urllib2


URL_TESTFILE = "./tests/data/code.google.html"

URL_WXFC_04_ALPHA = "http://code.google.com/p/pyrat/downloads/detail?name=wxfalsecolor_v04alpha.exe"



class TestDownloadParser:

    def __init__(self):
        self._parser = self._newParser()

    def _newParser(self):
        text = file(URL_TESTFILE, "r").read()
        parser = DownloadParser("%a %b %d %H:%M:%S %Y")
        parser.feed(text)
        parser.close()
        return parser

    def test_hasData(self):
        assert self._parser.hasData() == True

    def test_isUpdate_same_day(self):
        assert self._parser.isUpdate("Thu Jan 13 12:29:20 2011") == False

    def test_isUpdate_next_day(self):
        assert self._parser.isUpdate("Fri Jan 14 12:29:20 2011") == False

    def test_isUpdate_previous_day(self):
        assert self._parser.isUpdate("Wed Jan 12 12:29:20 2011") == True



class TestUpdateManager:

    def __init__(self):
        if os.name == 'nt':
            self.fileurl = "file:///%s" % os.path.abspath(URL_TESTFILE)
        else:
            self.fileurl = "file://%s" % os.path.abspath(URL_TESTFILE)

    def test_same_day(self):
        um = UpdateManager(self.fileurl)
        um.setDate("Thu Jan 13 12:29:20 2011")
        assert um.updateAvailable() == False

    def test_next_day(self):
        um = UpdateManager(self.fileurl)
        um.setDate("Fri Jan 14 12:29:20 2011")
        assert um.updateAvailable() == False

    def test_previous_day(self):
        um = UpdateManager(self.fileurl)
        um.setDate("Wed Jan 12 12:29:20 2011")
        assert um.updateAvailable() == True

    def test_remote_site(self):
        um = UpdateManager(URL_WXFC_04_ALPHA)
        ## date of 0.4alpha is Jul 20 2010
        um.setDate("Wed Jul 20 12:00:00 2010")
        assert um.updateAvailable() == True

    def test_getDownloadPage_success(self):
        um = UpdateManager(self.fileurl)
        assert um.getDownloadPage() == True
        assert um.text == file(URL_TESTFILE).read()

    @mock.patch("urllib2.urlopen") 
    def test_getDownloadPage_HTTPError(self, urlopen):
        urlopen.side_effect = urllib2.HTTPError(self.fileurl, 404, "test", {}, file(URL_TESTFILE))
        um = UpdateManager(self.fileurl)
        assert um.getDownloadPage() == False
        assert um.text == ""
    
    @mock.patch("urllib2.urlopen") 
    def test_getDownloadPage_URLError(self, urlopen):
        urlopen.side_effect = urllib2.URLError((404, "test"))
        um = UpdateManager(self.fileurl)
        assert um.getDownloadPage() == False
        assert um.text == ""
       



class wxUpdaterTestFrame(wx.Frame):

    def __init__(self, parent=None, id=-1, title="updater test frame"):
        self._log = get_logger()
        self.fileurl = "file://%s" % os.path.abspath(URL_TESTFILE)
        wx.Frame.__init__(self, parent, id, title, size=wx.Size(150,150))
        self.Show()

        ## 'no update' button
        noupdate = wx.Button(self, wx.ID_ANY, 'no update', (20,10) )
        noupdate.Bind(wx.EVT_LEFT_DOWN, self.onNoUpdate)
        
        ## 'update' button
        updateb = wx.Button(self, -1, 'update', (20,40) )
        updateb.Bind(wx.EVT_LEFT_DOWN, self.onUpdate)
        
        ## 'update error' button
        update_err = wx.Button(self, -1, 'update error', (20,70) )
        update_err.Bind(wx.EVT_LEFT_DOWN, self.onUpdateError)
        
        ## 'quit' button
        quitbutton = wx.Button(self, wx.ID_EXIT, 'quit', (20,100) )
        quitbutton.Bind(wx.EVT_LEFT_DOWN, self.onQuit)

    def onNoUpdate(self, evt):
        self._log.info("starting update (no update) url='%s'" % URL_TESTFILE)
        um = UpdateManager(self.fileurl)
        um.setDate("Fri Jan 14 12:29:20 2011")
        um.showDialog(self)
    
    def onUpdate(self, evt):
        self._log.info("starting update url='%s'" % URL_WXFC_04_ALPHA)
        um = UpdateManager(URL_WXFC_04_ALPHA)
        um.setDate("Tue Jul 20 12:00:00 2010")
        um.showDetails() 
        um.showDialog(self)
        self.Close()

    def onUpdateError(self, evt):
        fileurl = "file://%s" % os.path.abspath(URL_TESTFILE)
        um = UpdateManager(self.fileurl+"foo")
        um.setDate("Thu Jan 13 12:29:20 2011")
        um.showDialog(self)
        
    def onQuit(self, evt):
        self.Close()




def get_logger():
    import logging
    log = logging.getLogger(logname)
    log.setLevel(logging.DEBUG)
    format = logging.Formatter("[%(levelname)1.1s] %(name)s %(module)s : %(message)s")
    log_handler = logging.StreamHandler() 
    log_handler.setLevel(logging.DEBUG)
    log_handler.setFormatter(format)
    log.addHandler(self._logHandler)
    return log


if __name__ == '__main__':
    app = wx.App(redirect = False)
    frame = wxUpdaterTestFrame()
    frame.onUpdate(-1)
    app.MainLoop()




