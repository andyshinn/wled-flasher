# This GUI is a fork of the brilliant https://github.com/marcelstoer/nodemcu-pyflasher
import re
import sys
import threading
from typing import BinaryIO
import os

import wx
import wx.adv
import wx.svg
import wx.lib.inspection
import wx.lib.mixins.inspection

from wledflasher.helpers import list_serial_ports
from wledflasher.wled import get_releases, download_firmware
from wledflasher.__main__ import run_wledflasher


APP_NAME = "WLED Flasher"
COLOR_RE = re.compile(r"(?:\033)(?:\[(.*?)[@-~]|\].*?(?:\007|\033\\))")
COLORS = {
    "black": wx.BLACK,
    "red": wx.RED,
    "green": wx.GREEN,
    "yellow": wx.YELLOW,
    "blue": wx.BLUE,
    "magenta": wx.Colour(255, 0, 255),
    "cyan": wx.CYAN,
    "white": wx.WHITE,
}
FORE_COLORS = {**COLORS, None: wx.WHITE}
BACK_COLORS = {**COLORS, None: wx.BLACK}


# See discussion at http://stackoverflow.com/q/41101897/131929
class RedirectText:
    def __init__(self, text_ctrl):
        self._out = text_ctrl
        self._i = 0
        self._line = ""
        self._bold = False
        self._italic = False
        self._underline = False
        self._foreground = None
        self._background = None
        self._secret = False

    def _add_content(self, value):
        attr = wx.TextAttr()
        if self._bold:
            attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
        attr.SetTextColour(FORE_COLORS[self._foreground])
        attr.SetBackgroundColour(BACK_COLORS[self._background])
        wx.CallAfter(self._out.SetDefaultStyle, attr)
        wx.CallAfter(self._out.AppendText, value)

    def _write_line(self):
        pos = 0
        while True:
            match = COLOR_RE.search(self._line, pos)
            if match is None:
                break

            j = match.start()
            self._add_content(self._line[pos:j])
            pos = match.end()

            for code in match.group(1).split(";"):
                code = int(code)
                if code == 0:
                    self._bold = False
                    self._italic = False
                    self._underline = False
                    self._foreground = None
                    self._background = None
                    self._secret = False
                elif code == 1:
                    self._bold = True
                elif code == 3:
                    self._italic = True
                elif code == 4:
                    self._underline = True
                elif code == 5:
                    self._secret = True
                elif code == 6:
                    self._secret = False
                elif code == 22:
                    self._bold = False
                elif code == 23:
                    self._italic = False
                elif code == 24:
                    self._underline = False
                elif code == 30:
                    self._foreground = "black"
                elif code == 31:
                    self._foreground = "red"
                elif code == 32:
                    self._foreground = "green"
                elif code == 33:
                    self._foreground = "yellow"
                elif code == 34:
                    self._foreground = "blue"
                elif code == 35:
                    self._foreground = "magenta"
                elif code == 36:
                    self._foreground = "cyan"
                elif code == 37:
                    self._foreground = "white"
                elif code == 39:
                    self._foreground = None
                elif code == 40:
                    self._background = "black"
                elif code == 41:
                    self._background = "red"
                elif code == 42:
                    self._background = "green"
                elif code == 43:
                    self._background = "yellow"
                elif code == 44:
                    self._background = "blue"
                elif code == 45:
                    self._background = "magenta"
                elif code == 46:
                    self._background = "cyan"
                elif code == 47:
                    self._background = "white"
                elif code == 49:
                    self._background = None

        self._add_content(self._line[pos:])

    def write(self, string):
        for char in string:
            if char == "\r":
                current_value = self._out.GetValue()
                last_newline = current_value.rfind("\n")
                wx.CallAfter(self._out.Remove, last_newline + 1, len(current_value))
                # self._line += '\n'
                self._write_line()
                self._line = ""
                continue
            self._line += char
            if char == "\n":
                self._write_line()
                self._line = ""
                continue

    def flush(self):
        pass


class VersionChoice(wx.Choice):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Append("Loading versions...")
        wx.CallLater(50, self.load_versions)

    def load_versions(self):
        self.Append("Select a version to flash")
        for release in get_releases():
            self.Append(release.title, release)
        self.Delete(0)


class FlashingThread(threading.Thread):
    def __init__(self, parent, firmware: BinaryIO, port, show_logs=False):
        threading.Thread.__init__(self)
        self.daemon = True
        self._parent = parent
        self._firmware = firmware
        self._port = port
        self._show_logs = show_logs

    def run(self):
        try:
            argv = ["wledflasher", "--port", self._port, self._firmware.name]
            if self._show_logs:
                argv.append("--show-logs")
            run_wledflasher(argv)
            self._firmware.close()
        except Exception as error:
            print("Unexpected error: {}".format(error))
            raise


class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(
            self, parent, -1, title, size=(725, 650), style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE
        )

        self._firmware = None
        self._port = None
        self._version = None

        self._init_ui()

        sys.stdout = RedirectText(self.console_ctrl)

        self.SetMinSize((640, 480))
        self.Centre(wx.BOTH)
        self.Show(True)

    def _init_ui(self):
        def on_reload(event):  # pylint: disable=unused-argument
            self.choice.SetItems(self._get_serial_ports())

        def on_clicked(event: wx.CommandEvent):  # pylint: disable=unused-argument
            # self.console_ctrl.SetValue("")

            firmware_file = download_firmware(self._version)

            worker = FlashingThread(self, firmware_file, self._port)
            worker.start()

        def on_logs_clicked(event):  # pylint: disable=unused-argument
            self.console_ctrl.SetValue("")
            worker = FlashingThread(self, "dummy", self._port, show_logs=True)
            worker.start()

        def on_select_port(event):
            choice = event.GetEventObject()
            self._port = choice.GetString(choice.GetSelection())

        # def on_pick_file(event):
        #     self._firmware = event.GetPath().replace("'", "")

        def on_pick_release(event: wx.CommandEvent):
            # self._version = event.GetString()
            release = event.GetClientData()
            self.bin_picker.Clear()

            if release:
                for asset in release.get_assets():
                    if asset.name.endswith(".bin"):
                        self.bin_picker.Append(asset.name, asset)
                self._version = self.bin_picker.GetClientData(self.bin_picker.CurrentSelection)

            # print([asset.name for asset in list(release.get_assets()) if asset.name.endswith(".bin")])

        def on_pick_version(event: wx.CommandEvent):
            self._version = event.GetClientData()

        def get_bitmap_system_color():
            appearance = wx.SystemSettings.GetAppearance()
            refresh = wx.svg.SVGimage.CreateFromFile(image("data/icons/refresh-dark.svg"))
            if appearance.IsDark():
                refresh = wx.svg.SVGimage.CreateFromFile(image("data/icons/refresh-light.svg"))
            return refresh.ConvertToScaledBitmap(wx.Size(20, 20))

        def update_button_icon(event: wx.SysColourChangedEvent):
            button = event.GetEventObject()
            button.SetBitmap(get_bitmap_system_color())

        def image(file):
            try:
                base_path = sys._MEIPASS  # pylint: disable=protected-access
            except AttributeError:
                base_path = os.path.abspath(".")

            return os.path.join(base_path, file)

        self.SetIcon(wx.Icon(image("data/icons/icon.ico")))

        panel = wx.Panel(self)

        image_panel = wx.Panel(panel)
        logo = wx.Image(image("data/images/wled_logo_akemi.png"), wx.BITMAP_TYPE_ANY)
        logo = logo.Scale(500, 156)
        logo_image = wx.Bitmap(logo)
        wx.StaticBitmap(image_panel, bitmap=logo_image)

        menu_bar = wx.MenuBar()
        self.SetMenuBar(menu_bar)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        fgs = wx.FlexGridSizer(8, 2, 10, 10)

        self.choice = wx.Choice(panel, choices=self._get_serial_ports())
        self.choice.Bind(wx.EVT_CHOICE, on_select_port)

        bmp = get_bitmap_system_color()
        reload_button = wx.Button(panel, -1, "Refresh Serial")
        reload_button.SetBitmap(bmp)
        reload_button.Bind(wx.EVT_BUTTON, on_reload)
        reload_button.SetToolTip("Reload serial device list")
        reload_button.Bind(wx.EVT_SYS_COLOUR_CHANGED, update_button_icon)

        # file_picker = wx.FilePickerCtrl(panel, style=wx.FLP_USE_TEXTCTRL)
        # file_picker.Bind(wx.EVT_FILEPICKER_CHANGED, on_pick_file)
        version_picker = VersionChoice(panel)
        version_picker.Bind(wx.EVT_CHOICE, on_pick_release)

        self.bin_picker = wx.Choice(panel)
        self.bin_picker.Bind(wx.EVT_CHOICE, on_pick_version)

        serial_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        serial_boxsizer.Add(self.choice, 1, wx.EXPAND)
        serial_boxsizer.AddStretchSpacer(0)
        serial_boxsizer.Add(reload_button, 0, wx.ALIGN_NOT, 20)

        button = wx.Button(panel, -1, "Flash ESP")
        button.Bind(wx.EVT_BUTTON, on_clicked)

        logs_button = wx.Button(panel, -1, "View Logs")
        logs_button.Bind(wx.EVT_BUTTON, on_logs_clicked)

        self.console_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.console_ctrl.SetFont(wx.Font((0, 13), wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.console_ctrl.SetBackgroundColour(wx.BLACK)
        self.console_ctrl.SetForegroundColour(wx.WHITE)
        self.console_ctrl.SetDefaultStyle(wx.TextAttr(wx.WHITE))

        port_label = wx.StaticText(panel, label="Serial port")
        version_label = wx.StaticText(panel, label="Version")
        file_label = wx.StaticText(panel, label="File")

        console_label = wx.StaticText(panel, label="Console")

        image_box = wx.BoxSizer(wx.HORIZONTAL)
        image_box.Add(image_panel)

        # hbox.Add(image_box, 0, wx.ALIGN_CENTER_VERTICAL, 1)

        fgs.AddMany(
            [
                # Port selection row
                (port_label, 1, wx.ALIGN_CENTER_VERTICAL),
                (serial_boxsizer, 1, wx.EXPAND),
                # Firmware selection row (growable)
                version_label,
                (version_picker, 1, wx.EXPAND),
                file_label,
                (self.bin_picker, 1, wx.EXPAND),
                # Flash ESP button
                (wx.StaticText(panel, label="")),
                (button, 1, wx.EXPAND),
                # View Logs button
                (wx.StaticText(panel, label="")),
                (logs_button, 1, wx.EXPAND),
                # Console View (growable)
                (console_label, 1, wx.EXPAND),
                (self.console_ctrl, 1, wx.EXPAND),
            ]
        )
        fgs.AddGrowableRow(5, 1)
        fgs.AddGrowableCol(1, 1)
        # hbox.Add(image_panel)
        hbox.Add(fgs, proportion=2, flag=wx.ALL | wx.EXPAND, border=15)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(image_box, 0, wx.CENTER)
        vbox.Add(hbox, 1, wx.EXPAND)
        panel.SetSizer(vbox)

    def _get_serial_ports(self):
        ports = []
        for port, _ in list_serial_ports():
            ports.append(port)
        if not self._port and ports:
            self._port = ports[0]
        if not ports:
            ports.append("")
        return ports

    # Menu methods
    def _on_exit_app(self, event):  # pylint: disable=unused-argument
        self.Close(True)

    def log_message(self, message):
        self.console_ctrl.AppendText(message)


class App(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    def OnInit(self):  # pylint: disable=invalid-name
        wx.SystemOptions.SetOption("mac.window-plain-transition", 1)
        self.SetAppName(APP_NAME)

        frame = MainFrame(None, APP_NAME)
        frame.Show()

        return True


def main():
    app = App(False)
    app.MainLoop()


if __name__ == "__main__":
    main()
