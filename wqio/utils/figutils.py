import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec
import scipy.stats as stats

from . import misc


def _check_ax(ax):
    if ax is None:
        fig, ax = plt.subplots()
    elif isinstance(ax, plt.Axes):
        fig = ax.figure
    else:
        msg = "`ax` must be a matplotlib Axes instance or None"
        raise ValueError(msg)

    return fig, ax


def rotateTickLabels(ax, rotation, which, rotation_mode='anchor', ha='right'):
    axes = []
    if which in ['x', 'both']:
        axes.append(ax.xaxis)

    elif which in ['y', 'both']:
        axes.append(ax.yaxis)

    for axis in axes:
        for t in axis.get_ticklabels():
            t.set_horizontalalignment(ha)
            t.set_rotation(rotation)
            t.set_rotation_mode(rotation_mode)


def setProbLimits(ax, N, which):
    minval = 10 ** (-1 *np.ceil(np.log10(N) - 2))
    if which in ['x', 'both']:
        ax.set_xlim(left=minval, right=100-minval)
    elif which in ['y', 'both']:
        ax.set_ylim(bottom=minval, top=100-minval)


def gridlines(axes, xlabel=None, ylabel=None, xscale=None, yscale=None,
              xminor=True, yminor=True):
    '''
    Deal with normal gridlines and other formats on an axes

    Input:
        axes (matplotlib axes object) : the axes to format
        xlabel (string) : the label of the x-axis
        ylabel (string) : the label of the y-axis
        xscale (string, default 'log') : scale of the x-axis (linear or log)
        yscale (string, default 'log') : scale of the y-axis (linear or log)
        xminor (bool, default True) : toggles inclusion of the x minor grid
        yminor (bool, default True) : toggles inclusion of the y minor grid

    Writes:
        None

    Returns:
        None
    '''
    # set the scales
    if xscale is not None:
        axes.set_xscale(xscale)
        if xscale == 'log':
            axes.xaxis.set_major_formatter(mticker.FuncFormatter(logLabelFormatter))

    if yscale is not None:
        axes.set_yscale(yscale)
        if yscale == 'log':
            axes.yaxis.set_major_formatter(mticker.FuncFormatter(logLabelFormatter))

    # set the labels
    if xlabel is not None:
        axes.set_xlabel(xlabel)

    if ylabel is not None:
        axes.set_ylabel(ylabel)

    # major grids
    axes.yaxis.grid(True, which='major', ls='-', alpha=0.35)
    axes.xaxis.grid(True, which='major', ls='-', alpha=0.35)

    # minor grids
    if xminor:
        axes.xaxis.grid(True, which='minor', ls='-', alpha=0.17)

    if yminor:
        axes.yaxis.grid(True, which='minor', ls='-', alpha=0.17)


def boxplot(axes, data, position, median=None, CIs=None,
            mean=None, meanmarker='o', meancolor='b'):
    '''
    Adds a boxplot to an axes from the ROS'd data in a
        `bmp.dataAccess.Location` object

    Input:
        axes (matplotlib axes object) : the axes to format
        rosdata (utils.ros object) : dataset to plot
        position (int) : position along the x-axis where the boxplot should go

    Writes:
        None

    Returns:
        bp (dictionary of matplotlib artists) : graphical elements of the
            boxplot
    '''

    if median is not None and np.isscalar(median):
        median = [median]

    if CIs is not None:
        if not isinstance(CIs, np.ndarray):
            CIs = np.array(CIs)

        if len(CIs.shape) == 1:
            CIs = CIs.reshape(1,2)

        CIs = CIs.tolist()

    # plot the data
    bp = axes.boxplot(data, notch=1, positions=[position],
                      widths=0.6, usermedians=median, conf_intervals=CIs)

    # plot the mean value as a big marker
    if mean is not None:
        # (geomean for bacteria data)
        axes.plot(position, mean, marker=meanmarker, markersize=4,
                  markerfacecolor=meancolor, markeredgecolor='k')

    return bp


def formatBoxplot(bp, color='b', marker='o', markersize=4, linestyle='-',
                  showcaps=False, patch_artist=False):
    '''
    Easily format a boxplots for stylistic consistency

    Input:
        bp (dictionary of matplotlib artists) : graphical elements of the
            boxplot
        color (string) : any valid matplotlib color string
            for the median lines and outlier markers
        marker (string) : any valid matplotlib marker string
            for the outliers
        markersize (int) : size in points of the outlier marker
        linestyle (string) : any valid matplotlib linestyle string
            for the medians
        patch_artist : optional bool (default = False)
            Toggles the use of patch artist instead of a line artists
            for the boxes.

    Writes:
        None

    Returns:
        None
    '''
    if patch_artist:
        # format the box itself
        for box in bp['boxes']:
            plt.setp(box, edgecolor='k', facecolor=color, linewidth=0.75, zorder=4, alpha=0.5)

        # format the medians
        for med in bp['medians']:
            plt.setp(med, linewidth=1.00, color='k', linestyle=linestyle, zorder=5)

    else:
        # format the box itself
        for box in bp['boxes']:
            plt.setp(box, color='k', linewidth=0.75, zorder=4)

        # format the medians
        for med in bp['medians']:
            plt.setp(med, linewidth=1.00, color=color, linestyle=linestyle, zorder=3)

    # format the whiskers
    for whi in bp['whiskers']:
        plt.setp(whi, linestyle='-', color='k', linewidth=0.75, zorder=4)

    # format the caps on top of the whiskers
    for cap in bp['caps']:
        plt.setp(cap, color='k', linewidth=0.75, zorder=4, alpha=int(showcaps))

    # format the outliers
    for fli in bp['fliers']:
        plt.setp(fli, marker=marker, markersize=markersize, zorder=4,
                 markerfacecolor='none', markeredgecolor=color, alpha=1)


def probplot(data, ax=None, axtype='prob', color='b', marker='o',
             linestyle='none', xlabel=None, ylabel=None, yscale='log',
             **plotkwds):
    '''Probability, percentile, and quantile plots.

    Parameters
    ----------
    data : sequence or array-like
        1-dimensional data to be plotted
    ax : optional matplotlib axes object or None (default).
        The Axes on which to plot. If None is provided, one will be
        created.
    axtype : string (default = 'pp')
        Type of plot to be created. Options are:
            - 'prob': probabilty plot
            - 'pp': percentile plot
            - 'qq': quantile plot
    color : color string or three tuple (default = 'b')
        Just needs to be any valid matplotlib color representation.
    marker : string (default = 'o')
        String representing a matplotlib marker style.
    linestyle : string (default = 'none')
        String representing a matplotlib line style. No line is shown by
        default.
    [x|y]label : string or None (default)
        Axis label for the plot.
    yscale : string (default = 'log')
        Scale for the y-axis. Use 'log' for logarithmic (default) or
        'linear'.
    **plotkwds : optional arguments passed directly to plt.plot(...)

    Returns
    -------
    fig : matplotlib.Figure instance

    '''

    fig, ax = _check_ax(ax)
    if axtype not in ['pp', 'qq', 'prob']:
        raise ValueError("invalid axtype: {}".format(axtype))

    qntls, ranked = stats.probplot(data, fit=False)
    if axtype == 'qq':
        xdata = qntls
    else:
        xdata = stats.norm.cdf(qntls) * 100

    markerfacecolor = plotkwds.pop('markerfacecolor', 'none')
    markersize = plotkwds.pop('markersize', 4)

    # plot the final ROS data versus the Z-scores
    ax.plot(xdata, ranked, linestyle=linestyle, marker=marker,
            markeredgecolor=color, markerfacecolor=markerfacecolor,
            markersize=markersize, **plotkwds)

    ax.set_yscale(yscale)
    if axtype == 'prob':
        ax.set_xscale('prob')
        #left, right = ax.get_xlim()
        #ax.set_xlim(left=left*0.96, right=right*1.04)

    if xlabel is not None:
        ax.set_xlabel(xlabel)

    if ylabel is not None:
        ax.set_ylabel(ylabel)

    return fig


def logLabelFormatter(tick, pos=None):
    '''
    Y-tick label formatter to deal with scientific notation
    the way I like
    '''
    if 10**3 >= tick > 1:
        tick = int(tick)
    elif tick > 10**3 or tick < 10**-3:
        tick = r'$1 \times 10 ^ {%d}$' % int(np.log10(tick))

    return tick


def alt_logLabelFormatter(tick, pos=None):
    '''
    X-tick label formatter to deal with scientific notation
    the way I like
    '''
    if 10**3 >= tick > 1:
        tick = int(tick)
    elif tick > 10**3 or tick < 10**-3:
        tick = r'$10 ^ {%d}$' % int(np.log10(tick))

    return tick


def scatterHistogram(X, Y, xlabel=None, ylabel=None, figname=None, axes=None,
                     symbolkwds=None, barkwds=None, xlim=None, ylim=None,
                     color='CornflowerBlue'):
    '''
    Makes a figure with a scatter plot of two variables and a histogram for each
    variable.

    Input:
        X : array-like
            Data to be plotted along the x-axis

        Y : array-like
            Data to be plotted along the y-axis

        xlabel : optional string (default=None)
            Optional label for the x-axis of the scatter plot. Note that the
            default value means that x-axis of histogram will not be labeled.

        ylabel : optional string (default=None)
            Optional label for the y-axis of the scatter plot. Note that the
            default value means that y-axis of histogram will not be labeled.

        figname : optional string (default=None)
            Filename to which the figure will be saved (if provided).

        axes : optional iterable of matplotlib `Axes` objects (default=None)
            If provided, this must be a list of matplotlib axes in the
            following order:
                1) top axes for the x-data histogram
                2) main axes for the scatter plot
                3) right axes for the y-data histogram.
            Otherwise, axes will be create during this routine.

        symbolkwds : optional dictionary (default={})
            Kwargs to be passed on to the `axes.plot` command for the scatter
            plot. If not specified, `linestyle` will be set to "none" (the
            string, not the `None` object)

        barkwds : optional dictionary (default={})
            Kwargs to be passed on to the `axes.bar` command for the histogram plot.

    Returns:
        fig : matplotlib Figure instance.

    '''

    scatter_symbol = {
        'marker': 'o',
        'markeredgecolor': 'white',
        'markerfacecolor': color,
        'markersize': 4,
        'linestyle': 'none',
        'alpha': 0.75
    }

    bar_symbol = {
        'facecolor': color,
        'edgecolor': 'white',
        'alpha': 0.75
    }

    if axes is None:
        # set up the figure
        fig = plt.figure(figsize=(6, 6))
        fig_gs = gridspec.GridSpec(2, 2, height_ratios=[4, 10],
                                   width_ratios=[10, 4])

        # create histogram axes for x-data (upper left)
        hist_x = fig.add_subplot(fig_gs[0, 0])

        # create the main scatter plot axes (lower left)
        mainax = fig.add_subplot(fig_gs[1, 0])

        # histogram axes for y-data (lower right)
        hist_y = fig.add_subplot(fig_gs[1, 1])

    else:
        if len(axes) != 3:
            raise ValueError("`axes` must be an iterable with N = 3")

        for n, ax in enumerate(axes):
            if not isinstance(ax, plt.Axes):
                msg = "element at index {0} is not an `Axes` object".format(n)
                raise ValueError(msg)

        hist_x, mainax, hist_y = axes
        fig = hist_x.get_figure()

    # force count axes to format as ints
    hist_y.xaxis.set_major_locator(mticker.MaxNLocator(4, integer=True))
    hist_y.xaxis.set_major_formatter(mticker.FormatStrFormatter('%d'))

    hist_x.yaxis.set_major_locator(mticker.MaxNLocator(4, integer=True))
    hist_x.yaxis.set_major_formatter(mticker.FormatStrFormatter('%d'))

    # be sure that the scatter plots dots, not lines
    if symbolkwds is not None:
        scatter_symbol.update(symbolkwds)

    if barkwds is not None:
        bar_symbol.update(barkwds)

    # plot stuff on main axis
    mainax.plot(X, Y, **scatter_symbol)
    if xlim is not None:
        mainax.set_xlim(**xlim)
    if ylim is not None:
        mainax.set_ylim(**ylim)

    # format stuff
    mainax.xaxis.tick_bottom()
    mainax.yaxis.tick_left()

    if xlabel is not None:
        mainax.set_xlabel(xlabel)

    if ylabel is not None:
        mainax.set_ylabel(ylabel)

    # make the x-data bar plot
    hist_x.hist(X, orientation='vertical', align='mid', **bar_symbol)

    # format x-histogram
    hist_x.set_xticklabels([])
    hist_x.tick_params(axis='x', length=0)
    hist_x.xaxis.tick_bottom()
    hist_x.yaxis.tick_left()
    hist_x.set_xticks(mainax.get_xticks())
    hist_x.set_xlim(mainax.get_xlim())
    if ylabel is not None:
        hist_x.set_ylabel('Count')

    # make the y-data bar plot
    hist_y.hist(Y, orientation='horizontal', align='mid', **bar_symbol)

    # format the y-data histogram
    hist_y.set_yticklabels([])
    hist_y.tick_params(axis='y', length=0)
    hist_y.yaxis.tick_left()
    hist_y.xaxis.tick_bottom()
    hist_y.set_yticks(mainax.get_xticks())
    hist_y.set_ylim(mainax.get_xlim())
    if xlabel is not None:
        hist_y.set_xlabel('Count')

    # tighten things up
    fig.subplots_adjust(wspace=0.08, hspace=0.08, left=0.15,
                        right=0.98, bottom=0.08, top=0.98)

    # save if necessary
    if figname is not None:
        fig.savefig(figname, dpi=300, bbox_inches='tight')

    return fig


def shiftedColorMap(cmap, start=0, midpoint=0.5, stop=1.0, name='shiftedcmap'):
    '''
    Function to offset the "center" of a colormap. Useful for
    data with a negative min and positive max and you want the
    middle of the colormap's dynamic range to be at zero

    Input
    -----
      cmap : The matplotlib colormap to be altered
      start : Offset from lowest point in the colormap's range.
          Defaults to 0.0 (no lower ofset). Should be between
          0.0 and `midpoint`.
      midpoint : The new center of the colormap. Defaults to
          0.5 (no shift). Should be between `start` and `stop`.
          In general, this should be  1 - vmax/(vmax + abs(vmin))
          For example if your data range from -15.0 to +5.0 and
          you want the center of the colormap at 0.0, `midpoint`
          should be set to  1 - 5/(5 + 15)) or 0.75
      stop : Offset from highets point in the colormap's range.
          Defaults to 1.0 (no upper ofset). Should be between
          `midpoint` and 1.0.
    '''
    if midpoint <= start or midpoint >= stop:
        raise ValueError("`midpoint` must be between `start` and `stop`")

    if start < 0 or start >= midpoint:
        raise ValueError("`start` must be between 0.0 and `midpoint`")

    if stop <= midpoint or stop > 1:
        raise ValueError("`stop` must be between `midpoint` and 1.0")

    cdict = {
        'red': [],
        'green': [],
        'blue': [],
        'alpha': []
    }

    # regular index to compute the colors
    reg_index = np.linspace(start, stop, 256)

    # shifted index to match the data
    shift_index = np.hstack([
        np.linspace(0.0, midpoint, 128, endpoint=False),
        np.linspace(midpoint, 1.0, 128, endpoint=True)
    ])

    for ri, si in zip(reg_index, shift_index):
        r, g, b, a = cmap(ri)

        cdict['red'].append((si, r, r))
        cdict['green'].append((si, g, g))
        cdict['blue'].append((si, b, b))
        cdict['alpha'].append((si, a, a))

    newcmap = matplotlib.colors.LinearSegmentedColormap(name, cdict)
    plt.register_cmap(cmap=newcmap)

    return newcmap

