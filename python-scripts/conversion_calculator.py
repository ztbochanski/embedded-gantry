#!/usr/bin/python
# conversion functions for encoder position
# 2019.06.18
# Aunders Hallsten
# Zachary Bochanski
# Kyle Bochanski

# Imports
################################################################################

# get absolute values of encoder pos to perform calculations
################################################################################


# check if neg or pos in order to calculate abs value
def neg(value):
    if (value < 0):
        return True
    else:
        return False


# return absolute value difference
def deltaCalc(a, b):
    if neg(a) ^ neg(b):
        delta = abs(a) + abs(b)
    else:
        delta = abs(a - b)
    return delta


# main function return the conversion factor enc_units/cm
def converter(pos1, pos2, zeroing_val_cm):
    delta = deltaCalc(pos1, pos2)
    ans = delta / zeroing_val_cm
    return ans


# takes x1 and x2 from measure function and converts cm before storage
def convert_x(x1, x2, x_conversion_factor):
    if x_conversion_factor == 0:
        return x1, x2
    else:
        # # handle encoder position reset at 255 (starts over at 0)
        # # exclusive or (only run if one x measurment is above 126)
        # if x1 > 126 & x2 < 126 | x2 > 126 & x1 < 126:
        #     if x1 > 126:
        #         x1 = BYTE_INT - x1
        #     elif x1 < 126:
        #         ans = BYTE_INT - x1
        #         x1 = BYTE_INT - ans
        #
        #     if x2 > 126:
        #         x2 = BYTE_INT - x2
        #     elif x2 < 126:
        #         ans = BYTE_INT - x2
        #         x2 = BYTE_INT - ans

        x1 = x1 / x_conversion_factor  # encoder units / conversion factor
        x2 = x2 / x_conversion_factor
        return x1, x2


# takes y1 and y2 from measure function and converts to cm before storage
def convert_y(y1, y2, y_conversion_factor):
    if y_conversion_factor == 0:
        return y1, y2
    else:
        y1 = y1 / y_conversion_factor
        y2 = y2 / y_conversion_factor
        return y1, y2


# testing purposes
def test():
    pos1 = 10
    pos2 = 6
    zeroing_val_cm = 2

    ans = converter(pos1, pos2, zeroing_val_cm)
    print("conversion enc/cm: ", ans)


if __name__ == "__main__":
    test()
