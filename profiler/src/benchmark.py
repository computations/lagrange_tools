#!/usr/bin/env python3
import dataset
import plots
import program
import experiment
import util
import itertools
import os
import sys
import csv
import rich
import rich.progress
import yaml
import subprocess
import flamegraph
import pandas
import seaborn
import matplotlib
import hashlib
import datetime


def make_datasets(taxa_count, length, ds_count):
    return [
        dataset.lagrange_dataset(prefix, taxa_count=taxa_count, length=length)
        for prefix in util.base58_generator(ds_count)
    ]


def compute_hash_with_path(path):
    with open(path, 'rb') as program_file:
        m = hashlib.sha256()
        m.update(program_file.read())
        return m.hexdigest()


def load_parameters(prefix):
    paramters_filename = os.path.join(prefix, 'parameters.yaml')
    with open(paramters_filename) as yamlfile:
        return yaml.safe_load(yamlfile.read())


def run(prefix, regions, taxa, iters, procs, program_path, profile,
        flamegraph_cmd):
    os.makedirs(prefix, exist_ok=True)

    exp_program = [
        program.lagrange(binary_path=os.path.abspath(program_path),
                         profile=profile)
    ]

    exp = []

    exp_name_format = "{taxa}taxa_{regions}regions"

    with rich.progress.Progress() as progress_bar:

        total_datasets = len(regions) * len(taxa)
        total_work = total_datasets * iters
        extra_work = 0
        if profile:
            extra_work += 1
        make_task = progress_bar.add_task("Making datasets...",
                                          total=total_datasets)

        with open(os.path.join(prefix, 'parameters.yaml'), 'w') as yamlfile:
            yamlfile.write(
                yaml.dump(
                    {
                        'prefix': prefix,
                        'regions': regions,
                        'taxa': taxa,
                        'iters': iters,
                        'procs': procs,
                        'program_path': program_path,
                        'program_sha256': compute_hash_with_path(program_path),
                        'profile': profile,
                    },
                    explicit_start=True,
                    explicit_end=True))

        with open(os.path.join(prefix, 'notes.md'), 'w') as notesfile:
            notesfile.write("- Started on: {}\n".format(
                datetime.datetime.now().isoformat()))

        for r, t in itertools.product(regions, taxa):
            exp_path = os.path.join(prefix,
                                    exp_name_format.format(regions=r, taxa=t))
            exp.append(
                experiment.experiment(exp_path, make_datasets(t, r, iters),
                                      exp_program))
            progress_bar.update(make_task, advance=1.0)

        overall_task = progress_bar.add_task("Running...",
                                             total=total_datasets + extra_work)

        for e in exp:
            e.run(procs)
            progress_bar.update(overall_task, advance=1.0)

        if not profile:
            results = []
            for e in exp:
                results.extend(e.collect_results())

            with open(os.path.join(prefix, 'results.csv'), 'w') as csv_file:
                writer = csv.DictWriter(csv_file,
                                        fieldnames=results[0].header())
                writer.writeheader()
                for result in results:
                    writer.writerow(result.write_row())

            dataframe = pandas.read_csv(os.path.join(prefix, 'results.csv'))
            plots.make_plots(dataframe, prefix)

        else:
            fg_work = len(exp) * len(exp[0].datasets)
            fg_task = progress_bar.add_task("Making Flamegraphs...",
                                            total=fg_work)

            for e in exp:
                for d in e.datasets:
                    flamegraph.build(d)
                    progress_bar.update(fg_task, advance=1.0)

            progress_bar.update(overall_task, advance=1.0)

        with open(os.path.join(prefix, 'notes.md'), 'a') as notesfile:
            notesfile.write("- Finshed on: {}\n".format(
                datetime.datetime.now().isoformat()))
