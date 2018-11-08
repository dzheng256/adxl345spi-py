# adxl345spi-py
Reading data from the ADXL345 accelerometer over SPI on a raspberry pi w/ python. 
Essentially a python port of part of [this project](https://github.com/nagimov/adxl345spi).

## Setup
First install the `pigpio` library.
```
wget abyz.co.uk/rpi/pigpio/pigpio.zip
unzip pigpio.zip
cd PIGPIO
make -j4
sudo make install
```
## Usage
Start the `pigpiod` daemon with `sudo pigpiod`. Then, you can use the library like this:
```python
import adxl345
adxl = adxl345.ADXL345(sample_rate=100, time=10)
adxl.read()
```



