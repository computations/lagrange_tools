#!/usr/bin/env python3

import argparse
import tester
import tempfile
import os

SOURCE_DIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
DEFAULT_PROGRAM = os.path.abspath(os.path.join(SOURCE_DIR,
    "../../../bin/lagrange"))
DEFAULT_ARCHIVE = os.path.abspath(os.path.join(SOURCE_DIR,
    "../archives/regression_tests_short_created_2020-06-05.tar.gz"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--prefix', type=str)
    parser.add_argument('--archive', type=str, default=DEFAULT_ARCHIVE)
    parser.add_argument('--program', type=str, default=DEFAULT_PROGRAM)
    parser.add_argument('--fail-threshold', type=int, default=10)
    parser.add_argument('--distance-threshold', type=float, default=1e-4)
    args = parser.parse_args()

    prefix_specified = True
    if args.prefix is None:
        prefix_specified = False
        tempdir = tempfile.TemporaryDirectory()
        print("Using the tempdir:", tempdir.name)
        args.prefix = tempdir.name

    args.program = os.path.abspath(args.program)
    tester.run(args.prefix, args.archive, args.program, prefix_specified,
            args.fail_threshold, args.distance_threshold)
