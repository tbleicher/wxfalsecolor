from mock import patch
import wx
import unittest
from resizedialog import ResizeDialog


class TestResizeDialog(unittest.TestCase):
    
    def setUp(self):
        self.info = { 'x':3000, 'y':2000, 'new_x':1350, 'new_y':900,
          'backup_name':'img_3000x2000.hdr', 'do_resize': False}
        self.app = wx.PySimpleApp()
        self.dialog = ResizeDialog(parent=None, ID=-1, title="title")
        
    def teardown(self):
        self.dialog.Destroy()
        self.app.Exit()

    def test_instance_of_wxDialog(self):
        assert self.dialog

    def test_setImageInfo(self):
        self.dialog.setImageInfo(self.info)
        self.assertEqual( self.dialog.img_backup.GetValue(), self.info['backup_name'] ) 
        self.assertEqual( int(self.dialog.img_width.GetValue()), self.info['new_x'] ) 
        self.assertEqual( int(self.dialog.img_height.GetValue()), self.info['new_y'] ) 
    
    def test_do_resize(self):
        self.dialog.setImageInfo(self.info)
        self.assertFalse(self.dialog.cb_resize.IsChecked())
        self.assertEqual(self.dialog.btn_ok.GetLabel(), "load data")
        self.check_textcontrol_status(False)

        self.info['do_resize'] = True
        self.dialog.setImageInfo(self.info)
        self.assertTrue(self.dialog.cb_resize.IsChecked())
        self.assertEqual(self.dialog.btn_ok.GetLabel(), "resize")
        self.check_textcontrol_status(True)

    def check_textcontrol_status(self, state):
        for t in [self.dialog.img_backup, self.dialog.img_width, self.dialog.img_height]:
            self.assertEqual(t.IsEnabled(), state)
