# Default template for XBee MicroPython projects

import urequests
import umqtt
import uftp
import remotemanager
import hdc1080
import ds1621

# Default template for XBee MicroPython projects #
# Need to import any tools I will need (SPI, GPIO control, ADC, etc)


import time

# Initialize ports and pins
import network
import xbee
from machine import Pin

# EXAMPLE!!!!!!~~~~~`
# Set up a Pin object to represent pin 6 (PWM0/RSSI/DIO10).
# The second argument, Pin.OUT, sets the pin's mode to be an OUTPUT.
# The third argument sets the initial value, which is 0 here, meaning OFF.
# dio10 = Pin("P0", Pin.OUT, value=0)
# END EXAMPLE~~~~~~~


# These are the buttons to be used (SW2 through SW5)
# DIO0-DIO3 are the buttons in the bottom right of the schematic assuming the USB is the bottom
# ADC also occupies the same memory as D0-D3
# Pin(Label of Pin we wish to use, Input or Output, Pull Up or Pull Down)
# Value sets buttons to be digital inputs that can control

dio0 = Pin("D0", Pin.OUT, value=4)  # Digital Low~~~~~~~Digital High = 5
dio1 = Pin("D1", Pin.OUT, value=4)  # Digital Low~~~~~~~Digital High = 5
dio2 = Pin("D2", Pin.OUT, value=4)  # Digital Low~~~~~~~Digital High = 5
dio3 = Pin("D3", Pin.OUT, value=4)  # Digital Low~~~~~~~Digital High = 5
led = Pin("D4", Pin.OUT, value=0)  # Turn on LED to signify startup
# this network command sets up the object for the Cellular Network
c = network.Cellular()
# I2C_PIN_ID = "P1"
i2c = Pin("D1", Pin.OUT, value=6)  # I2c Module
Pump1 = Pin("P1", Pin.OUT, value=4)  # Digital Low~~~~~~~Digital High = 5
Pump2 = Pin("P0", Pin.OUT, value=4)  # Digital Low~~~~~~~Digital High = 5

commands_list = ["?", "Check Can", "Pull Sample 1", "Pull Sample 2", "Reset", ]
send_list = "Commands: " + str(commands_list).strip('[]')


# Useful dictionary for later use of
# the commands we have at the moment


# RELAY PIN = "Digital logic line here"
def text_messages(string):  # This looks at the received message and returns a message to send
    # back to the user.
    string = string.lower()
    switcher = {
        "?": "Sending Commands",
        "Check Can".lower(): "Checking on Can",
        "Pull Sample 1".lower(): "Pulling Sample from pump 1",
        "Pull Sample 2".lower(): "Pulling Sample from pump 2",
        "Reset".lower(): "Resetting Pump system"
    }
    print(switcher.get(string, "Invalid command message"))
    return switcher.get(string, "Invalid command message")
    # This sets up a Dictionary based on {Received message: Sent message, etc.}
    # If the command is a valid command it will send back the 2nd response, but otherwise it will
    # send back "Invalid Command Message"
    # Check if the XBee has received any SMS.


xb = xbee.XBee()  # Initializes an Xbee object that can control internal functions of the Xbee


def shutdown():
    # when a switch (TBD) is hit, put the machine into sleep for 50 secs to that shutdown
    # is safe and the module is not damaged
    xb.sleep_now(50000, True)


def command_list(comm):
    if comm.lower() == "?":
        return 0
    elif comm.lower() == "check can":
        return 1
    elif comm.lower() == "pull sample 1":
        return 2
    elif comm.lower() == "pull sample 2":
        return 3
    elif comm.lower() == "reset":
        return 4
    else:
        return "Invalid Command"


def sleep(time):
    time.sleep(time)


def control_canister(intz): # this just reads in an integer that gets set based on the message received
    # These are still waiting for hardward lines to interface with
    if intz == 0:
        print("Nothing happens, commands are sent")
        send_back_number2 = sms['sender']
        try:
            c.sms_send(send_back_number2, send_list)
        except Exception as e:
            print("Send failure: %s" % str(e))
    elif intz == 1:  # Check Power GPIO flag, send statuses
        check_pins()
        print('I2C: {i2c}, Pump 1: {Pump1}, Pump 2: {Pump2)')
        try:
            c.sms_send(sms['sender'], send_list)
        except Exception as e:
            print("Send failure: %s" % str(e))
    elif intz == 2:  # Check Can status 1 too, but then power Solenoid
        if Pump1.value == 4:
            open_valve(Pump1)
        else:
            print("Valve busy")
    elif intz == 3:  # Check Can status 2 too, but then power Solenoid
        if Pump2.value == 4:
            open_valve(Pump2)
        else:
            print("Valve busy")
    elif intz == 4:  # Do a System or Canister Reset
        print("At some point this will reset something")
    else:
        return "Invalid command message"


def read_status():
    if Pump1.value() == 5:
        print("Pump1 Not available")
    if Pump2.value == 5:
        print("Pump2 not available.")
    if (Pump1.value() == 4) and (Pump2.value() == 4):
        print("Both Pumps are available")


def check_pins():
    print(i2c, Pump1, Pump2)


def open_valve(pump):
    # Non-Switching
    # time to open that solenoid
    # pulse power for 500 ms (for now)
    time.sleep(0.5)
    # stop pulsing
    time.sleep(30)
    close_valve(pump)


def close_valve(pump):
    # Non-Switching
    # time to close that valve
    # pulse the negative power for 500 ms
    time.sleep(0.5)
    # stop pulsing


def open_switch_valve(pump):
    # Non-Switching
    # time to open that solenoid
    # pulse power for 500 ms (for now)
    time.sleep(0.5)
    # stop pulsing
    time.sleep(30)
    close_valve(pump)


def close_switch_valve(pump):
    # Non-Switching
    # time to close that valve
    # pulse the negative power for 500 ms
    time.sleep(0.5)
    # stop pulsing


first_time = True
global current_sender
change = False  # This variable helpsKeep track of who the last sender was/is
while not c.isconnected():
    time.sleep(1)

while True:
    sms = c.sms_receive()
    if sms:
        if sms['sender'] != current_sender:
            change = True
    if (sms and first_time) or change:  # if a new user is texting in to the device,
        change = False                  # send them the commands
        current_sender = sms['sender']
        send_back_number = sms['sender']
        c.sms_send(send_back_number, send_list)
        first_time = False
        time.sleep(1)
    elif sms:
        print("SMS received from %s >> %s" % (sms['sender'], sms['message']))
        send_back_number = sms['sender']
        message_send = text_messages(sms['message'])
        control_canister(command_list(sms['message']))
        try:
            c.sms_send(send_back_number, message_send)
            print("Successful send")
        except Exception as e:
            print("Send failure: %s" % str(e))
    # Wait 1000 ms before checking for data again.
    time.sleep(1)
