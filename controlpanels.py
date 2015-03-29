##
## controlpanels.py - part of wxfalsecolor
##
## $Id$
## $URL$

import os
import wx
import wx.lib.foldpanelbar as fpb
# work around for bug in some new wxPython versions
if not 'FPB_DEFAULT_STYLE' in dir(fpb):
    fpb.FPB_DEFAULT_STYLE = fpb.FPB_VERTICAL
import wx.lib.buttons as buttons



class BaseControlPanel(wx.Panel):

    def __init__(self, parent, wxapp, *args, **kwargs):
        """save wxapp and call self.layout() to create buttons"""
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.wxapp = wxapp
        self._log = wxapp._log
        self._cmdLine = None
        self.layout()
    
    def createCenteredGrid(self, layout):
        """arrange controls in centered grid sizer"""
        ## create grid sizer
        grid = wx.GridBagSizer(2,2)
        for r,row in enumerate(layout):
            c1,c2 = row
            if c2:
                grid.Add( c1, (r,0),        flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
                grid.Add( c2, (r,1),        flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
            else:
                grid.Add( c1, (r,0), (1,2), flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
       
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.Panel(self), proportion=1, flag=wx.EXPAND,border=0)
        sizer.Add(grid)
        sizer.Add(wx.Panel(self), proportion=1, flag=wx.EXPAND,border=0)
        self.SetSizer(sizer)
        self.SetInitialSize()

    def layout(self):
        """create buttons here"""
        pass        




class FalsecolorControlPanel(BaseControlPanel):

    def __init__(self, parent, wxapp, *args, **kwargs):
        self.positions = ['WS','W','WN','NW','N','NE','EN','E','ES','SE','S','SW']
        BaseControlPanel.__init__(self, parent, wxapp, *args, **kwargs)

    def layout(self):
        """create control elements in grid layout"""
        ## type choice button
        self.fc_type = wx.Choice(self, wx.ID_ANY, choices=["color fill", "c-lines", "c-bands"])
        self.fc_type.SetStringSelection("color fill")
        self.Bind(wx.EVT_CHOICE, self.updateFCButton, self.fc_type)
        
        self.legpos = wx.Choice(self, wx.ID_ANY, choices=self.positions, size=(60,-1))
        self.legpos.SetStringSelection("WS")
        self.Bind(wx.EVT_CHOICE, self.updatePosition, self.legpos)
        self.inside = wx.CheckBox(self, wx.ID_ANY, 'in')
        self.Bind(wx.EVT_CHECKBOX, self.updateFCButton, self.inside)
        
        self.label = wx.TextCtrl(self, wx.ID_ANY, "cd/m2", size=(50,-1))
        self.scale = wx.TextCtrl(self, wx.ID_ANY, "1000",  size=(50,-1))
        self.steps = wx.TextCtrl(self, wx.ID_ANY, "8",     size=(50,-1))
        self.logv  = wx.TextCtrl(self, wx.ID_ANY, "2",     size=(50,-1))
        self.maskv = wx.TextCtrl(self, wx.ID_ANY, "0.001", size=(50,-1))

        self.fc_log  = wx.CheckBox(self, wx.ID_ANY, 'log')
        self.fc_mask = wx.CheckBox(self, wx.ID_ANY, 'mask')
        self.fc_col  = wx.CheckBox(self, wx.ID_ANY, 'old colours')
        self.fc_extr = wx.CheckBox(self, wx.ID_ANY, 'show extremes')
        self.fc_zero = wx.CheckBox(self, wx.ID_ANY, '0 based leg')
        
        self.legW = wx.TextCtrl(self, wx.ID_ANY, "100", size=(50,-1))
        self.legH = wx.TextCtrl(self, wx.ID_ANY, "200", size=(50,-1))
        
        ## 'hidden' option for background image
        self._background = ""

        ## 'falsecolor' button
        self.doFCButton = buttons.GenButton(self, wx.ID_ANY, label='falsecolor')
        self.doFCButton.Bind(wx.EVT_LEFT_DOWN, self.doFalsecolor)
        self.doFCButton.Disable()

        ## bind events
        self.Bind(wx.EVT_TEXT, self.updateFCButton, self.label)
        self.Bind(wx.EVT_TEXT, self.updateFCButton, self.scale)
        self.Bind(wx.EVT_TEXT, self.updateFCButton, self.steps)
        self.Bind(wx.EVT_TEXT, self.updateFCButton, self.logv)
        self.Bind(wx.EVT_TEXT, self.updateFCButton, self.maskv)
        self.Bind(wx.EVT_TEXT, self.updateFCButton, self.legW)
        self.Bind(wx.EVT_TEXT, self.updateFCButton, self.legH)
        self.Bind(wx.EVT_CHECKBOX, self.updateFCButton, self.fc_log)
        self.Bind(wx.EVT_CHECKBOX, self.updateFCButton, self.fc_mask)
        self.Bind(wx.EVT_CHECKBOX, self.updateFCButton, self.fc_col)
        self.Bind(wx.EVT_CHECKBOX, self.updateFCButton, self.fc_extr)
        self.Bind(wx.EVT_CHECKBOX, self.updateFCButton, self.fc_zero)
        
        layout = [(self.fc_type,                              None),
                  (self.inside,                               self.legpos),
                  (wx.Panel(self,wx.ID_ANY,size=(-1,10)),     None),
                  (wx.StaticText(self, wx.ID_ANY, "legend:"), self.label),
                  (wx.StaticText(self, wx.ID_ANY, "scale:"),  self.scale),
                  (wx.StaticText(self, wx.ID_ANY, "steps:"),  self.steps),
                  (wx.Panel(self,wx.ID_ANY,size=(-1,10)),     None),
                  (self.fc_log,                               self.logv),
                  (self.fc_mask,                              self.maskv),
                  (self.fc_col,                               None),
                  (self.fc_extr,                              None),
                  (self.fc_zero,                              None),
                  (wx.Panel(self,wx.ID_ANY,size=(-1,10)),     None),
                  (wx.StaticText(self, wx.ID_ANY, "leg-w:"),  self.legW),
                  (wx.StaticText(self, wx.ID_ANY, "leg-h:"),  self.legH),
                  (wx.Panel(self,wx.ID_ANY,size=(-1,10)),     None),
                  (self.doFCButton,                           None),
                  (wx.Panel(self,wx.ID_ANY,size=(-1,5)),      None)]
        
        ## arrange in grid 
        self.createCenteredGrid(layout)


    def doFalsecolor(self, event):
        """start conversion to falsecolor and update button"""
        args = self.getFCArgs()
        if self.wxapp.doFalsecolor(args) == True:
            self._cmdLine = " ".join(self.getFCArgs())
            self.doFCButton.SetLabel("update fc")
            self.doFCButton.Disable()
            self.doFCButton.SetBackgroundColour(wx.WHITE)
        else:
            self.doFCButton.SetLabel("update fc")
            self.doFCButton.Enable()
            self.doFCButton.SetBackgroundColour(wx.Colour(255,140,0))
        self.doFCButton.Refresh()


    def enableFC(self, text=""):
        """enable and update doFCButton"""
        self._log.debug("enableFC(): text='%s'" % text)
        self.doFCButton.Enable()
        if text != "":
            self.doFCButton.SetLabel(text)
        self.doFCButton.Refresh()


    def getFCArgs(self):
        """collect command line args as list"""
        args = []
        #args.extend(["-t", "./tempdir"])
        
        if self.fc_type.GetCurrentSelection() > 0:
            args.append(["", "-cl", "-cb"][self.fc_type.GetCurrentSelection()])
        
        position = self.positions[self.legpos.GetCurrentSelection()]
        if self.inside.GetValue():
            position = "-" + position
        args.extend(["-lp", position])
        args.extend(["-lw", self.legW.GetValue()])
        args.extend(["-lh", self.legH.GetValue()])

        args.extend(["-l", self.getFCLableText()])
        args.extend(["-s", self.scale.GetValue()])
        args.extend(["-n", self.steps.GetValue()])
        
        if self.fc_log.GetValue():
            args.extend(["-log", self.logv.GetValue()])
        if self.fc_mask.GetValue():
            args.extend(["-mask", self.maskv.GetValue()])
        if self.fc_col.GetValue():
            args.append("-spec")
        if self.fc_extr.GetValue():
            args.append("-e")
        if self.fc_zero.GetValue():
            args.append("-z")
        if self._background != "":
            args.extend(["-p", self._background])
            
        self._log.debug("getFCArgs(): args=%s" % str(args))
        return args        


    def getFCLableText(self):
        """return value of label text box"""
        return self.label.GetValue()


    def reset(self, label="cd/m2"):
        """reset controls to initial values"""
        self._log.debug("resetting falsecolor controls ...")
        self.enableFC("convert fc")
        self.label.SetValue(label)
        
        self.fc_type.SetSelection(0)
        self.fc_log.SetValue(False)
        self.fc_mask.SetValue(False)
        self.fc_col.SetValue(False)
        self.fc_extr.SetValue(False)
        self.fc_zero.SetValue(False)
        
        self.scale.SetValue("1000")
        self.steps.SetValue("8")
        
        self.legpos.SetStringSelection("WS")
        self.inside.SetValue(False)
        self.legW.SetValue("100")
        self.legH.SetValue("200")

        self._background = ""
        self._cmdLine = None
        

    def setFromArgs(self, args):
        """set control values from command line args"""
        args.append("#")
        args.reverse()
        ignore = ["-i", "-ip", "-df", "-t", "-r", "-g", "-b"]
        set_cmdline = True
        
        while args:
            arg = args.pop()
            self._log.debug("setFromArgs() arg='%s'" % arg)
            if arg == "#":
                pass
            elif arg == "-d":
                pass
            elif arg == "-v":
                pass
            elif arg == "-m":
                pass
            elif arg == "-nofc":
                set_cmdline = False
            elif arg in ignore:
                v = args.pop()

            elif arg == "-p":
                self._background = self.validatePath(args.pop())
            elif arg == "-cl":
                self.fc_type.SetSelection(1)
            elif arg == "-cb":
                self.fc_type.SetSelection(2)
            elif arg == "-e":
                self.fc_extr.SetValue(True)
            elif arg == "-l":
                self.label.SetValue(args.pop())
            elif arg == "-log":
                self.fc_log.SetValue(True)
                self.logv.SetValue(args.pop())
            elif arg == "-lh":  
                self.legH.SetValue(args.pop())
            elif arg == "-lw":
                self.legW.SetValue(args.pop())
            elif arg == "-lp":
                v = args.pop()
                if v.startswith("-"):
                    self.inside.SetValue(True)
                    v = v[1:]
                self.legpos.SetStringSelection(v)
            elif arg == "-mask":
                self.fc_mask.SetValue(True)
                self.maskv.SetValue(args.pop()) 
            elif arg == "-n":    
                self.steps.SetValue(args.pop())
            elif arg == "-s":    
                self.scale.SetValue(args.pop())
            elif arg == "-spec":
                self.fc_col.SetValue(True)
            elif arg == "-z":
                self.fc_zero.SetValue(True)
        
        if set_cmdline:
            self._cmdLine = " ".join(self.getFCArgs())
        else:
            ## _cmdLine needs to be set for updateFCButton
            self._cmdLine = ""

        ## set button label
        self.wxapp.expandControlPanel(1)
        self.updateFCButton()
        #self.doFCButton.Disable()


    def updateFCButton(self, event=None):
        """set label of falsecolor button to 'update'"""
        if self._cmdLine == None:
            return 
        newCmd = " ".join(self.getFCArgs())
        if self._cmdLine != newCmd:
            self.doFCButton.SetLabel("update fc")
            self.doFCButton.Enable()
            self.doFCButton.SetBackgroundColour(wx.Colour(255,140,0))
        else:
            self.doFCButton.Disable()
            self.doFCButton.SetBackgroundColour(wx.WHITE)
        self.doFCButton.Refresh()


    def updatePosition(self, event):
        """update height and width when position changes"""
        pos = self.positions[self.legpos.GetCurrentSelection()]
        pos = pos.replace("-", "")
        if pos.startswith("W") or pos.startswith("E"):
            self.legW.SetValue("100")
            self.legH.SetValue("200")
        else:
            self.legW.SetValue("400")
            self.legH.SetValue("50")


    def validatePath(self, path):
        """return path if file exists, otherwise empty string"""
        if os.path.isfile(path):
            return path
        else:
            return ""


class DisplayControlPanel(BaseControlPanel):
    
    def layout(self):
        """creates layout of ximage buttons"""

        self.acuity   = wx.CheckBox(self, wx.ID_ANY, 'acuity loss')
        self.glare    = wx.CheckBox(self, wx.ID_ANY, 'veiling glare')
        self.contrast = wx.CheckBox(self, wx.ID_ANY, 'contrast')
        self.colour   = wx.CheckBox(self, wx.ID_ANY, 'color loss')
        
        self.exposure = wx.CheckBox(self, wx.ID_ANY, 'exp')
        self.expvalue = wx.TextCtrl(self, wx.ID_ANY, "+0", size=(50,-1))
        self.linear   = wx.CheckBox(self, wx.ID_ANY, 'linear response')
        self.centre   = wx.CheckBox(self, wx.ID_ANY, 'centre-w. avg')
        
        self.dsprange = wx.CheckBox(self, wx.ID_ANY, 'display range')
        self.dsp_min  = wx.TextCtrl(self, wx.ID_ANY, "0.5", size=(40,-1))
        self.dsp_max  = wx.TextCtrl(self, wx.ID_ANY, "200", size=(40,-1))
        dsp_box = wx.BoxSizer(wx.HORIZONTAL)
        dsp_box.Add(self.dsp_min, proportion=0, flag=wx.EXPAND|wx.ALL, border=0)
        dsp_box.Add(wx.StaticText(self, wx.ID_ANY, "to", style=wx.ALIGN_CENTER), proportion=1, flag=wx.EXPAND|wx.Left|wx.RIGHT, border=0)
        dsp_box.Add(self.dsp_max, proportion=0, flag=wx.EXPAND|wx.ALL, border=0)
        
        self.Bind(wx.EVT_CHECKBOX, self.updatePcondButton, self.acuity)
        self.Bind(wx.EVT_CHECKBOX, self.updatePcondButton, self.glare)
        self.Bind(wx.EVT_CHECKBOX, self.updatePcondButton, self.contrast)
        self.Bind(wx.EVT_CHECKBOX, self.updatePcondButton, self.colour)
        self.Bind(wx.EVT_CHECKBOX, self.OnExposure,        self.exposure)
        self.Bind(wx.EVT_TEXT,     self.OnExpValue,        self.expvalue)
        self.Bind(wx.EVT_CHECKBOX, self.updatePcondButton, self.linear)
        self.Bind(wx.EVT_CHECKBOX, self.updatePcondButton, self.centre)
        self.Bind(wx.EVT_CHECKBOX, self.OnDspRange,        self.dsprange)
        self.Bind(wx.EVT_TEXT,     self.OnDspValue,        self.dsp_min)
        self.Bind(wx.EVT_TEXT,     self.OnDspValue,        self.dsp_max)

        self.pcondButton = buttons.GenButton(self, wx.ID_ANY, label='apply pcond', size=(-1,24))
        self.pcondButton.Bind(wx.EVT_BUTTON, self.OnDoPcond)
        self.pcondButton.Disable()

        saveBitmap = wx.Button(self, wx.ID_ANY, "save bitmap")
        saveBitmap.Bind(wx.EVT_BUTTON, self.OnSaveBitmap)

        layout = [(self.acuity,      None),
                  (self.glare,       None),
                  (self.contrast,    None),
                  (self.colour,      None),
                  (wx.Panel(self,wx.ID_ANY,size=(-1, 5)), None),
                  (self.exposure, self.expvalue),
                  (self.linear,      None),
                  (self.centre,      None),
                  (wx.Panel(self,wx.ID_ANY,size=(-1, 5)), None),
                  (self.dsprange,    None),
                  (dsp_box,          None),
                  (wx.Panel(self,wx.ID_ANY,size=(-1, 5)), None),
                  (self.pcondButton, None), 
                  (wx.Panel(self,wx.ID_ANY,size=(-1,10)), None),
                  (saveBitmap,       None),
                  (wx.Panel(self,wx.ID_ANY,size=(-1, 5)), None)]
                
        ## arrange in grid 
        self.createCenteredGrid(layout)


    def disablePcondButton(self):
        """disable pcond button and change colour"""
        self.pcondButton.Disable()
        self.pcondButton.SetBackgroundColour(wx.WHITE)


    def getPcondArgs(self):
        """collect pcond arguments and return as list"""
        args = []
        if self.acuity.GetValue():   args.append("-a");
        if self.glare.GetValue():    args.append("-v");
        if self.contrast.GetValue(): args.append("-s");
        if self.colour.GetValue():   args.append("-c"); 
        if self.linear.GetValue():   args.append("-l");
        if self.centre.GetValue():   args.append("-w");
        if self.exposure.GetValue():
            args.append("-e")
            args.append(self.expvalue.GetValue())
        if self.dsprange.GetValue():
            try:
                black = float(self.dsp_min.GetValue())
                white = float(self.dsp_max.GetValue())
                if black <= 0:
                    black == 0.5
                if white <= 0:
                    white = 100
                range = white/black
                args.extend(["-u", "%d" % white, "-d", "%d" % range])
            except ValueError:
                pass
        self._log.debug("getPcondArgs() args=%s" % str(args))
        return args


    def OnDoPcond(self, event):
        """run pcond and update imagepanel"""
        if self.wxapp.rgbeImg:
            args = self.getPcondArgs()
            if self.wxapp.doPcond(args) == True:
                self._cmdLine = " ".join(args)
        self.disablePcondButton()


    def OnDspRange(self, event):
        """check than min and max display settings are numbers"""
        if self.dsprange.GetValue() == False:
            self.updatePcondButton(event)
            return
        try:
            black = float(self.dsp_min.GetValue())
            if black <= 0:
                self.dsp_min.SetValue("0.5")
        except ValueError:
            self.dsp_min.SetValue("0.5")
        try:
            white = float(self.dsp_max.GetValue())
            if white <= 0:
                self.dsp_max.SetValue("200")
        except ValueError:
            self.dsp_max.SetValue("200")
        self.updatePcondButton(event)
        

    def OnDspValue(self, event):
        """set display range to True on dsp value change"""
        if self.dsp_min.GetValue() == "" or self.dsp_max.GetValue() == "":
            return
        else:
            try:
                black = float(self.dsp_min.GetValue())
                white = float(self.dsp_max.GetValue())
                self.dsprange.SetValue(True) 
                self.updatePcondButton(event)
            except ValueError:
                pass


    def OnExposure(self, event):
        """select 'linear' cb if exposure is enabled"""
        if self.exposure.GetValue() == True:
            self.linear.SetValue(True)
            try:
                v = float(self.expvalue.GetValue())
            except ValueError:
                self.expvalue.SetValue("+0")
        self.updatePcondButton(event)


    def OnExpValue(self, event):
        """enable exposure cb on expvalue change"""
        try:
            v = float(self.expvalue.GetValue())
            self.exposure.SetValue(True)
            self.linear.SetValue(True)
            self.updatePcondButton(event)
        except ValueError:
            self.exposure.SetValue(False)


    def OnSaveBitmap(self, event):
        """call imagepanel's saveBitmap() function"""
        self.wxapp.imagepanel.saveBitmap()


    def reset(self):
        """set buttons to initial state"""
        self.acuity.SetValue(False)
        self.glare.SetValue(False)
        self.contrast.SetValue(False)
        self.colour.SetValue(False) 
        self.expvalue.SetValue("+0")
        self.exposure.SetValue(False)
        self.linear.SetValue(False)
        self.centre.SetValue(False)
        
        self.pcondButton.Enable()
        self.pcondButton.SetBackgroundColour(wx.WHITE)
        

    def updatePcondButton(self, event):
        """enable pcond button if new options are selected"""
        if not self.wxapp.rgbeImg:
            self.disablePcondButton()
            return
        if " ".join(self.getPcondArgs()) != self._cmdLine:
            self.pcondButton.Enable()
            self.pcondButton.SetBackgroundColour(wx.Colour(255,140,0))
        else:
            self.disablePcondButton()





class LablesControlPanel(BaseControlPanel):

    def __init__(self, parent, wxapp, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.wxapp = wxapp
        self._log = wxapp._log
        self._layout()

    def _layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.loadClearButton = wx.Button(self, wx.ID_ANY, "no data")
        self.loadClearButton.Bind(wx.EVT_BUTTON, self.OnShowValues)
        self.loadClearButton.Disable()
        sizer.Add(self.loadClearButton, proportion=0, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        
        lable = wx.StaticText(self, wx.ID_ANY, "text:")
        self.lableText = wx.TextCtrl(self, wx.ID_ANY, "")
        self.Bind(wx.EVT_TEXT, self.OnTextChange, self.lableText)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(lable, flag=wx.ALL, border=2)
        hsizer.Add(self.lableText, proportion=1)
        sizer.Add(hsizer, proportion=0, flag=wx.EXPAND|wx.ALL, border=10)
        
        spacer = wx.Panel(self, wx.ID_ANY, size=(-1,5))
        sizer.Add(spacer, proportion=0, flag=wx.EXPAND|wx.ALL, border=0)
        
        saveBitmap = wx.Button(self, wx.ID_ANY, "save bitmap")
        saveBitmap.Bind(wx.EVT_BUTTON, self.OnSaveBitmap)
        sizer.Add(saveBitmap, proportion=0, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=5)
        
        ## add spacer and set size
        spacer = wx.Panel(self, wx.ID_ANY, size=(-1,5))
        sizer.Add(spacer, proportion=0, flag=wx.EXPAND|wx.ALL, border=0)
        self.SetSizer(sizer)
        self.SetInitialSize()

    def getLableText(self):
        return self.lableText.GetValue()

    def OnShowValues(self, event):
        """load data from image and clear labels"""
        self.wxapp.imagepanel.clearLabels()
        self.loadClearButton.Disable()
        self.wxapp.statusbar.SetStatusText("loading image data ...")
        if self.wxapp.loadValues() == False:
            self.loadClearButton.SetLabel("no data")
            self.wxapp.statusbar.SetStatusText("Error loading image data!")
        elif self.wxapp.loadingCanceled == True:
            self.wxapp.statusbar.SetStatusText("Loading of image data canceled.")
            self.loadClearButton.SetLabel("load data")
            self.loadClearButton.Enable()
        else:
            ## if we have data
            self.loadClearButton.SetLabel("clear lables")
            self.wxapp.statusbar.SetStatusText("")
            if self.wxapp.rgbeImg.isIrridiance():
                self.setLable("Lux")
            else:
                self.setLable("cd/m2")

    def OnSaveBitmap(self, event):
        """call imagepanel's saveBitmap() function"""
        self.wxapp.imagepanel.saveBitmap()

    def OnTextChange(self, event):
        """call imagepanel's saveBitmap() function"""
        self.wxapp.imagepanel.UpdateDrawing()

    def reset(self):
        self.loadClearButton.Enable()
        self.loadClearButton.SetLabel("load data")
        self.setLable(" ")
    
    def setLable(self, text):
        self.lableText.SetValue(text)




class MiscControlPanel(wx.Panel):
    
    def __init__(self, parent, wxapp, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.wxapp = wxapp
        self._layout()

    def _layout(self):
        """create buttons for various functions"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        buttons = [("show header", self.wxapp.showHeaders,      20),
                ("check update",   self.wxapp.check_for_update, 10), 
                ("about",          self.wxapp.showAboutDialog,  5)]
        
        ## create buttons and spacers
        for label, func, space in buttons:
            button = wx.Button(self, wx.ID_ANY, label)
            button.Bind(wx.EVT_BUTTON, func)
            sizer.Add(button, proportion=0, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=5)
            if space > 0:
                spacer = wx.Panel(self, wx.ID_ANY, size=(-1,space))
                sizer.Add(spacer, proportion=0, flag=wx.EXPAND|wx.ALL, border=0)

        ## set sizer and finish
        self.SetSizer(sizer)
        self.SetInitialSize()




class MyFoldPanelBar(fpb.FoldPanelBar):
    """base for FoldPanelBar in controlls panel"""
    
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, *args,**kwargs):
        fpb.FoldPanelBar.__init__(self, parent, id, pos, size, *args, **kwargs)

    def OnPressCaption(self, event):
        """collapse all other panels on EVT_CAPTIONBAR event"""
        fpb.FoldPanelBar.OnPressCaption(self, event)
        for i in range(self.GetCount()):
            p = self.GetFoldPanel(i)
            if p != event._tag:
                self.Collapse(p)



class FoldableControlsPanel(wx.Panel):
    """combines individual feature panels"""
    
    def __init__(self, parent, wxapp, style=wx.DEFAULT_FRAME_STYLE):

        wx.Panel.__init__(self, parent, id=wx.ID_ANY)
        self.wxapp = wxapp
        self.SetSize((140,350))
        self._layout()
        self.Bind(wx.EVT_SIZE, self.setBarSize)


    def expand(self, idx):
        """expand element <idx> on self.pnl"""
        if not self.pnl:
            return False
        total = self.pnl.GetCount()
        if idx >= total:
            return False
        for i in range(total):
            panel = self.pnl.GetFoldPanel(i)
            self.pnl.Collapse(panel)
        panel = self.pnl.GetFoldPanel(idx)
        self.pnl.Expand(panel)


    def _layout(self, vertical=True):
                           
        bar = MyFoldPanelBar(self, style=fpb.FPB_DEFAULT_STYLE|fpb.FPB_VERTICAL)

        item = bar.AddFoldPanel("lables", collapsed=False)
        self.lablecontrols = LablesControlPanel(item, self.wxapp)
        bar.AddFoldPanelWindow(item, self.lablecontrols, flags=fpb.FPB_ALIGN_WIDTH)

        item = bar.AddFoldPanel("falsecolor", collapsed=True)
        self.fccontrols = FalsecolorControlPanel(item, self.wxapp)
        bar.AddFoldPanelWindow(item, self.fccontrols, flags=fpb.FPB_ALIGN_WIDTH)
        
        item = bar.AddFoldPanel("display", collapsed=True)
        self.displaycontrols = DisplayControlPanel(item, self.wxapp)
        bar.AddFoldPanelWindow(item, self.displaycontrols, flags=fpb.FPB_ALIGN_WIDTH)
        
        item = bar.AddFoldPanel("misc", collapsed=True)
        pc_controls = MiscControlPanel(item, self.wxapp)
        bar.AddFoldPanelWindow(item, pc_controls)
        
        if hasattr(self, "pnl"):
            self.pnl.Destroy()
        self.pnl = bar

        size = self.GetClientSize()
        self.pnl.SetDimensions(0, 0, size.GetWidth(), size.GetHeight())


    def setBarSize(self, event):
        size = event.GetSize()
        self.pnl.SetDimensions(0, 0, size.GetWidth(), size.GetHeight())
        

