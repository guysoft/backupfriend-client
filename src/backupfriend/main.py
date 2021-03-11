import wx.adv
import wx
from wx import MenuBar, Panel, WindowList
import sys
from wx import xrc
import yaml
import os
import schedule
from dataclasses import dataclass
import subprocess
import time
from backupfriend.common import get_data_path, ensure_dir, resource_path
from collections.abc import Iterable
import wx.lib.inspection
import shutil
import shlex
from pubsub import pub


TRAY_ICON = os.path.join(os.path.dirname(__file__), "images", 'icon.png')
TRAY_TOOLTIP = 'BackupFriend'
CFG_UPDATE_MSG = "config_update"

# TODO:
# 1. Make settings window

debug = 'DEBUG' in os.environ and os.environ['DEBUG'] == "on"

DATA_PATH = get_data_path()

if "win" in sys.platform:
    CONFIG_PATH_DEFAULT = os.path.join(os.path.dirname(__file__), "config", "config-windows.yml")
else:
    CONFIG_PATH_DEFAULT = os.path.join(os.path.dirname(__file__), "config", "config.yml")
CONFIG_PATH = os.path.join(DATA_PATH, "config", "config.yml")

def get_config():
    if not os.path.isfile(CONFIG_PATH):
        ensure_dir(os.path.dirname(CONFIG_PATH))
        shutil.copy(CONFIG_PATH_DEFAULT, CONFIG_PATH)
    with open(CONFIG_PATH) as f:
        return yaml.load(f, Loader=yaml.FullLoader)
    return

def save_config():
    with open(CONFIG_PATH, 'w') as f:
        yaml.safe_dump(config, f)

config = get_config()

if "ssh" not in config["main"] and "win" not in sys.platform:
    ssh = subprocess.run(['which', 'ssh'], capture_output=True, text=True).stdout.strip()
    config["main"]["ssh"] = ssh
    save_config()

def _run_command(command, **kwargs):
    if debug:
        print(" ".join(command))
    p = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    stdout = p.stdout.read()
    stderr = p.stderr.read()
    try:
        stdout = stdout.decode("utf-8")
    except UnicodeDecodeError as e:
        print("Error: can't decode stdout")
        print(e)
        print(stdout)
        stdout = ""

    try:
        stderr = stderr.decode("utf-8")
    except UnicodeDecodeError as e:
        print("Error: can't decode stderr")
        print(stderr)
        print(e)
        stderr = ""

    return_value = [stdout, stderr]
    return return_value


def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item


class Settings(wx.Dialog):
    def __init__(self, settings, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)
        self.settings = settings

        self.panel = wx.Panel(self)
        self.button_ok = wx.Button(self.panel, label="OK")
        self.button_cancel = wx.Button(self.panel, label="Cancel")
        self.button_ok.Bind(wx.EVT_BUTTON, self.onOk)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.onCancel)

        self.checkboxes = []
        for i in range(3):
            checkbox = wx.CheckBox(self.panel, label=str(i))
            checkbox.SetValue(self.settings[i])
            self.checkboxes.append(checkbox)

        self.sizer = wx.BoxSizer()
        for checkbox in self.checkboxes:
            self.sizer.Add(checkbox)
        self.sizer.Add(self.button_ok)
        self.sizer.Add(self.button_cancel)

        self.panel.SetSizerAndFit(self.sizer)

    def onCancel(self, e):
        self.EndModal(wx.ID_CANCEL)

    def onOk(self, e):
        for i in range(3):
            self.settings[i] = self.checkboxes[i].GetValue()
        self.EndModal(wx.ID_OK)

    def GetSettings(self):
        return self.settings


class SettingsFrame(wx.Frame):
    """
    Class used for creating frames other than the main one
    """

    def __init__(self, title, parent=None):
        wx.Frame.__init__(self, parent=parent, title=title)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Centre()
        self.Show()
        if debug:
            print(self.GetParent().sync_jobs)
        ## End Window init stuff ##

        self.panel = wx.Panel(self)
        self.button_ok = wx.Button(self.panel, label="OK")
        self.button_cancel = wx.Button(self.panel, label="Cancel")

        self.checkboxes = []
        for i in range(3):
            checkbox = wx.CheckBox(self.panel, label=str(i))
            self.checkboxes.append(checkbox)

        self.sizer = wx.BoxSizer()
        for checkbox in self.checkboxes:
            self.sizer.Add(checkbox)
        self.sizer.Add(self.button_ok)
        self.sizer.Add(self.button_cancel)

        self.panel.SetSizerAndFit(self.sizer)

        # print(wx.geta.sync_jobs)

    def onClose(self, event):
        """"""
        print("closing")
        # TODO - also delete from memmory
        # self.Hide()
        self.Destroy()
        # print(self)


def get_object_by_id(panel, xrc, name, actual_id=None, child_current_level=None):
    if actual_id is None:
        actual_id = xrc.XRCID(name)

    # First recursion
    if child_current_level is None:
        child_current_level = panel.GetChildren()

    if hasattr(child_current_level, 'GetId') and child_current_level.GetId() == actual_id:
        print("WEWEADBaSIDA")
        return child_current_level

    if type(child_current_level) != WindowList:
        print(child_current_level.GetName())
    else:
        print(child_current_level)
        # sys.exit()

    if isinstance(child_current_level, Iterable):
        print('bo')
        for child in child_current_level:
            widget = child
            if widget.GetId() == actual_id:
                print("WEWEADBaSIDA")
                sys.exit()
                return widget

            # item = get_object_by_id(panel, xrc, name, actual_id, child)

            if item is not None:
                print("AWDEADNaSN")
                # return item


class MainFrame(wx.Frame):
    """
    Class used for creating frames other than the main one
    """

    def __init__(self, parent=None, title=None):
        self.res = xrc.XmlResource(os.path.join(os.path.dirname(__file__), "res", 'main.xrc'))

        wx.Frame.__init__(self, parent=parent, title=title)
        self.SetSize((1000, 700))
        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap(TRAY_ICON, wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        self.menuBar = self.res.LoadMenuBar("m_menubar1")
        self.panel = self.res.LoadPanel(self, "MainPanel")
        self.panel.SetLayoutDirection(wx.Layout_LeftToRight)
        self.SetLayoutDirection(wx.Layout_LeftToRight)

        # Menu Logic
        self.SetMenuBar(self.menuBar)
        self.Bind(wx.EVT_MENU, self.exit, id=xrc.XRCID('m_exit'))
        self.Bind(wx.EVT_MENU, self.show_public_key, id=xrc.XRCID('m_show_public_key'))
        self.Bind(wx.EVT_MENU, self.start_first_time_wizard, id=xrc.XRCID('m_generate_keys'))

        self.Bind(wx.EVT_MENU, self.open_settings, id=xrc.XRCID('m_settings'))
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.select_backup, id=xrc.XRCID('m_list_syncs'))
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.deselect_backup, id=xrc.XRCID('m_list_syncs'))
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.select_run, id=xrc.XRCID('m_list_runs'))

        self.Bind(wx.EVT_CLOSE, self.onClose)

        # Buttons
        self.m_run_btn = xrc.XRCCTRL(self.panel, "m_run")
        self.m_edit_btn = xrc.XRCCTRL(self.panel, "m_edit")
        self.m_delete_btn = xrc.XRCCTRL(self.panel, "m_delete")

        self.Bind(wx.EVT_BUTTON, self.run_job, self.m_run_btn)
        self.Bind(wx.EVT_BUTTON, self.delete_job, self.m_delete_btn)
        self.Bind(wx.EVT_BUTTON, self.show_edit_dialog, self.m_edit_btn)
        self.Bind(wx.EVT_BUTTON, self.show_create_dialog, id=xrc.XRCID('m_add'))

        self.Centre()
        self.Show()

        if not os.path.isfile(os.path.join(DATA_PATH, "id_rsa")):
            self.start_first_time_wizard()

        self.m_log_label = xrc.XRCCTRL(self.panel, 'm_log_label')

        # wx.lib.inspection.InspectionTool().Show()

        ## End Window init stuff ##

        # print(len(self.GetParent().sync_jobs))

        self.m_console = xrc.XRCCTRL(self.panel, 'm_console')

        self.m_list_syncs = xrc.XRCCTRL(self.panel, 'm_list_syncs')
        self.m_list_syncs.data_keys = ["name", "dest", "every", "time"]

        self.m_list_runs = xrc.XRCCTRL(self.panel, 'm_list_runs')
        self.m_list_runs.data_keys = ["id", "Time Ran"]

        for i, key in enumerate(self.m_list_runs.data_keys):
            self.m_list_runs.InsertColumn(i, key)

        for i, key in enumerate(self.m_list_syncs.data_keys):
            self.m_list_syncs.InsertColumn(i, key)

        self.update_list_sync()
        pub.subscribe(self.update_list_sync, CFG_UPDATE_MSG)

        # print(wx.geta.sync_jobs)

    def select_backup(self, event):
        item = event.GetItem()
        job_name = item.GetText()
        self.current_job = job_name
        self.display_job(job_name)

        self.m_run_btn.Enable()
        self.m_edit_btn.Enable()
        self.m_delete_btn.Enable()

        return

    def deselect_backup(self, event):
        self.current_job = None

        self.m_run_btn.Disable()
        self.m_edit_btn.Disable()
        self.m_delete_btn.Disable()

    def run_job(self, event):
        if debug:
            print("Running: " + str(self.current_job))
        job = self.GetParent().get_job_by_name(self.current_job)
        if not job.running():
            job.run_backup()
        else:
            print("Job already running")

    def delete_job(self, event):
        dialog = self.res.LoadDialog(self, 'delete_job_dialog')
        dialog.ShowModal(job_name=self.current_job)
        self.current_job = None

        return


    def start_first_time_wizard(self, event=None):
        wizard = self.res.LoadObject(None, 'first_run_wizard', 'wxWizard')
        page1 = wx.xrc.XRCCTRL(wizard, 'm_wizPage1')
        wizard.RunWizard(page1)

    def select_run(self, event):
        self.current_run = event.Index
        item = event.GetItem()
        run_name = item.GetText()
        if debug:
            print("Selected run: " + run_name)
        self.display_run(self.current_job, run_name)

    def display_job(self, job_name):
        self.m_list_runs.DeleteAllItems()
        self.m_console.SetValue("")
        job = self.GetParent().get_job_by_name(job_name)

        for i, file_name in enumerate(job.get_log_files()):
            self.m_list_runs.InsertItem(i, job.name)
            if debug:
                print(i, file_name)
            self.m_list_runs.SetItem(i, self.m_list_runs.data_keys.index("id"), file_name)
            self.m_list_runs.SetItem(i, self.m_list_runs.data_keys.index("Time Ran"), job.get_run_created(file_name))
        self.m_list_runs.resizeLastColumn(0)

        return

    def display_run(self, job_name, run_name):
        self.m_console.SetValue("")
        log = self.GetParent().get_job_by_name(job_name).get_log(run_name)

        self.m_console.SetValue(log)
        return

    def update_list_sync(self):
        items_num = self.m_list_syncs.GetItemCount();
        sync_jobs_list = list(self.GetParent().sync_jobs)
        self.m_list_syncs.DeleteAllItems()

        for i, job in enumerate(sync_jobs_list):
            self.m_list_syncs.InsertItem(i, job.name)
            for j, key in enumerate(self.m_list_syncs.data_keys):
                self.m_list_syncs.SetItem(i, j, job.__dict__[key])

        self.m_list_syncs.resizeLastColumn(0)

    def exit(self, event):
        wx.Exit()
        return

    def show_public_key(self, event):
        dialog = self.res.LoadDialog(self, 'show_key_dialog')
        dialog.ShowModal()
        return

    def show_edit_dialog(self, event):
        dialog = self.res.LoadDialog(self, 'edit_job_dialog')
        dialog.ShowModal()
        return

    def show_create_dialog(self, event):
        dialog = self.res.LoadDialog(self, 'job_dialog')
        dialog.ShowModal()
        return

    def open_settings(self, event):
        if debug:
            print("open settings")
        if "win" in sys.platform:
            os.system(CONFIG_PATH)
        else:
            os.system("xdg-open '" + CONFIG_PATH + "'")
        return

    def onClose(self, event):
        print("closing")
        # TODO - also delete from memmory
        # self.Hide()
        self.Destroy()
        # print(self)


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        self.frame = frame
        self.frame.SetLayoutDirection(wx.Layout_LeftToRight)
        super(TaskBarIcon, self).__init__()
        self.set_icon(TRAY_ICON)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        # TODO make settings menu
        # create_menu_item(menu, 'Settings', self.on_hello)
        self.x = create_menu_item(menu, 'Main', self.on_open_main)
        menu.AppendSeparator()
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.Icon(path)
        self.SetIcon(icon, TRAY_TOOLTIP)

    def on_left_down(self, event):
        print('Tray icon was left-clicked.')
        # TODO: When clicked and main is open, should ask if to minimize
        self.on_open_main(None)

    def on_hello(self, event):
        if debug:
            print('Hello, world!')
        if not hasattr(self, 'settings_frame'):
            self.settings_frame = SettingsFrame("Settings", self.frame)
        else:
            if not self.settings_frame:
                print("closed")
                self.settings_frame = SettingsFrame("Settings", self.frame)
            # print(self.settings_frame.Show())
            print(dir(self.settings_frame))

    def on_open_main(self, event):
        if debug:
            print('Opening Main')
        if not hasattr(self, 'main_frame'):

            # self.main_frame = res.LoadObject(self.frame, "MyFrame1", "wxFrame")
            self.main_frame = MainFrame(self.frame, "Main")
        else:
            if not self.main_frame:
                print("closed")
                self.main_frame = MainFrame(self.frame, "Main")
            print(dir(self.main_frame))

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Close()


class SyncProcess(wx.Process):
    def __init__(self, *args, **kw):
        self.terminated = False
        wx.Process.__init__(self, *args, **kw)

    def OnTerminate(self, pid, status):
        self.terminated = True


@dataclass
class Backup:
    name: str
    source: str
    dest: str
    port: str
    key: str
    every: str
    time: str
    window: wx.Frame

    def prepare_job(self):
        self.process_object = None
        self.pid = None
        if debug:
            print("Starting: " + str(self.name))
        self.log_file = os.path.join(self.get_run_folder(), str(self.get_id()))
        return

    def __post_init__(self):
        self.process_object = None
        self.pid = None
        if self.every == "daily":
            # schedule.every().seconds.do(
            #     lambda: self.run_backup())
            schedule.every().day.at(self.time).do(lambda: self.run_backup())

    def get_run_folder(self):
        return os.path.join(DATA_PATH, "jobs_data", str(self.name))

    def get_id(self):
        run_folder = self.get_run_folder()
        if not ensure_dir(run_folder):
            return 0

        log_files = self.get_log_files()
        for i, folder in enumerate(log_files):
            # print(i, folder)
            if str(i) != str(folder):
                return str(i)

        return len(log_files)

    def get_log_files(self):
        """ Returns the list of log files sorted by id
        """
        run_folder = self.get_run_folder()
        if not os.path.isdir(run_folder):
            return []
        return sorted(os.listdir(run_folder), key=lambda x: float(x))

    def update_log(self, text):
        with open(self.log_file, "ab") as log:
            log.write(text)

    def get_log(self, run_name):
        with open(os.path.join(self.get_run_folder(), run_name), "r") as log:
            return_value = log.read()
        return return_value

    def get_run_created(self, run_id):
        run_path = os.path.join(self.get_run_folder(), run_id)

        return time.ctime(os.path.getctime(run_path))

    def running(self):
        return self.process_object is not None and ( not self.process_object.terminated)

    def run_backup(self):
        self.prepare_job()
        if debug:
            print("hello!!!!!!!!!!!!!!")
        config = get_config()

        self.process_object = SyncProcess(self.window)
        self.process_object.Redirect()
        bin_path = config["main"]["bin"]
        ssh_path = config["main"]["ssh"]

        if "win" in sys.platform:
            if debug:
                print("windows detected, adjusting binary path in package")
            
            # rdiff_path = r'"C:\Users\user\Desktop\backupfriend-client\src\rdiff-backup.exe"'
            # ssh_path = r'C:\Users\user\Desktop\backupfriend-client\ssh.exe'            
            ssh_path = ssh_path.replace("__package_path__", resource_path())
            bin_path = bin_path.replace("__package_path__", resource_path())
            
            cmd = [bin_path, "-v6", "--remote-schema",
                   '"' + ssh_path + " -p " + str(self.port) + " -o StrictHostKeyChecking=no -i '" + self.key + "' %s rdiff-backup --server" + '"', "--", self.source,
                   self.dest]
            command = " ".join(cmd)
            known_hosts_location = os.path.realpath(os.path.join(os.path.dirname(ssh_path), "..", "home", os.getlogin()))
            ensure_dir(known_hosts_location)

        else:
            cmd = [bin_path,
                   "-v6",
                   " --remote-schema 'ssh -p " + str(self.port) + " -o StrictHostKeyChecking=no -i " + self.key + " %s rdiff-backup --server'",
                   "--", self.source, self.dest]
            command = " ".join(cmd)

        if debug:
            print("running: " + command)
        print("running: " + str(command))
        
        self.pid = wx.Execute(command, wx.EXEC_ASYNC, callback=self.process_object)

        if debug:
            print("pid: " + str(self.pid))
        time.sleep(1)
        stream = self.process_object.GetInputStream()

        while stream is not None and stream.CanRead():
            text = stream.read()
            self.update_log(text)
            wx.LogMessage(text)

        stream_err = self.process_object.GetErrorStream()

        while stream_err is not None and stream_err.CanRead():
            text = stream_err.read()
            self.update_log(text)
            wx.LogMessage(text)

        print("Finish reading")

        return


class MainInvisibleWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None)

        self.sync_jobs = []
        self.add_backups(config["backups"], True)
        # self.Bind(wx.EVT_IDLE, self.OnIdle)

        self.on_timer()

    def add_backups(self, backups_list, in_config=False):
        jobs_names = list(map(lambda backup: backup.name, self.sync_jobs))

        for backup in backups_list:
            # Sanity_check
            if backup["name"] in jobs_names:
                raise ValueError(f"'{backup['name']}' is alredy exist")
            if backup["name"] == "":
                raise ValueError("Name can't be empty")
            if backup["source"] == "":
                raise ValueError("Source can't be empty")
            if backup["dest"] == "":
                raise ValueError("Destination can't be empty")

            if not in_config:
                config["backups"].append(backup)
            backup_class = Backup(**backup, window=self)
            self.sync_jobs.append(backup_class)

        if not in_config:
            save_config()

        pub.sendMessage(CFG_UPDATE_MSG)

    def delete_backup(self, backup_name):
        try:
            del_index = next(i for i, elem in enumerate(config["backups"]) if elem["name"] == backup_name)
            config["backups"].pop(del_index)

            del_index = next(i for i, elem in enumerate(self.sync_jobs) if elem.name == backup_name)
            self.sync_jobs.pop(del_index)
        except StopIteration:
            print(f"Error: no backup named {backup_name}")

        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f)

        pub.sendMessage(CFG_UPDATE_MSG)

    def update_backup(self, backup_name, edit_dict):
        config_index = next(
            i for i, elem in enumerate(config["backups"]) if elem["name"] == backup_name)

        jobs_index = next(
            i for i, elem in enumerate(self.sync_jobs) if elem.name == backup_name)

        for key, val in edit_dict.items():
            config["backups"][config_index][key] = val
            self.sync_jobs[jobs_index].__dict__[key] = val

        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f)

        pub.sendMessage(CFG_UPDATE_MSG)

    def on_timer(self):
        # wx.CallLater(1000 * 60, self.on_timer)
        wx.CallLater(1000, self.on_timer)
        schedule.run_pending()
        if self.sync_jobs is not None:
            for sync_job in self.sync_jobs:
                if sync_job.process_object is not None:
                    if sync_job.process_object.terminated:
                        print("terminated")

                        stream = sync_job.process_object.GetInputStream()

                        while stream is not None and stream.CanRead():
                            text = stream.read()
                            sync_job.update_log(text)

                            print(text.decode())

                        stream_err = sync_job.process_object.GetErrorStream()

                        while stream_err is not None and stream_err.CanRead():
                            text = stream_err.read()
                            sync_job.update_log(text)

                        sync_job.process_object = None
                    else:
                        try:
                            stream = sync_job.process_object.GetInputStream()

                            while stream is not None and stream.CanRead():
                                text = stream.read()
                                sync_job.update_log(text)

                                print(text.decode())

                            stream_err = sync_job.process_object.GetErrorStream()

                            while stream_err is not None and stream_err.CanRead():
                                text = stream_err.read()
                                sync_job.update_log(text)

                                print(text.decode())
                        except RuntimeError as e:
                            print(e)
                            # import code;
                            # code.interact(local=dict(globals(), **locals()))

                # print("Done idle")

    def get_job_by_name(self, name):
        for job in self.sync_jobs:
            if debug:
                print(job.name)
                print(name)
            if job.name == name:
                return job
        return


##    def OnIdle(self, evt):
##        if self.sync_jobs is not None:
##            for sync_job in self.sync_jobs:
##                if sync_job.process_object is not None:
##                    if sync_job.process_object.terminated:
##                        print("terminated")
##
##                        stream = sync_job.process_object.GetInputStream()
##
##                        while stream is not None and stream.CanRead():
##                            text = stream.read()
##                            sync_job.update_log(text)
##
##                            print(text.decode())
##
##                        stream_err = sync_job.process_object.GetErrorStream()
##
##                        while stream_err is not None and stream_err.CanRead():
##                            text = stream_err.read()
##                            sync_job.update_log(text)
##
##                        sync_job.process_object = None
##                    else:
##                        try:
##                            stream = sync_job.process_object.GetInputStream()
##
##                            while stream is not None and stream.CanRead():
##                                text = stream.read()
##                                sync_job.update_log(text)
##
##                                print(text.decode())
##
##                            stream_err = sync_job.process_object.GetErrorStream()
##
##                            while stream_err is not None and stream_err.CanRead():
##                                text = stream_err.read()
##                                sync_job.update_log(text)
##
##                                print(text.decode())
##                        except RuntimeError as e:
##                            print(e)
##                            # import code;
##                            # code.interact(local=dict(globals(), **locals()))
##
##                # print("Done idle")


class App(wx.App):

    def OnInit(self):
        wx.Log.SetActiveTarget(wx.LogStderr())

        if debug:
            print("Starting App OnInit")
        frame = MainInvisibleWindow()
        self.SetTopWindow(frame)
        taskbar = TaskBarIcon(frame)

        if not os.path.isfile(os.path.join(DATA_PATH, "id_rsa")):
            taskbar.on_open_main(None)
        # frame2 = MainFrame(frame, "Main")

        return True


def main():
    app = App(False)
    app.MainLoop()


if __name__ == '__main__':
    main()
