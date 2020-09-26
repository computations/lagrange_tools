import pandas
import seaborn
import matplotlib
import os


def make_plots(dataframe, prefix):
    seaborn.set_style("whitegrid")
    plot = seaborn.FacetGrid(dataframe,
                             row="taxa",
                             col="regions",
                             height=7,
                             sharex=False,
                             margin_titles=True).map(
                                 seaborn.histplot,
                                 "time",
                                 kde=True,
                             )
    plot.savefig(os.path.join(prefix, 'time_hist.png'))
