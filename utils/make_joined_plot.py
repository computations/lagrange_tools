#!/usr/bin/env python3

import pandas
import seaborn
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--baseline', type=str, required=True)
parser.add_argument('--ng', type=str, required=True)
parser.add_argument('--palette', type=str, default='deep')
parser.add_argument('--output', type=str, default='deep')

args = parser.parse_args()

baseline_df = pandas.read_csv(args.baseline)
ng_df = pandas.read_csv(args.ng)

ng_df['program'] = 'lagrange-ng'

aug_baseline_df = baseline_df.copy()

for w in ng_df['workers'].unique():
    if w == 1:
        continue
    df = baseline_df.copy()
    df['workers'] = w
    aug_baseline_df = aug_baseline_df.append(df)

all_df = aug_baseline_df.append(ng_df)

plot = seaborn.catplot(y='time',
                       x='taxa',
                       col='regions',
                       row='workers',
                       data=all_df,
                       kind='violin',
                       hue='program',
                       split=True,
                       sharey=False,
                       margin_titles=True,
                       inner='quartiles',
                       palette=seaborn.color_palette(args.palette))

plot.set_axis_labels("Taxa", "Time (s)")
plot.set_titles(col_template="{col_name} Regions",
                row_template="{row_name} Workers")

plot.tight_layout()

plot.savefig(args.output)
