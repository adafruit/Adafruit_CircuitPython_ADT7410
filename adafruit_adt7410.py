# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_adt7410`
====================================================

CircuitPython driver for reading temperature from the Analog Devices ADT7410
precision temperature sensor

* Author(s): ladyada, Jose David M.

Implementation Notes
--------------------

**Hardware:**

* `Adafruit ADT7410 analog temperature Sensor Breakout
  <https://www.adafruit.com/product/4089>`_ (Product ID: 4089)


**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

* Adafruit's Bus Device library:
  https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

* Adafruit's Register library:
  https://github.com/adafruit/Adafruit_CircuitPython_Register

"""


import time
import struct
from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register.i2c_bit import RWBit, ROBit
from micropython import const

try:
    # Used only for typing
    import busio  # pylint: disable=unused-import
except ImportError:
    pass

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_ADT7410.git"


_ADT7410_TEMPMSB: int = const(0x0)
_ADT7410_TEMPLSB: int = const(0x1)
_ADT7410_STATUS: int = const(0x2)
_ADT7410_CONFIG: int = const(0x3)
_ADT7410_THIGHMSB: int = const(0x4)
_ADT7410_THIGHLSB: int = const(0x5)
_ADT7410_TLOWMSB: int = const(0x6)
_ADT7410_TLOWLSB: int = const(0x7)
_ADT7410_TCRITMSB: int = const(0x8)
_ADT7410_TCRITLSB: int = const(0x9)
_ADT7410_THYST: int = const(0x0A)
_ADT7410_ID: int = const(0xB)
_ADT7410_SWRST: int = const(0x2F)


class ADT7410:
    """Interface to the Analog Devices ADT7410 temperature sensor.

    :param ~busio.I2C i2c_bus: The I2C bus the ADT7410 is connected to.
    :param int address: The I2C device address. Default is :const:`0x48`

    **Quickstart: Importing and using the ADT7410 temperature sensor**

        Here is an example of using the :class:`ADT7410` class.
        First you will need to import the libraries to use the sensor

        .. code-block:: python

            import board
            import adafruit_adt7410

        Once this is done you can define your `board.I2C` object and define your sensor object

        .. code-block:: python

            i2c = board.I2C()  # uses board.SCL and board.SDA
            adt = adafruit_adt7410.ADT7410(i2c_bus, address=0x48)

        Now you have access to the temperature using :attr:`temperature`.

        .. code-block:: python

            temperature = adt.temperature

    """

    # many modes can be set with register objects for simplicity
    ready: ROBit = ROBit(_ADT7410_STATUS, 7)
    ctpin_polarity: RWBit = RWBit(_ADT7410_CONFIG, 2)
    intpin_polarity: RWBit = RWBit(_ADT7410_CONFIG, 3)
    comparator_mode: RWBit = RWBit(_ADT7410_CONFIG, 4)
    high_resolution: RWBit = RWBit(_ADT7410_CONFIG, 7)

    # Status Information configuration
    temp_over_critiq: ROBit = ROBit(_ADT7410_STATUS, 6)
    temp_over_high: ROBit = ROBit(_ADT7410_STATUS, 5)
    temp_under_low: ROBit = ROBit(_ADT7410_STATUS, 4)

    def __init__(self, i2c_bus: busio.I2C, address: int = 0x48):
        self.i2c_device = I2CDevice(i2c_bus, address)
        self._buf = bytearray(3)
        # Verify the manufacturer and device ids to ensure we are talking to
        # what we expect.
        _id = (self._read_register(_ADT7410_ID)[0]) & 0xF8
        if _id != 0xC8:
            raise ValueError(
                "Unable to find ADT7410 at i2c address " + str(hex(address))
            )
        self.reset()

    @property
    def temperature(self) -> float:
        """The temperature in Celsius"""
        temp = self._read_register(_ADT7410_TEMPMSB, 2)
        return struct.unpack(">h", temp)[0] / 128

    @property
    def status(self) -> int:
        """The ADT7410 status registers current value"""
        return self._read_register(_ADT7410_STATUS)[0]

    @property
    def configuration(self) -> int:
        """The ADT7410 configuration register"""
        return self._read_register(_ADT7410_CONFIG)[0]

    @configuration.setter
    def configuration(self, val: int) -> None:
        self._write_register(_ADT7410_CONFIG, val)

    def reset(self) -> None:
        """Perform a software reset"""
        self._write_register(_ADT7410_SWRST)
        time.sleep(0.5)

    def _read_register(self, addr: int, num: int = 1) -> int:
        self._buf[0] = addr
        with self.i2c_device as i2c:
            i2c.write_then_readinto(
                self._buf, self._buf, out_end=1, in_start=1, in_end=num + 1
            )
        return self._buf[1 : num + 1]

    def _write_register(self, addr: int, data: int = None) -> None:
        self._buf[0] = addr
        end = 1
        if data:
            self._buf[1] = data
            end = 2
        with self.i2c_device as i2c:
            i2c.write(self._buf, end=end)

    @property
    def high_temperature(self) -> int:
        """The over temperature limit value in Celsius"""
        temp = self._read_register(_ADT7410_THIGHMSB, 2)
        return struct.unpack(">h", temp)[0] / 128

    @high_temperature.setter
    def high_temperature(self, value: int) -> None:
        value = struct.pack(">h", int(value * 128))
        self._write_register(_ADT7410_THIGHMSB, value[0])
        self._write_register(_ADT7410_THIGHLSB, value[1])

    @property
    def low_temperature(self) -> int:
        """The over temperature limit value in Celsius. Only works when
        comparator mode is selected"""
        temp = self._read_register(_ADT7410_TLOWMSB, 2)
        return struct.unpack(">h", temp)[0] / 128

    @low_temperature.setter
    def low_temperature(self, value: int) -> None:
        value = struct.pack(">h", int(value * 128))
        self._write_register(_ADT7410_TLOWMSB, value[0])
        self._write_register(_ADT7410_TLOWLSB, value[1])

    @property
    def critical_temperature(self) -> int:
        """The critical temperature limit value in Celsius. Only works when
        comparator mode is selected"""
        temp = self._read_register(_ADT7410_TCRITMSB, 2)
        return struct.unpack(">h", temp)[0] / 128

    @critical_temperature.setter
    def critical_temperature(self, value: int) -> None:
        """The over temperature limit value in Celsius
        There is a bug in the sensor, so the address 0x09 could no be written to 0x00
        for this reason only odd numbers could be given. We could make the 0x09 with
        a value of 0x01, however make the logic more complex. Only works when
        comparator mode is selected
        """
        value = struct.pack(">h", int(value * 128))
        self._write_register(_ADT7410_TCRITMSB, value[0])
        self._write_register(_ADT7410_TCRITLSB, value[1])

    @property
    def hysteresis(self) -> int:
        """The hysteresis temperature limit value in Celsius. Only works when
        comparator mode is selected. From 0 to 15 Celsius"""
        temp = self._read_register(_ADT7410_THYST)[0]
        return temp

    @hysteresis.setter
    def hysteresis(self, value: int) -> None:
        if value > 15 or isinstance(value, float):
            raise ValueError(
                "Hysteresis value must be an integer lower than 15 Celsius"
            )

        self._write_register(_ADT7410_THYST, value)
