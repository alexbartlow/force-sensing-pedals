import board
import digitalio
import analogio
import usb_hid

from hid_gamepad import Gamepad

gp = Gamepad(usb_hid.devices)

class HX711:
    def __init__(self, pd_sck, dout, gain=128):
        self.pSCK = pd_sck
        self.pOUT = dout
        self.pSCK.value = False

        self.GAIN = 0
        self.OFFSET = 0
        self.SCALE = 1

        self.time_constant = 0.25
        self.filtered = 0

        self.set_gain(gain)

    def set_gain(self, gain):
        if gain is 128:
            self.GAIN = 1
        elif gain is 64:
            self.GAIN = 3
        elif gain is 32:
            self.GAIN = 2

        self.read()
        self.filtered = self.read()

    def is_ready(self):
        return self.pOUT == 0

    def read(self):
        # wait for the device being ready
        for _ in range(500):
            if self.pOUT.value == 0:
                break
            time.sleep(0.001)
        else:
            raise OSError("Sensor does not respond")

        # shift in data, and gain & channel info
        result = 0
        for j in range(24 + self.GAIN):
          #  state = disable_irq()
            self.pSCK.value = True
            self.pSCK.value = False
          #  enable_irq(state)
            result = (result << 1) | self.pOUT.value

        # shift back the extra bits
        result >>= self.GAIN

        # check sign
        if result > 0x7fffff:
            result -= 0x1000000

        return result

    def read_average(self, times=3):
        sum = 0
        for i in range(times):
            sum += self.read()
        return sum / times

    def read_lowpass(self):
        self.filtered += self.time_constant * (self.read() - self.filtered)
        return self.filtered

    def get_value(self):
        return self.read_lowpass() - self.OFFSET

    def get_units(self):
        return self.get_value() / self.SCALE

    def tare(self, times=15):
        self.set_offset(self.read_average(times))

    def set_scale(self, scale):
        self.SCALE = scale

    def set_offset(self, offset):
        self.OFFSET = offset

    def set_time_constant(self, time_constant = None):
        if time_constant is None:
            return self.time_constant
        elif 0 < time_constant < 1.0:
            self.time_constant = time_constant

    def power_down(self):
        self.pSCK.value(False)
        self.pSCK.value(True)

    def power_up(self):
        self.pSCK.value(False)

import board
import digitalio

import time
#import ticks_ms, ticks_diff, sleep, sleep_ms

pin_OUT = digitalio.DigitalInOut(board.GP26)
pin_OUT2 = digitalio.DigitalInOut(board.GP17)
#pin_OUT.direction = digitalio.Direction.OUTPUT

pin_SCK = digitalio.DigitalInOut(board.GP16)
pin_SCK.direction = digitalio.Direction.OUTPUT

pin_SCK2 = digitalio.DigitalInOut(board.GP27)
pin_SCK2.direction = digitalio.Direction.OUTPUT

hx1 = HX711(pin_SCK, pin_OUT)
hx2 = HX711(pin_SCK2, pin_OUT2)
hx1.set_gain(128)
hx2.set_gain(128)
hx1.set_time_constant(0.875)
hx2.set_time_constant(0.875)

hx1.tare()
hx2.tare()

time.sleep(0.050)
scale = 100.0

def range_map(x, in_min, in_max, out_min, out_max):
    if(x < in_min):
        return out_min
    if(x > in_max):
        return out_max

    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

xmin = 0
xmax = 0

ymin = 0
ymax = 0

def getdata():
    while True:
        d1 = int(hx1.get_value() / scale)
        d2 = int(hx2.get_value() / scale)

        nx = range_map(d1, -30000, 0, -127, 127)
        ny = range_map(d2, -30000, 0, -127, 127)
        yaw = range_map(d1-d2,-30000,30000, -127, 127)
        z = max([nx, ny])

        print("d1: ", d1, "d2: ", d2, "yaw: ", yaw, "z: ", z) 

        gp.move_joysticks(
            x=nx,
            y=ny,
            z=yaw,
            r_z=z
        )

        time.sleep(0.005)
        
       # lcd.putstr("Strain Gauge " +"\n")
       # lcd.putstr(str(data)+"\n")

        
if __name__=="__main__":
    print("NOT CALIBRATED!")
    getdata()