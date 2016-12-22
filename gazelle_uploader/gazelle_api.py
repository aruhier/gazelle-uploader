#!/usr/bin/env python3

from gazelleapi import GazelleAPI

from . import CONFIG


def search_release(artist, release):
    api = configure_api_and_connect()
    artist_data = get_artist(artist, api)
    for tgroup in artist_data.get("torrentgroup", []):
        if tgroup["groupName"] == release:
            yield tgroup


def configure_api_and_connect():
    api = GazelleAPI(
        username=CONFIG["login"], password=CONFIG["password"],
        site_url=CONFIG["site"], announce_url=CONFIG["announce"]
    )
    api.connect()

    return api


def get_artist(artist, api):
    return api.request("artist", artistname=artist)
