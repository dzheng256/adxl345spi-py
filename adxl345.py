import time
from collections import deque, defaultdict
import ctypes as ct

import pigpio


class ADXL345:
    def __init__(self):
        self.DATA_FORMAT = 0x31
        self.DATA_FORMAT_B = 0x0b
        self.READ_BIT = 0x80
        self.MULTI_BIT = 0x40
        self.BW_RATE = 0x2c
        self.POWER_CTL = 0x2d
        self.DATAX0 = 0x32

        self.time_default = 10
        self.freq_default = 30
        self.freq_max_spi = 100000
        self.spi_speed = 2000000
        self.cold_start_samples = 2
        self.cold_start_delay = 0.1
        self.acc_conversion = 2 * 16.0/8192

        self.pi = pigpio.pi()
        self.data = bytearray(b'\0\0\0\0\0\0\0')

        self.READ_DATA = self.data[:]
        self.READ_DATA[0] = self.DATAX0
        self.READ_DATA[0] |= self.MULTI_BIT
        self.WRITE_DATA = self.READ_DATA[:]
        self.READ_DATA[0] |= self.READ_BIT
        self.v_save = ""
        self.v_time = self.time_default
        self.v_freq = self.freq_default
        self.samples = self.v_freq * self.v_time
        self.samples_max_spi = self.freq_max_spi * self.v_time
        self.h = self.pi.spi_open(0, self.spi_speed, 3)
        self.cold_start()
 
        self.data[0] = self.BW_RATE
        self.data[1] = 0x0F
        self.write_bytes(self.pi, self.h, self.data[:2])
        self.data[0] = self.DATA_FORMAT
        self.data[1] = self.DATA_FORMAT_B
        self.write_bytes(self.pi, self.h, self.data[:2])
        self.data[0] = self.POWER_CTL
        self.data[1] = 0x08
        self.write_bytes(self.pi, self.h, self.data[:2])
        self.delay = 1.0 / self.v_freq
        self.saved_data = defaultdict(deque)

    def cold_start(self):
        for _ in range(self.cold_start_samples):
            # read bytes
            count, data = self.pi.spi_xfer(self.h, self.READ_DATA)
            time.sleep(self.cold_start_delay)

    def read(self):
        success = 1
        start_time = time.time()
        for _ in range(self.samples):
            count, data = self.pi.spi_xfer(self.h, self.READ_DATA)
            if count == 7:
                x = ct.c_int16(((data[2] << 8)) | data[1]).value
                y = ct.c_int16(((data[4] << 8)) | data[3]).value
                z = ct.c_int16(((data[6] << 8)) | data[5]).value
                t = time.time() - start_time
                for k, v in zip(('t', 'x', 'y', 'z'), (t, x, y, z)):
                    self.saved_data[k].append(v)
                # print("time={:10.5f},x={:10.5f},y={:10.5f},z={:10.5f}"
                #      .format(t, x*acc_conversion, y*acc_conversion, z*acc_conversion))
                yield t, x, y, z
            else:
                success = 0
            time.sleep(self.delay)
        duration = time.time() - start_time
        # print("{} samples read in {} seconds at sample rate {}".format(samples,
        #     duration, samples/duration))
        if not success:
            print("Error occurred!")
