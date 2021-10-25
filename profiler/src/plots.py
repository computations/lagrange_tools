import pandas
import seaborn
import matplotlib
import os


def make_region_taxa_plot(dataframe):
    return seaborn.FacetGrid(dataframe,
                             row="taxa",
                             col="regions",
                             height=7,
                             sharex=False,
                             margin_titles=True).map(
                                 seaborn.histplot,
                                 "time",
                                 kde=True,
                             )


def make_woker_threads_plot(dataframe):
    return seaborn.FacetGrid(dataframe,
                             row="workers",
                             col="tpw",
                             height=7,
                             sharex=True,
                             margin_titles=True).map(
                                 seaborn.histplot,
                                 "time",
                                 kde=True,
                             )


def make_threading_violinplot(dataframe):
    dataframe['threading_configuration'] =\
            dataframe['workers'].astype('str') + '/' +\
            dataframe['tpw'].astype('str')
    return seaborn.catplot(y='time',
                           x='threading_configuration',
                           col='regions',
                           row='taxa',
                           data=dataframe,
                           kind='violin',
                           sharey=False).set_axis_labels(
                               "Threading Configuration (Workers/TPW)", "Time")

def make_threading_boxplot(dataframe):
    dataframe['threading_configuration'] =\
            dataframe['workers'].astype('str') + '/' +\
            dataframe['tpw'].astype('str')
    return seaborn.catplot(y='time',
                           x='threading_configuration',
                           col='regions',
                           row='taxa',
                           data=dataframe,
                           kind='box',
                           sharey=False).set_axis_labels(
                               "Threading Configuration (Workers/TPW)", "Time")


def make_plots(dataframe, prefix):
    seaborn.set_style("whitegrid")
    plot = make_region_taxa_plot(dataframe)
    plot.savefig(os.path.join(prefix, 'regions_taxa_hist.png'))
    plot = make_woker_threads_plot(dataframe)
    plot.savefig(os.path.join(prefix, 'threading_hist.png'))
    plot = make_threading_boxplot(dataframe)
    plot.savefig(os.path.join(prefix, 'threading_box.png'))
    plot = make_threading_violinplot(dataframe)
    plot.savefig(os.path.join(prefix, 'threading_violin.png'))
