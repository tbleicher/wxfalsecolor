
import os
import urllib2
import time
from HTMLParser import HTMLParser

import wx
import wx.lib.scrolledpanel as scrolled 

URL_WXFALSECOLOR = "http://code.google.com/p/pyrat/downloads/detail?name=wxfalsecolor.exe"



class DummyLogger(object):

    def debug(self, msg):
        print "D " + msg.strip()

    def info(self, msg):
        print "I " + msg.strip()

    def warning(self, msg):
        print "W " + msg.strip()

    def error(self, msg):
        print "E " + msg.strip()

    def exception(self, exc):
        print "X " + exc.args[0]()




class IncrementalDownloader(object):
    """downloads data while updating a wx.ProgressDialog instance"""

    def __init__(self, url, dlg=None, logger=None):
        """create new instace with url (and optional dialog)"""

        self._log = logger if logger else DummyLogger()
        
        self._url = url
        self._dlg = dlg
        self._content_length = 0
        self.error = None


    def update_dialog(self, bytes_so_far):
        """update progress bar to percentage of download"""
        if self._content_length != 0:
            percent = float(bytes_so_far) / self._content_length
            percent = round(percent*100, 2)
        else:
            self._log.warning("update_dialog called while self._content_length == 0")
            return
        if self._dlg:
            (keepGoing, foo) = self._dlg.Update(int(percent), "download status: %d%%" % percent)
            return keepGoing
        else:
            return True


    def _download_in_chunks(self, response, chunk_size=250000):
        """retrieve download file in small bits and report progress"""
        bytes_so_far = 0
        data = ""
        keepGoing = True

        while keepGoing:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            bytes_so_far += len(chunk)
            data += chunk
            self._log.debug("downloaded %d of %d bytes" % (bytes_so_far, self._content_length))
            keepGoing = self.update_dialog(bytes_so_far)
        
        ## finally return data
        return data


    def download(self):
        """start incremental download; return data and expected size"""
        self._log.info("downloading from '%s'" % self._url)
        try:
            response = urllib2.urlopen(self._url)
            content_length = response.info().getheader('Content-Length').strip()
            self._content_length = int(content_length)
        except Exception, err:
            self._log.exception(err)
            self.error = err
            return (None, -1)
        
        ## set up incremental download
        chunk_size = 250000
        self._log.info("incremental download of %d bytes (chunksize=%d)" %
                (self._content_length, chunk_size))
        data = self._download_in_chunks(response, chunk_size)
        self._log.info("-> retreived %d bytes" % len(data))
        if len(data) != self._content_length:
            self._log.error("wrong download size: %d vs %d bytes" % (len(data), self._content_length))

        ## return data and expected size 
        return (data, self._content_length) 





class DownloadParser(HTMLParser):
    """parses the project's wxfalsecolor.exe download site"""

    def __init__(self, dfmt, logger=None):
        """create new instance with optional data format and logger instance""" 
        HTMLParser.__init__(self)
        self._log = logger if logger else DummyLogger()

        ## keep context state
        self._box_inner = False
        self._pagetitle = False
        self._tableheader = False
        self._expect_date = False
        self._expectDownload = False
        self._expect_description = False

        ## the things we need to find in page
        self.downloadLink = None
        self.filesize = None
        self.filename = "wxfalsecolor.exe"
        self.uploadedDate = None
        self.struct_time = None
        self.description = None
        self.version = None

        self.setFormat(dfmt)


    def _getDateFromAttributes(self, attrs):
        """extract the uploaded time stamp from 'title' attribute"""
        ## set old date as default
        datestamp = "Thu Jan 1 00:00:00: 2000"
        for k,v in attrs:
            if k == "title":
                datestamp = v
                self._log.info("found datestamp: '%s'" % datestamp)
        try:
            ## format: Thu Jan 13 12:29:20 2011
            self.struct_time = time.strptime(datestamp, self._dateFormat)
            self.uploadedDate = datestamp
        except ValueError:
            self.warn("datestamp '%s' does not match format '%s'" % (datestamp, self._dateFormat))
            pass
        self._expect_date = False
   

    def getDetailsDict(self):
        """return dict with download details"""
        return {'url' :         self.downloadLink,
                'description' : self.description,
                'date' :        self.uploadedDate,
                'struct_time' : self.struct_time,
                'version' :     self.version,
                'filesize' :    self.filesize,
                'filename' :    self.filename}
   

    def _getVersionFromTitle(self, data):
        """extract version number from page title (upload summary)"""
        words = data.split()
        if "version" in words:
            version = words[words.index("version")+1]
            try:
                self.version = float(version)
                self._log.info("found version number: %s" % version)
            except:
                pass


    def handle_starttag(self, tag, attrs):
        """set attributes depending on html context"""
        
        ## summary (for version) is part of the title
        if tag == "title":
            self._pagetitle = True
        
        ## description is in <pre> tag
        elif tag == "pre":
            self._in_pre = True
        
        ## div for download link and file size 
        elif tag == "div":
            for k,v in attrs:
                if k == "class" and v == "box-inner":
                    self._box_inner = True
        
        ## important fields are preceeded by <th>
        elif tag == "th":
            self._tableheader = True

        ## upload date is the 'title' attribute of a <span>
        elif tag == "span" and self._expect_date:
            self._getDateFromAttributes(attrs)
            
        ## download links
        elif tag == "a" and self._box_inner:
            for k,v in attrs:
                if k == "href":
                    self.downloadLink = v
                    self._expectDownload = False


    def handle_endtag(self, tag):
        """reset context attributes"""
        if tag == "th":
            self._tableheader = False
        elif tag == "title":
            self._pagetitle = False
        elif tag == "pre":
            self._in_pre = False
        elif tag == "span":
            self._expect_date = False
        elif tag == "div":
            if self._box_inner:
                self._box_inner = False


    def handle_data(self, data):
        """process text information"""

        ## skip layout only tags (plenty of those)
        data = data.strip()
        if data == "":
            return
        
        ## file size from main download box
        if self._box_inner == True:
            if data.endswith("exe"):
                self.filename = data
            else:
                self.filesize = data
        
        ## set next attribute based on header text
        if self._tableheader:
            if data == "Uploaded:":
                self._expect_date = True
            elif data == "Description:":
                self._expect_description = True
            elif data == "File:":
                self._expectDownload = True
        
        ## check length of data to find download description
        elif self._expect_description and self._in_pre:
            self.description = data
            self._log.info("found download description (%d bytes)" % len(data))
            self._expect_description = False
        
        elif self._pagetitle:
            self._getVersionFromTitle(data)


    def hasData(self):
        """return True if all info fields were found"""
        if self.downloadLink == None:
            self._log.info("download link is not available")
            return False
        if self.uploadedDate == None:
            self._log.info("uploaded date is not available")
            return False
        return True


    def isUpdate(self, testdate):
        """return True if testdate is older than upload date"""
        if not self.hasData():
            return False
        if type(testdate) == type(""):
            self._log.debug("converting string '%s' to struct_time" % testdate)
            testdate = time.strptime(testdate, self._dateFormat)
        if isinstance(testdate, time.struct_time):
            return testdate < self.struct_time
       

    def setFormat(self, format):
        """set format to use to parse date string"""
        self._dateFormat = format 
        self._log.info("set date format to '%s'" % self._dateFormat)






class UpdateDetailsDialog(wx.Dialog):
    """this dialog shows details of the available update"""

    def __init__(self, parent, details, id=wx.ID_ANY, title="update details"):
        wx.Dialog.__init__(self, parent, id, title)
        
        ## layout
        sizer = self.layout(details)
        self.SetSizer(sizer)
        sizer.Fit(self) 
    
    
    def description_panel(self, text, width=350):
        """return scrolled panel for description text"""
        scr_panel = scrolled.ScrolledPanel(self, wx.ID_ANY, size=(width,200))
        scr_sizer = wx.BoxSizer(wx.VERTICAL)
        scr_sizer.Add(wx.StaticText(scr_panel, wx.ID_ANY, text, size=(width-20,-1)))
        scr_panel.SetSizer(scr_sizer)
        scr_panel.SetAutoLayout(1)
        scr_panel.SetupScrolling()
        return scr_panel

  
    def layout(self, details):
        """create layout of text fields and buttons"""

        sizer = wx.BoxSizer(wx.VERTICAL)
        
        ## title
        label = wx.StaticText(self, -1,
		"Update available for %s" % details.get("filename", "wxfalsecolor.exe"))
        font_dflt = label.GetFont()
        font_big = wx.Font(font_dflt.GetPointSize()+2,
                font_dflt.GetFamily(),
                font_dflt.GetStyle(),
               L, wx.BOLD)
        label.SetFont(font_big)
        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 15)
        
        ## grid of title - value fields
        self._layo_labels(sizer, details, font_dflt15)
        
        ## divider
        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.LEFT|wx.RIGHT, 10)

        ## bottom row 
        stretch = wx.StaticText(self, wx.ID_ANY, "")
        skip = wx.Button(self, wx.ID_CANCEL, "not now")
        dload = wx.Button(self, wx.ID_OK, "download")
        dload.SetDefault()
        
        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btnsizer.Add(stretch, 1, wx.EXPAND|wx.ALL, 5)
        btnsizer.Add(skip,    0, wx.EXPAND|wx.ALL, 5)
        btnsizer.Add(dload,   0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(btnsizer, 1, wx.EXPAND|wx.ALL, 10)

        return sizer


    def _layo_labels(self, sizer, details, font_dflt):
        """create text labels for keys in details dict"""
        font_bold = wx.Font(font_dflt.GetPointSize(),
                font_dflt.GetFamily(),
                font_dflt.GetStyle(),
                wx.BOLD)
        
        ## add StaticText for header and value fieldsD)
        for header,value in [
                ("version:",     details.get('version', "n/a")),
                ("upload date:", details.get('date', "n/a")),
                ("size (Mb):",   details.get('filesize', "n/a")),
                ("description:", "")]:

            box = wx.BoxSizer(wx.HORIZONTAL)
            label1 = wx.StaticText(self, wx.ID_ANY, header, size=(85,-1))
            label1.SetFont(font_bold)
            box.Add(label1, 0, wx.ALIGTOP|wx.ALL, 5)
            if header != "description:":
                label2 = wx.StaticText(self, wx.ID_ANY, str(value), size=(150,-1))
                box.Add(label2, 1, wx.ALIGN_TOP|wx.ALL, 5)
            else:
                text = details.get('description', "no description available")
                box.Add(self._description_panel(text, 350), 1, wx.ALIGN_TOPRE|wx.ALL, 5)
            sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 10)




class UpdateManager(object):

    def __init__(self, url, date=None, format=None, logger=None):
        """create new instance of UpdateManager for url"""  
        self._log = logger if logger else DummyLogger()
        
        self.date = None
        self.error = None
        self.format = format if format else "%a %b %d %H:%M:%S %Y"
        self._parser = DownloadParser(self.format, logger=self._log)
        self.parent = None
        self.url = url
        self.text = ""

        if date:
            self.setDate()
        

    def getDownloadPage(self):
        """try to retrieve wxfalsecolor.exe download page"""
        try:
            page = urllib2.urlopen(self.url)
            self.text = page.read()
            self._log.debug("urlopen() read %d bytes from '%s'" % (len(self.text), self.url))
            page.close()
            return True
        except urllib2.HTTPError, err:
            self.error = str(err)
            self._log.error("urlopen() failedServer responded with error code %d" % err.code)
            return False
        except urllib2.URLError, err:
            self.error = "URLError: %s" % str(err.reason)
            self._log.error("urlopen() failed: '%s'" % str(err.reason))
            return False


    def parseText(self, text=""):
        """process contents of html page"""
        if text == "":
            text = self.text
        self._log.info("parsing text (%d bytes" % len(self.text))
        self._parser.feed(text)
        self._parser.close()


    def getDownloadDetails(self):
        """return download details as dict""" 
        if not self._parser.hasData():
            self._log.warning("parser has no data")
            return {}
        else:
            return self._parser.getDetailsDict()


    def logDetails(self):
        """write details of update out to debug log"""
        for k,v in self._parser.getDetailsDict().items():
            self._log.debug("> %11s : %s" % (k, str(v)[:50]))


    def showDetails(self):
        """print contents of details dict"""
        for k,v in self._parser.getDetailsDict().items():
            print "%11s : %s" % (k, str(v)[:60])
        

    def showDialog(self, parent):
        """show dialog according to update availability"""
        self.parent = parent
        available = self.updateAvailable()
        if available == True:
            self._log.info("update is available")
            self.logDetails()
            details = self.getDownloadDetails()
            return self._showDetailsDialog(details)
        elif self.error:
            self._showErrorDialog()
            return False
        else:
            self._log.info("no update available")
            self._showInfoDialog("no update", "No new updates available.\nTry again in a few weeks.")
            return True


    def _showDetailsDialog(self, details):
        """show dialog with details of the download file"""
        dlg = UpdateDetailsDialog(self.parent, details)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            self._log.debug("update accepted; showing file selector ...")
            return self.showFileSelector(details)
        else:
            self._log.info("update skipped; no download")
            return True


    def _showErrorDialog(self, title="Error during update!"):
        """show error message dialog"""
        self._log.error("error message: '%s'" % " ".join(self.error.split()))
        dlg = wx.MessageDialog(self.parent,
            "error message:\n%s" % self.error,
            title, 
            wx.OK|wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
    

    def showFileSelector(self, details):
        """on download show a file selector to save data to"""
        filedialog = wx.FileDialog(self.parent,
                          message = 'save download',
                          defaultDir = os.getcwd(),
                          defaultFile = details.get("filename", "wxfalsecolor.exe"),
                          style = wx.SAVE)
        
        if filedialog.ShowModal() != wx.ID_OK:
            self._log.info("change of mind: no file path chosen")
            return True
        
        ## start download with selected path
        path = filedialog.GetPath()
        self._log.debug("selected file name: '%s'" % path)
        self.startDownload(path, details)
        if self.error:
            self._showErrorDialog()
            return False

        ## if everything went well show good-bye message
        self._showInfoDialog("Download completed.", 
                "Enjoy the new version.\nfilepath: '%s'" % path)
        return True

    
    def _showInfoDialog(self, title="title line", info="info line"):
        """show info message dialog"""
        logmsg = "%s - %s" % (title, info)
        logmsg = " ".join(logmsg.split())
        self._log.info(logmsg)
        dlg = wx.MessageDialog(self.parent,
                info,
                title, 
                wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
    

    def startDownload(self, path, details):
        """illustrate download with progress bar dialog"""

        filename = details.get("filename", "UNKNOWN")
        self._log.info("download of '%s' to file '%s'" % (filename,path))
        url = details.get('url')
        if not url:
            self._log.error("no url for download")
            return False
        
        ## create progress dialog window
        dlg = wx.ProgressDialog("downloading file '%s'" % filename,
                "download status: 0%",
                maximum = 101,
                parent = self.parent,
                style = wx.PD_APP_MODAL|wx.PD_CAN_ABORT|wx.PD_ELAPSED_TIME)
        
        incr = IncrementalDownloader(url, dlg, logger=self._log)
        data, size = incr.download()
        dlg.Destroy()

        if data and len(data) == size:
            return self.saveData(data, path)

        elif data and len(data) != size:
            self.error = "download file incomplete"
            _showErrorDialog(self,
                    title="Error during download!",
                    info="Download file is incomplete.\nPlease try again another time.")
            return False
        
        else:
            self.error = incr.error.args[0] if incr.error else "Download failed."
            _showErrorDialog(self,
                    title="Download error!",
                    info="Download file could not be retrieved.\nPlease try again with debugging enabled to see more details.")
            return False
            

    def saveData(self, data, path):
        """write downloaded data out to file"""
        self._log.info("saving data to file '%s' (%d bytes)" % (path, len(data)))
        try:
            f = file(path, "wb")
            f.write(data)
            f.close()
            return True
        except Exception, err:
            self.error = str(err)
            if self.parent:
                self._showErrorDialog(self, "Error saving file!")
            else:
                self._log.error("Error saving file! - '%s'" % self.error.args[0])
    

    def setDateFormat(self, format):
        """set new format for date parsing"""
        self.format = format
        self._parser.setFormat(format)


    def setDate(self, date):
        """set new date to check"""
        try: 
            testdate = time.strptime(date, self.format)
            self.date = date
            return True
        except ValueError, err:
            self._log.error("error setting date: '%s'" % err.args[0])
            return False


    def updateAvailable(self, date=None):
        """check if uploaded date is newer than release date"""
        if self.error:
            return False
        if date:
            if self.setDate(date) == False:
                self._log.error("could not check date string '%s' against update date")
                return False
        if self.text == "":
            self.getDownloadPage()
            self.parseText()
        return self._parser.isUpdate(self.date)
