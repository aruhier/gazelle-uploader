#!/usr/bin/env python3

import argparse
import logging
import os
import sys

from . import APP_NAME, VERSION, beets_api, gazelle_api
from .utils import find_logfile_from, gen_torrent_for
from .decorators import connect_api, for_each_path_from_args


if __name__ == "__main__":
    parse_args()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Upload music on a gazelle based tracker"
    )

    sp_action = parser.add_subparsers()

    sp_list = sp_action.add_parser("list", help=("list releases"))
    sp_list.add_argument("releases", metavar="release", type=str, nargs="*",
                         help="music data")
    sp_list.set_defaults(func=list_releases)

    sp_check = sp_action.add_parser(
        "check", help=("check if releases are already on the tracker")
    )
    sp_check.add_argument("releases", metavar="release", type=str, nargs="*",
                          help="music data")
    sp_check.set_defaults(func=are_on_tracker)

    sp_upload = sp_action.add_parser(
        "upload", help=("upload releases on the tracker")
    )
    sp_upload.add_argument('-o', '--outdir',
                           help="directory to store the generated torrents",
                           dest="output_dir", default="./", required=False)
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


@connect_api
@for_each_path_from_args
def list_releases(parsed_args, *args, **kwargs):
    api, path = kwargs["api"], kwargs["path"]
    for t in beets_api.get_tags_for_path(path):
        print(t.cur_artist, "-", t.cur_album)


@connect_api
@for_each_path_from_args
def are_on_tracker(parsed_args, *args, **kwargs):
    api, path = kwargs["api"], kwargs["path"]
    for release in beets_api.get_tags_for_path(path):
        uploaded = bool(gazelle_api.search_exact_beets_release(api, release))
        _print_release_status_on_tracker(release, uploaded)


def _print_release_status_on_tracker(release, uploaded):
    msg_status = (
        "already on the tracker" if uploaded else "not found on the tracker"
    )
    print(release.cur_artist, "-", release.cur_album, msg_status)


@connect_api
def search_on_tracker(parsed_args, *args, **kwargs):
    api = kwargs["api"]
    artist = parsed_args.artist
    release = parsed_args.release
    result = gazelle_api.search_release(api, artist, release)

    for r in result:
        for torrent in r["torrent"]:
            print(torrent["remasterRecordLabel"], torrent["remasterTitle"],
                  torrent["media"], torrent["format"], torrent["encoding"])


@connect_api
@for_each_path_from_args
def upload(parsed_args, *args, **kwargs):
    """
    Only for testing, for the moment, as it does handle the creation of any
    torrent file
    """
    api, path = kwargs["api"], kwargs["path"]
    output_dir = parsed_args.output_dir

    for release in beets_api.get_tags_for_path(path):
        already_uploaded = bool(
            gazelle_api.search_exact_beets_release(api, release)
        )
        _print_release_status_on_tracker(release, already_uploaded)
        if already_uploaded:
            continue

        release_path = release.paths[-1].decode()
        try:
            logfiles_paths = [find_logfile_from(release_path)]
        except FileNotFoundError:
            logfiles_paths = []

        torrent_file = gen_torrent_for(release_path, output_dir)
        response = gazelle_api.upload(
            api, release.cur_artist, release, torrent_file,
            logfiles_paths=logfiles_paths
        )
        import pdb; pdb.set_trace()
        print(
            "{} uploaded, torrent file: {}".format(release_path, torrent_file)
        )
