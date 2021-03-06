#!/usr/bin/env python3

import gazelleapi
from gazelleapi import GazelleAPI
import editor
import json
import logging
import os

from . import CONFIG, APP_NAME
from . import compare, utils


LOGGER = logging.getLogger(APP_NAME)

MEDIA_SEARCH_MAP = {
    "cd": "CD",
    "dvd": "DVD",
    "vinyl": "Vinyl",
    "soundboard": "Soundboard",
    "sacd": "SACD",
    "dat": "DAT",
    "web": "WEB",
    "blu-ray": "Blu-ray"
}

MEDIA_TYPE_SEARCH_MAP = {
    "album": 1,
    "soundtrack": 3,
    "ep": 5,
    "anthology": 6,
    "compilation": 7,
    "single": 9,
    "liv album": 11,
    "remix": 13,
    "bootleg": 14,
    "interview": 15,
    "mixtape": 16,
    "unknown": 21,
}

TAGS_SEARCH_MAP = {
    "acapella": "acapella",
    "acoustic": "acoustic",
    "alternative": "alternative",
    "ambient": "ambient",
    "blues": "blues",
    "classical": "classical",
    "country": "country",
    "dance": "dance",
    "disco": "disco",
    "drum and bass": "drum.and.bass",
    "electro": "electro",
    "electronic": "electronic",
    "emo": "emo",
    "experimental": "experimental",
    "folk": "folk",
    "funk": "funk",
    "grunge": "grunge",
    "hard rock": "hard.rock",
    "hardcore": "hardcore",
    "hardcore dance": "hardcore.dance",
    "harcore punk": "hardcore.punk",
    "hip hop": "hip.hop",
    "house": "house",
    "idm": "idm",
    "indie": "indie",
    "instrumental": "instrumental",
    "jazz": "jazz",
    "jpop": "jpop",
    "mashup": "mashup",
    "metal": "metal",
    "opera": "opera",
    "pop": "pop",
    "progressive house": "progressive.house",
    "progressive rock": "progressive.rock",
    "psy trance": "psy.trance",
    "psychedelic": "psychedelic",
    "punk": "punk",
    "r and b": "r.and.b",
    "rave": "rave",
    "reggae": "reggae",
    "rock": "rock",
    "rock and roll": "rock.and.roll",
    "ska": "ska",
    "soul": "soul",
    "soundtrack": "soundtrack",
    "swing": "swing",
    "techno": "techno",
    "trance": "trance",
    "trip hop": "trip.hop",
    "uk garage": "uk.garage",
    "vanity house": "vanity.house",
    "world music": "world.music",
}


def search_exact_beets_release(api, beets_release):
    torrent_groups = utils.search_torrents_from_beets_release(
        api, beets_release
    )
    matching_torrent = None
    for torrent_group in torrent_groups:
        matching_torrent = compare.get_matching_torrent_from_group(
            torrent_group, beets_release
        )
        if matching_torrent:
            break
    return matching_torrent


def search_release(api, artist, release):
    try:
        artist_data = get_artist(api, artist)
    except gazelleapi.gazelleapi.RequestException:
        return
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


def get_artist(api, artist):
    return api.request("artist", artistname=artist)


def upload(api, artists, release, torrent_path, description=None,
           logfiles_paths=[]):
    """
    :param arists: list of artists
    :type artists: list
    :param release: beets release item
    :param torrent_path: torrent file path
    :param description: optional description
    :param logfiles_paths: list of logfiles paths
    :type logfiles_paths: list
    """
    url = "{}/{}.php".format(api.site_url, "upload")
    params = _get_release_infos_to_upload(release)

    params["submit"] = "true"
    if api.authkey:
        params['auth'] = api.authkey
    params["artists[]"] = artists
    # TODO: link with artists
    params["importance[]"] = "1"
    params["album_desc"] = (
        description if description else _build_descr_from_titles(release)
    )

    files = {}
    opened_logfiles = []
    try:
        # TODO: maybe throwing an exception if canceled
        with open(torrent_path, "rb") as torrent:
            files["file_input"] = torrent

            files["logfiles[]"] = []
            for l in logfiles_paths:
                files["logfiles[]"].append(open(l, "rb"))
            if not len(files["logfiles[]"]):
                files.pop("logfiles[]")
                if release.items[0].format == "FLAC":
                    if not _confirm_no_logfile_not_web_flac(params):
                        return

            confirm, params = _confirm_or_edit_infos_before_upload(
                params, files
            )
            if confirm:
                return api.session.post(url, data=params, files=files)
    finally:
        for l in opened_logfiles:
            try:
                l.close()
            except Exception as e:
                LOGGER.error("Cannot close file")
                LOGGER.error(e)


def _build_descr_from_titles(release):
    description = []
    for i in release.items:
        description.append("{}{} {} {}".format(
            str(i.disc) + "-" if i.disctotal > 0 else "",
            i.track, i.title, "{:.0f}:{:02.0f}".format(*divmod(i.length, 60))
        ))

    return "\n".join(description)


def _get_release_infos_to_upload(release):
    uploading_datas = {}
    first_item = release.items[0]

    uploading_datas["title"] = release.cur_album
    uploading_datas["releasetype"] = (
        MEDIA_TYPE_SEARCH_MAP.get(first_item["albumtype"], 21)
    )
    uploading_datas["year"] = first_item["year"]
    release_tags = TAGS_SEARCH_MAP.get(first_item["genre"].lower(), None)
    if release_tags:
        uploading_datas["tags"] = release_tags

    uploading_datas = _fill_infos_format(first_item, uploading_datas)

    if first_item["albumdisambig"]:
        uploading_datas = _fill_infos_remaster(first_item, uploading_datas)

    uploading_datas["media"] = (
        MEDIA_SEARCH_MAP.get(first_item["media"].lower(), "CD")
    )

    return uploading_datas


def _fill_infos_format(release_item, uploading_datas):
    release_format = release_item.format
    if release_format == "MP3":
        uploading_datas["format"] = "MP3"
        uploading_datas["bitrate"] = str(
            numeric_bitrate_to_gazelle_bitrate(release_item.bitrate)
        )
    elif release_format == "FLAC":
        uploading_datas["format"] = (
            "FLAC 24bit" if release_item.bitdepth == 24 else "FLAC"
        )
        uploading_datas["bitrate"] = "Lossless"

    return uploading_datas


def _fill_infos_remaster(release_item, uploading_datas):
    uploading_datas["remaster"] = 1
    uploading_datas["remaster_year"] = str(release_item.year)
    uploading_datas["year"] = str(release_item.original_year)
    uploading_datas["remaster_title"] = str(
        release_item["albumdisambig"]
    ).title()
    uploading_datas["remaster_record_label"] = str(
        release_item["label"]
    ).title()

    if release_item["catalognum"]:
        uploading_datas["remaster_catalogue_number"] = (
            release_item["catalognum"]
        )

    return uploading_datas


def _confirm_no_logfile_not_web_flac(params):
    """
    Gazelle trackers require a logfile for lossless releases

    If no logfile is indicated, ask if the user wants to change the release
    type to "web" (no logfile required), ignore the lack of logfile and
    continue the upload or cancel it

    :returns continue: boolean defining if resuming or not the upload
    """
    default = "1"
    choice = input(
        "No logfile is used with a not web release:\n"
        "   [1] Change the release type to WEB\n"
        "    2  Ignore and upload\n"
        "    3  Cancel\n\n"
        "Choice: "
    ) or default
    print()

    if choice == "1":
        params["media"] = "WEB"
        return True
    elif choice == "2":
        return True
    elif choice == "3":
        return False
    else:
        print("Wrong option, please retry…")
        return _confirm_no_logfile_not_web_flac(params)


def _confirm_or_edit_infos_before_upload(params, files):
    """
    Show infos about the current upload and confirm

    :returns continue: boolean defining if resuming or not the upload
    """
    print(" Summarize:\n============\n")
    _show_upload_details(params, files)
    print()

    default = "y"
    choice = input("Confirm the upload [Y/e (edit)/n]: ") or default
    print()

    if choice.lower() in ("e", "edit"):
        params_json = editor.edit(
            contents=json.dumps(
                params, sort_keys=True, indent=4, separators=(",", ": ")
            ).encode()
        )
        try:
            params = json.loads(params_json)
        except Exception as e:
            LOGGER.error("Error when parsing edited info: {}".format(e))
        return _confirm_or_edit_infos_before_upload(params, files)

    return (
        choice.lower() in ("y", "yes"),
        params
    )


def _show_upload_details(params, files):
    default = "Undefined"

    def print_param_or_default(descr, param):
        print("{}: {}".format(descr, params.get(param, default)))

    def print_files_param_file_path(descr, param):
        if files.get(param, None):
            f_name = getattr(files[param], "name", default)
        else:
            f_name = default
        print("{}: {}".format(descr, f_name))

    print_param_or_default("Artist(s)", "artists[]")
    print_param_or_default("Title", "title")
    print_param_or_default("Type", "releasetype")
    print_param_or_default("Year", "year")
    print_param_or_default("Tags", "tags")
    print()
    print_param_or_default("Format", "format")
    print_param_or_default("Bitrate", "bitrate")
    print()
    if params.get("remaster", 0) == 1:
        print("Remaster: Yes")
        print_param_or_default("Remaster year", "remaster_year")
        print_param_or_default("Remaster title", "remaster_title")
        print_param_or_default("Remaster label", "remaster_record_label")
        print_param_or_default("Catalogue number", "remaster_catalogue_number")
        print()
    for l in files.get("logfiles[]", []):
        print("{}: {}".format("Logfile: ", l.name))
    print_files_param_file_path("Torrent", "file_input")
    print()
    print_param_or_default("Description", "album_desc")


def numeric_bitrate_to_gazelle_bitrate(num_bitrate):
    bitrate_in_kb = int(num_bitrate/1000)
    if bitrate_in_kb == 320:
        return "320"
    elif bitrate_in_kb == 256:
        return "256"
    elif 224 < bitrate_in_kb <= 320:
        return "V0 (VBR)"
    elif bitrate_in_kb == 196:
        return "196"
    elif 160 <= bitrate_in_kb <= 224:
        return "V2 (VBR)"
