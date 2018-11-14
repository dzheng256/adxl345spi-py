import time
import ctypes as ct

import pigpio


class ADXL345:
    def __init__(self, sample_rate=10):
        self.DATA_FORMAT = 0x31
        self.DATA_FORMAT_B = 0x0b
        self.READ_BIT = 0x80
        self.MULTI_BIT = 0x40
        self.BW_RATE = 0x2c
        self.POWER_CTL = 0x2d
        self.DATAX0 = 0x32

        self.freq_max_spi = 100000
        self.v_freq = sample_rate
        self.spi_speed = 2000000
        self.cold_start_samples = 2
        self.cold_start_delay = 0.1
        self.acc_conversion = 2 * 16.0/8192

        self.pi = pigpio.pi()
        self.data = bytearray(b'\0\0\0\0\0\0\0')

        self.READ_DATA = self.data[:]
        self.READ_DATA[0] = self.DATAX0
        self.READ_DATA[0] |= self.MULTI_BIT
        self.READ_DATA[0] |= self.READ_BIT

        self.h = self.pi.spi_open(0, self.spi_speed, 3)

        self.data[0] = self.BW_RATE
        self.data[1] = 0x0F
        self.data[0] |= self.MULTI_BIT
        self.pi.spi_xfer(self.h, self.data[:2])
        self.data[0] = self.DATA_FORMAT
        self.data[1] = self.DATA_FORMAT_B
        self.data[0] |= self.MULTI_BIT
        self.pi.spi_xfer(self.h, self.data[:2])
        self.data[0] = self.POWER_CTL
        self.data[1] = 0x08
        self.data[0] |= self.MULTI_BIT
        self.pi.spi_xfer(self.h, self.data[:2])

        self.cold_start()

        self.delay = 1.0 / self.v_freq

    def cold_start(self):
        for _ in range(self.cold_start_samples):
            # read bytes
            count, data = self.pi.spi_xfer(self.h, self.READ_DATA)
            time.sleep(self.cold_start_delay)

    def read(self, samples):
        for _ in range(samples):
            yield self.read_one()
            time.sleep(self.delay)

    def read_with_delay(self, samples):
        for _ in range(samples):
            yield self.read_one()
            time.sleep(self.delay)



    def read_one(self):
        count, data = self.pi.spi_xfer(self.h, self.READ_DATA)
        if count == 7:
            x = ct.c_int16(((data[2] << 8)) | data[1]).value * self.acc_conversion
            y = ct.c_int16(((data[4] << 8)) | data[3]).value * self.acc_conversion
            z = ct.c_int16(((data[6] << 8)) | data[5]).value * self.acc_conversion
            t = time.time()
            return t, x, y, z
        else:
            raise ValueError('Error occurred, did not read 7 bytes!')

    def close(self):
        self.pi.spi_close(self.h)
