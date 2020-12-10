#!/usr/bin/env python3

import argparse
import lagrange_log
import graph

parser = argparse.ArgumentParser()

parser.add_argument("jsons", type=str, nargs="+")

args = parser.parse_args()

with open(args.jsons[0]) as infile:
    json1 = lagrange_log.jsonlog(infile)

with open(args.jsons[1]) as infile:
    json2 = lagrange_log.jsonlog(infile)

for d1, d2 in lagrange_log.DistributionVectorGenerator(json1, json2, 5):
    d = d1-d2
    p = graph.problem(d)
    print(p.normalized_dist())
