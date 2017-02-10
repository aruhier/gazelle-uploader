#!/usr/bin/env python3

from . import gazelle_api


def connect_api(func):
    """
    Configure the gazelle API and start a connection

    Call the sent function by sending the api object as `api`
    """
    def func_wrapper(*args, **kwargs):
        api = gazelle_api.configure_api_and_connect()
        return func(*args, api=api, **kwargs)

    return func_wrapper


def for_each_path_from_args(func):
    def func_wrapper(parsed_args, *args, **kwargs):
        paths = parsed_args.releases
        return [func(parsed_args, *args, path=p, **kwargs) for p in paths]

    return func_wrapper
