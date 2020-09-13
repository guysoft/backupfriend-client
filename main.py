import wx.adv
import wx
import yaml
TRAY_TOOLTIP = 'Name' 
TRAY_ICON = 'icon.png'
import os
import schedule
from dataclasses import dataclass
import subprocess
import time

#TODO:
# 1. Save logs so they can be shown in main screen
# 2. main frame needs to show the backups and stuff from them


debug = 'DEBUG' in os.environ and os.environ['DEBUG'] == "on"


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yml")


def get_config():
    with open(CONFIG_PATH) as f:
        return yaml.load(f, Loader=yaml.FullLoader)
    return


config = get_config()


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
        print(parent)
        wx.Frame.__init__(self, parent=parent, title=title)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Centre()
        self.Show()
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
        #self.Hide()
        self.Destroy()
        # print(self)


class MainFrame(wx.Frame):
    """
    Class used for creating frames other than the main one
    """

    def __init__(self, title, parent=None):
        wx.Frame.__init__(self, parent=parent, title=title)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Centre()
        self.Show()

        ## End Window init stuff ##

        print("aa")
        print(len(self.GetParent().sync_jobs))

        for job in list(self.GetParent().sync_jobs):
            print(type(job))

        # print(wx.geta.sync_jobs)

    def onClose(self, event):
        """"""
        print("closing")
        # TODO - also delete from memmory
        #self.Hide()
        self.Destroy()
        # print(self)


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        self.frame = frame
        super(TaskBarIcon, self).__init__()
        self.set_icon(TRAY_ICON)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        # TODO make settings menu
        # create_menu_item(menu, 'Settings', self.on_hello)
        create_menu_item(menu, 'Main', self.on_open_main)
        menu.AppendSeparator()
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.Icon(path)
        self.SetIcon(icon, TRAY_TOOLTIP)

    def on_left_down(self, event):      
        print ('Tray icon was left-clicked.')

    def on_hello(self, event):
        print ('Hello, world!')
        if not hasattr(self, 'settings_frame'):
            self.settings_frame = SettingsFrame("Settings", self.frame)
        else:
            if not self.settings_frame:
                print("closed")
                self.settings_frame = SettingsFrame("Settings", self.frame)
            # print(self.settings_frame.Show())
            print(dir(self.settings_frame))

    def on_open_main(self, event):
        print ('Opening Main')
        if not hasattr(self, 'main_frame'):
            self.main_frame = MainFrame("Main", self.frame)
        else:
            if not self.main_frame:
                print("closed")
                self.main_frame = MainFrame("Main", self.frame)
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

    def __post_init__(self):
        self.process_object = None
        self.pid = None
        print("Starting: " + str(self.name))
        if self.every == "daily":
            # schedule.every().seconds.do(
            #     lambda: self.run_backup())
            schedule.every().day.at(self.time).do(lambda: self.run_backup())

    def run_backup(self):
        print("hello!!!!!!!!!!!!!!")
        config = get_config()

        self.process_object = SyncProcess(self.window)
        self.process_object.Redirect()
        cmd = [config["main"]["bin"],
               "-v6",
               " --remote-schema 'ssh -p " + str(self.port) + " -i " + self.key + " %s rdiff-backup --server'",
               "--",
               self.source, self.dest]
        print("running: " + str(" ".join(cmd)))
        self.pid = wx.Execute(" ".join(cmd), wx.EXEC_ASYNC, callback=self.process_object)
        print("pid: " + str(self.pid))
        time.sleep(1)
        stream = self.process_object.GetInputStream()

        if stream.CanRead():
            text = stream.read()
            print(text)
            wx.LogMessage(text)

        print("Finish reading")

        return


class MainInvisibleWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None)

        self.sync_jobs = []
        for backup in config["backups"]:
            backup_class = Backup(**backup, window=self)
            self.sync_jobs.append(backup_class)
        print(len(self.sync_jobs))

        self.Bind(wx.EVT_IDLE, self.OnIdle)

        self.on_timer()

    def on_timer(self):
        # wx.CallLater(1000 * 60, self.on_timer)
        wx.CallLater(1000, self.on_timer)
        schedule.run_pending()
        # print("bu")

    def OnIdle(self, evt):
        # print("idle")
        if self.sync_jobs is not None:
            for sync_job in self.sync_jobs:
                if sync_job.process_object is not None:
                    if sync_job.process_object.terminated:
                        sync_job.process_object = None
                    else:
                        try:
                            stream = sync_job.process_object.GetInputStream()

                            if stream.CanRead():
                                text = stream.read()

                                print(text.decode())
                        except RuntimeError as e:
                            print(e)
                            # import code;
                            # code.interact(local=dict(globals(), **locals()))

                # print("Done idle")


class App(wx.App):

    def OnInit(self):
        wx.Log.SetActiveTarget(wx.LogStderr())

        print("Staring App OnInit")
        frame = MainInvisibleWindow()
        self.SetTopWindow(frame)
        TaskBarIcon(frame)
        return True


def main():
    app = App(False)
    app.MainLoop()


if __name__ == '__main__':
    main()
