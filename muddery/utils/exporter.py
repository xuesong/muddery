"""
This module imports data from files to db.
"""

from __future__ import print_function

import os
import tempfile
import zipfile
from django.apps import apps
from django.conf import settings
from evennia.utils import logger
from muddery.utils.exception import MudderyError
from muddery.utils import writers


def get_header(model_name):
    """
    Get a model's header.
    """
    # get model
    model_obj = apps.get_model(settings.WORLD_DATA_APP, model_name)
    return model_obj._meta.fields


def get_lines(model_name):
    """
    Import data from a data file to the db model

    Args:
        file_name: (string) file's name
        model_name: (string) db model's name.
    """
    # get model
    model_obj = apps.get_model(settings.WORLD_DATA_APP, model_name)
    fields = model_obj._meta.fields
    yield [field.name for field in fields]

    # get records
    for record in model_obj.objects.all():
        line = [str(record.serializable_value(field.name)) for field in fields]
        yield line


def export_file(filename, model_name, file_type=None):
    """
    Export a table to a csv file.
    """
    if not file_type:
        # Get file's extension name.
        file_type = os.path.splitext(filename)[1].lower()
        if len(file_type) > 0:
            file_type = file_type[1:]

    writer = None
    all_writers = writers.get_writers()
    for w in all_writers:
        if file_type == w.file_type:
            writer = w(filename)
            break

    if not writer:
        print("Can not export file %s" % filename)
        return

    for line in get_lines(model_name):
        writer.writeln(line)

    writer.save()


def export_zip_all(file, file_type=None):
    """
    Export all tables to a zip file which contains a group of csv files.
    """
    if not file_type:
        # Set default file type.
        file_type = "csv"

    # Get tempfile's name.
    temp = tempfile.mktemp()

    try:
        archive = zipfile.ZipFile(file, 'w', zipfile.ZIP_DEFLATED)

        # get model names
        app_config = apps.get_app_config(settings.WORLD_DATA_APP)
        for model in app_config.get_models():
            model_name = model._meta.object_name
            export_file(temp, model_name, file_type)
            filename = model_name + "." + file_type
            archive.write(temp, filename)
    finally:
        os.remove(temp)


def export_resources(file):
    """
    Export all resource files to a zip file.
    """
    dir_name = settings.MEDIA_ROOT
    dir_length = len(dir_name)

    archive = zipfile.ZipFile(file, 'w', zipfile.ZIP_DEFLATED)   
    for root, dirs, files in os.walk(dir_name):
        for file in files:
            if file[:1] == '.':
                continue

            full_path = os.path.join(root, file)
            file_name = full_path[dir_length:]
            archive.write(full_path, file_name)
