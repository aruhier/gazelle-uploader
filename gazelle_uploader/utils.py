#!/usr/bin/env python3

from . import gazelle_api


def search_torrents_from_beets_release(beets_release):
    artist = beets_release.cur_artist
    album = beets_release.cur_album

    return gazelle_api.search_release(artist, album)
