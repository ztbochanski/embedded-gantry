#!/usr/bin/python
# Rotary Encoder and LCD software for plant morphology gantry operation
# 2019.06.11
# Zachary Bochanski

################################################################################
# Imports
################################################################################
# LCD
import time
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
# ROTARY ENCODER
from RPi import GPIO
import subprocess
import queue
from threading import Thread
import axis_rotary_encoders
# CALULATION AND SQLITE3/GOOGLE STORAGE
import math
import conversion_calculator
import db
from google_interfaces import SheetsInterface


################################################################################
# LCD SETUP
lcd_rs = digitalio.DigitalInOut(board.D26)
lcd_en = digitalio.DigitalInOut(board.D19)
lcd_d7 = digitalio.DigitalInOut(board.D27)
lcd_d6 = digitalio.DigitalInOut(board.D22)
lcd_d5 = digitalio.DigitalInOut(board.D24)
lcd_d4 = digitalio.DigitalInOut(board.D25)


# LCD screen size
lcd_columns = 16
lcd_rows = 2

# Initialise the LCD class
lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
                                      lcd_d7, lcd_columns, lcd_rows)
################################################################################
# Define a queue to communicate with worker thread
lcdq = queue.Queue()
################################################################################


# Constants
# Our first hardware interrupt pin is digital pin number:
APIN = 6
# Our second hardware interrupt pin is digital pin number:
BPIN = 16
# Button reading, including debounce without delay function declarations
SPIN = 5  # this is the pi pin we are connecting the push button to(sw pin)
# oldButtonState = HIGH  # assume switch open because of pull-up resistor
DEBOUNCE = 2  # milliseconds
SW_DEBOUNCE = 10  # milliseconds

# menu min and max number of options
MIN = 0
MAX = 0

# CONSTANT FOR CALIBRATION in cm
CONVERSION_CONSTANT = 30

# Global variables
# somewhere to store the direct values we read from our interrupt pins before checking to see if we have moved a whole detent
pin_reading = 0
# last pin reading
last_pin = None
# let's us know when we're expecting a rising edge on APIN to signal that the encoder has arrived at a detent
bflag = 0
# let's us know when we're expecting a rising edge on BPIN to signal that the encoder has arrived at a detent (opposite direction to when AFLAG is set)
aflag = 0
# this variable stores our current value of encoder position.
encoderpos = 0
# stores the last encoder position value so we can compare to the current reading and see if it has changed (so we know when to print to the serial monitor)
old_encoderpos = None
# state of the button initialized at 0 for not pressed
button_pressed = False
x_conversion_factor = 0
y_conversion_factor = 0


################################################################################
# GPIO Setup
################################################################################
def setup():
    GPIO.setmode(GPIO.BCM)

    # rotary encoder setup
    GPIO.setup(APIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(BPIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    GPIO.add_event_detect(
        APIN, GPIO.RISING, callback=a_call, bouncetime=DEBOUNCE)
    # GPIO.add_event_detect(
    #     BPIN, GPIO.RISING, callback=b_call, bouncetime=DEBOUNCE)

    # push button setup
    GPIO.setup(SPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # GPIO.add_event_detect(
    #     SPIN, GPIO.FALLING, callback=switch_call, bouncetime=SW_DEBOUNCE)


################################################################################
# Interrupt Functions
################################################################################
# A channel
def a_call(channel):
    global encoderpos

    a = GPIO.input(APIN)
    b = GPIO.input(BPIN)

    if a == 1 and b == 0:
        down()
        # print("direction -> ", encoderpos)
        # at this point, B may still need to go high, wait for it
        while b == 0:
            b = GPIO.input(APIN)
        # now wait for B to drop to end the click cycle
        while b == 1:
            b = GPIO.input(BPIN)
        return

    elif a == 1 and b == 1:
        up()
        # print("direction <- ", encoderpos)
        # A is already high, wait for A to drop to end the click cycle
        while a == 1:
            a = GPIO.input(APIN)
        return

    else:
        return


# # B channel
# def b_call(channel):
#     global aflag, bflag
#
#     # get b pin and compare to HIGH or 1
#     b_pin = GPIO.input(APIN)
#     if b_pin == 1 and bflag:
#         down()
#         bflag = 0
#         aflag = 0
#     elif b_pin == 0:
#         aflag = 1


# Button (this is called twice because of the "click" action of the button)
# def switch_call(channel):
#     if GPIO.input(SPIN) == 0:
#         button_pushed()
#         print("pushed")


################################################################################
# Interrupt Control Outputs
################################################################################
# subtract 1 to go up within min max
def up():
    global encoderpos
    encoderpos -= 1
    if encoderpos < MIN:
        encoderpos = MAX


# add 1 to go down within min max
def down():
    global encoderpos
    encoderpos += 1
    if encoderpos > MAX:
        encoderpos = MIN


# set global variable to true when pressed
def button_pushed():
    if GPIO.input(SPIN):
        return False
    else:
        return True


def set_minmax(min, max):
    global MAX, MIN
    MIN = min
    MAX = max


################################################################################
# gettters for inerrupt outputs
################################################################################
# output of rotary encoder, up or down (-, +) within the specified MIN/MAX
def get_position():
    global encoderpos, old_encoderpos
    if old_encoderpos != encoderpos:
        return encoderpos
        old_encoderpos = encoderpos


################################################################################
# menu helper functions
################################################################################
# intro on device startup
def intro():
    intro_message = "Plenty - Traverskran"
    lcd.message = intro_message
    # Scroll message to the left
    for i in range(len(intro_message)):
        time.sleep(0.2)
        lcd.move_left()


# commands for subprocess
def run_cmd(cmd):
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = p.communicate()[0]
    return output


# reset encoder position when navigating in and out of menus
def reset(scroll):
    scroll = 0
    return scroll


################################################################################
# ----------------------------
# MAIN LOOP
# ----------------------------
def main():
    try:
        # setup functions
        # lcd plate
        lcd.clear()
        # backlight on/off?
        # rotary encoder setup
        setup()
        # startup display
        intro()

        # create worker thread and make a daemon for screen managment
        worker = Thread(target=update_lcd, args=(lcdq,))
        worker.setDaemon(True)
        worker.start()

        # Control functions
        navigation()

    except KeyboardInterrupt:
        print('\nexiting...')
        lcd.clear()
        lcd.message = 'Interrupted \nby keyboard'

    # except:
    #     lcd.clear()
    #     lcd.message = 'Unknown Error \nManually Reboot'

    finally:
        GPIO.cleanup()


# ----------------------------
# WORKER THREAD
# ----------------------------
# Define a function to run in the worker thread aka screen managment daemon
def update_lcd(q):
    while True:

        # Pull strings from queue
        msg = q.get()
        while not q.empty():
            q.task_done()
            msg = q.get()

        # LCD Rendering
        lcd.clear()
        lcd.cursor = True
        lcd.blink = True

        # Display in top row
        lcd.message = msg
        q.task_done()
    return


# ----------------------------
# NAVIGATION
# ----------------------------
def navigation():
    MENU_LIST = [
        '1. Calibrate',
        '2. Measure',
        '3. Delete Last',
        '4. Reboot'
    ]

    # this menu has 4 options, set min and maxes for menu navigation
    set_minmax(0, 3)

    initial_position = 0
    scrolling_position = 0
    lcd.clear()
    lcdq.put(MENU_LIST[initial_position], True)

    keep_loop = True
    while keep_loop:
        # resests min max when coming from other submenus of differend lengths
        set_minmax(0, 3)

        # use encoder position to search through list index only if the encoder
        # position has changed
        scrolling_position = get_position()
        if initial_position != scrolling_position:
            if scrolling_position == 0:
                lcdq.put(MENU_LIST[0], True)
            elif scrolling_position == 1:
                lcdq.put(MENU_LIST[1], True)
            elif scrolling_position == 2:
                lcdq.put(MENU_LIST[2], True)
            elif scrolling_position == 3:
                lcdq.put(MENU_LIST[3], True)
            # update scrolling position to current_selection
            initial_position = scrolling_position

        if button_pushed():
            time.sleep(.2)
            if scrolling_position == 0:
                calibrate()
            elif scrolling_position == 1:
                measure()
            elif scrolling_position == 2:
                delete_last()
            elif scrolling_position == 3:
                exit()


################################################################################
# sub-menu functions for measuring and calibration
################################################################################
def calibrate():
    global x_conversion_factor, y_conversion_factor, encoderpos
    CALIBRATION_LIST = [
        '1. Calibrate X',
        '2. Calibrate Y',
        '3. Exit'
    ]

    # this menu has 4 options, set min and maxes for menu navigation
    set_minmax(0, 2)

    initial_position = 0
    lcd.clear()
    lcdq.put(CALIBRATION_LIST[initial_position], True)

    keep_loop = True
    while keep_loop:
        # resests min max when coming from other submenus of differend lengths
        set_minmax(0, 2)

        # use encoder position to search through list index only if the encoder
        # position has changed
        scrolling_position = get_position()
        if initial_position != scrolling_position:
            if scrolling_position == 0:
                lcdq.put(CALIBRATION_LIST[0], True)
            elif scrolling_position == 1:
                lcdq.put(CALIBRATION_LIST[1], True)
            elif scrolling_position == 2:
                lcdq.put(CALIBRATION_LIST[2], True)
            # update scrolling position to current_selection
            initial_position = scrolling_position

        if button_pushed():
            if scrolling_position == 0:
                x_conversion_factor = calibrate_x()
                print("conversion x: ", x_conversion_factor)
            elif scrolling_position == 1:
                y_conversion_factor = calibrate_y()
                print("conversion y: ", y_conversion_factor)
            elif scrolling_position == 2:
                encoderpos = 1
                break


def measure():
    global encoderpos, x_conversion_factor, y_conversion_factor
    # distance formula to find the measurement
    D_LIST = [
        'Press at \ncoordinate 1..',
        'Press at \ncoordinate 2..'
    ]

    lcdq.put(D_LIST[0], True)
    while True:
        time.sleep(.2)
        if button_pushed():
            x1, y1 = axis_rotary_encoders.get_position()
            lcdq.put('C2: ' + str(x1) + ", " + str(y1), True)
            time.sleep(1)
            break

    lcdq.put(D_LIST[1], True)
    while True:
        time.sleep(.2)
        if button_pushed():
            x2, y2 = axis_rotary_encoders.get_position()
            lcdq.put('C2: ' + str(x2) + ", " + str(y2), True)
            time.sleep(1)
            encoderpos = 1
            break

    # convert axis_rotary_encoders outputs using calibrations
    x1, x2 = conversion_calculator.convert_x(x1, x2, x_conversion_factor)
    y1, y2 = conversion_calculator.convert_y(y1, y2, y_conversion_factor)
    print("\nx values in cm: ", x1, x2)
    print("y values in cm: ", y1, y2)
    # distance formula
    dx = (x2 - x1)**2
    dy = (y2 - y1)**2
    dxy = dx + dy
    dxy = math.sqrt(dxy)
    dxy = '%.2f' % (dxy)
    print("\ndistance formuala output: ", dxy)

    # ##########

    # # store measurement in sqlite3 db: open connection, check if table exists
    # con = db.connection_open()
    # db.create_table_ifnot_exists(con)
    #
    # # insert dxy
    # db.insert(con, dxy)
    #
    # # close Connection
    # db.connection_close(con)

    # store measurement in google sheet
    spread_id = '1O3sziM6HUfD8bkoxaUNzrejZ0yVy__M8RsMzt4EGqa0'

    si = SheetsInterface(spread_id=spread_id)
    row = [dxy]
    sheet_name = 'gantry_test_input1'
    si.append_values_to_sheet(sheet_name, values=row)
    print(dxy, 'loaded to sheets')

    # ##########

    # show measuremnt on lcd screen
    distance_str = str(dxy) + " Press again \n>Or trn 2 exit "
    lcdq.put(distance_str, True)
    time.sleep(1)


def delete_last():
    con = db.connection_open()
    db.delete(con)
    db.connection_close(con)
    msg = "Last point \ndeleted..."
    print(msg)
    lcdq.put(msg, True)
    time.sleep(2)


def exit():
    lcdq.put('   Rebooting \nTraverskaran...  ', True)
    lcdq.join()
    run_cmd("sudo reboot")
    lcd.clear()


################################################################################
# logic functions to perform calculations
################################################################################
# -----------------------
# calibration
# -----------------------
# calibration of y axis
def calibrate_y():
    global encoderpos, CONVERSION_CONSTANT
    Y_LIST = [
        '...Push for Y1',
        '...Push for Y2'
    ]

    lcdq.put(Y_LIST[0], True)
    while True:
        time.sleep(.2)
        if button_pushed():
            y1 = get_axis_rotary_encoders_y()
            lcdq.put('Y1 Stored: ' + str(y1), True)
            time.sleep(1)
            break

    lcdq.put(Y_LIST[1], True)
    while True:
        time.sleep(.2)
        if button_pushed():
            y2 = get_axis_rotary_encoders_y()
            lcdq.put('Y2 Stored: ' + str(y2), True)
            time.sleep(1)
            encoderpos = 2
            break

    # convert the rotary encoder units to measurement standard
    result = conversion_calculator.converter(y1, y2, CONVERSION_CONSTANT)
    return result


# calibration of x axis
def calibrate_x():
    global encoderpos, CONVERSION_CONSTANT
    X_LIST = [
        '...Push for X1',
        '...Push for X2'
    ]

    lcdq.put(X_LIST[0], True)
    while True:
        time.sleep(.2)
        if button_pushed():
            x1 = get_axis_rotary_encoders_x()
            lcdq.put('X1 Stored: ' + str(x1), True)
            time.sleep(1)
            break

    lcdq.put(X_LIST[1], True)
    while True:
        time.sleep(.2)
        if button_pushed():
            x2 = get_axis_rotary_encoders_x()
            lcdq.put('X2 Stored: ' + str(x2), True)
            time.sleep(1)
            encoderpos = 1
            break

    # convert the rotary encoder units to measurement standard
    result = conversion_calculator.converter(x1, x2, CONVERSION_CONSTANT)
    return result
# -----------------------


################################################################################
# measurment getters
################################################################################
# returns x position
def get_axis_rotary_encoders_x():
    x, y = axis_rotary_encoders.get_position()
    return x


# returns y position
def get_axis_rotary_encoders_y():
    x, y = axis_rotary_encoders.get_position()
    return y
# ----------------------------


# ----------------------------
if __name__ == "__main__":
    main()

    # testing
    # ----------------------------
    # x, y = axis_rotary_encoders.get_position()
    #
    # print(x, y)
