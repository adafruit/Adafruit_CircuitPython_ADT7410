# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time

import adt7410
import board

i2c = board.I2C()
adt = adt7410.ADT7410(i2c)

adt.resolution_mode = adt7410.HIGH_RESOLUTION

while True:
    for resolution_mode in adt7410.resolution_mode_values:
        print("Current Resolution mode setting: ", adt.resolution_mode)
        for _ in range(10):
            temp = adt.temperature
            print(f"Temperature :{temp:.2f}C")
            time.sleep(0.5)
        adt.resolution_mode = resolution_mode
