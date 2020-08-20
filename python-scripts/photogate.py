#!/usr/bin/python
# Photogate controls
# 2019.06.11
# Zachary Bochanski

# Imports
################################################################################
from smbus2 import SMBus, i2c_msg, SMBusWrapper
import time

# smbus setup for i2c connection and return postion of optical encoders
################################################################################
CHANNEL = 1  # channel on rpi

# I2C address of Arduino Slave
i2c_address1 = 0x20  # x axis
i2c_address2 = 0x40  # y axis

# I2C Register
I2C_REGISTER = 0x02


# bus = SMBus(CHANNEL)


def get_position():
    x = bus.read_word_data(i2c_address1, 0)
    y = bus.read_word_data(i2c_address2, 0)
    return x, y


def main():
    global x, y
    while True:
        # x, y = get_position()
        # print("Y:", y, "X:", x)
        get_position()
        time.sleep(.2)


# ----------------------------
if __name__ == "__main__":
    # main()

    while True:
        time.sleep(.2)
        with SMBusWrapper(1) as bus:
            b = bus.read_byte(i2c_address2)
            print(b)
