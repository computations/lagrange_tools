import json
import numpy
import os
import shutil
import enum
import graph

NODE_RESULTS_KEY = 'node-results'
ATTRIBUTES_KEY = 'attributes'
PARAMS_KEY = 'params'


class LagrangeLogFileType(enum.Enum):
    BGKey = 0
    BGStates = 1
    ResultsJSON = 2
    ConsoleLog = 3

    Config = 4
    Phylip = 5
    Newick = 6

    Misc = 100
    Unknown = 101


class LagrangeLog:
    def __init__(self, elog, bglog, jlog=None):
        self._execution_log = ExecutionLog(elog)
        self._bgstates_log = BGStatesLog(bglog)
        if not jlog is None:
            self._json_log = JSONLog(jlog)

    def __eq__(self, other):
        return self._bgstates_log == other._bgstates_log

    def wassersteinMetric(self, other):
        return self._json_log.normalizedWasserSteinMetric(other._json_log)

    def paramsVector(self):
        return self._json_log.params_vector()


class LogFile:
    def __init__(self, logfile):
        self._file_path = os.path.abspath(logfile)
        self._file_contents = self._read_file()

    def _read_file(self):
        with open(self._file_path) as infile:
            return infile.read()

    def __eq__(self, other):
        return self._file_contents == other._file_contents


class BGStatesLog(LogFile):
    pass


class BGStatesKeyLog(LogFile):
    pass


class ExecutionLog(LogFile):
    def __eq__(self, other):
        raise NotImplementedError()


class JSONLog(LogFile):
    def __init__(self, logfile):
        super(JSONLog, self).__init__(logfile)
        self._log = json.loads(self._file_contents)
        self._setup()

    def _setup_index_map(self):
        self._indexes = []
        for obj in self._log[NODE_RESULTS_KEY]:
            self._indexes.append(obj['number'])

        self._indexes = sorted(self._indexes)

        self._index_json_map = {}
        for obj in self._log[NODE_RESULTS_KEY]:
            self._index_json_map[obj['number']] = obj

    def _setup_read_attributes(self):
        self._regions = self._log[ATTRIBUTES_KEY]['regions']
        self._taxa = self._log[ATTRIBUTES_KEY]['taxa']
        self._dispersion_rate = self._log[PARAMS_KEY]['dispersion']
        self._extinction_rate = self._log[PARAMS_KEY]['extinction']

    def _setup(self):
        self._setup_index_map()
        self._setup_read_attributes()

    def distribution_vector(self, index, regions):
        obj = self._index_json_map[index]
        dist_vec = numpy.zeros(2**regions)
        for s in obj['states']:
            dist_vec[s['distribution']] = s['ratio']

        return dist_vec

    def params_vector(self):
        return numpy.array([self._dispersion_rate, self._extinction_rate])

    def __and__(self, other):
        return sorted(set(self._indexes) & set(other._indexes))

    def __eq__(self, other):
        raise NotImplementedError()

    def wassersteinMetric(self, other):
        if self._regions != other._regions:
            raise RuntimeError(
                "The two lagrange runs should have the same" +
                "number of regions to compare compute the wasserstein" +
                "metric")
        total_dist = 0.0
        for d1, d2 in DistributionVectorGenerator(self, other, self._regions):
            p = graph.problem(d1 - d2)
            total_dist += p.normalized_dist()
        return total_dist

    def normalizedWasserSteinMetric(self, other):
        return self.wassersteinMetric(other) / (self._taxa - 1)


def DistributionVectorGenerator(json1, json2, regions):
    inds = json1 & json2
    for i in inds:
        d1 = json1.distribution_vector(i, regions)
        d2 = json2.distribution_vector(i, regions)
        yield (d1, d2)
