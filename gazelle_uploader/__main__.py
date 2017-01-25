#!/usr/bin/env python3

import argparse
import logging
import sys

from . import APP_NAME, VERSION
from . import beets_api, gazelle_api, compare, utils


def upload(parsed_args, *args, **kwargs):
    """
    Only for testing, for the moment, as it does handle the creation of any
    torrent file
    """
    paths = parsed_args.releases
    api = gazelle_api.configure_api_and_connect()
    for p in paths:
        for release in beets_api.get_tags_for_path(p):
            gazelle_api.upload(api, release.cur_artist, release, None, None)


def are_on_tracker(parsed_args, *args, **kwargs):
    paths = parsed_args.releases
    api = gazelle_api.configure_api_and_connect()
    for p in paths:
        for release in beets_api.get_tags_for_path(p):
            torrent_groups = utils.search_torrents_from_beets_release(
                api, release
            )
            matching_torrent = None
            for torrent_group in torrent_groups:
                matching_torrent = compare.get_matching_torrent_from_group(
                    torrent_group, release
                )
                if matching_torrent:
                    print(
                        release.cur_artist, "-", release.cur_album,
                        "already on the tracker"
                    )
                    # to remove
                    gazelle_api.upload(api, "k.flay", release, None, None)
                    break
            if not matching_torrent:
                print(
                    release.cur_artist, "-", release.cur_album,
                    "not found on tracker"
                )


def search_on_tracker(parsed_args, *args, **kwargs):
    artist = parsed_args.artist
    release = parsed_args.release
    api = gazelle_api.configure_api_and_connect()
    result = gazelle_api.search_release(api, artist, release)

    for r in result:
        for torrent in r["torrent"]:
            print(torrent["remasterRecordLabel"], torrent["remasterTitle"],
                  torrent["media"], torrent["format"], torrent["encoding"])


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

    sp_list = sp_action.add_parser(
        "check", help=("check if releases are already on the tracker")
    )
    sp_list.add_argument("releases", metavar="release", type=str, nargs="*",
                         help="music data")
    sp_list.set_defaults(func=are_on_tracker)

    sp_upload = sp_action.add_parser(
        "upload", help=("upload releases on the tracker")
    )
    sp_upload.add_argument("releases", metavar="release", type=str, nargs="*",
                           help="music data")
    sp_upload.set_defaults(func=upload)

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
