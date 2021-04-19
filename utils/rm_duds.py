#!/usr/bin/env python3

import os
import shutil

for d in os.listdir():
    if os.path.isfile(d):
        continue
    time_hist = os.path.join(d, "time_hist.png")
    if not os.path.exists(time_hist):
        shutil.rmtree(d)

