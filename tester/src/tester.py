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
from timeit import default_timer as timer


def run(prefix, archive, program, prefix_specified, copy_threshold,
        distance_threshold):
    start = timer()
    failed_runs = []
    error_runs = []
    lagrange_runner = lagrange.lagrange(program)

    console = rich.console.Console()
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
            dist = expected.metricCompare(experiment)
            if dist > distance_threshold:
                failed_runs.append(
                    directory.ExperimentWithDistance(experiment, dist))
            progress.update(check_task, advance=1.0)

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
            console.print("Tests that completed, but gave a wrong result:",
                          sorted(failed_runs, key=lambda a: a._dist))
            console.print("Total of {} paths failed".format(len(failed_runs)))
        if len(error_runs) != 0:
            console.print("Tests that failed to complete:",
                          sorted(error_runs, key=lambda d: d._path))
            console.print("Total of {} paths failed to run".format(
                len(error_runs)))
        if not prefix_specified and (len(failed_runs) > copy_threshold
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


"""
def run(prefix, archive, program, prefix_specified, fail_threshold):
    runner = lagrange.lagrange(program)

    console = rich.console.Console()
    with rich.progress.Progress() as progress:
        tar = tarfile.open(archive)

        member_count = len(tar.getmembers())
        extract_task = progress.add_task("[red]Extracting...",
                                         total=member_count)

        for member in tar.getmembers():
            member_ft = file_type(member.name)
            if member_ft == 'newick' or member_ft == 'phylip' or member_ft ==\
                'config':
                extract_with_path(tar, member, prefix)
            if member_ft == 'log' or member_ft == 'bgkey' or member_ft ==\
                'bgstates':
                extract_with_set_name(tar, member, 'expected', prefix)
            progress.update(extract_task, advance=1.0)

        with util.directory_guard(prefix):
            work_paths = []
            #work_task = progress.add_task("[blue]Building tests...")
            for root, dirs, files in os.walk('.'):
                config_file = find_config_file(files)
                if not config_file is None:
                    work_paths.append((root, config_file))
                #progress.update(work_task)

            test_task = progress.add_task("[green]Testing...",
                                          total=len(work_paths))

            for path, config_file in work_paths:
                runner.run(path, config_file)
                progress.update(test_task, advance=1.0)
                result = compare_results_expected(path)
                if result == experiment_result_t.results_differ:
                    failed_paths.append(path)
                elif result == experiment_result_t.run_failed:
                    failed_runs.append(path)

    with open(os.path.join(prefix, "failed_paths.yaml"), "w") as outfile:
        outfile.write(yaml.dump(failed_paths))
    if len(failed_paths) != 0 or len(failed_runs) != 0:
        if len(failed_paths) != 0:
            console.print("Tests that completed, but gave a wrong result:",
                          sorted(failed_paths))
            console.print("Total of {} paths failed".format(len(failed_paths)))
        if len(failed_runs) != 0:
            console.print("Tests that failed to complete:",
                          sorted(failed_runs))
            console.print("Total of {} paths failed to run".format(
                len(failed_runs)))
        if not prefix_specified and (len(failed_paths) > fail_threshold
                                     or len(failed_runs) != 0):
            basename = os.path.split(prefix)[1]
            new_prefix = os.path.abspath(os.path.join(os.getcwd(), basename))
            console.print(
                "Copying the failed directories to {}".format(new_prefix))
            shutil.copytree(prefix, new_prefix)

    else:
        console.print("[bold green]All Clear!")
    end = timer()
    console.print("Testing took {:.3f} seconds".format(end - start))
"""
