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
from shlex import quote
import webbrowser
import traceback

def get_os():
    if sys.platform.startswith("win"):
        return "windows"
    elif sys.platform == "darwin":
        return "osx"
    elif sys.platform == "linux":
        return "linux"
    else:
        return "unkonwn"

APP_PATH = os.path.join(os.path.dirname(__file__))

# OS X app bin path.
APP_BIN_PATH = None
if get_os() == "osx":
    if not __file__.endswith(".py"):
        APP_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        APP_BIN_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "MacOS"))

TRAY_ICON = os.path.join(APP_PATH, "images", 'icon.png')
TRAY_TOOLTIP = 'BackupFriend'
CFG_UPDATE_MSG = "config_update"
START_JOB_MSG = "job_start"
END_JOB_MSG = "job_end"

# TODO:
# 1. Make settings window

debug = 'DEBUG' in os.environ and os.environ['DEBUG'] == "on"

DATA_PATH = get_data_path()


if get_os() == "windows":
    CONFIG_PATH_DEFAULT = os.path.join(os.path.dirname(__file__), "config", "config-windows.yml")
elif get_os() == "osx":
    CONFIG_PATH_DEFAULT = os.path.join(APP_PATH, "config", "config-osx.yml")
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

if "ssh" not in config["main"] and not get_os() == "windows":
    ssh = subprocess.run(['which', 'ssh'], capture_output=True, text=True).stdout.strip()
    config["main"]["ssh"] = ssh
    save_config()

def _run_command(command, **kwargs):
    is_timeout = False
    if debug:
        print(" ".join(command))
    p = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    try:
        stdout, stderr = p.communicate(timeout=5)
    except subprocess.TimeoutExpired as e:
        p.kill()
        stdout,stderr = p.communicate()
        is_timeout = True
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

    return_value = [stdout, stderr, is_timeout]
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
            print(self.sync_jobs)
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

    def __init__(self, title=None):
        # Sync control logic
        self.sync_jobs = []
        self.add_backups(config["backups"], True)
        # self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.on_timer()
        
        
        self.res = xrc.XmlResource(os.path.join(APP_PATH, "res", 'main.xrc'))

        wx.Frame.__init__(self, parent=None, title=title)
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
        self.m_go_to_server_btn = xrc.XRCCTRL(self.panel, "m_go_to_server")

        self.Bind(wx.EVT_BUTTON, self.run_job, self.m_run_btn)
        self.Bind(wx.EVT_BUTTON, self.show_edit_dialog, self.m_edit_btn)
        self.Bind(wx.EVT_BUTTON, self.delete_job, self.m_delete_btn)
        self.Bind(wx.EVT_BUTTON, self.go_to_server, self.m_go_to_server_btn)
        self.Bind(wx.EVT_BUTTON, self.show_create_dialog, id=xrc.XRCID('m_add'))

        self.Centre()
        self.Show()

        def is_first_run():
            return not os.path.isfile(os.path.join(DATA_PATH, "id_rsa"))

        if is_first_run():
            self.start_first_time_wizard()

        
        if not is_first_run():
            self.Hide()

        self.m_log_label = xrc.XRCCTRL(self.panel, 'm_log_label')

        # wx.lib.inspection.InspectionTool().Show()

        ## End Window init stuff ##

        # print(len(self.sync_jobs))

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
        pub.subscribe(self.update_start_job, START_JOB_MSG)
        pub.subscribe(self.update_end_job, END_JOB_MSG)

        # print(wx.geta.sync_jobs)
        
    # Sync functions logic
    def add_backups(self, backups_list, in_config=False):
        jobs_names = list(map(lambda backup: backup.name, self.sync_jobs))

        for backup in backups_list:
            # Sanity_check
            if backup["name"] in jobs_names:
                raise ValueError(f"Job with the name '{backup['name']}' already exists")
            if backup["name"] == "":
                raise ValueError("Name can't be empty")
            if backup["source"] == "":
                raise ValueError("Source can't be empty")
            if backup["dest"] == "":
                raise ValueError("Destination can't be empty")

            backup["key"] = os.path.expanduser(backup["key"])
            backup["source"] = os.path.expanduser(backup["source"])

            # Fix missing fields from older builds
            for item in ["server_url", "server_username"]:
                if item not in backup:
                    backup[item] = ""

            if not in_config:
                config["backups"].append(backup)
            backup_class = Backup(**backup, window=self, test_dummy=False)
            self.sync_jobs.append(backup_class)

        if not in_config:
            save_config()

        pub.sendMessage(CFG_UPDATE_MSG)

    def delete_backup(self, backup_name):
        try:
            del_index = next(
                i for i, elem in enumerate(config["backups"]) if elem["name"] == backup_name)
            config["backups"].pop(del_index)

            del_index = next(
                i for i, elem in enumerate(self.sync_jobs) if elem.name == backup_name)
            self.sync_jobs.pop(del_index)
        except StopIteration:
            print(f"Error: no backup named {backup_name}")

        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f)

        run_dir = os.path.join(DATA_PATH, "jobs_data", backup_name)
        if os.path.isdir(run_dir):
            shutil.rmtree(run_dir)

        pub.sendMessage(CFG_UPDATE_MSG)

    def update_backup(self, backup_name, edit_dict):
        config_index = next(
            i for i, elem in enumerate(config["backups"]) if elem["name"] == backup_name)

        jobs_index = next(
            i for i, elem in enumerate(self.sync_jobs) if elem.name == backup_name)

        for key, val in edit_dict.items():
            if key=="name":
                jobs_names = list(map(lambda backup:
                                        backup.name if backup.name != backup_name else '',
                                      self.sync_jobs))
                if val in jobs_names:
                    raise ValueError(f"'{val}' is alredy exist")

                # rename the run dir
                old_run_dir = os.path.join(DATA_PATH, "jobs_data",
                                           config["backups"][config_index]["name"])
                new_run_dir = os.path.join(DATA_PATH, "jobs_data", val)
                if os.path.isdir(old_run_dir):
                    os.rename(old_run_dir, new_run_dir)

            config["backups"][config_index][key] = val
            self.sync_jobs[jobs_index].__dict__[key] = val

        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f)

        pub.sendMessage(CFG_UPDATE_MSG)

    def get_backup_by_name(self, backup_name):
        job_index = next(
            i for i, elem in enumerate(self.sync_jobs) if elem.name == backup_name)

        return self.sync_jobs[job_index]

    def on_timer(self):
        # wx.CallLater(1000 * 60, self.on_timer)
        wx.CallLater(1000, self.on_timer)
        schedule.run_pending()
        if self.sync_jobs is not None:
            for sync_job in self.sync_jobs:
                if sync_job.process_object is not None:
                    if sync_job.process_object.terminated:
                        print("terminated")
                        # TODO: Parse output and mark success False on fail
                        pub.sendMessage(END_JOB_MSG, name=sync_job.name, success=True)

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
    # End sync functions logic

    def select_backup(self, event):
        item = event.GetItem()
        job_name = item.GetText()
        self.current_job = job_name
        self.display_job(job_name)

        self.m_run_btn.Enable()
        self.m_edit_btn.Enable()
        self.m_delete_btn.Enable()
        self.m_go_to_server_btn.Enable()

        return

    def deselect_backup(self, event):
        self.current_job = None

        self.m_run_btn.Disable()
        self.m_edit_btn.Disable()
        self.m_delete_btn.Disable()

    def run_job(self, event):
        if debug:
            print("Running: " + str(self.current_job))
        job = self.get_job_by_name(self.current_job)
        if not job.running():
            job.run_backup()
        else:
            print("Job already running")
            wx.MessageDialog(self, 'Job "' + job.name + '" already running', caption="Job already running",
              style=wx.OK|wx.CENTRE, pos=wx.DefaultPosition).ShowModal()


    def delete_job(self, event):
        dialog = self.res.LoadDialog(self, 'delete_job_dialog')
        dialog.ShowModal(job_name=self.current_job)
        self.current_job = None

        return

    def go_to_server(self, event):
        job = self.get_job_by_name(self.current_job)
        print(job.server_url)
        print(job.server_username)
        dest = job.dest.split("::")[1]
        dest = "/".join(dest.split("/")[2:])

        url = job.server_url + "/browse/" + job.server_username + "/" + dest
        if debug:
            print(url)
        webbrowser.open(url)
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
        job = self.get_job_by_name(job_name)

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
        job = self.get_job_by_name(job_name)
        if job is not None:
            log = job.get_log(run_name)
            self.m_console.SetValue(log)
        else:
            self.m_console.SetValue("Log not generated")
        return

    def update_list_sync(self):
        items_num = self.m_list_syncs.GetItemCount()
        sync_jobs_list = list(self.sync_jobs)
        self.m_list_syncs.DeleteAllItems()

        for i, job in enumerate(sync_jobs_list):
            self.m_list_syncs.InsertItem(i, job.name)
            for j, key in enumerate(self.m_list_syncs.data_keys):
                self.m_list_syncs.SetItem(i, j, job.__dict__[key])

        self.m_list_syncs.resizeLastColumn(0)

    def set_row_runnung(self, name, color):
        items_num = self.m_list_syncs.GetItemCount()
        name_col = self.m_list_syncs.data_keys.index("name")

        for i in range(items_num):
            name_in_list = self.m_list_syncs.GetItem(i, name_col).GetText()
            if name_in_list == name:
                self.m_list_syncs.SetItemTextColour(i, color)
        return

    def add_new_job_to_run_list(self, name):
        name_col = self.m_list_syncs.data_keys.index("name")

        selected_item = self.m_list_syncs.GetFirstSelected()

        items_num = self.m_list_syncs.GetItemCount()
        # TODO: debug wx._core.wxAssertionError exception of line below
        try:
            name_in_list = self.m_list_syncs.GetItem(selected_item, name_col).GetText()

            job = self.get_job_by_name(name)

            # Add item to list if selected
            item_count = len(job.get_log_files())
            if name_in_list == name:
                self.m_list_runs.InsertItem(item_count, str(item_count))
                if debug:
                    print(item_count)
                self.m_list_runs.SetItem(item_count, self.m_list_runs.data_keys.index("id"), str(item_count))
                self.m_list_runs.SetItem(item_count, self.m_list_runs.data_keys.index("Time Ran"), "now")
            self.m_list_runs.resizeLastColumn(0)
        except wx._core.wxAssertionError as e:
            print("Got wx._core.wxAssertionError")
            print(str(traceback.format_exc()))
            print(e)

    def update_start_job(self, name):
        self.set_row_runnung(name, "blue")
        self.add_new_job_to_run_list(name)


    def update_end_job(self, name, success):
        if success:
            self.set_row_runnung(name, "green")
        else:
            self.set_row_runnung(name, "red")

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
        if get_os() == "windows":
            os.system("notepad " + quote(CONFIG_PATH))
        elif get_os() == "osx":
            os.system("open " + quote(CONFIG_PATH))
        else:
            os.system("xdg-open '" + CONFIG_PATH + "'")
        return

    def onClose(self, event):
        print("closing")
        self.Hide()
        # self.Destroy()
        # print(self)


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame, app):
        self.frame = frame
        self.app = app
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
        self.frame.Show()
        self.frame.Raise()
        self.app.SetTopWindow(self.frame)


    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Close()
        self.frame.Destroy()


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
    server_url: str
    server_username: str
    every: str
    time: str
    window: wx.Frame
    test_dummy: bool

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
        if "__user_data__" in self.key:
            self.key = self.key.replace("__user_data__", "")
            if self.key.startswith("\\"):
                self.key = self.key[1:]
            self.key = os.path.join(DATA_PATH, self.key)
        
        if not self.test_dummy and self.every == "daily":
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
        log_file = os.path.join(self.get_run_folder(), run_name)
        if not os.path.isfile(log_file):
            return "Log empty"
        with open(log_file, "r") as log:
            return_value = log.read()
        return return_value

    def get_run_created(self, run_id):
        run_path = os.path.join(self.get_run_folder(), run_id)

        return time.ctime(os.path.getctime(run_path))

    def running(self):
        return self.process_object is not None and ( not self.process_object.terminated)

    def test_connection(self):
        # TODO: Test if path to ssh command exist beforehand
        if not os.path.isdir(self.source):
            return "Path does not exist"

        if self.key == "":
            return "SSH key can't be empty"

        if not os.path.isfile(self.key):
            return "SSH key path does not exist"

        _, ssh_path = self.get_bin_ssh_path()
        
        hostname_and_user = self.dest.split("::")[0]
        hostname = hostname_and_user.split("@")[1]
        dest_path = self.dest.split("::")[1]

        command = [ssh_path, hostname_and_user, "-p", str(self.port), "-o", "StrictHostKeyChecking=no", "-i", self.key, "whoami"]

        try:
            stdout, stderror, is_timeout = _run_command(command)
            if is_timeout:
                return "Failed to conenct to server: " + str(hostname)
            if stderror != "":
                return stderror
        except Exception as e:
            return "Got exception when running command: " + str(e)
        

        # At this point we have a connection that works, the dest folder might be missing

        command = [ssh_path, hostname_and_user, "-p", str(self.port), "-o", "StrictHostKeyChecking=no", "-i", self.key, "mkdir -p " + dest_path]

        try:
            stdout, stderror, is_timeout = _run_command(command)
            if is_timeout:
                return "Failed to conenct to server: " + str(hostname)
            if stderror != "":
                return "Folder on server does not exist or has no permission: " + dest_path
        except Exception as e:
            return "Got exception when running command: " + str(e)

        return "Connection succeeded"
    
    def get_bin_ssh_path(self):
        bin_path = config["main"]["bin"]
        ssh_path = config["main"]["ssh"]

        if get_os() == "windows":
            if debug:
                print("windows detected, adjusting binary path in package")
            
            # rdiff_path = r'"C:\Users\user\Desktop\backupfriend-client\src\rdiff-backup.exe"'
            # ssh_path = r'C:\Users\user\Desktop\backupfriend-client\ssh.exe'            
            ssh_path = ssh_path.replace("__package_path__", resource_path())
            bin_path = bin_path.replace("__package_path__", resource_path())
            
            # Handle in mac first run from app, or first run from python script
            if APP_BIN_PATH is not None:
                bin_path = bin_path.replace("__app_bin_path__", APP_BIN_PATH)
            else:
                bin_path = bin_path.replace("__app_bin_path__", "/usr/local/bin")
        return bin_path, ssh_path
    
    def run_backup(self):
        pub.sendMessage(START_JOB_MSG, name=self.name)
        self.prepare_job()
        if debug:
            print("hello!!!!!!!!!!!!!!")
        config = get_config()

        self.process_object = SyncProcess(self.window)
        self.process_object.Redirect()
        
        bin_path, ssh_path = self.get_bin_ssh_path()
        
        if get_os() == "windows":
            cmd = [bin_path, "-v6", "--remote-schema",
                   '"' + ssh_path + " -p " + str(self.port) + " -o StrictHostKeyChecking=no -i '" + self.key + "' %s rdiff-backup --server" + '"', "--", '"' + self.source + '"',
                   self.dest]
            command = " ".join(cmd)
            
            known_hosts_location = os.path.realpath(os.path.join(os.path.dirname(ssh_path), "..", "home", os.getlogin()))
            ensure_dir(known_hosts_location)

        else:
            cmd = [bin_path,
                   "-v6",
                   " --remote-schema 'ssh -p " + str(self.port) + " -o StrictHostKeyChecking=no -i \"" + self.key + "\" %s rdiff-backup --server'",
                   "--", quote(self.source), quote(self.dest)]
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
        frame = MainFrame("BackupFriend")
        self.SetTopWindow(frame)
        taskbar = TaskBarIcon(frame, self)

        # if not os.path.isfile(os.path.join(DATA_PATH, "id_rsa")):
        #     taskbar.on_open_main(None)
        # frame2 = MainFrame(frame, "Main")

        return True


def main():
    app = App(False)
    app.MainLoop()


if __name__ == '__main__':
    main()
