#!/usr/bin/env python3

import pandas
import argparse
import os
import itertools
import rich

parser = argparse.ArgumentParser()
parser.add_argument("--directory")
args = parser.parse_args()

results_csv_filename = os.path.join(os.path.abspath(args.directory),
                                    "results.csv")

dfs = pandas.read_csv(results_csv_filename)
region_keys = dfs['regions'].unique()
taxa_keys = dfs['taxa'].unique()

for region, taxa in itertools.product(region_keys, taxa_keys):
    time_series = dfs.loc[(dfs['regions'] == region)
                          & (dfs['taxa'] == taxa)]['time']
    rich.print("Regions: {}, Taxa: {}: Mean: {}, Median: {}".format(
        region, taxa, time_series.mean(), time_series.median()))
