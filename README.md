# WLED Flasher

WLED Flasher is a utility app for the [WLED](https://github.com/Aircoookie/WLED) firmware and is designed to make flashing ESPs with WLED as simple as possible by:

 * Having pre-built binaries for most operating systems.
 * Hiding all non-essential options for flashing. All necessary options for flashing (bootloader, flash mode) are automatically extracted from the binary.

This project was originally intended to fix some ESPHome Flasher issues when flashing WLED firmware. It is a fork of [ESPHome-Flasher](https://github.com/esphome/esphome-flasher) which in turn is a fork of the [NodeMCU PyFlasher](https://github.com/marcelstoer/nodemcu-pyflasher)
project.

The flashing process is handled by Espressif [esptool](https://github.com/espressif/esptool).

## Installation

The utility doesn't have have an installer. Just double-click it to get started. Check the [releases section](https://github.com/andyshinn/wled-flasher/releases) to download for your platform.

## Build it yourself

If you want to build this application yourself you need to:

- Install Python 3.x
- `pip install requirements.txt`
- Start the GUI using `wledflasher`. Alternatively, you can use the command line interface (
  type `wledflasher -h` for info)

### macOS

`pyinstaller installer-macos.spec`

### Windows

1. Start up VM
2. Install Python (3) from App Store
3. Download esphome-flasher from GitHub
4. `pip install -e.` and `pip install pyinstaller`
5. Check with `python -m wledflasher.__main__`
6. `python -m PyInstaller.__main__ -F -w -n WLED Flasher -i icon.ico wledflasher\__main__.py`
7. Go to `dist` folder, check WLED Flasher.exe works.



## Linux Notes

Installing wxpython for linux can be a bit challenging (especially when you don't want to install from source).
You can use the following command to install a wxpython suitable with your OS:

```bash
# Go to https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ and select the correct OS type
# here, we assume ubuntu 18.03 bionic
pip3 install -U \
    -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-18.04 \
    wxPython
```

## License

[MIT](http://opensource.org/licenses/MIT) © Marcel Stör, Otto Winter
