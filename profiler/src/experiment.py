#!/usr/bin/env python3

import util
import os
import dataset
import program
import multiprocessing
import multiprocessing.pool
import itertools
import rich.progress
from rich import print

# The plan is to have a root level class call experiment that handels the
# deployment and running of the process. There are a few questions:
#   - How to specify the datasets
#   - How to collect results
#   - How to summarize results
# For now, I think I will leave the last 2 points to be implemented later, and
# instead implement the first point. I have two ideas on how to specify the
# datasets:
#   - Pass the experiment class a dataset generator
#   - Pass the experiment class a list of already made datasets
# The problem with the first one is that it can be difficult to co-ordinate the
# generator with the number of experiments that are going to be made. So
# instead, I think that I am going to just pass a list of datasets. This pushes
# a lot of the complexity to the dataset class, which is fine. and is where I
# will write most of the file operations.


class experiment:

    def __init__(self, root_path, datasets, programs):
        self._root_path = root_path
        self._datasets = datasets
        self._programs = programs
        for ds in self._datasets:
            ds.add_prefix_dir(self._root_path)

    @property
    def path(self):
        return os.path.abspath(self._root_path)

    @property
    def datasets(self):
        return self._datasets

    @staticmethod
    def _internal_run(ds, prog, redo_enabled=False):
        ds.write()
        ret = prog.run(ds)
        if not ret and redo_enabled:
            print("[red]Redoing this run")
            ds.remove()
            ds._generate()
            experiment._internal_run(ds, prog, redo_enabled)

    def run(self, procs=None, progress_bar=None, redo_enabled=False):
        jobs = [(ds, prog) for ds in self._datasets for prog in self._programs]
        if procs is None:
            procs = 1
        if procs == 1:
            cur_task = progress_bar.add_task("Current Experiment",
                                             total=len(jobs))
            for ds, prog in jobs:
                progress_bar.update(cur_task, advance=1.0)
                self._internal_run(ds, prog, redo_enabled)
            progress_bar.update(cur_task, visible=False)
        else:
            with multiprocessing.pool.Pool(procs) as pool:
                pool.starmap(experiment._internal_run, jobs)

    def collect_results(self):
        return [
            prog.get_result(ds) for prog in self._programs
            for ds in self._datasets
        ]
