#!/usr/bin/env python3
import os
import tarfile
import argparse
import pathlib
import util
import lagrange
import directory
import rich
import rich.console
import rich.progress
import yaml
import enum
import shutil
import numpy
import scipy.stats
from sklearn.linear_model import LinearRegression
from timeit import default_timer as timer
from matplotlib import pyplot


def run(prefix, archive, program, prefix_specified, copy_threshold,
        distance_threshold):
    start = timer()
    failed_runs = []
    error_runs = []
    lagrange_runner = lagrange.lagrange(program)

    console = rich.console.Console()
    linreg_xs = []
    linreg_ys = []

    with rich.progress.Progress() as progress:
        jobs = directory.extractTarFileAndMakeDirectories(
            archive, prefix, progress)

        work_task = progress.add_task("[red]Running...", total=len(jobs))
        for expected, experiment in jobs:
            try:
                experiment.runExperiment(lagrange_runner)
            except directory.ExperimentFilesMissing:
                error_runs.append(experiment)
            progress.update(work_task, advance=1.0)

        check_task = progress.add_task("[red]Checking...", total=len(jobs))

        for expected, experiment in jobs:
            if experiment.failed():
                continue
            parameter_diff = expected.parameterVectorDifference(experiment)
            dist = expected.metricCompare(experiment)
            linreg_xs.append(parameter_diff)
            linreg_ys.append(dist)
            if dist > distance_threshold:
                failed_runs.append(
                    directory.ExperimentWithDistance(experiment, dist))
            progress.update(check_task, advance=1.0)

    if len(linreg_xs) > 0:
        linreg_result = LinearRegression().fit(linreg_xs, linreg_ys)
        linreg_rsquared = linreg_result.score(linreg_xs, linreg_ys)
        console.print("Parameter error regression coefficient: {}".format(
            linreg_rsquared))

    with open(os.path.join(prefix, "failed_paths.yaml"), "w") as outfile:
        yaml.add_representer(directory.ExpectedTrialDirectory,
                             directory.DirectoryRepresenter)
        yaml.add_representer(directory.ExperimentTrialDirectory,
                             directory.DirectoryRepresenter)
        yaml.add_representer(directory.ExperimentWithDistance,
                             directory.ExperimentWithDistanceRepresenter)
        outfile.write(
            yaml.dump({
                "failed-runs": failed_runs,
                "error-runs": error_runs
            }))

    if len(failed_runs) != 0 or len(error_runs) != 0:
        if len(failed_runs) != 0:
            console.print(
                "Tests that completed, but gave a wrong result (top 10):",
                sorted(failed_runs, key=lambda a: a._dist)[-10:])
            console.print(
                "Total of {} ({}%) jobs resulted in errors over tolerance".
                format(len(failed_runs),
                       len(failed_runs) / len(jobs) * 100))
        if len(error_runs) != 0:
            console.print("Tests that failed to complete:",
                          sorted(error_runs, key=lambda d: d._path))
            console.print("Total of {} ({}%) jobs failed to run".format(
                len(error_runs),
                len(error_runs) / len(jobs) * 100))
        if not prefix_specified and (
            (len(failed_runs) > copy_threshold and not linreg_rsquared > 0.95)
                or len(error_runs) != 0):
            basename = os.path.split(prefix)[1]
            new_prefix = os.path.abspath(os.path.join(os.getcwd(), basename))
            console.print(
                "Copying the failed directories to {}".format(new_prefix))
            shutil.copytree(prefix, new_prefix)

    else:
        console.print("[bold green]All Clear!")
    end = timer()
    console.print("Testing took {:.3f} seconds".format(end - start))
