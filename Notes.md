# Notes

To validate:

 * [OK] TUSB2046 USB hub
 * [OK] DUT power control: VIN, 5V, 3V3
 * [OK] INA260 current sensors (Using library)
 * [OK] Piezo beeper
 * [OK] TCA9548 I2C multiplexer
 * [OK] AD5593R I/O expander
 * CAT24C32 EEPROM (Test Module, on I2C bus 1)
 * CAT24C32 EEPROM (HAT, on I2C bus 0)


## Light Box

Logitech Brio MX 4K webcam

sudo apt install fswebcam

To check available resolutions:

v4l2-ctl --list-formats-ext

Must be plugged into USB3 port and detected as a USB3 device to provide 4K res.

fswebcam -r 3840x2160 -p MJPEG --skip 10 test9.jpg

It's only being detected as USB2.0:

lsusb -t

shows 480M (USB2.0) instead of 5000M (USB3.0) even plugged in directly.

According to Gemini, Pi 3B+ only has a shared internal USB2.0 bus, even 
though it exposes USB3 ports externally! This sucks

Got it working an a Pi 5B with a Comsol USB-A to C cable CMAM12BK

Options like this work, although gain doesn't seem to do anything:

fswebcam -r 3840x2160 -p MJPEG --set brightness=100% --set contrast=60% --set sharpness=80% --set gain=255 --skip 20 test17.jpg

### Stacking images

Script to take a series of pics:

#!/bin/bash

# Create a directory for the images if it doesn't exist
mkdir -p webcam_images
cd webcam_images

# Capture 10 images with a 1-second delay between captures
for i in {1..5}; do
    echo "Capturing image $i..."
    # -r specifies resolution, --no-banner removes the timestamp
    # -S 10 skips the first 10 frames to allow calibration
    fswebcam -r 3840x2160 -p MJPEG --no-banner --set brightness=80% --set contrast=60% --set sharpness=60% --skip 20 image_$i.jpeg
    sleep 1
done

echo "Capture complete."

Install ImageMagick:

sudo apt install imagemagick

Process pics:

magick convert *.jpeg -evaluate-sequence median stacked_image.jpeg

### Printer control

Alternative to using external process and passing it a text file:

https://github.com/python-escpos/python-escpos

### Colour sensing

https://github.com/DevelopiumTech/VEML3328

https://www.digikey.com.au/en/products/detail/vishay-semiconductor-opto-division/VEML3328SL/10673128

https://www.finntestelectronics.com/product/mega-module/

### Writing tests

Use Given - When - Then format? Or AAA?

Use raw Python, or some kind of config? Config is hard! For eg:

---
## How to format error message with results?

Simple string, then output of all "then" lines?


object:
  title: 5V power rail
  abort_on_fail: true
  fail_message: 5V power rail out of spec
  given:
    - 5v: true
    - boolean: true
  when:
    - 5v: true
    - delay: 100ms
  then:
    - analogread a5: 4.7 - 5.1
    
object:
  title: 3V3 power rail
  abort_on_fail: true
  fail_message: 3V3 power rail out of spec
  given:
    - 5v: true
    - boolean: true
  when:
    - 5v: true
    - delay: 100ms
  then:
    - analogread a6: 2.9 - 3.4



### TCA9548 I2C multiplexer

Needs Blinka installed:

https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi

    sudo apt-get update
    sudo apt-get -y upgrade
    sudo apt-get install -y python3-pip

    pip install rpi-lgpio

https://learn.adafruit.com/adafruit-tca9548a-1-to-8-i2c-multiplexer-breakout/circuitpython-python

    sudo pip3 install adafruit-circuitpython-tca9548a
    

### AD5593R I/O expander

https://github.com/101Robotics/AD5593-MicroPython

https://learn.adafruit.com/adafruit-ad5693r-16-bit-dac-breakout-board/circuitpython-and-python

    python -m venv venv
    source venv/bin/activate
    pip install adafruit-circuitpython-ad569x
    pip install lgpio


### Pi power control

To allow Node-RED to shut down the Pi:

https://flows.nodered.org/node/node-red-contrib-rpi-shutdown


### INA260 current sensors

https://pypi.org/project/ina260/

    pip install ina260
    
    from ina260.controller import Controller
    c = Controller(address=0x40)
    print(c.voltage())
    print(c.current())
    print(c.power()))


### MCP23017 I/O expanders

Use Adafruit Blinka for CP style access to MCP23017 from within Python:

https://learn.adafruit.com/using-mcp23008-mcp23017-with-circuitpython/python-circuitpython#python-installation-of-mcp230xx-library-3005480

Created a test script called mcp-test.py

Pullup example:

    pin1.direction = digitalio.Direction.INPUT
    pin1.pull = digitalio.Pull.UP



### DUT Power Control
    pinctrl 17 op dh   // Turn on VIN
    pinctrl 27 op dh   // Turn on 5V
    pinctrl 22 op dh   // Turn on 3.3V


### Piezo control
    pinctrl 23 op dh   // Turn on piezo
    pinctrl 23 op dl   // Turn off piezo



### Data import

Export spreadsheet from gdocs as XLSX, and scp it to the portal VM.

    cd /var/www/register-test/pyproj
    . env/bin/activate
    ./manage.py import-xlsx ~/Device-Serial-Numbers-.xlsx

### Label printer

Brother label printer on Linux: [https://github.com/HenrikBengtsson/brother-ptouch-label-printer-on-linux]()

For CAN:
MCP251863 controller/ transceiver
(See CANPico board)

[https://github.com/kentindell/canhack/tree/master/CANPico]()

[https://core-electronics.com.au/adafruit-picowbell-can-bus-for-pico-mcp2515-can-controller.html]()

[https://github.com/LukePrior/Raspberry-Pi-Thermal-Printer]()


Firmata for Raspberry Pi Pico:

 * Use ConfigurableFirmata with zero changes
 * Board profile is "Arduino Mbed OS RP2040 Boards" -> "Raspberry Pi Pico"
 * Upload methd: UF2


Impressive 3D printed test jig run by a Raspberry Pi:

[https://www.youtube.com/watch?v=iTLnJ0uIZIg]()


Firmata equivalent for RPi Pic:

[https://github.com/MrYsLab/telemetrix-rpi-pico]()

Equivalent to Firmata:

[https://abyz.me.uk/picod/py_picod.html]()



Config files using configparser:

[https://stackoverflow.com/questions/19078170/python-how-would-you-save-a-simple-settings-config-file]()

[https://www.geeksforgeeks.org/how-to-create-gui-applications-under-linux-desktop-using-pygobject/]()

Thermal camera for Raspberry Pi:

[https://www.flir.com.au/developer/lepton-integration/lepton-integration-raspberry-pi/]()

Thea's tester:

[https://twitter.com/theavalkyrie/status/1552714810038657025]()

[https://github.com/wntrblm/Hubble]()

Capturing from Raspberry Pi cam:

    raspistill -st -t 200 -o image.jpg




Process
=======

Install Raspberry Pi OS 64-bit. Edit the settings:

 * Set hostname to tester(x).local
 * Set username to testomatic
 * Set password to something secret
 * Set WiFi credentials
 * Set WiFi country
 * Set locale
 * Enable SSH

Put SD card in Pi and boot it.

SSH to the pi:

    ssh testomatic@tester.local

Update system and install Vim:

    sudo apt update
    sudo apt dist-upgrade
    sudo apt install vim

Install node-red

Go to http://tester3.local:1880/

Install the palette item "node-red-contrib-ip"
Install the palette item "@flowfuse/node-red-dashboard"

    sudo apt install pipx
    pipx install esptool



Kiosk tutorial: https://www.raspberrypi.com/tutorials/how-to-use-a-raspberry-pi-in-kiosk-mode/

    sudo apt install wtype
    sudo apt install chromium-browser

    sudo vim .config/wayfire.ini

Add this new section:

[autostart]
chromium = chromium-browser http://localhost:1880/dashboard/page1 --kiosk --noerrdialogs --disable-infobars --no-first-run --ozone-platform=wayland --enable-features=OverlayScrollbar --start-maximized










    sudo apt install chromium-browser

Add to /etc/xdg/lxsession/LXDE-pi/autostart:

@xset s off
@xset -dpms
@xset s noblank
@chromium-browser --noerrdialogs --disable-infobars --kiosk https://localhost:1880/dashboard/page1





## Enable Screen


edit /boot/firmware/config.txt and find this line:

    dtoverlay = vc4-kms-v3d

Replace it with:

    dtoverlay = vc4-fkms-v3d

    sudo vim /boot/firmware/config.txt
    
Add these lines to the end:

    hdmi_force_hotplug=1
    max_usb_current=1
    hdmi_group=2
    hdmi_mode=1
    hdmi_mode=87
    hdmi_cvt 1024 600 60 6 0 0 0
    hdmi_drive=1

Elecrow 7" touchscreen setup: [https://www.elecrow.com/rc070p-7-inch-1024x600-raspberry-pi-monitor-touchscreen-capacitive-ips-display-with-built-in-speaker-stand.html](https://www.elecrow.com/rc070p-7-inch-1024x600-raspberry-pi-monitor-touchscreen-capacitive-ips-display-with-built-in-speaker-stand.html)

## Receipt Printer Driver

copy printer-driver-pos_3.13.11_all.deb to machine

    sudo dpkg -i printer-driver-pos_3.13.11_all.deb

Open printer preferences and enable network administration.

Use a browser to connect to https://tester.local:631

Add local printer.

Select the POS-80.

On the printer type page, select Make -> POS
Select Model -> POS-80 (en)

## Install Software

Copy over test software directory.

    pip3 install pytz
    pip3 install esptool
