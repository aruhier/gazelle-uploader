#!/usr/bin/env python3

import argparse
import logging
import sys

from . import APP_NAME, VERSION
from . import beets_api, gazelle_api


def search_on_tracker(parsed_args, *args, **kwargs):
    artist = parsed_args.artist
    release = parsed_args.release
    result = gazelle_api.search_release(artist, release)
    import pdb; pdb.set_trace()

    print(result)


def list_releases(parsed_args, *args, **kwargs):
    paths = parsed_args.releases
    for p in paths:
        for t in beets_api.get_tags_for_path(p):
            print(t.cur_artist, "-", t.cur_album)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Upload music on a gazelle based tracker"
    )

    sp_action = parser.add_subparsers()

    sp_list = sp_action.add_parser("list", help=("list releases"))
    sp_list.add_argument("releases", metavar="release", type=str, nargs="*",
                         help="music data")
    sp_list.set_defaults(func=list_releases)

    sp_search = sp_action.add_parser(
        "search", help=("search releases on tracker")
    )
    sp_search.add_argument('-a', '--artist', help="filter artist",
                           dest="artist", required=True)
    sp_search.add_argument('-r', '--release', help="filter release",
                           dest="release", required=True)
    sp_search.set_defaults(func=search_on_tracker)

    # Debug option
    parser.add_argument("-d", "--debug", help="set the debug level",
                        dest="debug", action="store_true")
    parser.add_argument(
        "--version", action="version",
        version="{} {}".format(APP_NAME, VERSION)
    )
    arg_parser = parser

    # Parse argument
    args = arg_parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    # Execute correct function, or print usage
    if hasattr(args, "func"):
        args.func(parsed_args=args)
    else:
        arg_parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    parse_args()
