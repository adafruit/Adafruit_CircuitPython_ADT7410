Introduction
============

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-adt7410/badge/?version=latest
    :target: https://circuitpython.readthedocs.io/projects/adt7410/en/latest/
    :alt: Documentation Status

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://adafru.it/discord
    :alt: Discord

.. image:: https://github.com/adafruit/Adafruit_CircuitPython_ADT7410/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_ADT7410/actions/
    :alt: Build Status

CircuitPython driver for reading temperature from the Analog Devices ADT7410 precision temperature sensor

Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* `Bus Device <https://github.com/adafruit/Adafruit_CircuitPython_BusDevice>`_
* `Register <https://github.com/adafruit/Adafruit_CircuitPython_Register>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://github.com/adafruit/Adafruit_CircuitPython_Bundle>`_.

Installing from PyPI
--------------------

On supported GNU/Linux systems like the Raspberry Pi, you can install the driver locally `from
PyPI <https://pypi.org/project/adafruit-circuitpython-adt7410/>`_. To install for current user:

.. code-block:: shell

    pip3 install adafruit-circuitpython-adt7410

To install system-wide (this may be required in some cases):

.. code-block:: shell

    sudo pip3 install adafruit-circuitpython-adt7410

To install in a virtual environment in your current project:

.. code-block:: shell

    mkdir project-name && cd project-name
    python3 -m venv .env
    source .env/bin/activate
    pip3 install adafruit-circuitpython-adt7410

Usage Example
=============

.. code-block:: python

	import time
	import board
	import busio
	import adafruit_adt7410

	i2c_bus = busio.I2C(board.SCL, board.SDA)
	adt = adafruit_adt7410.ADT7410(i2c_bus, address=0x48)
	adt.high_resolution = True

	while True:
		print(adt.temperature)
		time.sleep(0.5)


Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_ADT7410/blob/master/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Documentation
=============

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.
