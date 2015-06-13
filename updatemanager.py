
import os
import json
import requests
import time
import cStringIO

from distutils.version import StrictVersion

import wx
import wx.lib.scrolledpanel as scrolled





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





class UpdateDetailsDialog(wx.Dialog):
    """this dialog shows details of the available update"""

    def __init__(self, parent, details, id=wx.ID_ANY, title="update details"):
        wx.Dialog.__init__(self, parent, id, title)
        
        ## layout
        sizer = self.layout(details)
        self.SetSizer(sizer)
        sizer.Fit(self) 
    
    
    def _description_panel(self, text, width=350):
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
                wx.BOLD)
        label.SetFont(font_big)
        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 15)
        
        ## grid of title - value fields
        self._layout_labels(sizer, details, font_dflt)
        
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


    def _layout_labels(self, sizer, details, font_dflt):
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
            box.Add(label1, 0, wx.ALIGN_TOP|wx.ALL, 5)

            if header != "description:":
                label2 = wx.StaticText(self, wx.ID_ANY, str(value), size=(150,-1))
                box.Add(label2, 1, wx.ALIGN_TOP|wx.ALL, 5)
            else:
                text = details.get('description', "no description available")
                box.Add(self._description_panel(text, 350), 1, wx.ALIGN_TOP|wx.ALL, 5)
            sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 10)





class Release(object):

    def __init__(self, dict):
        """wrapper for JSON release object to implement comparison operator"""
        self._release = dict

    @property
    def assets(self):
        return self._release['assets']

    @property
    def body(self):
        return self._release['body']

    @property
    def created_at(self):
        return self._release['created_at']

    @property
    def draft(self):
        return self._release['draft']

    @property
    def prerelease(self):
        return self._release['prerelease']

    @property
    def version(self):
        t = self._release['tag_name']
        v = t[1:] if t.startswith("v") else t
        return StrictVersion(v)
    
    def __eq__(self, other):
        return self.version == other.version

    def __ne__(self, other):
        return not self == other

    def __gt__(self, other):
        return self.version > other.version

    def __lt__(self, other):
        return self.version < other.version

    def __ge__(self, other):
        return (self > other) or (self == other)

    def __le__(self, other):
        return (self < other) or (self == other) 





class UpdateManager(object):

    def __init__(self, url="", logger=None):
        """create new instance of UpdateManager for url"""  
        
        self._log = logger if logger else DummyLogger()
        self.error = None
        self.parent = None
        self.url = ""
        self.releases = []
        self._updates = []

        if url:
            self.get_releases(url)


    def _version(self, tag_name):
        """remove leading 'v' from tag_name"""
        return tag_name[1:] if tag_name.startswith("v") else tag_name


    def find_updates(self, versionstring, include_prerelease=False):
        """filter list of releases by draft, prerelease and version tag"""

        self._log.info("check for updates ...")
        self._log.debug("-> current version='%s'" % versionstring)
        self._log.debug("-> url='%s'" % self.url)
        
        releases = [Release(r) for r in self.releases if r["assets"]] 
        releases = [r for r in releases if r.draft == False]
        if not include_prerelease:
            releases = [r for r in releases if r.prerelease == False]

        self._updates = [r for r in releases if r.version > StrictVersion(self._version(versionstring))]
        self._updates.sort()
        self._log.debug("-> found %d updates" % len(self._updates))


    def get_releases(self, url):
        """return list of releases retreived from GitHub api"""
        self.releases = []
        self.url = ""
        try:
            response = requests.get(url, verify=False)
            response.raise_for_status()
            if response.status_code == 200:
                self.releases = json.loads(response.text)
                self.url = url

        except requests.exceptions.RequestException as e:  
            self.error = e
            

    def getDownloadDetails(self):
        """return download details as dict"""

        if self._updates == []:
            self._log.info("no updates found")
            return {}

        update = self._updates[-1]
        asset = update.assets[0]
        return {'url':         asset['browser_download_url'],
                'description': update.body,
                'date':        update.created_at,
                'version':     "%s" % update.version,
                'filesize':    round(asset['size']/(1024*1024.0), 2),
                'filename':    asset['name']}


    def log_details(self):
        """write details of update out to debug log"""
        for k,v in self.getDownloadDetails().items():
            self._log.debug("> %11s : %s" % (k, str(v)[:50]))


    def print_details(self):
        """print contents of details dict"""
        for k,v in self.getDownloadDetails().items():
            print "%11s : %s" % (k, str(v)[:60])
        
            
    def saveData(self, data, path):
        """write downloaded data out to file"""
        self._log.info("saving data to file '%s' (%d bytes)" % (path, len(data)))
        try:
            with open(path, 'wb') as f:
                f.write(data)
            return True
        except Exception, err:
            self.error = str(err)
            if self.parent:
                self._showErrorDialog(self, "Error saving file!")
            else:
                self._log.error("Error saving file! - '%s'" % self.error.args[0])


    def showDialog(self, parent):
        """show dialog according to update availability"""
        self.parent = parent
        available = self.updateAvailable()
        
        if self.error:
            self._showErrorDialog()
            return False

        elif self.updateAvailable():
            self._log.info("update is available")
            self.log_details()
            self._showUpdateDialogs()

        else:
            self._log.info("no update available")
            self._showInfoDialog("no update", "No new updates available.\nTry again in a few weeks.")
            return True


    def _showUpdateDialogs(self):
        """show dialogs to show update, filepath selector and download progress"""

        details = self.getDownloadDetails()
        do_download = self._showDetailsDialog(details)
        if not do_download:
            return

        path = self._showFileSelector(details)
        if not path:
            return

        data = self._startDownload(details)
        if self.error:
            self._showErrorDialog()
            return

        if not data:
            return

        success = self.saveData(data, path)
        if success:
            self._showInfoDialog("Download completed.", 
                    "Enjoy the new version.\nfilepath: '%s'" % path)


    def _showDetailsDialog(self, details):
        """show dialog with details of the download file"""

        dlg = UpdateDetailsDialog(self.parent, details)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            self._log.debug("update accepted; showing file selector ...")
            return True
        else:
            self._log.info("update skipped; no download")
            return False


    def _showErrorDialog(self, title="Error during update!", info=""):
        """show error message dialog"""
        
        msg = info if info != "" else self.error
        self._log.error( "error message: '%s'" % " ".join(msg.split()) )
        msg = "error message:\n%s" % msg

        dlg = wx.MessageDialog(self.parent, msg, title, wx.OK|wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
    

    def _showFileSelector(self, details):
        """on download show a file selector to save data to"""
        
        filedialog = wx.FileDialog(self.parent,
                          message = 'save download',
                          defaultDir = os.getcwd(),
                          defaultFile = details.get("filename", "wxfalsecolor.exe"),
                          style = wx.SAVE)
        
        if filedialog.ShowModal() != wx.ID_OK:
            self._log.info("change of mind: no file path chosen")
            return False
        
        ## start download with selected path
        path = filedialog.GetPath()
        self._log.debug("selected file name: '%s'" % path)
        return path

    
    def _showInfoDialog(self, title="title line", info="info line"):
        """show info message dialog"""
        
        logmsg = "%s - %s" % (title, info)
        logmsg = " ".join(logmsg.split())
        self._log.info(logmsg)

        dlg = wx.MessageDialog(self.parent, info, title, wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()


    def _startDownload(self, details):
        """illustrate download with progress bar dialog"""
        
        filename = details.get("filename", "UNKNOWN")
        url = details.get('url')
        self._log.debug("beginning download of '%s'" % url)
        
        ## create progress dialog window
        dlg = wx.ProgressDialog("downloading file '%s'" % filename,
                "download status: 0%",
                maximum = 101,
                parent = self.parent,
                style = wx.PD_APP_MODAL|wx.PD_CAN_ABORT|wx.PD_ELAPSED_TIME)
        
        data, content_length = self._download(url, dlg)
        dlg.Destroy()

        if content_length == -1:
            ## download interruped by user
            self._log.info("download canceled by user")
            return False

        if self.error:
            return False

        if len(data) != content_length:
            self._log.warning("download incomplete: retrieved=%d  - expected=%d" % (len(data), content_length))
            return False

        self._log.info("download complete")
        return data


    def _download(self, url, dlg):
        """download data and update ProgressDialog; return data and expected length"""

        try:
            r = requests.get(url, stream=True, verify=False)
            content_length = int(r.headers['content-length'])
            current_length = 0
        except requests.exceptions.RequestException as e:
            self.error = e
            return (None, 0)

        io = cStringIO.StringIO()
        for chunk in r.iter_content(chunk_size=1024*128): 
            if chunk: # filter out keep-alive new chunks

                io.write(chunk)

                current_length += len(chunk)
                percent = float(current_length) / content_length
                percent = round(percent*100, 2)
                
                (keepGoing, foo) = dlg.Update(int(percent), "download status: %d%%" % percent)
                
                ## close dialog and IO memory file
                if keepGoing == False:
                    dlg.Destroy()
                    io.close()
                    return (None,-1)

        ## close dialog and IO return data and expected length of data
        data = io.getvalue()
        io.close()
        return (data, content_length)


    def updateAvailable(self):
        """check if uploaded """
        if self.error:
            return False
        if not self._updates:
            return False
        return True

