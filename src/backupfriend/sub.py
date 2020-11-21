import wx
from wx.adv import Wizard, WizardPageSimple
from wx.lib.mixins import listctrl
from wx import xrc
import os.path
from backupfriend.make_ssh_key import generate_keys
from backupfriend.common import get_data_path
from .main import Backup

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


class JobDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        wx.Dialog.__init__(self, *args, **kw)
        self.Bind(wx.EVT_BUTTON, self.close, id=xrc.XRCID('m_cancel'))
        self.Bind(wx.EVT_BUTTON, self.save, id=xrc.XRCID('m_save'))
        # self.Bind(wx.EVT_INIT_DIALOG, self.on_init_dialog)
        return

    def ShowModal(self, *args, **kw):
        m_key = xrc.XRCCTRL(self, 'm_key_picker')
        key_path = os.path.join(DATA_PATH, "id_rsa")
        # m_key.SetInitialDirectory(os.path.dirname(key_path))
        m_key.SetPath(key_path)
        print(m_key.GetPath())
        m_key.Refresh()
        return wx.Dialog.ShowModal(self, *args, **kw)

    def close(self, event):
        self.Close()

    def save(self, event):
        errors = []
        m_name = xrc.XRCCTRL(self, 'm_name')
        m_source = xrc.XRCCTRL(self, 'm_source')
        m_dest = xrc.XRCCTRL(self, 'm_dest')
        m_port = xrc.XRCCTRL(self, 'm_port')
        m_key = xrc.XRCCTRL(self, 'm_key_picker')
        m_repeat = "daily"
        m_time = xrc.XRCCTRL(self, 'm_time')

        # Sanity_check
        if m_name.GetValue() == "":
            errors.append("Name can't be empty")
        if m_source.GetPath() == "":
            errors.append("Source can't be empty")
        if m_dest.GetValue() == "":
            errors.append("Destination can't be empty")

        if m_key.GetPath() == "":
            errors.append("SSH key can't be empty")
        elif not os.path.isfile(m_key.GetPath()):
            errors.append("SSH key path does not exist")

        m_info = xrc.XRCCTRL(self, 'm_info')
        if len(errors) > 0:
            m_info.SetForegroundColour((255, 0, 0))
            m_info.SetLabel("\n".join(errors))
        else:
            m_info.SetForegroundColour((0, 0, 0))
            m_info.SetLabel("Implement saving, and sanity test")

        # TODO: Implement saving a new job

        # Backup()
        # self.Close()


