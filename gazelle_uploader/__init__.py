#!/usr/bin/env python3

import argparse
import logging
import sys

import beets_api

APP_NAME = "gazelle_uploader"
VERSION = "0.0.1"


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

    sp_backup = sp_action.add_parser("list", help=("list releases"))
    sp_backup.add_argument("releases", metavar="release", type=str, nargs="*",
                           help="music data")
    sp_backup.set_defaults(func=list_releases)

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
