import argparse
import toml
from src.Registration import registration
from src.Segmentation import run
from src.Tracking import tracking, draw_tracking
from src.Graphs import NMA_control, plot_NMA, show_NMA_settings, plot

def main():
    # top-level parser
    parser = argparse.ArgumentParser(prog='forNMA', description='----')
    subparsers = parser.add_subparsers(help='sub-command help', dest="subparser_name")

    # parser for the "registration" command
    parser_registration = subparsers.add_parser('registration', description='Register images in a folder',
                                                help='hhh')
    parser_registration.add_argument('--path', '-p', required=True, type=str, nargs='+', action='store',
                                     help='path to folder to register. If there are more than one image channel,'
                                          ' each must be in a separate folder and passed to the parser.')
    parser_registration.add_argument('--path_to_save', '-ps', required=True, type=str,
                                     help='path to save registered images')
    parser_registration.add_argument('--crop', nargs='?', type=bool, default=True,
                                     help='Crop images to keep only portions that are always in the field of view')

    # parser for the "segmentation" command
    parser_segmentation = subparsers.add_parser('segmentation', description='Runs segmentation and feature extraction',
                                                help='b help')
    parser_segmentation.add_argument('parameters', type=str, help='path to parameters.toml')
    parser_segmentation.add_argument('--headless', type=bool, default=False, help='path to save registered images')

    # parser for the "tracking" command
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

    # parser for the "draw tracking" command
    parser_draw = subparsers.add_parser('draw_tracking', description='Draw tracking at images', help='hhh')
    parser_draw.add_argument('path_to_table', type=str, help='pah to forNMA tracking Results.csv')
    parser_draw.add_argument('path_to_images', type=str, help='path to images folder')
    parser_draw.add_argument('path_to_save', type=str, help='path to save images')
    parser_draw.add_argument('-rs', '--rescale_intensity', nargs='?', type=bool, default=False,
                             help='if True, adjusts image intensities. Recommended for low intensity images.')

    # parser for the "NMA" command
    parser_NMA = subparsers.add_parser('NMA', help='To plot NMA, you first need to specify control settings, by calling'
                                                   '"fonrma NMA control".')
    subparser_one = parser_NMA.add_subparsers()

    # NMA settings
    parser_control = subparser_one.add_parser('settings', help='Creates the settings parameters for NMA plots.')
    parser_control.add_argument('path', type=str, help='Path to control group table.')
    parser_control.add_argument('--standard_deviation', '-sd', type=float, default=2.0,
                                help='The standard deviation to select control populations.')
    parser_control.add_argument('--headless', '-hd', type=bool, default=False,
                                help="Run in headless mode")

    # NMA show settings
    parser_show_settings = subparser_one.add_parser('show_settings', help='Displays the current NMA settings')

    # NMA heatmap_plot
    parser_heatmap = subparser_one.add_parser('heatmap_plot', help="Plots a NMA heatmap")
    parser_heatmap.add_argument('path', type=str, nargs='+', action='store', help='Paths to tables to plot.')
    parser_heatmap.add_argument('saving_path', action='store', help='Path to save results.')
    parser_heatmap.add_argument('--overtime', '-o', type=bool, default=False,
                                help='Set True if your data is a time sequence')
    parser_heatmap.add_argument('--single', '-s', type=bool, default=False,
                                help='Set True if you want a single plot with grouped data '
                                     '(equivalent to having one condition)')

    # NMA dot_plot
    parser_dot = subparser_one.add_parser('dot_plot', help= 'plots a NMA dot plot')
    parser_dot.add_argument('paths', type=str, nargs='+', action='store',  help='Paths to tables to plot.')
    parser_dot.add_argument('--saving_path', '-sp', action='store', help='Path to save results.')
    parser_dot.add_argument('--column1', '-c1', type=str, default=None,
                            help='Grouping column that will produce different dot colors')
    parser_dot.add_argument('--column2', '-c2', type=str, default=None,
                            help='Grouping column that will produce different dot sizes')
    parser_dot.add_argument('--sample_size', '-sz', type=int, default=None,
                            help='If you want to plot only a sample of total data, set a smple size')
    parser_dot.add_argument('--single', '-s', type=bool, default=False,
                            help='Set True if you want a single plot with grouped data '
                                 '(equivalent to having one condition)')
    parser_dot.add_argument('--overtime', '-o', type=bool, default=False,
                            help='Set True if your data is a time sequence')

    # parser for "plot" command
    parser_plots = subparsers.add_parser('plot', help="forNMA's plotting functions module. You must call it with the"
                                                      " following options: box, dot, violin, bar, scatter, line,"
                                                      "rolling-average or cpd. You can type 'forma plot box -h' to"
                                                      "obtain more specific tips on usage")
    parser_plots.add_argument('--gate', type=bool, default=False,
                              help='Set value for True if you want to gate your data before plotting')
    parser_plots.add_argument('--x', type=str, help='Name of X column to gate. Setting another X column inside graphs '
                                                    'arguments will override it')
    parser_plots.add_argument('--y', type=str, help='Name of Y column to gate. Setting another Y column inside graphs '
                                                    'arguments will override it')
    subparser_plots = parser_plots.add_subparsers()

    # plot box
    parser_box = subparser_plots.add_parser('box', help='Plots a box plot of your data')
    parser_box.add_argument('path', type=str, help='Path to results table to plot data')
    parser_box.add_argument('path_to_save', type=str, help='path to save the plots')
    parser_box.add_argument('y', type=str, help='Column to use in Y axis')
    parser_box.add_argument('--hue', type=str, default=None, help='Grouping column that will produce different colors')
    parser_box.add_argument('--dot', type=str, default=None, help='Plots a dot plot inside the box')
    parser_box.add_argument('--conditions', '-c', type=str, action='store', nargs='+',
                            help='Conditions to plot. If empty, will retrieve a plot with all conditions')

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

    # plot dot
    parser_dot = subparser_plots.add_parser('dot', help='Plots a dot plot of your data')
    parser_dot.add_argument('path', type=str, help='Path to results table to plot data')
    parser_dot.add_argument('y', type=str, help='Column to use in Y axis')
    parser_dot.add_argument('--hue', type=str, default=None,
                            help='Grouping column that will produce different dor colors')
    parser_dot.add_argument('path_to_save', type=str, help='path to save the plots')
    parser_dot.add_argument('--conditions', '-c', type=str, action='store', nargs='+',
                            help='Conditions to plot. If empty, will retrieve a plot with all conditions')

    # plot bar
    parser_bar = subparser_plots.add_parser('dot', help='Plots a bar plot of your data')
    parser_bar.add_argument('path', type=str, help='Path to results table to plot data')
    parser_bar.add_argument('y', type=str, help='Column to use in Y axis')
    parser_bar.add_argument('path_to_save', type=str, help='path to save the plots')
    parser_bar.add_argument('--conditions', '-c', type=str, action='store', nargs='+',
                            help='Conditions to plot. If empty, will retrieve a plot with all conditions')

    # plot scatter
    parser_scatter = subparser_plots.add_parser('dot', help='Plots a scatter plot of your data')
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

    args = parser.parse_args()
    print(args)

    if args.subparser_name == 'registration':
        registration(args.path, args.path_to_save, args.crop)

    elif args.subparser_name == 'segmentation':
        run(toml.load(args.parameters), headless=args.headless)
    elif args.subparser_name == 'tracking':
        tracking(args.path_to_table, args.path_to_save, args.max_distance, args.time_window, args.max_split_distance,
                 args.max_gap_closing_distance, args.allow_merging)
    elif args.subparser_name == 'draw_tracking':
        draw_tracking(args.path_to_table, args.path_to_images, args.path_to_save, args.rescale_intensity)
    elif args.subparser_name == 'NMA':
        if hasattr(args, 'standard_deviation'):
            NMA_control(args.path, args.standard_deviation, args.headless)
        elif args.subparser_name == 'show_settings':
            show_NMA_settings()
        elif hasattr(args, 'column1'):
            plot_NMA(args.paths, args.saving_path, "dot", args.column1, args.column2, args.sample_size, args.single,
                     args.overtime)
        else:
            plot_NMA(args.path, args.saving_path, "heatmap", None, None, None, args.single, args.overtime)
    elif args.subparser_name == 'plot':
        x = args.x if hasattr(args, 'x') else None
        y = args.y if hasattr(args, 'y') else None
        hue = args.hue if hasattr(args, 'hue') else None
        size = args.size if hasattr(args, 'size') else None
        control = args.control if hasattr(args, 'control') else False
        n = args.n if hasattr(args, 'n') else None
        style = args.style if hasattr(args, 'style') else None
        ci = args.ci if hasattr(args, 'ci') else None
        dot = args.dot if hasattr(args, 'dot') else None
        plot(args.path, args.path_to_save, args.conditions, args.frames, args.subparser_name, args.gate, x=x, y=y,
             hue=hue, size=size, control=control, n=n, style=style, ci=ci, dot=dot)
    else:
        print('No option was found')
    return


if __name__ == '__main__':
    main()
