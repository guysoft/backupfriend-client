import wx
from wx.adv import Wizard, WizardPageSimple
from wx.lib.mixins import listctrl
from wx import xrc
import os.path
from backupfriend.make_ssh_key import generate_keys
from backupfriend.common import get_data_path

DATA_PATH = get_data_path()

class ResizedList(wx.ListCtrl, listctrl.ListCtrlAutoWidthMixin):
    def __init__(self, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self)
        listctrl.ListCtrlAutoWidthMixin.__init__(self)
        # self.setResizeColumn(0)


class ResizedSecondList(wx.ListCtrl, listctrl.ListCtrlAutoWidthMixin):
    def __init__(self, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self)
        listctrl.ListCtrlAutoWidthMixin.__init__(self)
        self.setResizeColumn(2)


class FirstRunWizard(Wizard):
    def __init__(self, *args, **kw):
        Wizard.__init__(self, *args
                        , **kw)
        self.m_wiz_gnerate_keys = xrc.XRCCTRL(self, 'm_wiz_gnerate_keys')
        self.Bind(wx.EVT_BUTTON, self.generate_keys, id=xrc.XRCID('m_generate_keys'))
        self.Bind(wx.EVT_BUTTON, self.select_all, id=xrc.XRCID('m_select_all'))
        self.m_public_key = xrc.XRCCTRL(self, 'm_public_key')

    def select_all(self, event):
        page = self.GetCurrentPage()
        m_public_key = xrc.XRCCTRL(page, 'm_public_key')
        m_public_key.SetSelection(-1, -1)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(m_public_key.GetValue()))
            wx.TheClipboard.Close()
        return

    def generate_keys(self, event):
        private_key_str, public_key_str = generate_keys(DATA_PATH)
        # self.m_public_key.SetValue(public_key_str)
        page = self.GetCurrentPage()
        m_result = xrc.XRCCTRL(page, 'm_result')
        m_generate_keys = xrc.XRCCTRL(page, 'm_generate_keys')

        m_result.SetLabel("Generated keys")
        m_generate_keys.Disable()
        next_page = page.GetNext()
        m_public_key = xrc.XRCCTRL(next_page, 'm_public_key')
        m_public_key.SetValue(public_key_str)
        return


class ShowPublicKeyDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        wx.Dialog.__init__(self, *args, **kw)
        self.Bind(wx.EVT_BUTTON, self.select_all, id=xrc.XRCID('m_select_all'))
        self.Bind(wx.EVT_BUTTON, self.close, id=xrc.XRCID('m_close'))

    def close(self, event):
        self.Close()

    def select_all(self, event):
        m_public_key = xrc.XRCCTRL(self, 'm_public_key')
        m_public_key.SetSelection(-1, -1)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(m_public_key.GetValue()))
            wx.TheClipboard.Close()
        return

    def ShowModal(self, *args, **kw):
        m_public_key = xrc.XRCCTRL(self, 'm_public_key')

        public_key_path = os.path.join(DATA_PATH, "id_rsa.pub")
        if os.path.isfile(public_key_path):
            with open(public_key_path) as f:
                public_key_str = f.read()
            m_public_key.SetValue(public_key_str)
        wx.Dialog.ShowModal(self, *args, **kw)

