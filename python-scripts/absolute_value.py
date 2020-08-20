import math

cx1 = -57
cx2 = 27


def neg(value):
    if (value < 0):
        print("neg")
        return True
    else:
        print("pos")
        return False


def deltaCalc(a, b):
    if neg(a) ^ neg(b):
        delta = abs(a) + abs(b)
    else:
        delta = abs(a - b)
    return delta


deltaX = deltaCalc(cx1, cx2)
calConstX = deltaX / 30  # EU/cm
print(deltaX)
print(calConstX)

x1 = -5  # Test Numbers
x2 = 73
y1 = -24
y2 = 90

# while True:
#     time.sleep(.01)
#     if button_pressed():
#         (x1,y1) = get_position();
#         break

# while True:
#     time.sleep(.01)
#     if button_pressed():
#         (x2,y2) = get_position();
#         break

delx = deltaCalc(x1, x2)
dely = deltaCalc(y1, y2)

distEU = math.sqrt((delx ^ 2) + (dely ^ 2))
distCM = distEU / calConstX  # EU/(EU/cm)

print(delx, dely)
print(distEU)
print(distCM)
