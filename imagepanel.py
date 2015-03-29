##
## imagepanel.py - part of wxfalsecolor
##
## $Id$
## $URL$

import os
import cStringIO
import traceback
import wx
from rgbeimage import RGBEImage, WX_IMAGE_FORMATS, WX_IMAGE_WILDCARD

import wx.lib.scrolledpanel as scrolled


class FileDropTarget(wx.FileDropTarget):
    """implement file drop feature for ImagePanel"""
    
    def __init__(self, app):
        wx.FileDropTarget.__init__(self)
        self.wxapp = app

    def OnDropFiles(self, x, y, filenames):
        """validate image before passing it on to self.app.loadImage()"""
        path = filenames[0]
	## create RGBEImage to check file type and data
        rgbeImg = RGBEImage(self, self.wxapp._log, ["-i", path])
        rgbeImg.readImageData(path)
        if rgbeImg.error:
            msg = "Error loading image.\nFile: %s\nError: %s" % (path,rgbeImg.error)
            self.wxapp.showError(msg)
        else:
            ## now load for real
            self.wxapp.loadImage(path)
    



class ImagePanel(wx.Panel):
    """A panel to display the bitmap image data."""

    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent,
                          style=wx.NO_FULL_REPAINT_ON_RESIZE,
                          *args, **kwargs)
        
        self.parent = parent
        self._background_color = wx.Colour(237,237,237) # Apple window bg
        self._log = parent._log
        self.rgbeImg = None
        self.img = None
        self._scale = 0
        self._scaledImg = None
        self._labels = []
        self._dragging = False
        self._draggingFrame = (0,0)

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.DoNothing)

        self.SetDropTarget(FileDropTarget(parent))
        self.OnSize(None)


    def addLabel(self, x, y, dx=0, dy=0):
        """get value for (x,y) and add to self._labels"""
        self._dragging = False
        if self.rgbeImg == False:
            return

        self._log.debug("addLabel(x=%d, y=%d, dx=%d, dy=%d)" % (x,y,dx,dy))
        w,h = self._scaledImg.GetSize()
        if x > w or y > h:
            ## outside image area
            return
        
        ## get rgbe value for image location
        if self._scale > 1:
            x = int(x*self._scale)
            y = int(y*self._scale)
            dx = int(dx*self._scale)
            dy = int(dy*self._scale)
        if dx == 0:
            r,g,b,v = self.parent.getRGBVAt((x,y))
        else:
            r,g,b,v = self.parent.getRGBVAverage((x,y),(x+dx,y+dy))
        if r <= 0:
            return

        ## format label text
        if self.rgbeImg.isIrridiance():
            label = "%s" % self.parent.formatNumber(v)
        else:
            lum = (r*0.265+g*0.67+b*0.065)*179
            label = "%s" % self.parent.formatNumber(lum)
        
        self._log.info("new label: '%s' at (x=%d,y=%d) (dx=%d, dy=%d)" % (label,x,y,dx,dy))
        self._labels.append((x,y, dx,dy, label))


    def adjustLabels(self, dx, dy):
        """move labels if legend offset has changed"""
        if self._labels == []:
            return
        self._log.debug("adjustLabels(dx=%d, dy=%d)" % (dx,dy))
        for i in range(len(self._labels)):
            x,y,sx,sy,text = self._labels[i]
            self._labels[i] = (x+dx,y+dy,sx,sy,text)
 
    
    def clearLabels(self):
        """reset lables list"""
        self._log.info("clearLabels()")
        self._labels = []
        self.UpdateDrawing()

    
    def doFalsecolor(self, args):
        """convert rgbeimage to falsecolor and reload image"""
        xo,yo = self.rgbeImg.legendoffset
        self.rgbeImg.resetDefaults()

        if self.rgbeImg.setOptions(args) == False:
            self._log.warn("self.rgbeImg.setOptions() == False")
            return False
        self.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
        if self.rgbeImg.doFalsecolor() == False:
            self.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
            self._log.warn("self.rgbeImg.doFalsecolor() == False")
            return False
        else:
            self.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
            xn,yn = self.rgbeImg.legendoffset
            self.adjustLabels(xn-xo, yn-yo)
            self.update()
            return True

    
    def doPcond(self, args):
        """apply pcond args to rgbeimage and reload image"""
        xo,yo = self.rgbeImg.legendoffset
        self.rgbeImg.resetDefaults()
        if self.rgbeImg.doPcond(args) == False:
            self._log.warn("self.rgbeImg.doPcond() == False")
            return False
        else:
            xn,yn = self.rgbeImg.legendoffset
            self.adjustLabels(xn-xo, yn-yo)
            self.update()
            return True


    def DoNothing(self, evt):
        """swallow EVT_ERASE_BACKGROUND"""
        pass


    def Draw(self, dc):
        """do the actual drawing"""
        try:
            gc = wx.GraphicsContext.Create(dc)
        except NotImplementedError:
            dc.DrawText("wx.GraphicsContext not supported", 25, 25)
            return

        self._drawBackground(gc)
        ## draw image
        if self._scaledImg:
            self._drawBMP(gc)
        ## draw overlay
        if self._labels != []:
            self._drawLabels(gc)
        
        if self._dragging:
            self._drawDraggingFrame(gc)


    def _drawBackground(self, gc):
        """draw background to avoid black frame in Windows"""
        path_bg = gc.CreatePath()
        w,h = self.GetClientSizeTuple()
        path_bg.AddRectangle(0,0,w,h)
        gc.SetBrush(wx.Brush(self._background_color))
        gc.DrawPath(path_bg)


    def _drawBMP(self, gc):
        """draw (background) bitmap to graphics context"""
        bmp = wx.BitmapFromImage(self._scaledImg)
        size = bmp.GetSize()
        gc.DrawBitmap(bmp, 0, 0, size.width, size.height)


    def _drawDraggingFrame(self,gc):
        """draw translucent frame over dragging area"""
        x,y = self._dragging
        dx,dy = self._draggingFrame
        if dx < 0:
            x += dx
            dx *= -1
        if dy < 0:
            y += dy
            dy *= -1
        gc.PushState()
        gc.SetPen(wx.Pen(wx.BLUE, 1))
        gc.SetBrush(wx.Brush(wx.Colour(0,0,255,51), wx.SOLID))
        gc.Translate(x,y)
        path = gc.CreatePath()
        path.AddRectangle(0,0,dx,dy)
        gc.DrawPath(path)
        gc.PopState()


    def _drawLabels(self, gc):
        """draw labels with r,g,b or lux values""" 
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetWeight(wx.BOLD)
        gc.SetFont(font)

        lableText = self.parent.getLableText()
        if lableText.strip() != "":
            lableText = " " + lableText
        
        for x,y,dx,dy,l in self._labels:
            x /= self._scale
            y /= self._scale
            if dx == 0:
                dx = 2
            else:
                dx /= self._scale
            if dy == 0:
                dy = 2
            else:
                dy /= self._scale
                
            l += lableText
            w,h = gc.GetTextExtent(l)
            
            path_spot = gc.CreatePath()
            path_spot.AddRectangle(-1,-1,dx,dy)
            path_label = gc.CreatePath()
            path_label.AddRectangle(0,-1,w+3,h+1)
            
            ## move to spot location
            gc.PushState()
            gc.Translate(x,y)
            
            ## new state for label 
            gc.PushState()
            gc.SetPen(wx.Pen(wx.BLACK, 1))
            gc.SetBrush(wx.Brush(wx.WHITE))
            imgw,imgh = self.GetClientSize()
            if x+w+3 > imgw:
                gc.Translate(-(w+3), 0)
            if y+h > imgh:
                gc.Translate(0,-(h-1))
            gc.DrawPath(path_label)
            gc.DrawText(l,2,0)
            gc.PopState()
            
            ## back to spot state
            gc.SetPen(wx.Pen(wx.RED, 1))
            gc.SetBrush(wx.Brush(wx.RED, wx.TRANSPARENT))
            gc.DrawPath(path_spot)
            gc.PopState()


    def _drawTestPath(self, gc):
        """debuging method"""
        BASE  = 80.0    # sizes used in shapes drawn below
        BASE2 = BASE/2
        BASE4 = BASE/4
        path = gc.CreatePath()
        path.AddCircle(0, 0, BASE2)
        path.MoveToPoint(0, -BASE2)
        path.AddLineToPoint(0, BASE2)
        path.MoveToPoint(-BASE2, 0)
        path.AddLineToPoint(BASE2, 0)
        path.CloseSubpath()
        path.AddRectangle(-BASE4, -BASE4/2, BASE2, BASE4)

        # Now use that path to demonstrate various capbilites of the grpahics context
        gc.PushState()             # save current translation/scale/other state 
        gc.Translate(60, 75)       # reposition the context origin

        gc.SetPen(wx.Pen("navy", 1))
        gc.SetBrush(wx.Brush("pink"))
        gc.DrawPath(path)
        gc.PopState()


    def _getBitmapPath(self):
        """show dialog to save bitmap file"""
        path = self.parent.path
        if path == '':
            return ''
        
        dirname, filename = os.path.split(path)
        filebase = os.path.splitext(filename)[0]
        filedialog = wx.FileDialog(self,
                          message = 'save image',
                          defaultDir = dirname,
                          defaultFile = filebase + '.bmp',
                          wildcard = WX_IMAGE_WILDCARD,
                          style = wx.SAVE)
        if filedialog.ShowModal() == wx.ID_OK:
            return filedialog.GetPath()
        else:
            return '' 


    def hasLables(self):
        return len(self._labels)


    def OnLeftDown(self, evt):
        """set dragging flag when left mouse button is pressed"""
        if self._scaledImg == None:
            return
        self._dragging = evt.GetPosition()
        self._draggingFrame = (0,0)


    def OnLeftUp(self, evt):
        """show spot or average reading"""
        if self._scaledImg == None:
            return
        x2,y2 = evt.GetPosition() 
        if self._dragging == False:
            self.addLabel(x2,y2)
        else:
            x1,y1 = self._dragging
            if x1 > x2:
                x1,x2 = x2,x1
            if y1 > y2:
                y1,y2 = y2,y1
            dx = x2 - x1
            dy = y2 - y1
            if dx > 2 and dy > 2:
                self.addLabel(x1,y1,dx,dy)
            else:
                self.addLabel(x2,y2)
        self._dragging = False
        self._draggingFrame = (0,0)
        self.UpdateDrawing()
        self.parent.onImagePanelClick()


    def OnMouseMotion(self, evt):
        """return cursor (x,y) in pixel coords of self.img - (x,y) is 0 based!"""
        if self._scaledImg == None:
            return
        
        x,y = evt.GetPosition()
        if self._dragging != False:
            ## draw dragging frame
            dx = x - self._dragging[0]
            dy = y - self._dragging[1]
            self._draggingFrame = (dx,dy)
            self.UpdateDrawing()

        w,h = self._scaledImg.GetSize()
        if x <= w and y <= h:
            if self._scale > 1:
                x *= self._scale
                y *= self._scale
            self.parent.showPixelValueAt( (int(x),int(y)) )
        
    
    def OnPaint(self, evt):
        """refresh image panel area on screen"""
        ## copy image in buffer to dc
        dc = wx.BufferedPaintDC(self, self._Buffer)
        ## dc is copied to screen automatically; no need for Draw() etc.


    def OnSize(self, evt):
        """create new buffer and update window"""
        size = self.GetClientSizeTuple()
        if size != (0,0):
            self._Buffer = wx.EmptyBitmap(*size)
            self.resizeImage(size)
            self.UpdateDrawing()


    def resizeImage(self, size):
        """scale image to fit frame proportionally"""
        if self._set_image_scale(size) == True:
            self.parent.statusbar.setZoom(self._scale)
            if self._scale != 0:
                w,h = self.img.GetSize()
                self._scaledImg = self.img.Scale( int(w/self._scale), int(h/self._scale) )
        
            
    def _set_image_scale(self, size):
        """set image scale to fit; return True if scale has changed"""
        if not self.img:
            return False
        w,h = self.img.GetSize()
        if w*h*size[0]*size[1] != 0:
            scale_x = w / float(size[0])
            scale_y = h / float(size[1])
            scale   = max(scale_x,scale_y)
            ## use rounded scale values to reduce resizing of image
            scale   = int(scale * 10.0) / 10.0
            if w/scale > size[0] or h/scale > size[1]:
                scale += 0.1
            ## only make image smaller, not bigger
            if scale < 1.0:
                scale = 1.0
            if scale != self._scale:
                self._scale = scale
                self._log.info("new scale: 1:%.2f" % self._scale)
                return True
                

    def saveBitmap(self, path=''):
        """save buffer image to file"""
        if path == '':
            path = self._getBitmapPath()

        if path == '':
            return

        self._log.info("saving bitmap to file '%s' ..." % path)
        ext = os.path.splitext(path)[1]
        ext = ext.lower()
        format = WX_IMAGE_FORMATS.get(ext, wx.BITMAP_TYPE_BMP)
        
        fw,fh = self.GetSize()
        try:
            img = self._Buffer.ConvertToImage()
            w,h = img.GetSize()
            if w > fw and h > fh:
                img = img.Size((fw,fh), (0,0))
            elif w > fw:
                img = img.Size((fw,h), (0,0))
            elif h > fh:
                img = img.Size((w,fh), (0,0))
            img.SaveFile(path, format)
            self._log.info("saved file '%s'" % path)
        except Exception, err:
            msg = "Error saving image:\n%s\n%s" % (str(err), traceback.format_exc())
            self._log.error(msg)
            self.parent.showError(msg)
    

    def setImage(self, img):
        """set wx.Image"""
        self.img = img
        self._scale = 0
        self.OnSize(None)
        ## call parent.Layout() to force resize of panel
        self.parent.Layout()
        self.UpdateDrawing()





    def update(self, rgbeImg=None):
        """set new rgbeImg"""
        self._log.info("updating image (rgbeImg=%s)" % rgbeImg)
        if rgbeImg:
            self.rgbeImg = rgbeImg
        try:
            ppm = self.rgbeImg.toPPM()
            io = cStringIO.StringIO(ppm)
            img = wx.ImageFromStream(io)
        except:
            self._log.error("conversion to wx.Image failed")
            return False
        self.setImage(img)
        return True
        

    def UpdateDrawing(self):
        """updates drawing when needed (not by system)"""
        dc = wx.BufferedDC(wx.ClientDC(self), self._Buffer)
        self.Draw(dc)


