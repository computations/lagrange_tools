#!/usr/bin/env python3

import subprocess
import util
import filecmp


class lagrange:
    def __init__(self, lagrange_path):
        self._lagrange_path = lagrange_path

    def run(self, path, config_file):
        with util.directory_guard(path):
            with open('lagrange.log', 'w') as logfile:
                subprocess.run([self._lagrange_path, config_file],
                               stdout=logfile,
                               stderr=logfile)
