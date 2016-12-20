#!/usr/bin/env python3

import beets
from beets.importer import ImportSession, ImportTaskFactory
import logging

BEETS_CONFIG = beets.config


def get_tags_for_path(path):
    import_session = ImportSession(None, logging.Handler(), path, None)
    import_session.set_config(BEETS_CONFIG["import"])
    import_task_factory = ImportTaskFactory(path, import_session)

    for t in import_task_factory.tasks():
        if type(t) is beets.importer.ImportTask:
            t.lookup_candidates()
            yield t
