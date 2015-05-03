
import wx

#---------------------------------------------------------------------------

class ResizeDialog(wx.Dialog):
    def __init__(self, parent, ID, title,
            size=wx.DefaultSize, pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self, parent, ID, title, pos, size, style)

        self.text = "\n".join(["You are trying to load a large image",
                "(width=%dpx, height=%dpx).",
                "Do you want to resize the image before loading?",
                "A backup of the original image will be crated."])

        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.text_label = wx.StaticText(self, -1, self.text, style=wx.ALIGN_CENTRE)
        sizer.Add(self.text_label, 0, wx.ALIGN_CENTRE|wx.ALL, 15)
       
        sizer.Add(wx.StaticLine(self), 0, wx.ALL|wx.EXPAND, 5)

        self.cb_resize = wx.CheckBox(self, -1, "resize image", size=(20,-1))
        self.Bind(wx.EVT_CHECKBOX, self.OnResizeCheckBox, self.cb_resize)
        sizer.Add(self.cb_resize, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 10)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "backup image:", size=(150,-1))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.img_backup = wx.TextCtrl(self, -1, "", size=(30,-1))
        box.Add(self.img_backup, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 15)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "new image width:", size=(150,-1))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.img_width = wx.TextCtrl(self, -1, "", size=(5,-1))
        box.Add(self.img_width, 1, wx.ALIGN_LEFT|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 15)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "new image height:", size=(150,-1))
        box.Add(label, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.img_height = wx.TextCtrl(self, -1, "", size=(5,-1))
        box.Add(self.img_height, 1, wx.ALIGN_LEFT|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 15)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()
        self.btn_ok = wx.Button(self, wx.ID_OK, "load data", size=(80,-1))
        self.btn_ok.SetDefault()
        btnsizer.AddButton(self.btn_ok)
        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        sizer.Add(btnsizer, 0, wx.ALIGN_RIGHT|wx.ALL, 15)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self._setControlState(False)
   
    def OnResizeCheckBox(self, evt):
        if self.cb_resize.IsChecked():
            self._setControlState(True)
        else:
            self._setControlState(False)

    def _setControlState(self, state):
        """enable/disable text controls for image size"""
        if state:
            label = "resize"
            fg_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        else:
            label = "load data"
            fg_color = "#999999"
        self.btn_ok.SetLabel(label)
        for c in [self.img_width, self.img_height, self.img_backup]:
            c.Enable(state)
            c.SetForegroundColour(fg_color)
        self.Refresh() 

    def setImageInfo(self, info):
        """update controls with info about hdr image"""
        self.text_label.SetLabel(self.text % (info['x'],info['y']))
        self.img_width.SetValue(str(info['new_x']))
        self.img_height.SetValue(str(info['new_y']))
        self.img_backup.SetValue(info['backup_name'])
        self._setControlState(info['do_resize'])
        self.cb_resize.SetValue(info['do_resize'])
        self.Refresh() 
         

#---------------------------------------------------------------------------


if __name__ == '__main__':
    app = wx.PySimpleApp()
    td = ResizeDialog(parent=None, ID=-1, title="Large Image", size=(500,300))
    
    info = { 'x':3000, 'y':2000, 'new_x':1350, 'new_y':900,
        'backup_name':'img_3000x2000.hdr', 'do_resize': False}
    
    td.setImageInfo( info );
    result = td.ShowModal()
    if result == wx.ID_OK:
        print "OK"
        if td.cb_resize.IsChecked():
            print "resize image:"
            print "  image width:  ", td.img_width.GetValue()
            print "  image heigh:  ", td.img_height.GetValue()
            print "  image backup: ", td.img_backup.GetValue()
        else:
            print "load original image"
    else:
        print "loading cancelled"
    td.Destroy()

    app.MainLoop()

