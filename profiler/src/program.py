#!/usr/bin/env python3

import subprocess
import os
import util
import result
import datetime


class program:

    def __init__(self, **kwargs):
        self._binary_path = kwargs['binary_path']
        self._profile = kwargs['profile']

    def run(self, *args, **kwargs):
        raise NotImplementedError("Run is not implemented in the base class")

    @property
    def binary(self):
        return os.path.abspath(self._binary_path)

    @property
    def profile_cmd(self):
        if self._profile is True:
            return "perf record -g".split()
        return []

    @staticmethod
    def _donefile(path):
        return os.path.join(path, ".done")

    def set_done(self, path):
        with open(program._donefile(path), 'w') as donefile:
            donefile.write(str(datetime.datetime.now()))
            donefile.write("\n")

    def check_done(self, path):
        if not os.path.exists(program._donefile(path)):
            return False
        if not os.path.exists(os.path.join(path, 'lagrange.log')):
            return False
        with open(os.path.join(path, 'lagrange.log')) as logfile:
            for line in logfile:
                if 'runtime_error' in line:
                    print("found bad logfile for path", path)
                    return False
        return True


class lagrange(program):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, dataset):
        if self.check_done(dataset.path):
            return None
        with util.directory_guard(dataset.path):
            with open('lagrange.log', 'w') as logfile:
                cmd = []
                cmd.extend(self.profile_cmd)
                cmd.extend([self.binary, dataset.lagrange_config_path])
                ret = subprocess.run(cmd, stdout=logfile, stderr=logfile)
                #self.set_done(dataset.path)
                self.set_done('')
                return ret.returncode == 0

    def get_result(self, dataset):
        return lagrange_result(dataset)


class lagrange_result(result.result):
    _logfile_filename = "lagrange.log"
    _program = "lagrange"

    def __init__(self, dataset, **kwargs):
        super().__init__(**kwargs)
        self._dataset = dataset
        with open(self.logfile_path) as logfile:
            time_line = list(logfile)[-1]

        try:
            self._time = lagrange_result._parse_timeline(time_line)
        except:
            raise RuntimeError("Could not parse the time line for file: " +
                               self.logfile_path)

    @property
    def logfile_path(self):
        return os.path.join(self._dataset.path, self._logfile_filename)

    @staticmethod
    def _parse_timeline(line):
        line = line.strip()
        if "Analysis took: " not in line:
            print(line)
            raise RuntimeError("The time line of the log file was malformed")
        prefix_length = len("Analysis took: ")
        return float(line[prefix_length:-1])

    def write_row(self):
        return {
            'program': self.program,
            'taxa': self._dataset.taxa_count,
            'regions': self._dataset.region_count,
            'workers': self._dataset.workers,
            'tpw': self._dataset.threads_per_worker,
            'time': self._time
        }

    def header(self):
        return [
            'program', 'taxa', 'regions', 'workers', 'tpw', 'approximate',
            'time'
        ]
