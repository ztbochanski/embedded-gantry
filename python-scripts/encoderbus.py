import time
from smbus2 import SMBus, i2c_msg

# Initialize I2C (SMBus)
bus = SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

# A1 address on the I2C bus
A1_address = 8
A2_address = 9

# Read temperature registers and calculate Celsius
# def read_enc():

# pull the encoder position from A1
#    A1Pos = i2c.read(A1_address, 1)
#    A2Pos = i2c.read(A2_address, 1)
#    A1Pos = bus.read_byte(A1_address)
#    A2Pos = bus.read_byte(A2_address)
#    return A1Pos, A2Pos

# Print out temperature every second
# while True:
#    pos = read_enc()
#    print(pos)
#    time.sleep(.5)


# This is the address we setup in the Arduino Program
address = 0x04


def writeNumber(value):
    bus.write_byte(address, value)
    # bus.write_byte_data(address, 0, value)
    return -1


def readNumber():
    number = bus.read_byte(address)
    # number = bus.read_byte_data(address, 1)
    return number


while True:
    # var = input("Enter number 1-9: ")
    # if not var:
    #     continue
    # writeNumber(var)
    # print("RPI: Hi Arduino, I sent you", var)
    time.sleep(.5)
    number = readNumber()
    print("number type:", type(number), "number str:",
          str(number), "num cast:", bytes(number))
