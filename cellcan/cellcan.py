# Default template for XBee MicroPython projects


# Default template for XBee MicroPython projects #
# Need to import any tools I will need (SPI, GPIO control, ADC, etc)


import time
# from datetime import datetime, date, time
# Initialize ports and pins
import network
import xbee
import machine
from machine import Pin
from machine import UART
import utime
from machine import I2C
import sys

# EXAMPLE!!!!!!~~~~~`
# Set up a Pin object to represent pin 6, which is P0 according to XCTU (PWM0/RSSI/DIO10).
# The second argument, Pin.OUT, sets the pin's mode to be an OUTPUT.
# The third argument sets the initial value, which is 0 here, meaning OFF.
# dio10 = Pin("P0", Pin.OUT, value=0)
# END EXAMPLE~~~~~~~

# This Canister class holds the static variables we need for sending back a log to the user, as well as how many
# times the the can has been sampled total.
# datetime = datetime.now()
Pumpon = Pin("D7", Pin.OUT, value=0)  # Digital Low~~~~~~~Digital High = 1 P0 is on DIO10
Pumpoff = Pin("D9", Pin.OUT, value=0)  # Digital Low~~~~~~~Digital High = 1 D2 is on DIO2
class Canister:
    can_log = []

    sample_number = 0

    def __init__(self, status):
        self.status = status

    def log(self, info):
        self.can_log.append(info)


# This will be our can status class for multiple use cases

can = Canister(1)

# These are the buttons to be used (SW2 through SW5)
# DIO0-DIO3 are the buttons in the bottom right of the schematic assuming the USB is the bottom
# ADC also occupies the same memory as D0-D3
# Pin(Label of Pin we wish to use, Input or Output, Pull Up or Pull Down)
# Value sets buttons to be digital inputs that can control
uart = UART(1, 9600)  # init with given baudrate
uart.init(9600, bits=8, parity=None, stop=1)  # init with given parameters

# Read a line, ending in a newline character. It may return sooner if a timeout is reached.
# The timeout is configurable in the constructor.

analog0 = machine.ADC('D0')
analog1 = machine.ADC('D3')

dio0 = Pin("D0", Pin.OUT, value=0)  # Digital Low~~~~~~~Digital High = 1
# dio1 = Pin("D1", Pin.OUT, value=0)  # Digital Low~~~~~~~Digital High = 1
# dio2 = Pin("D2", Pin.OUT, value=0)  # Digital Low~~~~~~~Digital High = 1
reset_pin = Pin("D5", Pin.IN, Pin.PULL_UP)  # Digital Low~~~~~~~Digital High = 1
led = Pin("D4", Pin.OUT, value=0)  # Turn on LED to signify startup
# this network command sets up the object for the Cellular Network
c = network.Cellular()
# I2C_PIN_ID = "P1"

# NOTE: CHANGED PUMPOFF FROM P1 TO D2.

# I2C LINES ARE D1: pin 19, and P1: pin 7


i2c = I2C(1, freq=400000)  # I2c Module


commands_list = ["?", "Check Can", "Pull Sample 1","Pull Sample 2", "Reset", "Time Sample X"]
send_list = "Commands: " + str(commands_list).strip('[]')
pump_ready = 1
print("Starting up again!")
# Useful dictionary for later use of
# the commands we have at the moment
# Pump_time is the variable which controls how long the pump is on for.
data = []
Pump_time = 30


# RELAY PIN = "Digital logic line here"


def text_messages(string):  # This looks at the received message and returns a message to send
    # back to the user.
    time_msg = t_split(string)
    if time_msg[0].lower() is "time" and time_msg[1].lower() is "sample":
        return "Time Sample set"
    string = string.lower().strip()
    switcher = {
        "?": "^Commands^",
        "Check Can".lower().strip(): "Can Check Complete",
        "Pull Sample 1".lower().strip(): "Done Pulling from solenoid 1",
        "Pull Sample 2".lower().strip(): "Done Pulling from solenoid 2",
        "Reset".lower().strip(): "Resetting Pump system",

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
    global Pump_time
    global data
    data = t_split(comm)
    print(data)
    if comm.lower().strip() == "?":
        return 0
    elif comm.lower().strip() == "check can":
        return 1
    elif comm.lower().strip() == "pull sample 1":
        return 2
    elif comm.lower().strip() == "pull sample 2":
        return 3
    elif comm.lower().strip() == "reset":
        return 4
    elif data[0].lower().strip() == "time" and data[1].lower() == "sample":
        change_time(data[2])
        return 5
    else:
        return "Invalid Command"


# def i2comms():
#    channel = i2c.scan()  # scan for slaves, returning a list of 7-bit addresses
#    time.sleep(0.015)
#    print(channel)

def sleep(time):
    time.sleep(time)


def t_split(string):
    global data
    # AAAA string parsign sux
    data = string.split(" ", 2)
    return data


def control_canister(intz):  # this just reads in an integer that gets set based on the message received
    global Pump_time
    global data
    # These are still waiting for hardware lines to interface with
    global pump_ready
    time_passed = 0
    if intz == 0:
        strength = acknowledge()
        print("Nothing happens, commands are sent")
        send_back_number2 = sms['sender']
        try:
            # c.sms_send(send_back_number2, strength)
            # utime.sleep_ms(500)
            c.sms_send(send_back_number2, send_list)
        except Exception as e:
            print("Send failure: %s" % str(e))
    elif intz == 1:  # Check Power GPIO flag, send statuses
        strength = acknowledge()
        send_back_number2 = sms['sender']
        check_pins()
        try:
            # c.sms_send(send_back_number2, strength)
            # utime.sleep_ms(500)
            if pump_ready is 1:
                c.sms_send(sms['sender'], "Ready to Sample")
            elif pump_ready is 0:
                c.sms_send(sms['sender'], "Not Ready to Sample")

        except Exception as e:
            print("Send failure: %s" % str(e))
    elif intz == 2:  # Check Can status 1 too, but then power Solenoid
        strength = acknowledge()
        send_back_number2 = sms['sender']
        print(Pumpon.value())
        if Pumpon.value() == 0 and pump_ready is 1:
            open_valve()
            pump_ready = 0
        else:
            try:
                # c.sms_send(send_back_number2, strength)
                # utime.sleep_ms(500)
                if Pumpon.value() == 1:
                    c.sms_send(send_back_number2, "Pump Busy")
                if pump_ready is 0:
                    c.sms_send(send_back_number2, "Pump already Sampled")
                if Pumpon.value() == 1 and pump_ready is 0:
                    c.sms_send(send_back_number2, "Pump already Sampled and is Busy")
            except Exception as e:
                print("Send failure: %s" % str(e))
            print("Valve busy")
    elif intz == 3:  # Check Can status 2 too, but then power Solenoid RIGHT NOW THIS DOES THE SAME AS 2
        strength = acknowledge()
        pump_ready = 1
        send_back_number2 = sms['sender']
        if Pumpon.value == 0:
            open_valve()
        else:
            print("Valve busy")
    elif intz == 4:  # Do a System or Canister Reset
        strength = acknowledge()
        send_back_number2 = sms['sender']
        pump_ready = 1
        try:
            # c.sms_send(send_back_number2, strength)
            # utime.sleep_ms(500)
            c.sms_send(send_back_number2, "Pump Resetting")
        except Exception as e:
            print("Send failure: %s" % str(e))
        print("At some point this will reset something")
    elif intz == 5:  # Get new Time
        pump_ready = 1
        send_back_number2 = sms['sender']
        # time_passed = 0
        """while time_passed < 60:
            sms2 = c.sms_receive() # wait for seconds
            if sms2:
                t = sms2['message']
                change_time(t)
                break
            time.sleep(1)
            time_passed = time_passed + 1 # Ichibio Keka
            """
        try:
            # c.sms_send(send_back_number2, strength)
            # utime.sleep_ms(500)
            c.sms_send(send_back_number2, "Pump Time Changed to " + data[2])
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


def read_adc0():
    global analog0
    val = analog0.read()
    return val


def read_adc1():
    global analog1
    val = analog1.read()
    return val


"""def i2c_request():
    global i2c
    data_i2c = i2c.readfrom(40, 2)
    data_i2c=  int.from_bytes(data_i2c, byteorder='big') # may be little
    output = ((.80)/(30))*(data_i2c+15) + .1
    return output
"""

def read_status():
    if Pumpon.value() == 1:
        print("Pump1 Not available")
    # if Pump2.value == 1:
    #    print("Pump2 not available.")
    # if (Pump1.value() == 0) dand (Pump2.value() == 0):
    #    print("Both Pumps are available")


def check_pins():
    print(Pumpon, Pumpoff)  # i2c,


def open_valve():
    # Latching
    # time to open that solenoid
    Pumpon.value(1)
    # pulse power for 500 ms (for now)
    utime.sleep_ms(500)
    Pumpon.value(0)
    # stop pulsing
    # let valve stay open for 30 seconds, currently commented out for demo purposes
    time.sleep(Pump_time)
    # still on until... close valve! Make sure to use off switch line
    close_valve()
    # should be ded now


def close_valve():
    # Latching
    Pumpoff.value(1)
    # time to close that valve
    # pulse the  power for 500 ms
    utime.sleep_ms(500)
    # stop pulsing
    Pumpoff.value(0)
    time.sleep(2)
    # now its off, yay


def open_nonswitch_valve(pump):
    # Non-Switching
    # time to open that solenoid
    # pulse power for 500 ms (for now)
    pump.value(1)
    utime.sleep_ms(500)
    # stop pulsing
    time.sleep(Pump_time)
    close_valve(pump)


def close_nonswitch_valve(pump):
    # Non-Switching
    # time to close that valve
    # pulse the negative power for 500 ms
    pump.value(0)
    utime.sleep_ms(500)
    # stop pulsing


def open_valve_timed(pump, t):
    # Latching
    # time to open that solenoid
    pump.value(1)
    # pulse power for 500 ms (for now)
    utime.sleep_ms(500)
    pump.value(0)
    # stop pulsing
    time.sleep(t)
    # still on until... close valve! Make sure to use off switch line
    close_valve(Pumpoff)
    # should be ded now


def close_valve_timed(pump, t):
    # Latching
    pump.value(1)
    # time to close that valve
    # pulse the  power for 500 ms
    utime.sleep_ms(500)
    # stop pulsing
    pump.value(0)
    time.sleep(t)
    # now its off, yay


def change_time(t):
    global Pump_time
    Pump_time = float(t)


def reset_time():
    global Pump_time
    Pump_time = 30


def timestamp():
    now = utime.localtime() # time.struct_time(tm_year=2020, tm_mon=7, tm_mday=13, tm_hour=17, tm_min=10, tm_sec=35, tm_wday=0, tm_yday=195, tm_isdst=0)
    year = now[0]
    month = now[1]
    day = now[2]
    hour = now[3]
    min = now[4]
    sec = now[5]
    # can.can_log.append(now)
    # can.sample_count = can.sample_count + 1
    datetime = ""+str(year)+"-"+str(month)+"-"+str(day)+"  "+str(hour)+":"+str(min)+":"+str(sec)
    return datetime

first_time = True


def acknowledge():
    strength = xbee.atcmd('DB')
    message_ak = "SS: " + str(strength) + " dB"
    return message_ak


global current_sender
change = False  # This variable helpsKeep track of who the last sender was/is
# while True:
#    open_valve(Pumpon)
# if reset_pin.value() == 0:

#    xbee.atcmd('FR')
#    machine.soft_reset()
#    print(reset_pin.value())
close_valve()
print("Closing the pump just in case")
while not c.isconnected():
    # print("I am not connected")
    """if reset_pin.value() == 0:
        xbee.atcmd('FR')
        print(reset_pin.value())
        machine.soft_reset()
        print(reset_pin.value())
        """
    time.sleep(1)

while True:
    if reset_pin.value() == 0:
        #  led.value(1)
        print(reset_pin.value())
        # xbee.atcmd('FR')
        machine.soft_reset()
    sms = c.sms_receive()
    if sms and first_time:  # or change:  # if a new user is texting in to the device,
        change = False  # send them the commands
        first_time = False
        current_sender = sms['sender']
        send_back_number = sms['sender']
        c.sms_send(send_back_number, send_list)  # Sender gets command list

        time.sleep(1)  # wait one second
    elif sms:  # no change in sender or the first time it has been activated
        print("SMS received from %s >> %s" % (sms['sender'], sms['message']))
        send_back_number2 = sms['sender']  # this sets up the sender as the receiver of the Xbee Message
        message_send = text_messages(sms['message'])
        # new_msg = "" + i2c_request()
        strength = acknowledge()

        new_msg = " strength: " + strength + ", Pressure: " + str(read_adc0()) + ". Timestamp: " + timestamp()

        try:
            c.sms_send(send_back_number2, new_msg)
            print("Successful send")
        except Exception as e:
            print("Send failure: %s" % str(e))
        time.sleep(1)

        control_canister(command_list(sms['message']))
        try:
            c.sms_send(send_back_number2, message_send)
            print("Successful send")
        except Exception as e:
            print("Send failure: %s" % str(e))
    # Wait 1000 ms before checking for data again.
    time.sleep(1)
