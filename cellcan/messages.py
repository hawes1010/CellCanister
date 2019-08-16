import time

# Initialize ports and pins
import network
import xbee
import machine
from machine import Pin
from machine import I2C
i2c = I2C("D1", "P1", freq=400000)  # I2c Module
