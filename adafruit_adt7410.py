# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
# SPDX-FileCopyrightText: 2023 Jose D. Montoya
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
from collections import namedtuple

from adafruit_bus_device import i2c_device
from adafruit_register.i2c_bits import RWBits
from adafruit_register.i2c_struct import UnaryStruct
from micropython import const

try:
    from busio import I2C
except ImportError:
    pass

try:
    from typing import Union
except ImportError:
    pass

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_ADT7410.git"

_REG_WHOAMI = const(0xB)
_TEMP = const(0x00)
_STATUS = const(0x02)
_CONFIGURATION = const(0x03)
_TEMP_HIGH = const(0x04)
_TEMP_LOW = const(0x06)
_TEMP_CRITICAL = const(0x08)
_TEMP_HYSTERESIS = const(0x0A)

CONTINUOUS = const(0b00)
ONE_SHOT = const(0b01)
SPS = const(0b10)
SHUTDOWN = const(0b11)
operation_mode_values = (CONTINUOUS, ONE_SHOT, SPS, SHUTDOWN)
operation_mode_strings = (
    "CONTINUOUS",
    "ONE_SHOT",
    "SPS",
    "SHUTDOWN",
)

LOW_RESOLUTION = const(0b0)
HIGH_RESOLUTION = const(0b1)
resolution_mode_values = (LOW_RESOLUTION, HIGH_RESOLUTION)
resolution_mode_strings = ("LOW_RESOLUTION", "HIGH_RESOLUTION")

COMP_DISABLED = const(0b0)
COMP_ENABLED = const(0b1)
comparator_mode_values = (COMP_DISABLED, COMP_ENABLED)
comparator_mode_strings = ("COMP_DISABLED", "COMP_ENABLED")

AlertStatus = namedtuple("AlertStatus", ["high_alert", "low_alert", "critical_alert"])


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

    _device_id = UnaryStruct(_REG_WHOAMI, "B")
    _temperature = UnaryStruct(_TEMP, ">h")
    _temperature_high = UnaryStruct(_TEMP_HIGH, ">h")
    _temperature_low = UnaryStruct(_TEMP_LOW, ">h")
    _temperature_critical = UnaryStruct(_TEMP_CRITICAL, ">h")
    _temperature_hysteresis = UnaryStruct(_TEMP_HYSTERESIS, "B")
    _status = UnaryStruct(_STATUS, "B")

    # Configuration register
    _resolution_mode = RWBits(1, _CONFIGURATION, 7)
    _operation_mode = RWBits(2, _CONFIGURATION, 5)
    _comparator_mode = RWBits(1, _CONFIGURATION, 4)

    # Status Register
    _critical_alert = RWBits(1, _STATUS, 6)
    _high_alert = RWBits(1, _STATUS, 5)
    _low_alert = RWBits(1, _STATUS, 4)

    def __init__(self, i2c_bus: I2C, address: int = 0x48) -> None:
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)

        if self._device_id != 0xCB:
            raise RuntimeError("Failed to find ADT7410")

    @property
    def operation_mode(self) -> str:
        """
        Sensor operation_mode

        Continuous Mode
        ---------------

        In continuous conversion mode, the read operation provides the most recent
        converted result.

        One Shot Mode
        --------------

        When one-shot mode is enabled, the ADT7410 immediately
        completes a conversion and then goes into shutdown mode. The
        one-shot mode is useful when one of the circuit design priorities is
        to reduce power consumption.

        SPS Mode
        ----------

        In this mode, the part performs one measurement per second.
        A conversion takes only 60 ms, and it remains in the idle state
        for the remaining 940 ms period

        Shutdown Mode
        ---------------
        The ADT7410 can be placed in shutdown mode, the entire IC is
        shut down and no further conversions are initiated until the
        ADT7410 is taken out of shutdown mode. The conversion result from the
        last conversion prior to shutdown can still be read from the
        ADT7410 even when it is in shutdown mode. When the part is
        taken out of shutdown mode, the internal clock is started and a
        conversion is initiated

        +--------------------------------+------------------+
        | Mode                           | Value            |
        +================================+==================+
        | :py:const:`adt7410.CONTINUOUS` | :py:const:`0b00` |
        +--------------------------------+------------------+
        | :py:const:`adt7410.ONE_SHOT`   | :py:const:`0b01` |
        +--------------------------------+------------------+
        | :py:const:`adt7410.SPS`        | :py:const:`0b10` |
        +--------------------------------+------------------+
        | :py:const:`adt7410.SHUTDOWN`   | :py:const:`0b11` |
        +--------------------------------+------------------+
        """
        return operation_mode_strings[self._operation_mode]

    @operation_mode.setter
    def operation_mode(self, value: Union[int, str]) -> None:
        if value not in operation_mode_values:
            if value not in operation_mode_strings:
                raise ValueError("Value must be a valid operation_mode setting")

            value = operation_mode_strings.index(value)
        self._operation_mode = value
        time.sleep(0.24)

    @property
    def temperature(self) -> float:
        """
        Temperature in Celsius
        In normal mode, the ADT7410 runs an automatic conversion
        sequence. During this automatic conversion sequence, a conversion
        takes 240 ms to complete and the ADT7410 is continuously
        converting. This means that as soon as one temperature conversion
        is completed, another temperature conversion begins.
        On power-up, the first conversion is a fast conversion, taking
        typically 6 ms. Fast conversion temperature accuracy is typically
        within ±5°C.
        The measured temperature value is compared with a critical
        temperature limit, a high temperature limit, and a low temperature
        limit. If the measured value
        exceeds these limits, the INT pin is activated; and if it exceeds the
        :attr:`critical_temp` limit, the CT pin is activated.
        """
        return self._temperature / 128

    @property
    def resolution_mode(self) -> str:
        """
        Sensor resolution_mode

        +-------------------------------------+-----------------+
        | Mode                                | Value           |
        +=====================================+=================+
        | :py:const:`adt7410.LOW_RESOLUTION`  | :py:const:`0b0` |
        +-------------------------------------+-----------------+
        | :py:const:`adt7410.HIGH_RESOLUTION` | :py:const:`0b1` |
        +-------------------------------------+-----------------+
        """

        return resolution_mode_strings[self._resolution_mode]

    @resolution_mode.setter
    def resolution_mode(self, value: Union[int, str]) -> None:
        if value not in resolution_mode_values:
            if value not in resolution_mode_strings:
                raise ValueError("Value must be a valid resolution_mode setting")

            value = resolution_mode_strings.index(value)
        self._resolution_mode = value

    @property
    def high_resolution(self) -> bool:
        """Whether the device is currently configured for high resolution mode."""
        return self.resolution_mode == HIGH_RESOLUTION

    @high_resolution.setter
    def high_resolution(self, value: bool) -> None:
        self.resolution_mode = HIGH_RESOLUTION if value else LOW_RESOLUTION

    @property
    def alert_status(self):
        """The current triggered status of the high and low temperature alerts as a AlertStatus
        named tuple with attributes for the triggered status of each alert.

        .. code-block :: python

            import time
            import board
            import adt7410

            i2c = board.I2C()  # uses board.SCL and board.SDA
            adt = adt7410.ADT7410(i2c)

            tmp.low_temperature = 20
            tmp.high_temperature = 23
            tmp.critical_temperature = 30

            print("High limit: {}".format(tmp.high_temperature))
            print("Low limit: {}".format(tmp.low_temperature))
            print("Critical limit: {}".format(tmp.critical_temperature))

            adt.comparator_mode = adt7410.COMP_ENABLED

            while True:
                print("Temperature: {:.2f}C".format(adt.temperature))
                alert_status = tmp.alert_status
                if alert_status.high_alert:
                    print("Temperature above high set limit!")
                if alert_status.low_alert:
                    print("Temperature below low set limit!")
                if alert_status.critical_alert:
                    print("Temperature above critical set limit!")
                time.sleep(1)

        """

        return AlertStatus(
            high_alert=self._high_alert,
            low_alert=self._low_alert,
            critical_alert=self._critical_alert,
        )

    @property
    def comparator_mode(self) -> str:
        """
        Sensor comparator_mode

        +-----------------------------------+-----------------+
        | Mode                              | Value           |
        +===================================+=================+
        | :py:const:`adt7410.COMP_DISABLED` | :py:const:`0b0` |
        +-----------------------------------+-----------------+
        | :py:const:`adt7410.COMP_ENABLED`  | :py:const:`0b1` |
        +-----------------------------------+-----------------+
        """
        return comparator_mode_strings[self._comparator_mode]

    @comparator_mode.setter
    def comparator_mode(self, value: Union[int, str]) -> None:
        if value not in comparator_mode_values:
            if value not in comparator_mode_strings:
                raise ValueError("Value must be a valid comparator_mode setting")

            value = comparator_mode_strings.index(value)
        self._comparator_mode = value

    @property
    def high_temperature(self) -> float:
        """
        High temperature limit value in Celsius
        When the temperature goes above the :attr:`high_temperature`,
        and if :attr:`comparator_mode` is selected. The :attr:`alert_status`
        high_alert clears to 0 when the status register is read and/or when
        the temperature measured goes back below the limit set in the setpoint
        :attr:`high_temperature` + :attr:`hysteresis_temperature`

        The INT pin is activated if an over temperature event occur
        The default setting is 64°C

        """
        return self._temperature_high // 128

    @high_temperature.setter
    def high_temperature(self, value: int) -> None:
        if value not in range(-55, 151, 1):
            raise ValueError("Temperature should be between -55C and 150C")
        self._temperature_high = value * 128

    @property
    def low_temperature(self) -> float:
        """
        Low temperature limit value in Celsius.
        When the temperature goes below the :attr:`low_temperature`,
        and if :attr:`comparator_mode` is selected. The :attr:`alert_status`
        low_alert clears to 0 when the status register is read and/or when
        the temperature measured goes back above the limit set in the setpoint
        :attr:`low_temperature` + :attr:`hysteresis_temperature`

        The INT pin is activated if an under temperature event occur
        The default setting is 10°C
        """
        return self._temperature_low // 128

    @low_temperature.setter
    def low_temperature(self, value: int) -> None:
        if value not in range(-55, 151, 1):
            raise ValueError("Temperature should be between -55C and 150C")
        self._temperature_low = value * 128

    @property
    def critical_temperature(self) -> float:
        """
        Critical temperature limit value in Celsius
        When the temperature goes above the :attr:`critical_temperature`,
        and if :attr:`comparator_mode` is selected. The :attr:`alert_status`
        critical_alert clears to 0 when the status register is read and/or when
        the temperature measured goes back below the limit set in
        :attr:`critical_temperature` + :attr:`hysteresis_temperature`

        The INT pin is activated if a critical over temperature event occur
        The default setting is 147°C
        """
        return self._temperature_critical // 128

    @critical_temperature.setter
    def critical_temperature(self, value: int) -> None:
        if value not in range(-55, 151, 1):
            raise ValueError("Temperature should be between -55C and 15C")
        self._temperature_critical = value * 128

    @property
    def hysteresis_temperature(self) -> float:
        """
        Hysteresis temperature limit value in Celsius for the
        :attr:`critical_temperature`, :attr:`high_temperature` and
        :attr:`low_temperature` limits
        """
        return self._temperature_hysteresis

    @hysteresis_temperature.setter
    def hysteresis_temperature(self, value: int) -> None:
        if value not in range(0, 16, 1):
            raise ValueError("Temperature should be between 0C and 15C")
        self._temperature_hysteresis = value
