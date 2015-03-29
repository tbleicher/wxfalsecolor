#!/usr/bin/env python

## wxfalsecolor.py - main file of wxfalsecolor
##
## $Id$
## $URL$

VERSION=0.51
RELEASE_DATE = "Thu Dec 13 23:30:20 2012"

LICENSE="""Copyright 2010 Thomas Bleicher. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

   1. Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in
      the documentation and/or other materials provided with the
      distribution.

THIS SOFTWARE IS PROVIDED BY THOMAS BLEICHER ''AS IS'' AND ANY
EXPRESSOR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED.

IN NO EVENT SHALL THOMAS BLEICHER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation
are those of the authors and should not be interpreted as representing
official policies, either expressed or implied, of Thomas Bleicher."""


import os
import sys
import cStringIO
import logging
import time
import traceback

import wx
from wx.lib.wordwrap import wordwrap

from config import WxfcConfig
from controlpanels import FoldableControlsPanel
from falsecolor2 import FalsecolorOptionParser, InterfaceBase
from imagepanel import ImagePanel
from rgbeimage import RGBEImage, WX_IMAGE_FORMATS, WX_IMAGE_WILDCARD
from updatemanager import UpdateManager


DATE_FORMAT = "%a %b %d %H:%M:%S %Y"


class HeaderDialog(wx.Frame):
    """frame to display Radiance image headers"""

    def __init__(self, parent, header1):

        wx.Frame.__init__(self, parent, wx.ID_ANY, "Image Header")
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        scroll1, maxw, height = self.addTextWindow(header1)
        sizer.Add(scroll1, proportion=1, flag=wx.EXPAND|wx.ALL, border=10) 

        button = wx.Button(self, wx.ID_ANY, "Close")
        self.Bind(wx.EVT_BUTTON, self.destroy)
        sizer.Add(button, proportion=0, flag=wx.ALIGN_CENTER|wx.ALL, border=10) 
        height += 120 ## allow space for borders on Windows

        if maxw > 900:
            maxw = 800
        if height > 800:
            height = 400
        self.SetSizer(sizer)
        self.SetSize((maxw+40,height))


    def addTextWindow(self, text):
        """create new scrolled text window for header"""
        scroll = wx.ScrolledWindow(self, wx.ID_ANY)
        scroll.SetBackgroundColour(wx.WHITE)
        
        cachedLines = []
        y = 0
        maxw = 0
        for line in text.split("\n"):
            st = wx.StaticText(scroll, -1, "%s" % line, pos=wx.Point(0,y))
            if line == "modified:":
                st.SetForegroundColour(wx.Colour(0,0,255))
            if line in cachedLines:
                st.SetForegroundColour(wx.Colour(127,127,127))
            cachedLines.append(line)
            w,h = st.GetSizeTuple()
            maxw = max(maxw,w)
            dy = h + 2
            y += dy
        y -= dy
        scroll.SetScrollbars(1,1,maxw,y)
        return scroll,maxw,y


    def destroy(self, evt):
        self.Destroy()



class SplitStatusBar(wx.StatusBar):
    """status bar with embedded StaticText to display zoom level"""

    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent, -1)
        self.SetFieldsCount(2)
        self.SetStatusWidths([-6,-1])
        self._size_changed = False
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        
        ## self.SetStatusText("", 1) caused exception "pure virutal method called"
        ## workaround: show a StaticText on top of 2nd field
        self._zoom = wx.StaticText(self, -1, "zoom 1:1", style=wx.ALIGN_RIGHT)
    
    def OnIdle(self, evt):
        """reposition if necessary"""
        if self._size_changed:
            self.reposition()

    def OnSize(self, evt):
        """cause recalculation of StaticText position"""
        self.reposition()
        self._size_changed = True

    def reposition(self):
        """reposition StaticText element (zoom)"""
        rect = self.GetFieldRect(1)
        self._zoom.SetPosition((rect.x, rect.y))
        self._zoom.SetSize((rect.width-10, rect.height))
        self._size_changed = False

    def setZoom(self, zoom):
        """update label of StaticText"""
        s = "zoom 1:%.1f" % zoom
        self._zoom.SetLabel(s)



class WxfcApp(wx.App, InterfaceBase):

    def __init__(self, *args, **kwargs):
        """set up logger and config before wx.App"""
        self._log = self._initLog(sys.argv[0])
        self.setDebugLevel()
        self._config = WxfcConfig(logger=self._log)
        wx.App.__init__(self, *args, **kwargs)
        

    def OnInit(self):
        """create and show main window"""
        self.main = WxfcFrame(None, self, logger=self._log, config=self._config)
        self.main.Show()
        self.SetTopWindow(self.main)
        wx.CallAfter(self.after_show)
        return True


    def after_show(self):
        """parse cmd line arguments and check for updates"""
        self.main.process_cmd_line_args()
        ## check updates
        self.check_auto_update()

    
    def check_auto_update(self):
        """check config for update interval and start UpdateManager"""
        ## get interval (in days) for automatic update check
        interval = 0
        if self._config.has_option("Update", "interval"):
            interval = self._config.getint("Update", "interval")
        if interval == 0:
            ## 0 interval means: don't check for updates automatically
            self._log.debug("automatic update checks disabled")
            return
        
        ## get time of last update check
        if self._config.has_option("Update", "last_check_date"):
            last_string = self._config.get("Update", "last_check_date")
        else:
            self._log.debug("no time stamp for last update check found")
            last_string = time.strftime(DATE_FORMAT)
            self._config.set("Update", "last_check_date", last_string)

        ## convert date stamp to seconds
        try: 
            last_check = time.mktime(time.strptime(last_string, DATE_FORMAT))
        except ValueError, err:
            self._log.error("error parsing last update check date ('%s'): '%s'" % 
                (date_string, err.args[0]))
            self._config.set("Update", "last_check_date", time.strftime(DATE_FORMAT))
            return False
        
        ## check for updates if last update was too long ago
        next_check = last_check + (interval*24*60*60)
        if time.time() > next_check:
            self._log.info("automatic update check (last check: %s)" % last_string)
            self.check_for_update()
        else:
            days = (next_check-time.time()) / (24*60*60)
            self._log.debug("next update in %d days" % days)
        

    def check_for_update(self, event=None):
        """start UpdateManager to check google project page for update"""
        UPDATE_URL = "http://code.google.com/p/pyrat/downloads/detail?name=wxfalsecolor.exe"
        self._log.info("check for updates ...")
        self._log.debug("-> version='%.2f'" % VERSION)
        self._log.debug("-> date='%s'" % RELEASE_DATE)
        self._log.debug("-> url='%s'" % UPDATE_URL)
        um = UpdateManager(UPDATE_URL, logger=self._log)
        um.setDate(RELEASE_DATE)
        if event or um.updateAvailable():
            if um.showDialog(self.main) == True:
                ## update was successful or skipped by user
                self._config.set("Update", "last_check_date", time.strftime(DATE_FORMAT))


    def exit(self, error=None):
        """close logger and exit"""
        if error:
            self._log.error(str(error))
        self._config.save_changes()
        logging.shutdown()
        self.main.Close()





class WxfcOptionParser(FalsecolorOptionParser):
    """extend option parser class with wxfc specific options"""
    
    def __init__(self, logger=None, args=[]):
        FalsecolorOptionParser.__init__(self, logger, args)
        
        ## extend validators
        self.validators["-nofc"] = ("_NOFC", self._validateTrue, False)

    def get(self, k):
        """return value of self._settings[k]"""
        return self._settings.get(k)
    
    def get_options_as_args(self):
        """quick hack to allow passing of options as args list"""
        args = []
        for opt,v in self.validators.items():
            if self._settings.has_key(v[0]):
                if v[0] in ["redv", "grnv", "bluv"] and "-spec" not in args:
                    args.append("-spec")
                elif v[0] == 'docont':
                    if self._settings[v[0]] == "a":
                        args.append("-cl")
                    elif self._settings[v[0]] == "b":
                        args.append("-cb")
                else:
                    args.append(opt)
                    value = self._settings[v[0]]
                    if value is True:
                        pass
                    else:
                        args.append(self._value_to_arg(value,v[1]))
        return args

    def _value_to_arg(self, v, validator):
        if type(v) == type(""):
            return v
        elif validator == self._validateInt:
            return "%d" % v
        elif validator == self._validateFloat:
            s = "%.6f" % v
            return s.rstrip("0") 
        elif validator == self._validateScale:
            s = "%.6f" % v
            return s.rstrip("0") 
    
    def has_fc_option(self):
        """return True if a falsecolor option is set"""
        for opt,v in self.validators.items():
            if opt in ["-d", "-v", "-df", "-i"]:
                pass
            elif self._settings.has_key(v[0]):
                return True

    def has_option(self, k):
        """check self._settings for option 'k'"""
        if self._settings.get(k) != None:
            return True

    def _searchBinary(self, appname):
        """try to find <appname> in search path"""
        #XXX unused and better in config?
        paths = os.environ['PATH']
        extensions = ['']
        try:
            if os.name == 'nt':
                extensions = os.environ['PATHEXT'].split(os.pathsep)
            for path in paths.split(os.pathsep):
                for ext in extensions:
                    binpath = os.path.join(path,appname) + ext
                    if os.path.exists(binpath):
                        return binpath
        except Exception, err:
            self._log.exception(err)
            self._log.error(traceback.format_exc()) 
            return False
        ## if nothing was found return False
        return False

    
    



class WxfcFrame(wx.Frame):
    """main wxfalsecolor frame"""

    def __init__(self, parent, wxapp, logger, config):
        wx.Frame.__init__(self, parent, title="wxFalsecolor - Radiance Picture Viewer")
        
        self._log = logger
        self.parser = WxfcOptionParser(logger=self._log)
        self._config = config 
        self.wxapp = wxapp 
        self.imagepanel = ImagePanel(self)
        self.rgbeImg = None
        self.img = None
        self.path = ""
        self.filename = ""
        self.loadingCanceled = False

        ## layout and show main window
        self._layout()
        #TODO: self._addMenu()
        self.Size = (800,600)
        self.Show()
        
        
    def process_cmd_line_args(self):
        """check arguments, load and convert image"""
        ## check command line args
        if self.parser.parseOptions(sys.argv[1:]) != True:
            self.showError(self.parser.error)
            return
        ## load image if present
        if self.parser.has_option('picture'):
            self.loadImage(self.parser.get('picture'))
            self.Update()
        if self.parser.has_fc_option() == True:
            self.doFalsecolor()


    def _addFileButtons(self, panel):
        """create top buttons"""
        self.loadButton = wx.Button(panel, wx.ID_ANY, label='open HDR')
        self.loadButton.Bind(wx.EVT_LEFT_DOWN, self.onLoadImage)
        self.panelSizer.Add(self.loadButton, proportion=0, flag=wx.EXPAND|wx.ALL, border=5 )
        
        self.saveButton = wx.Button(panel, wx.ID_ANY, label='save image')
        self.saveButton.Bind(wx.EVT_LEFT_DOWN, self.onSaveImage)
        self.saveButton.Disable()
        self.panelSizer.Add(self.saveButton, proportion=0, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5 )
        
        spacepanel = wx.Panel(panel,wx.ID_ANY,size=(-1,5))
        self.panelSizer.Add(spacepanel, proportion=0, flag=wx.EXPAND)


    def _addMenu(self):
        """add menu to frame (disabled)"""
        return
        self.menubar = wx.MenuBar()
        self.SetMenuBar(self.menubar)
        self.fileMenu = wx.Menu()
        self.menubar.Append(self.file, '&File')
        self.fileOpen = self.file.Append(wx.ID_ANY, '&Open file')
        self.Bind(wx.EVT_MENU, self.onLoadImage, self.fileOpen)


    def _doButtonLayout(self):
        """create buttons"""
        panel = wx.Panel(self, style=wx.RAISED_BORDER)

        self.panelSizer = wx.BoxSizer(wx.VERTICAL)
        ## 'load' and 'save' buttons 
        self._addFileButtons(panel)
        
        ## foldable controls panel
        self._foldpanel = FoldableControlsPanel(panel, self, wx.ID_ANY)
        self.lablecontrols = self._foldpanel.lablecontrols
        self.fccontrols = self._foldpanel.fccontrols
        self.displaycontrols = self._foldpanel.displaycontrols
        self.panelSizer.Add(self._foldpanel, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        
        ## 'quit' button
        quitbutton = wx.Button(panel, wx.ID_EXIT, label='quit')
        quitbutton.Bind(wx.EVT_LEFT_DOWN,self.onQuit)
        self.panelSizer.Add(quitbutton, proportion=0, flag=wx.EXPAND|wx.ALL|wx.ALIGN_BOTTOM, border=10)
        panel.SetSizer(self.panelSizer)
        return panel


    def check_for_update(self, event=None):
        self.wxapp.check_for_update(event)


    def doFalsecolor(self, args=[]):
        """convert Radiance RGBE image to wx.Bitmap"""
        self._log.debug("doFalsecolor(%s)" % str(args))
        if not args:
            args = self.parser.get_options_as_args()
        if "-nofc" in args or self.imagepanel.doFalsecolor(args[:]) == True:
            self.fccontrols.setFromArgs(args[:]) 
            self.displaycontrols.reset()
            return True
        else:
            return False


    def doPcond(self, args):
        """apply pcond args to image"""
        if self.imagepanel.doPcond(args) == True:
            self.fccontrols.reset()
            return True
        else:
            return False


    def exit(self, error=None):
        """close logger and exit"""
        if error:
            self._log.error(str(error))
        self._config.save_changes()
        logging.shutdown()
        self.Close()

    
    def expandControlPanel(self, idx):
        """expand control panel with index idx"""
        self._foldpanel.expand(idx)


    def formatNumber(self, n):
        """use FalsecolorImage formating for consistency"""
        if self.rgbeImg:
            return self.rgbeImg.formatNumber(n)
        else:
            return str(n)


    def getLableText(self):
        """return text of lable text box"""
        return self.lablecontrols.getLableText()


    def getRGBVAt(self, pos):
        """return pixel value at position"""
        if self.rgbeImg:
            return self.rgbeImg.getRGBVAt(pos)
        else:
            return (-1,-1,-1,-1)


    def getRGBVAverage(self, start, end):
        """return average pixel value for rectangle"""
        if self.rgbeImg:
            return self.rgbeImg.getRGBVAverage(start,end)
        else:
            return (-1,-1,-1,-1)

    
    def _layout(self):
        """main layout of controls and image panel"""
        ## buttons
        panel = self._doButtonLayout()
        ## image - buttons layout
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(panel, proportion=0, flag=wx.EXPAND)
        self.sizer.Add(self.imagepanel, proportion=1, flag=wx.EXPAND)
        self.SetSizer(self.sizer)
        ## status bar
        self.statusbar = SplitStatusBar(self)
        self.SetStatusBar(self.statusbar)


    def loadImage(self, path, args=[]):
        """create instance of falsecolor image from <path>"""
        self._log.info("loadImage(%s)" % path)
        self.reset()
        
        self.rgbeImg = RGBEImage(self, self._log, ["-i", path])
        self.rgbeImg.readImageData(path)
        
        if self.rgbeImg.error:
            msg = "Error loading image:\n%s" % self.rgbeImg.error
            self.showError(msg)
            self.rgbeImg = None
            return False
        else:
            self.setPath(path)
            self.saveButton.Enable()
            self._loadImageData()
            self.imagepanel.update(self.rgbeImg)
            return True


    def _loadImageData(self):
        """load image data of small images immediately"""
        ## TODO: evaluate image data (exclude fc images)
        max_size = self._config.getint("lables", "max_data_load", 1000000)
        if max_size == 0:
            self._log.info("automatic data loading disabled")
            self.lablecontrols.reset()
            return

        ## compare image resolution against max_size
        x,y = self.rgbeImg.getImageResolution()
        if x*y <= max_size:
            ## call OnShowValues with fake event
            self.lablecontrols.OnShowValues(-1)
        else:
            self.statusbar.SetStatusText("confirm 'load data'")
            msg = "This is a large image.\nDo you want to load image data now?"
            dlg = wx.MessageDialog(self, message=msg, caption="Load data?", style=wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES:
                self.lablecontrols.OnShowValues(-1)
            else:
                self.lablecontrols.reset()
                self.statusbar.SetStatusText("skipping 'load data'.")


    def loadValues(self):
        """load luminance/illuminance data from image"""
        return self.rgbeImg.hasArrayData(self)


    def onImagePanelClick(self):
        """action on click on imagepanel"""
        if self.imagepanel.hasLables():
            self.lablecontrols.loadClearButton.Enable()
        elif self.lablecontrols.loadClearButton.GetLabelText() == "load data":
            self.lablecontrols.loadClearButton.Enable()
        else:
            self.lablecontrols.loadClearButton.Disable()


    def onLoadImage(self,event):
        """load new Radiance RGBE image"""
        filedialog = wx.FileDialog(self,
                          message = 'Choose an image to open',
                          defaultDir = '',
                          defaultFile = '',
                          wildcard = 'Radiance Image Files (*.hdr,*.pic)|*.hdr;*.pic|all files |*.*',
                          style = wx.OPEN)
        if filedialog.ShowModal() == wx.ID_OK:
            path = filedialog.GetPath()
            self.loadImage(path)


    def onQuit(self, event):
        """hasta la vista"""
        self.exit()


    def onSaveImage(self, event):
        """save bmp image to file"""
        dirname, filename = os.path.split(self.path)
        filebase = os.path.splitext(filename)[0]
        #formats = "|".join(["HDR file|*.hdr", WX_IMAGE_WILDCARD, "PIC (old)|*.pic"])
        formats = "|".join(["HDR file|*.hdr", WX_IMAGE_WILDCARD, "PPM file|*.ppm"])
        filedialog = wx.FileDialog(self,
                          message = 'save image',
                          defaultDir = dirname,
                          defaultFile = filebase + '.hdr',
                          wildcard = formats,
                          style = wx.SAVE)
        if filedialog.ShowModal() == wx.ID_OK:
            path = filedialog.GetPath()
            result = self.rgbeImg.saveToFile(path)
            if result != True:
                msg = "Error saving image:\n" + self.rgbeImg.error
                self.showError(msg)
            else:
                self.statusbar.SetStatusText("saved file '%s'" % path)


    def reset(self):
        """reset array to inital (empty) values"""
        self.displaycontrols.reset()
        self.imagepanel.clearLabels()
        self.fccontrols.reset()
        if self.rgbeImg:
            self.imagepanel.update(self.rgbeImg)
            if self.rgbeImg.isIrridiance():
                self.fccontrols.reset("Lux")


    def setPath(self, path):
        """update frame with new image path"""
        self.path = path
        self.filename = os.path.split(path)[1]
        self.SetTitle("wxFalsecolor - '%s'" % self.filename)


    def showAboutDialog(self, event=None):
        """show dialog with license etc"""
        info = wx.AboutDialogInfo()
        info.Name = "wxfalsecolor"
        info.Version = "v%.2f (rREV)" % VERSION  # placeholder for build script 
        info.Copyright = "(c) 2010 Thomas Bleicher"
        info.Description = "cross-platform GUI frontend for falsecolor"
        info.WebSite = ("http://sites.google.com/site/tbleicher/radiance/wxfalsecolor", "wxfalsecolor home page")
        info.Developers = ["Thomas Bleicher", "Axel Jacobs"]
        lines = [" ".join(line.split()) for line in LICENSE.split("\n\n")]
        info.License = wordwrap("\n\n".join(lines), 500, wx.ClientDC(self))
        wx.AboutBox(info)


    def showError(self, msg):
        """show dialog with error message"""
        self._log.error(" ".join(msg.split()))
        self.statusbar.SetStatusText(msg)
        dlg = wx.MessageDialog(self, message=msg, caption="Error", style=wx.OK|wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()

    
    def showHeaders(self, event=None):
        """display image headers in popup dialog"""
        if not self.rgbeImg:
            return
        header = self.rgbeImg.getHeader()
        if header == False:
            self.showError("Image header not available!")
            return
        header2 = self.rgbeImg.getDataHeader()
        if header2 and header != header2:
            header += "\n\nmodified:\n"
            header += header2

        ## create new dialog window        
        dlg = HeaderDialog(self, header)
        dlg.Show()


    def showPixelValueAt(self, pos):
        """set pixel position of mouse cursor"""
        value = ""
        if self.rgbeImg:
            r,g,b,v = self.rgbeImg.getRGBVAt(pos)
            if r > 0:
                value = "rgb=(%.3f,%.3f,%.3f)" % (r,g,b)
                if v > 0 and self.rgbeImg.isIrridiance():
                    value = "%s  value=%s lux" % (value,self.formatNumber(v)) 
            self.statusbar.SetStatusText("'%s':   x,y=(%d,%d)   %s" % (self.filename, pos[0],pos[1], value))




if __name__ == "__main__":   
    app = WxfcApp(redirect = False)
    try:
        app.MainLoop()
    except Exception, e:
        logging.exception(e)
        logging.error(traceback.format_exc())
        logging.shutdown()

