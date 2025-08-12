import argparse
from pathlib import Path

def main():
    # top-level parser
    parser = argparse.ArgumentParser(prog='forNMA', description='forNMA is a tool for single-cell analysis and '
                                                                'phenotype integration.')
    subparsers = parser.add_subparsers(help='sub-command help', dest="fornma")

    #----------------------------------
    # parser for the "registration" command
    # ----------------------------------
    parser_registration = subparsers.add_parser(
        'registration',
        description='Register images in a folder',
        help='Module to perform registration of images within a folder'
    )
    parser_registration.add_argument(
        'paths',
        type=str,
        nargs='+',
        action='store',
        help='paths to folders to register. If there are more than one image channels,'
        ' each must be in a separate folder and passed to the parser.'
    )
    parser_registration.add_argument('path_to_save', type=str, help='path to save registered images')
    parser_registration.add_argument('--crop', nargs='?', type=bool, default=True,
                                     help='Crop images to keep only portions that are always in the field of view')

    # ----------------------------------
    # parser for the "segmentation" command
    # ----------------------------------
    parser_segmentation = subparsers.add_parser(
        'segmentation',
        description='Runs segmentation and feature extraction',
        help='Module to perform image segmentation and feature extraction'
    )
    parser_segmentation.add_argument(
        'parameters',
        type=str,
        help='path to parameters.toml'
    )
    parser_segmentation.add_argument('--preview', action='store_true', help='Preview images before running')

    # ----------------------------------
    # parser for the "tracking" command
    # ----------------------------------
    parser_tracking = subparsers.add_parser('tracking', description='Track cells from table', help='hhh')
    parser_tracking.add_argument('path_to_table', type=str, help='path to forNMA Results.csv')
    parser_tracking.add_argument('path_to_save', type=str, help='path to save tracked csv')
    parser_tracking.add_argument('-md', '--max_distance', nargs='?', type=int, default=200,
                                 help='maximal distance to allow particle linking between frames')
    parser_tracking.add_argument('-t', '--time_window', nargs='?', type=int, default=10,
                                 help='maximal memory of the tracker to link track segments')
    parser_tracking.add_argument('-ms', '--max_split_distance', nargs='?', type=int, default=30,
                                 help='maximal distance to link segment starts to segment midpoints')
    parser_tracking.add_argument('-mg', '--max_gap_closing_distance', nargs='?', type=int, default=10,
                                 help='maximal distance for closing segment gaps')
    parser_tracking.add_argument('-am', '--allow_merging', nargs='?', type=bool, default=True,
                                 help='indicates whether object merging is allowed or not ')

    # ----------------------------------
    # parser for  "draw tracking" command
    # ----------------------------------
    parser_draw = subparsers.add_parser('draw_tracking', description='Draw tracking at images', help='hhh')
    parser_draw.add_argument('path_to_table', type=str, help='pah to forNMA tracking Results.csv')
    parser_draw.add_argument('path_to_images', type=str, help='path to images folder')
    parser_draw.add_argument('path_to_save', type=str, help='path to save images')
    parser_draw.add_argument('-rs', '--rescale_intensity', nargs='?', type=bool, default=False,
                             help='if True, adjusts image intensities. Recommended for low intensity images.')

    # ----------------------------------
    # parser for "filter" command
    # ----------------------------------
    parser_filters = subparsers.add_parser('filter', help='Applies filters to your data.')
    parser_filters.add_argument('path_to_table', type=str, help='pah to forNMA Results.csv')
    parser_filters.add_argument('path_to_save', type=str, help='path to save results')
    parser_filters.add_argument('column1', type=str, help='path to save results', default='NII')
    parser_filters.add_argument('column2', type=str, help='path to save results', default="Area")
    parser_filters.add_argument('--draw', '-d',action='store_true',
                                help="Draw nuclei contours again, removing nuclei that were filtered out")
    parser_filters.add_argument('--path_to_pkl', '-pp', type=str, help='Path to results folder named pkl')

    # ----------------------------------
    # parser for the "NMA" command
    # ----------------------------------
    parser_NMA = subparsers.add_parser('NMA', help='To plot NMA, you first need to specify control settings, by calling'
                                                   '"fonrma NMA control".')
    subparser_one = parser_NMA.add_subparsers()

    # NMA settings
    parser_control = subparser_one.add_parser('settings', help='Creates the settings parameters for NMA plots.')
    parser_control.add_argument('path', type=str, help='Path to control group table.')
    parser_control.add_argument('--area_standard_deviation', '-sda', type=float, default=2.0,
                                help='The number of standard deviations from the Area mean to use for settings')
    parser_control.add_argument('--NII_standard_deviation', '-sdn', type=float, default=2.0,
                                help='The number of standard deviations from the NII mean to use for settings')
    parser_control.add_argument('--headless', '-hd', type=bool, default=False,
                                help="Run in headless mode")

    # NMA show settings
    parser_show_settings = subparser_one.add_parser('show_settings', help='Displays the current NMA settings')
    parser_show_settings.set_defaults(dest='show')

    # NMA heatmap_plot
    parser_heatmap = subparser_one.add_parser('heatmap_plot', help="Plots a NMA heatmap")
    parser_heatmap.add_argument('path', type=str, nargs='+', action='store', help='Paths to tables to plot.')
    parser_heatmap.add_argument('saving_path', action='store', help='Path to save results.')
    parser_heatmap.add_argument('--overtime', '-o', action='store_true',
                                help='Set True if your data is a time sequence')
    parser_heatmap.add_argument('--single', '-s', action='store_true',
                                help='Set True if you want a single plot with grouped data '
                                     '(equivalent to having one condition)')
    parser_heatmap.add_argument('--jointplot', '-j', action='store_true',
                                help='Set True if you want to plot histograms of area and NII i axis')


    # NMA dot_plot
    parser_dot = subparser_one.add_parser('dot_plot', help='plots a NMA dot plot')
    parser_dot.add_argument('paths', type=str, nargs='+', action='store', help='Paths to tables to plot.')
    parser_dot.add_argument('saving_path', action='store', help='Path to save results.')
    parser_dot.add_argument('--column1', '-c1', type=str, default=None,
                            help='Grouping column that will produce different dot colors')
    parser_dot.add_argument('--column2', '-c2', type=str, default=None,
                            help='Grouping column that will produce different dot sizes')
    parser_dot.add_argument('--sample_size', '-sz', type=int, default=None,
                            help='If you want to plot only a sample of total data, set a smple size')
    parser_dot.add_argument('--single', '-s', action='store_true',
                            help='Set True if you want a single plot with grouped data '
                                 '(equivalent to having one condition)')
    parser_dot.add_argument('--overtime', '-o', action='store_true',
                            help='Set True if your data is a time sequence')

    # ----------------------------------
    # parser for "plot" command
    # ----------------------------------
    parser_plots = subparsers.add_parser('plot', help="forNMA's plotting functions module. You must call it with the"
                                                      " following options: box, dot, violin, bar, scatter, line,"
                                                      "rolling-average or cpd. You can type 'forma plot box -h' to"
                                                      "obtain more specific tips on usage")
    subparser_plots = parser_plots.add_subparsers(dest='graph_type')

    # plot box
    parser_box = subparser_plots.add_parser('box', help='Plots a box plot of your data')
    parser_box.add_argument('path', type=str, help='Path to results table to plot data')
    parser_box.add_argument('path_to_save', type=str, help='path to save the plots')
    parser_box.add_argument('y', type=str, help='Column to use in Y axis')
    parser_box.add_argument('--hue', type=str, default=None, help='Grouping column that will produce different colors')
    parser_box.add_argument('--dot', type=str, default=None, help='Plots a dot plot inside the box')
    parser_box.add_argument('--conditions', '-c', type=str, action='store', nargs='+',
                            help='Conditions to plot. If empty, will retrieve a plot with all conditions')
    parser_box.add_argument('--gate', action='store_true',
                            help='Set value for True if you want to gate your data before plotting')
    parser_box.add_argument('--x', type=str, help='Name of X column to gate. Setting another X column inside graphs '
                                                  'arguments will override it')

    # plot violin
    parser_violin = subparser_plots.add_parser('violin', help='Plots a violin plot of your data')
    parser_violin.add_argument('path', type=str, help='Path to results table to plot data')
    parser_violin.add_argument('y', type=str, help='Column to use in Y axis')
    parser_violin.add_argument('--hue', type=str, default=None,
                               help='Grouping column that will produce different colors')
    parser_violin.add_argument('--dot', type=str, default=None, help='Plots a dot plot inside the violin')
    parser_violin.add_argument('path_to_save', type=str, help='path to save the plots')
    parser_violin.add_argument('--conditions', '-c', type=str, action='store', nargs='+',
                               help='Conditions to plot. If empty, will retrieve a plot with all conditions')
    parser_violin.add_argument('--gate', action='store_true',
                               help='Set value for True if you want to gate your data before plotting')
    parser_violin.add_argument('--x', type=str, help='Name of X column to gate. Setting another X column inside graphs '
                                                     'arguments will override it')

    # plot dot
    parser_dot = subparser_plots.add_parser('dot', help='Plots a dot plot of your data')
    parser_dot.add_argument('path', type=str, help='Path to results table to plot data')
    parser_dot.add_argument('y', type=str, help='Column to use in Y axis')
    parser_dot.add_argument('path_to_save', type=str, help='path to save the plots')
    parser_dot.add_argument('--hue', type=str, default=None,
                            help='Grouping column that will produce different dor colors')
    parser_dot.add_argument('--conditions', '-c', type=str, action='store', nargs='+',
                            help='Conditions to plot. If empty, will retrieve a plot with all conditions')
    parser_dot.add_argument('--gate', action='store_true',
                            help='Set value for True if you want to gate your data before plotting')
    parser_dot.add_argument('--x', type=str, help='Name of X column to gate. Setting another X column inside graphs '
                                                  'arguments will override it')

    # plot bar
    parser_bar = subparser_plots.add_parser('bar', help='Plots a bar plot of your data')
    parser_bar.add_argument('path', type=str, help='Path to results table to plot data')
    parser_bar.add_argument('y', type=str, help='Column to use in Y axis')
    parser_bar.add_argument('path_to_save', type=str, help='path to save the plots')
    parser_bar.add_argument('--conditions', '-c', type=str, action='store', nargs='+',
                            help='Conditions to plot. If empty, will retrieve a plot with all conditions')
    parser_bar.add_argument('--gate', action='store_true',
                            help='Set value for True if you want to gate your data before plotting')
    parser_bar.add_argument('--x', type=str, help='Name of X column to gate. Setting another X column inside graphs '
                                                  'arguments will override it')

    # plot scatter
    parser_scatter = subparser_plots.add_parser('scatter', help='Plots a scatter plot of your data')
    parser_scatter.add_argument('path', type=str, help='Path to results table to plot data')
    parser_scatter.add_argument('x', type=str, help='Column to use in X axis')
    parser_scatter.add_argument('y', type=str, help='Column to use in Y axis')
    parser_scatter.add_argument('--hue', type=str, default=None,
                                help='Grouping column that will produce different dot colors')
    parser_scatter.add_argument('--size', type=str, default=None,
                                help='Grouping column that will produce different dot sizes')
    parser_scatter.add_argument('path_to_save', type=str, help='path to save the plots')
    parser_scatter.add_argument('--conditions', '-c', type=str, action='store', nargs='+',
                                help='Conditions to plot. If empty, will retrieve a plot with all conditions')
    parser_scatter.add_argument('--gate', action='store_true',
                                help='Set value for True if you want to gate your data before plotting')

    # plot line
    parser_line = subparser_plots.add_parser('line', help='Plots a line plot of your data. This only works with '
                                                          'time sequence data')
    parser_line.add_argument('path', type=str, help='Path to results table to plot data')
    parser_line.add_argument('path_to_save', type=str, help='path to save the plots')
    parser_line.add_argument('y', type=str, help='Column to use in Y axis')
    parser_line.add_argument('--frames', '-f', type=int, nargs='+', action='store',
                             help='Frames to plot')
    parser_line.add_argument('--confidence_interval', '-ci', type=int, default=None,
                             help='Size of the confidence interval to draw when aggregating.')
    parser_line.add_argument('--style', type=str, default=None,
                             help='Grouping column that will produce different line styles')
    parser_line.add_argument('--hue', type=str, default=None,
                             help='Grouping column that will produce different line colors')
    parser_line.add_argument('--size', type=str, default=None,
                             help='Grouping column that will produce different line sizes')
    parser_line.add_argument('--conditions', '-c', type=str, action='store', nargs='+',
                             help='Conditions to plot. If empty, will retrieve a plot with all conditions')
    parser_line.add_argument('--gate', action='store_true',
                             help='Set value for True if you want to gate your data before plotting')
    parser_line.add_argument('--x', type=str, help='Name of X column to gate. Setting another X column inside graphs '
                                                   'arguments will override it')

    # plot rolling_average
    parser_rolling_avg = subparser_plots.add_parser('rolling-average',
                                                    help='Plots a rolling average  plot of your data. This'
                                                         'only works with time sequence data')
    parser_rolling_avg.add_argument('path', type=str, help='Path results table to plot data')
    parser_rolling_avg.add_argument('path_to_save', type=str, help='path to save the plots')
    parser_rolling_avg.add_argument('y', type=str, help='Column use in Y axis')
    parser_rolling_avg.add_argument('n', type=int, help='Number of frames to average')
    parser_rolling_avg.add_argument('--conditions', '-c', type=str, action='store', nargs='+',
                                    help='Conditions to plot. If empty, will retrieve a plot with all conditions')
    parser_rolling_avg.add_argument('--gate', action='store_true',
                                    help='Set value for True if you want to gate your data before plotting')
    parser_rolling_avg.add_argument('--x', type=str,
                                    help='Name of X column to gate. Setting another X column inside graphs '
                                         'arguments will override it')

    # plot CPD
    parser_cpd = subparser_plots.add_parser('cpd',
                                            help='Plots the cumulative population doubling of your data. This'
                                                 'only works with time sequence data')
    parser_cpd.add_argument('path', type=str, help='Path to results table to plot data')
    parser_cpd.add_argument('path_to_save', type=str, help='path to save the plots')
    parser_cpd.add_argument('frames', type=int, action='store', nargs='+',
                            help='Frames to plot. They must represent time intervals of at least 24h')
    parser_cpd.add_argument('--control', type=str, help='oYur control group')
    parser_cpd.add_argument('--conditions', '-c', type=str, action='store', nargs='+',
                            help='Conditions to plot. If empty, will retrieve a plot with all conditions')
    parser_cpd.add_argument('--gate', action='store_true',
                            help='Set value for True if you want to gate your data before plotting')
    parser_cpd.add_argument('--x', type=str,
                            help='Name of X column to gate. Setting another X column inside graphs '
                                 'arguments will override it')
    parser_cpd.add_argument('--y', type=str,
                            help='Name of Y column to gate. Setting another Y column inside graphs '
                                 'arguments will override it')

    # ----------------------------------
    # parser for the "foci" command
    # ----------------------------------
    parser_foci = subparsers.add_parser('foci', help='Module for foci overlay functions. Choose between:\nfoci overlay'
                                                     '\nfoci plot_profile')
    subparser_foci = parser_foci.add_subparsers()

    # foci overlay
    parser_overlay = subparser_foci.add_parser('overlay', help='Creates foci overlay in two or more image channels.')
    parser_overlay.add_argument('path', type=str, help='Path to folder named pkl-data')
    parser_overlay.add_argument('path_to_save', type=str, help='path to save results')
    parser_overlay.add_argument('--ch', type=str, nargs='+', action='store', help='Channels to overlay')

    # foci plot profile
    parser_plot_profile = subparser_foci.add_parser('plot_profile', help='Plots intensity profile of all nucleus in '
                                                    'the pickle files of a folder. The x  profile is given by mean of y'
                                                    ' pixels in the x axis and the y profile is the mean of x pixels '
                                                     'in the y axis.')
    parser_plot_profile.add_argument('path', type=str, help='Path to folder named pkl-data')
    parser_plot_profile.add_argument('path_to_save', type=str, help='path to save the plots')

    # ----------------------------------
    # parser for the UMAP command
    # ----------------------------------
    parser_umap = subparsers.add_parser('umap', help='UMAP and clustering utilities')
    subparser_umap = parser_umap.add_subparsers(dest='umap_cmd', required=True)

    # umap run -> perform_clustering
    p_run = subparser_umap.add_parser('run', help='Compute UMAP and save embedding')
    p_run.add_argument('paths', nargs='+', type=str, help='CSV file(s) to read')
    p_run.add_argument('saving_path', type=str, help='Folder to save outputs')
    p_run.add_argument('--columns', nargs='+', type=str, default=None, help='Feature columns to use')
    p_run.add_argument('--n_neighbors', type=int, default=15)
    p_run.add_argument('--min_dist', type=float, default=0.1)
    p_run.add_argument('--metric', type=str, default='Euclidean')
    p_run.add_argument('--scale', dest='scale', action='store_true')
    p_run.add_argument('--no-scale', dest='scale', action='store_false')
    p_run.set_defaults(scale=True)

    # umap elbow -> plot_elbow
    p_elbow = subparser_umap.add_parser('elbow', help='Generate Elbow plot from UMAP CSV')
    p_elbow.add_argument('path', type=str)
    p_elbow.add_argument('saving_path', type=str)
    p_elbow.add_argument('--k_min', type=int, default=1)
    p_elbow.add_argument('--k_max', type=int, default=10)

    # umap color -> color_umap
    p_color = subparser_umap.add_parser('color', help='Color UMAP by column or KMeans')
    p_color.add_argument('df_umap_path', type=str)
    p_color.add_argument('saving_path', type=str)
    p_color.add_argument('--color_col', type=str, default=None)
    p_color.add_argument('--use_clusters', action='store_true')
    p_color.add_argument('--n_clusters', type=int, default=None)

    # ----------------------------------
    # parser for the stats command
    # ----------------------------------
    parser_stats = subparsers.add_parser('stats', help='Statistical analyses')
    sub_stats = parser_stats.add_subparsers(dest='stats_cmd', required=True)

    # stats oneway
    p_one = sub_stats.add_parser('oneway', help='One-way analysis (ANOVA/Kruskal + post-hoc)')
    p_one.add_argument('paths', nargs='+', type=str, help='One or more CSV files to concatenate')
    p_one.add_argument('numeric_col', type=str, help='Numeric column (dependent variable)')
    p_one.add_argument('group_col', type=str, help='Grouping column (independent variable)')
    p_one.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    p_one.add_argument('--pairs_of_interest', nargs='*', default=None,
                       help='Specific pairs for post-hoc test (e.g., A B  A C)')
    p_one.add_argument('--log_file', type=str, default=None, help='Log file path')
    p_one.add_argument('--save_dir', type=str, default='.', help='Directory to save outputs')

    # stats twoway
    p_two = sub_stats.add_parser('twoway', help='Two-way analysis (2-way ANOVA or SRH + post-hoc)')
    p_two.add_argument('paths', nargs='+', type=str, help='One or more CSV files to concatenate')
    p_two.add_argument('numeric_col', type=str, help='Numeric column (dependent variable)')
    p_two.add_argument('group_col1', type=str, help='First factor (independent variable)')
    p_two.add_argument('group_col2', type=str, help='Second factor (independent variable)')
    p_two.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    p_two.add_argument('--pairs_of_interest', nargs='*', default=None,
                       help='Specific cell pairs for post-hoc (e.g., A|X A|Y)')
    p_two.add_argument('--log_file', type=str, default=None, help='Log file path')
    p_two.add_argument('--save_dir', type=str, default='.', help='Directory to save outputs')

    # stats chi2
    p_chi = sub_stats.add_parser('chi2', help='Chi-square analysis (global test + pairwise post-hoc)')
    p_chi.add_argument('paths', nargs='+', type=str, help='One or more CSV files to concatenate')
    p_chi.add_argument('group_col', type=str, help='Grouping column (rows of contingency table)')
    p_chi.add_argument('category_col', type=str, help='Category column (columns of contingency table)')
    p_chi.add_argument('--expected_min', type=float, default=5.0, help='Minimum expected count threshold')
    p_chi.add_argument('--num_simulations', type=int, default=10000, help='Monte Carlo simulations')
    p_chi.add_argument('--correction_method', type=str, default='auto',
                       help="Multiple-comparisons method (e.g., 'bonferroni', 'fdr_bh', or 'auto')")
    p_chi.add_argument('--log_file', type=str, default=None, help='Log file path')
    p_chi.add_argument('--save_dir', type=str, default='.', help='Directory to save outputs')

    # stats chi2-subgroups
    p_chisg = sub_stats.add_parser('chi2-subgroups',
                                   help='Chi-square subgroup comparisons (per-category 2x2 tests with correction)')
    p_chisg.add_argument('paths', nargs='+', type=str, help='One or more CSV files to concatenate')
    p_chisg.add_argument('group_col', type=str, help='Category column to iterate over (e.g., phenotype)')
    p_chisg.add_argument('condition_col', type=str, help='Condition column to compare within each category')
    p_chisg.add_argument('--expected_min', type=float, default=5.0, help='Minimum expected count threshold')
    p_chisg.add_argument('--correction_method', type=str, default='bonferroni',
                         help="Multiple-comparisons method (e.g., 'bonferroni', 'fdr_bh', or 'auto')")
    p_chisg.add_argument('--log_file', type=str, default=None, help='Log file path')
    p_chisg.add_argument('--save_dir', type=str, default='.', help='Folder to save outputs')


    ######################################################################################################
    args = parser.parse_args()
    print(args)

    if args.fornma == 'registration':
        from src.fornma.Registration import registration
        registration(args.paths, args.path_to_save, args.crop)

    elif args.fornma == 'segmentation':
        import toml
        from src.fornma.Segmentation import run, check_user_inputs
        dic = toml.load(args.parameters)
        check_user_inputs(dic)
        run(dic, preview=args.preview)

    elif args.fornma == 'tracking':
        from src.fornma.Tracking import tracking
        tracking(args.path_to_table, args.path_to_save, args.max_distance, args.time_window, args.max_split_distance,
                 args.max_gap_closing_distance, args.allow_merging)

    elif args.fornma == 'draw_tracking':
        from src.fornma.Tracking import  draw_tracking
        draw_tracking(args.path_to_table, args.path_to_images, args.path_to_save, args.rescale_intensity)

    elif args.fornma == 'filters':
        from src.fornma.Filters import filters
        filters(args.path_to_table, args.path_to_save, args.draw, args.column1, args.column2, args.path_to_pkl)

    elif args.fornma == 'filers':
        from src.fornma.Filters import filters
        filters(args.path_to_table, args.path_to_save, args.draw, args.column1, args.column2, args.path_to_pkl)

    elif args.fornma == 'NMA':
        from src.fornma.Graphs import show_nma_settings
        from src.fornma.NMA import plot_NMA
        from src.fornma.NMA import NMA_control
        if (hasattr(args, 'dest')) and args.dest == 'show':
            show_nma_settings()
        elif hasattr(args, 'area_standard_deviation'):
            NMA_control(args.path, args.area_standard_deviation, args.NII_standard_deviation, args.headless)
        elif hasattr(args, 'column1'):
            plot_NMA(args.paths, args.saving_path, "dot", args.column1, args.column2, args.sample_size, args.single,
                     args.overtime)
        elif hasattr(args, 'jointplot') and args.jointplot:
            plot_NMA(args.path, args.saving_path, "jointplot", None, None, None, args.single, args.overtime)
        else:
            plot_NMA(args.path, args.saving_path, "heatmap", None, None, None, args.single, args.overtime)

    elif args.fornma == 'plot':
        from src.fornma.Graphs import plot
        x = args.x if hasattr(args, 'x') else None
        y = args.y if hasattr(args, 'y') else None
        hue = args.hue if hasattr(args, 'hue') else None
        size = args.size if hasattr(args, 'size') else None
        control = args.control if hasattr(args, 'control') else False
        n = args.n if hasattr(args, 'n') else None
        style = args.style if hasattr(args, 'style') else None
        ci = args.ci if hasattr(args, 'ci') else None
        dot = args.dot if hasattr(args, 'dot') else None
        conditions = args.conditions if hasattr(args, 'conditions') else None
        frames = args.frames if hasattr(args, 'frames') else None
        plot(args.path, args.path_to_save, conditions, frames, args.graph_type, args.gate, x=x, y=y, hue=hue, size=size,
             control=control, n=n, style=style, ci=ci, dot=dot)

    elif args.fornma == 'foci':
        from src.fornma.Foci_overlay import foci_overlay, plot_profile
        if hasattr(args, 'ch'):
            foci_overlay(args.path, args.path_to_save, args.ch)
        else:
            plot_profile(args.path, args.path_to_save)

    elif args.fornma == 'umap':
        from src.fornma.UMAP import perform_clustering, plot_elbow, color_umap
        if args.umap_cmd == 'run':
            perform_clustering(
                path=args.paths,
                saving_path=args.saving_path,
                columns=args.columns,
                n_neighbors=args.n_neighbors,
                min_dist=args.min_dist,
                metric=args.metric,
                scale=args.scale,
            )
        elif args.umap_cmd == 'elbow':
            plot_elbow(
                path=args.path,
                saving_path=args.saving_path,
                k_min=args.k_min,
                k_max=args.k_max,
            )
        elif args.umap_cmd == 'color':
            color_umap(
                df_umap_path=args.df_umap_path,
                saving_path=args.saving_path,
                color_col=args.color_col,
                use_clusters=args.use_clusters,
                n_clusters=args.n_clusters,
            )


    elif args.fornma == 'stats':
        if hasattr(args, 'save_dir') and args.save_dir:
            Path(args.save_dir).mkdir(parents=True, exist_ok=True)
            forced_log = str(Path(args.save_dir) / "logs-fornma.txt")
        else:
            forced_log = args.log_file

        from src.fornma.Statistics.Helpers import AnalysisHelper
        helper = AnalysisHelper(alpha=args.alpha if hasattr(args, 'alpha') else 0.05,
                                log_file=forced_log)
        df = helper.load_and_concat(args.paths)

        if args.stats_cmd == 'oneway':
            from src.fornma.Statistics.OneWayAnalysis import OneWayAnalysis
            ana = OneWayAnalysis(df=df, numeric_col=args.numeric_col, group_col=args.group_col,
                                 alpha=args.alpha, pairs_of_interest=args.pairs_of_interest, helper=helper)
            results = ana.run()
            helper.save_stats_bundle(args.save_dir, 'oneway',
                                     main_result=results['main_result'],
                                     posthoc=results['posthoc'],
                                     summary=results['summary'])


        elif args.stats_cmd == 'twoway':
            from src.fornma.Statistics.TwoWayAnalysis import TwoWayAnalysis

            ana = TwoWayAnalysis(df=df, numeric_col=args.numeric_col,
                                 group_col1=args.group_col1, group_col2=args.group_col2,
                                 alpha=args.alpha, pairs_of_interest=args.pairs_of_interest, helper=helper)

            results = ana.run()
            helper.save_stats_bundle(args.save_dir, 'twoway',
                                     main_result=results['main_result'],
                                     posthoc=results['posthoc'],
                                     summary=results['summary'])

        elif args.stats_cmd == 'chi2':
            from src.fornma.Statistics.ChiSquareAnalyzer import ChiSquareAnalyzer
            ana = ChiSquareAnalyzer(expected_min=args.expected_min, use_exact=True,
                                    log_file=forced_log, helper=helper)
            g = ana.global_test(df, args.group_col, args.category_col)
            post = ana.pairwise_posthoc(g.contingency_table, correction_method=args.correction_method)
            helper.save_chi2(args.save_dir, 'chi2', g, post)

        elif args.stats_cmd == 'chi2-subgroups':
            from src.fornma.Statistics.Helpers import AnalysisHelper
            from src.fornma.Statistics.ChiSquareSubgroupComparator import ChiSquareSubgroupComparator

            helper = AnalysisHelper(log_file=forced_log)
            df = helper.load_and_concat(args.paths)

            ana = ChiSquareSubgroupComparator(
                expected_min=args.expected_min,
                correction_method=args.correction_method,
                log_file=forced_log,
                helper=helper
            )

            df_results, prop_table = ana.compare(
                df=df,
                group_col=args.group_col,
                condition_col=args.condition_col
            )

            helper.save_chi2_subgroups(
                out_dir=args.save_dir,
                prefix='chi2_subgroups',
                df_results=df_results,
                prop_table=prop_table
            )

    else:
        print('No option was found')
    return

if __name__ == '__main__':
    main()
