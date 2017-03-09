#!/usr/bin/env python3

import glob
import os
import subprocess

from . import gazelle_api
from . import CONFIG


def search_torrents_from_beets_release(api, beets_release):
    artist = beets_release.cur_artist
    album = beets_release.cur_album

    return gazelle_api.search_release(api, artist, album)


def gen_torrent_for(path, output="./"):
    torrent_path = os.path.join(
        output, os.path.normpath(path).split(os.sep)[-1] + ".torrent"
    )

    cmd = [
        "mktorrent", path,
        "-a", CONFIG["announce"],
        "-p",
        "-o", torrent_path,
    ]
    subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    return torrent_path


def find_logfile_from(path):
    patterns = ("*.log", "*log*.txt")
    for pattern in patterns:
        try:
            return next(glob.iglob(os.path.join(path, pattern)))
        except StopIteration:
            continue

    raise FileNotFoundError()
