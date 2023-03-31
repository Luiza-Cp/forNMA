import argparse
import toml
from src.Registration import registration
from src.Segmentation import run
from src.Tracking import tracking, draw_tracking
from src.Graphs import NMA_control, plot_NMA

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
    parser_NMA = subparsers.add_parser('NMA', help='parser one')
    subparser_one = parser_NMA.add_subparsers()

    #NMA control
    parser_control = subparser_one.add_parser('control')
    parser_control.add_argument('path', type=str, help='option one')
    parser_control.add_argument('--standard_deviation', '-sd', type=float, default=2.0,  help='option one')
    parser_control.add_argument('--headless', '-hd', type=bool, default=False, help="hhh")

    #NMA heatmap_plot
    parser_heatmap = subparser_one.add_parser('heatmap_plot')
    parser_heatmap.add_argument('path', type=str, nargs='+', action='store', help='option 2')
    parser_heatmap.add_argument('saving_path', action='store', help='option 2')
    parser_heatmap.add_argument('--overtime', '-o', type=bool, default=False, help='option 2')
    parser_heatmap.add_argument('--single', '-s', type=bool, default=False, help='option 2')

    # NMA dot_plot
    parser_dot = subparser_one.add_parser('dot_plot')
    parser_dot.add_argument('path', type=str, nargs='+', action='store', help='option 2')
    parser_dot.add_argument('saving_path', action='store', help='option 2')
    parser_dot.add_argument('--column1', '-c1', type=str, default=None, help='option 2')
    parser_dot.add_argument('--column2', '-c2', type=str, default=None, help='option 2')
    parser_dot.add_argument('--sample_size', '-sz', type=int, default=None, help='option 2')
    parser_dot.add_argument('--single', '-s', type=bool, default=False, help='option 2')
    parser_dot.add_argument('--overtime', '-o', type=bool, default=False, help='option 2')

    args = parser.parse_args()
   # print(args)

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
            print(args)
            NMA_control(args.path, args.standard_deviation, args.headless)
        elif hasattr(args, 'column1'):
            plot_NMA(args.path, args.saving_path, "dot", args.column1, args.column2, args.sample_size, args.single,
                     args.overtime)
        else:
            plot_NMA(args.path, args.saving_path, "heatmap", None, None, None, args.single, args.overtime)

    else:
        print('No option was found')
    return


if __name__ == '__main__':
    main()
