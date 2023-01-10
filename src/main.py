import argparse
import toml
from src.Registration import registration
from src.Segmentation import run
from src.Tracking import tracking, draw_tracking


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
    parser.add_argument('--crop', nargs='?', type=bool, default=True,
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

    args = parser.parse_args()

    if args.subparser_name == 'registration':
        registration(args.path, args.path_to_save, args.crop)
    elif args.subparser_name == 'segmentation':
        run(toml.load(args.parameters), args.headless)
    elif args.subparser_name == 'tracking':
        tracking(args.path_to_table, args.path_to_save, args.max_distance, args.time_window, args.max_split_distance,
                 args.max_gap_closing_distance, args.allow_merging)
    elif args.subparser_name == 'draw_tracking':
        draw_tracking(args.path_to_table, args.path_to_images, args.path_to_save, args.rescale_intensity)
    else:
        print('nenhum')
    return


if __name__ == '__main__':
    main()
