#!/usr/bin/python
# Photogate controls
# 2019.07.27
# Aunders Hallsten

################################################################################
# imports
import termios
import serial


################################################################################
# communication setup
port = '/dev/ttyUSB0'
f = open(port)
print("port open")

# disable auto reset when port is opened to perserve encoder pos
attrs = termios.tcgetattr(f)
attrs[2] = attrs[2] & ~termios.HUPCL
termios.tcsetattr(f, termios.TCSAFLUSH, attrs)
f.close()
se = serial.Serial()
se.baudrate = 115200
se.port = port
print('dtr =', se.dtr)
se.open()
print("serial com successfully started")


def get_position():
    se.reset_input_buffer()
    while True:
        if se.in_waiting > 0:
            print("bytes in input buffer:", se.in_waiting)
            inputValue = se.readline()
            str_xy = inputValue.decode('utf-8')
            x, y = str_xy.split(",")
            # print("X:", int(x), "Y:", int(y))
            return int(x), int(y)


# testing
# ----------------------------
if __name__ == "__main__":

    # while True:
    #     print("before if:", se.in_waiting)
    #     if se.in_waiting > 0:
    #         print("after if:", se.in_waiting)
    #         inputValue = se.readline()
    #         str_xy = inputValue.decode('utf-8')
    #         x, y = str_xy.split(",")
    #         print("X:", int(x), "Y:", int(y))

    get_position()
