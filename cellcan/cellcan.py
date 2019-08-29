# Default template for XBee MicroPython projects


# Default template for XBee MicroPython projects #
# Need to import any tools I will need (SPI, GPIO control, ADC, etc)


import time

# Initialize ports and pins
import network
import xbee
import machine
from machine import Pin
from machine import I2C

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

dio0 = Pin("D0", Pin.OUT, value=0)  # Digital Low~~~~~~~Digital High = 1
# dio1 = Pin("D1", Pin.OUT, value=0)  # Digital Low~~~~~~~Digital High = 1
# dio2 = Pin("D2", Pin.OUT, value=0)  # Digital Low~~~~~~~Digital High = 1
reset_pin = Pin("D3", 2, Pin.PULL_UP)  # Digital Low~~~~~~~Digital High = 1
led = Pin("D4", Pin.OUT, value=0)  # Turn on LED to signify startup
# this network command sets up the object for the Cellular Network
c = network.Cellular()
# I2C_PIN_ID = "P1"
i2c = I2C("D1", "P1", freq=400000)  # I2c Module
Pumpon = Pin("P0", Pin.OUT, value=0)  # Digital Low~~~~~~~Digital High = 1
Pumpoff = Pin("D2", Pin.OUT, value=0)  # Digital Low~~~~~~~Digital High = 1
commands_list = ["?", "Check Can", "Pull Sample 1", "Pull Sample 2", "Reset", ""]
send_list = "Commands: " + str(commands_list).strip('[]')
global pump_ready
pump_ready = 1
print("Starting up again!")
# Useful dictionary for later use of
# the commands we have at the moment
# Pump_time is the variable which controls how long the pump is on for.
Pump_time = 30
# RELAY PIN = "Digital logic line here"
def text_messages(string):  # This looks at the received message and returns a message to send
    # back to the user.
    string = string.lower()
    switcher = {
        "?": "Sending Commands",
        "Check Can".lower(): "Checking on Can",
        "Pull Sample 1".lower(): "Pulling Sample from pump 1",
        "Pull Sample 2".lower(): "Pulling Sample from pump 2",
        "Reset".lower(): "Resetting Pump system",
        "Time Sample".lower(): "How many seconds do you want the pump open?"
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


def i2comms():
    channel = i2c.scan()  # scan for slaves, returning a list of 7-bit addresses
    time.sleep(0.015)
    print(channel)

def sleep(time):
    time.sleep(time)


def control_canister(intz): # this just reads in an integer that gets set based on the message received
    # These are still waiting for hardware lines to interface with
    time_passed=0
    if intz == 0:
        print("Nothing happens, commands are sent")
        send_back_number2 = sms['sender']
        try:
            c.sms_send(send_back_number2, send_list)
        except Exception as e:
            print("Send failure: %s" % str(e))
    elif intz == 1:  # Check Power GPIO flag, send statuses
        send_back_number2 = sms['sender']
        check_pins()
        print('I2C: {i2c}, Pump 1: {Pump1}, Pump 2: {Pump2)')
        try:
            c.sms_send(sms['sender'], send_list)
        except Exception as e:
            print("Send failure: %s" % str(e))
    elif intz == 2:  # Check Can status 1 too, but then power Solenoid
        pump_ready = 0
        send_back_number2 = sms['sender']
        print(Pumpon.value())
        if Pumpon.value() == 0:
            open_valve(Pumpon)
        else:
            try:
                c.sms_send(send_back_number2, "Pump Busy")
            except Exception as e:
                print("Send failure: %s" % str(e))
            print("Valve busy")
    elif intz == 3:  # Check Can status 2 too, but then power Solenoid RIGHT NOW THIS DOES THE SAME AS 2
        pump_ready = 0
        send_back_number2 = sms['sender']
        if Pumpon.value == 0:
            open_valve(Pumpon)
        else:
            print("Valve busy")
    elif intz == 4:  # Do a System or Canister Reset
        send_back_number2 = sms['sender']
        pump_ready = 1
        try:
            c.sms_send(send_back_number2, "Pump Resetting")
        except Exception as e:
            print("Send failure: %s" % str(e))
        print("At some point this will reset something")
    elif intz == 5:
        pump_ready = 0
        send_back_number2 = sms['sender']
        time_passed = 0
        while time_passed < 60:
            sms2 = c.sms_receive() # wait for seconds
            if sms2:
                t = sms2['message']
                open_valve_timed(Pumpon, t)
                break
            time.sleep(1)
            time_passed = time_passed + 1
        try:
            c.sms_send(send_back_number2, "Pump Resetting")
        except Exception as e:
            print("Send failure: %s" % str(e))
    else:
        return "Invalid command message"


def wait_for_message():
    while True:
        sms2 = c.sms_receive()  # wait for seconds
        if sms2:
            t = sms2['message']
            open_valve_timed(Pumpon, t)
            break
    time.sleep(1)


def read_status():
    if Pumpon.value() == 1:
        print("Pump1 Not available")
    # if Pump2.value == 1:
    #    print("Pump2 not available.")
    # if (Pump1.value() == 0) and (Pump2.value() == 0):
    #    print("Both Pumps are available")


def check_pins():
    print(i2c, Pumpon, Pumpoff)


def open_valve(pump):
    # Latching
    # time to open that solenoid
    pump.value(1)
    # pulse power for 500 ms (for now)
    time.sleep(0.5)
    pump.value(0)
    # stop pulsing
    time.sleep(Pump_time)
    # still on until... close valve! Make sure to use off switch line
    close_valve(Pumpoff)
    #should be ded now


def close_valve(pump):
    # Latching
    pump.value(1)
    # time to close that valve
    # pulse the  power for 500 ms
    time.sleep(0.5)
    # stop pulsing
    pump.value(0)
    time.sleep(1)
    # now its off, yay


def open_nonswitch_valve(pump):
    # Non-Switching
    # time to open that solenoid
    # pulse power for 500 ms (for now)
    pump.value(1)
    time.sleep(0.5)
    # stop pulsing
    time.sleep(30)
    close_valve(pump)


def close_nonswitch_valve(pump):
    # Non-Switching
    # time to close that valve
    # pulse the negative power for 500 ms
    pump.value(0)
    time.sleep(0.5)
    # stop pulsing


def open_valve_timed(pump, t):
    # Latching
    # time to open that solenoid
    pump.value(1)
    # pulse power for 500 ms (for now)
    time.sleep(0.5)
    pump.value(0)
    # stop pulsing
    time.sleep(t)
    # still on until... close valve! Make sure to use off switch line
    close_valve(Pumpoff)
    # should be ded now


def close_valve_timed(pump,t):
    # Latching
    pump.value(1)
    # time to close that valve
    # pulse the  power for 500 ms
    time.sleep(0.5)
    # stop pulsing
    pump.value(0)
    time.sleep(t)
    # now its off, yay


first_time = True


global current_sender
change = False  # This variable helpsKeep track of who the last sender was/is
# while True:
#    open_valve(Pumpon)
# if reset_pin.value() == 0:
#    xbee.atcmd('FR')
#    machine.soft_reset()
#    print(reset_pin.value())
while not c.isconnected():
    print("I am not connected")
    if reset_pin.value() == 0:
        xbee.atcmd('FR')
        machine.soft_reset()
        print(reset_pin.value())
    time.sleep(1)


while True:
    if reset_pin.value() == 0:
        led.value(1)
        print(reset_pin.value())
        #xbee.atcmd('FR')
        machine.soft_reset()
    sms = c.sms_receive()
   # if sms:
        # if sms['sender'] != current_sender:
        #  change = True
    if sms and first_time: # or change:  # if a new user is texting in to the device,
        change = False                  # send them the commands
        first_time = False
        current_sender = sms['sender']
        send_back_number = sms['sender']
        c.sms_send(send_back_number, send_list) # Sender gets command list

        time.sleep(1) # wait one second
    elif sms: # no change in sender or the first time it has been activated
        print("SMS received from %s >> %s" % (sms['sender'], sms['message']))
        send_back_number = sms['sender'] # this sets up the sender as the receiver of the Xbee Message
        message_send = text_messages(sms['message'])
        control_canister(command_list(sms['message']))
        try:
            c.sms_send(send_back_number, message_send)
            print("Successful send")
        except Exception as e:
            print("Send failure: %s" % str(e))
    # Wait 1000 ms before checking for data again.
    time.sleep(1)
