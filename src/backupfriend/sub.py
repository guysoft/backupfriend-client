import wx
import os.path
from wx.adv import Wizard
from wx.lib.mixins import listctrl
from wx import xrc
from backupfriend.make_ssh_key import generate_keys
from backupfriend.common import get_data_path
from abc import ABC, abstractmethod
from backupfriend.main import Backup

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


class AbstractJobDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        wx.Dialog.__init__(self, *args, **kw)
        self.Bind(wx.EVT_BUTTON, self.close, id=xrc.XRCID('m_cancel'))
        self.Bind(wx.EVT_BUTTON, self.save, id=xrc.XRCID('m_save'))
        self.Bind(wx.EVT_BUTTON, self.test, id=xrc.XRCID('m_test'))

        return


    def close(self, event):
        self.Close()

    def test(self, event):
        """ Test button for connection """
        m_info = xrc.XRCCTRL(self, 'm_info')
        m_info.SetLabel("Testing connection")

        backup_dict = self.gather_all_fields()

        test_backup = Backup(**backup_dict, window=self, test_dummy=True)
        result = test_backup.test_connection()
        m_info.SetLabel(result)

        print(result)
        return

    def gather_all_fields(self):
        return {
            "name": xrc.XRCCTRL(self, 'm_name').GetValue(),
            "source": xrc.XRCCTRL(self, 'm_source').GetPath(),
            "dest": xrc.XRCCTRL(self, 'm_dest').GetValue(),
            "port": xrc.XRCCTRL(self, 'm_port').GetValue(),
            "server_url": xrc.XRCCTRL(self, 'm_server_url').GetValue(),
            "server_username": xrc.XRCCTRL(self, 'm_server_username').GetValue(),
            "key": xrc.XRCCTRL(self, 'm_key_picker').GetPath(),
            "every": "daily",
            "time": self._time2str(xrc.XRCCTRL(self, 'm_time').GetTime())
        }

    def save(self, event):
        backup_dict = self.gather_all_fields()

        try:
            if backup_dict["key"] == "":
                raise ValueError("SSH key can't be empty")
            elif not os.path.isfile(backup_dict["key"]):
                raise ValueError("SSH key path does not exist")

            self.updateFunction(backup_dict)
            self.Close()
        except ValueError as e:
            wx.MessageBox(str(e), 'Error', wx.OK | wx.ICON_EXCLAMATION)

    def _time2str(self, time):
        time_str = map(str, time[:2])
        time_str = map(lambda st: st if len(st) >1 else "0" + st, time_str)
        time_str = ':'.join(time_str)
        return time_str

    def updateFunction(self, backup_dict):
        pass


class AddJobDialog(AbstractJobDialog):
    def ShowModal(self, *args, **kw):
        m_key = xrc.XRCCTRL(self, 'm_key_picker')
        key_path = os.path.join(DATA_PATH, "id_rsa")
        # m_key.SetInitialDirectory(os.path.dirname(key_path))
        m_key.SetPath(key_path)
        print(m_key.GetPath())
        m_key.Refresh()
        return wx.Dialog.ShowModal(self, *args, **kw)

    def updateFunction(self, backup_dict):
        self.GetParent().add_backups([backup_dict])


class EditJobDialog(AbstractJobDialog):
    def ShowModal(self, *args, **kw):
        self.job_name = self.GetParent().current_job
        self.backup_to_update = self.GetParent().get_backup_by_name(
            self.job_name)

        xrc.XRCCTRL(self, 'm_name').SetValue(self.backup_to_update.name)
        xrc.XRCCTRL(self, 'm_source').SetPath(self.backup_to_update.source)
        xrc.XRCCTRL(self, 'm_dest').SetValue(self.backup_to_update.dest)
        xrc.XRCCTRL(self, 'm_port').SetValue(self.backup_to_update.port)
        xrc.XRCCTRL(self, 'm_key_picker').SetPath(self.backup_to_update.key)
        xrc.XRCCTRL(self, 'm_server_url').SetValue(self.backup_to_update.server_url)
        xrc.XRCCTRL(self, 'm_server_username').SetValue(self.backup_to_update.server_username)

        m_time = xrc.XRCCTRL(self, 'm_time')
        time_elems = self.backup_to_update.time.split(':')
        time_elems = map(int, time_elems)
        m_time.SetTime(*time_elems, 0)

        return wx.Dialog.ShowModal(self, *args, **kw)

    def updateFunction(self, backup_dict):
        self.GetParent().update_backup(self.job_name, backup_dict)


class DeleteJobDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        wx.Dialog.__init__(self, *args, **kw)
        self.Bind(wx.EVT_BUTTON, self._close, id=xrc.XRCID('m_delete_btn_no'))
        self.Bind(wx.EVT_BUTTON, self._delete_job, id=xrc.XRCID('m_delete_btn_yes'))

    def ShowModal(self, *args, **kw):
        self.job_name = kw.pop('job_name')
        xrc.XRCCTRL(self, "m_static_text_delete").SetLabel(
            f"Are you sure you want to delete '{self.job_name}'?")

        return wx.Dialog.ShowModal(self, *args, **kw)

    def _delete_job(self, event):
        self.GetParent().delete_backup(self.job_name)
        self.Close()

    def _close(self, event):
        self.Close()
