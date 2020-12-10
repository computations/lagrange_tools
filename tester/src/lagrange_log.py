import json
import numpy


class jsonlog:
    def __init__(self, logfile):
        self._log = json.load(logfile)
        self._setup()

    def _setup_index_map(self):
        self._indexes = []
        for obj in self._log:
            self._indexes.append(obj['number'])

        self._indexes = sorted(self._indexes)

        self._index_json_map = {}
        for obj in self._log:
            self._index_json_map[obj['number']] = obj

    def _setup(self):
        self._setup_index_map()

    def distribution_vector(self, index, regions):
        obj = self._index_json_map[index]
        dist_vec = numpy.zeros(2**regions)
        for s in obj['states']:
            dist_vec[s['distribution']] = s['ratio']

        return dist_vec

    def __and__(self, other):
        return sorted(set(self._indexes) & set(other._indexes))


def DistributionVectorGenerator(json1, json2, regions):
    inds = json1 & json2
    for i in inds:
        d1 = json1.distribution_vector(i, regions)
        d2 = json2.distribution_vector(i, regions)
        yield (d1, d2)
