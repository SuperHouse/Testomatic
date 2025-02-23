Notes
=====

To allow Node-RED to shut down the Pi:

https://flows.nodered.org/node/node-red-contrib-rpi-shutdown


To validate:

 * [OK] INA260 current sensors (Using library)
 * [OK] MCP23017 I/O expanders (Using Blinka)
 * [OK] Piezo beeper
 * MCP4728 DAC
 * ADS1115 ADC
 * CAT24C32 EEPROM (Test Module, on I2C bus 1)
 * CAT24C32 EEPROM (HAT, on I2C bus 0)


=== INA260 current sensors

https://pypi.org/project/ina260/

pip install ina260

from ina260.controller import Controller
c = Controller(address=0x40)
print(c.voltage())
print(c.current())
print(c.power()))


=== MCP23017 I/O expanders

Use Adafruit Blinka for CP style access to MCP23017 from within Python:

https://learn.adafruit.com/using-mcp23008-mcp23017-with-circuitpython/python-circuitpython#python-installation-of-mcp230xx-library-3005480

Created a test script called mcp-test.py

Pullup example:

    pin1.direction = digitalio.Direction.INPUT
    pin1.pull = digitalio.Pull.UP



=== DUT Power Control
pinctrl 17 op dh   // Turn on VIN
pinctrl 27 op dh   // Turn on 5V
pinctrl 22 op dh   // Turn on 3.3V


=== Piezo control
pinctrl 23 op dh   // Turn on piezo
pinctrl 23 op dl   // Turn off piezo




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

#sudo apt install wtype
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








edit /boot/firmware/config.txt and find this line:

    dtoverlay = vc4-kms-v3d

Replace it with:

    dtoverlay = vc4-fkms-v3d

Elecrow 7" touchscreen setup: [https://www.elecrow.com/rc070p-7-inch-1024x600-raspberry-pi-monitor-touchscreen-capacitive-ips-display-with-built-in-speaker-stand.html](https://www.elecrow.com/rc070p-7-inch-1024x600-raspberry-pi-monitor-touchscreen-capacitive-ips-display-with-built-in-speaker-stand.html)

copy printer-driver-pos_3.13.11_all.deb to machine

    sudo dpkg -i printer-driver-pos_3.13.11_all.deb

Open printer preferences and enable network administration.

Use a browser to connect to https://tester.local:631

Add local printer.

Select the POS-80.

On the printer type page, select Make -> POS
Select Model -> POS-80 (en)


Copy over test software directory.

    pip3 install pytz
    pip3 install esptool
