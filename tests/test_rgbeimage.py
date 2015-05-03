import mock 
import unittest
from rgbeimage import RGBEImage

wxparent = mock.MagicMock()
log = mock.MagicMock()

class RGBEImageTest(unittest.TestCase):

    def test_doPcond(self):
        img = RGBEImage(wxparent, log)
        img._doPcommand = mock.MagicMock()
        args = ['a', 2]
        img.doPcond(args)
        img._doPcommand.assert_called_with("pcond", args)
    
    def test_doPfilt(self):
        img = RGBEImage(wxparent, log)
        img._doPcommand = mock.MagicMock()
        args = ['a', 2]
        img.doPfilt(args)
        img._doPcommand.assert_called_with("pfilt", args)
    
    @mock.patch('rgbeimage.FalsecolorImage.doFalsecolor')
    def test_doFalsecolor_fail(self, fci_mock):
        log.error = mock.MagicMock()
        fci_mock.return_value = False

        img = RGBEImage(wxparent, log)
        img.error = "some error"
        img.showError = mock.MagicMock()

        result = img.doFalsecolor()
        self.assertFalse(result)
        log.error.assert_called_with("FalsecolorImage.doFalsecolor() == False")
        img.showError.assert_called_with("falsecolor2 error:\nsome error")
    
    @mock.patch('rgbeimage.FalsecolorImage.doFalsecolor')
    def test_doFalsecolor(self, fci_mock):
        fci_mock.return_value = True
        img = RGBEImage(wxparent, log)
        result = img.doFalsecolor()
        self.assertTrue(result)

    def test_resize(self):
        img = RGBEImage(wxparent, log)
        img.doPfilt = mock.MagicMock()
        img.doPfilt.return_value = True
        img._analyzeImage = mock.MagicMock()
        img.resize(600,400)
        msg = "_analyzeImage() was not called after successful resize()"
        self.assertTrue(img._analyzeImage.called, msg)
    
    def test_resize_fail(self):
        img = RGBEImage(wxparent, log)
        img.doPfilt = mock.MagicMock()
        img.doPfilt.return_value = False
        img._analyzeImage = mock.MagicMock()
        img.resize(600,400)
        msg = "_analyzeImage() was called after failed resize()"
        self.assertFalse(img._analyzeImage.called, msg)


