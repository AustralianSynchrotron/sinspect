import os
import subprocess
from pyface.api import FileDialog, OK


xml_wildcard = 'XML (*.xml)|*.xml|' \
           'All files (*.*)|*.*'
def get_file_list_from_dialog():
    dlg = FileDialog(title='Choose files', action='open files', wildcard=xml_wildcard)
    if dlg.open() == OK:
        return dlg.paths
    return []


def get_file_from_dialog():
    dlg = FileDialog(title='Choose file', action='open', wildcard=xml_wildcard)
    if dlg.open() == OK:
        return dlg.paths[0]
    return None


def open_file_with_default_handler(filename):
    startfile(filename)


def open_file_dir_with_default_handler(filename):
    startfile(os.path.split(filename)[0])


def startfile(filename):
    try:
        os.startfile(filename)
    except:
        subprocess.Popen(['xdg-open', filename])
