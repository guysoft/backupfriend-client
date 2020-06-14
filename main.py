import wx.adv
import wx
import yaml
TRAY_TOOLTIP = 'Name' 
TRAY_ICON = 'icon.png'
import os


debug = 'DEBUG' in os.environ and os.environ['DEBUG'] == "on"


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yml")


def get_config():
    with open(CONFIG_PATH) as f:
        return yaml.load(f, Loader=yaml.FullLoader)
    return


config = get_config()


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
        self.GetParent().sync_jobs.append(1)
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


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        self.frame = frame
        super(TaskBarIcon, self).__init__()
        self.set_icon(TRAY_ICON)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        create_menu_item(menu, 'Settings', self.on_hello)
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

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Close()


class MainInvisibleWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None)
        self.sync_jobs = []


class App(wx.App):

    def OnInit(self):
        print("yay")
        frame = MainInvisibleWindow()
        self.SetTopWindow(frame)
        TaskBarIcon(frame)
        return True


def main():
    app = App(False)
    app.MainLoop()


if __name__ == '__main__':
    main()
