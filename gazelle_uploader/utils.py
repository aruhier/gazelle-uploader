#!/usr/bin/env python3

import subprocess

from . import gazelle_api
from . import CONFIG


def search_torrents_from_beets_release(api, beets_release):
    artist = beets_release.cur_artist
    album = beets_release.cur_album

    return gazelle_api.search_release(api, artist, album)


def gen_torrent_for(path, output):
    subprocess.check_output(
        [
            "mktorrent", path,
            "-a", CONFIG["announce"],
            "-p",
            "-o", output
        ], stderr=subprocess.STDOUT
    )
