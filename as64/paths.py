import os
import sys
from pathlib import Path


def base_path(relative_path=None):
    if not relative_path:
        return os.path.dirname(sys.argv[0])
    else:
        return os.path.join(os.path.dirname(sys.argv[0]), relative_path).replace('\\', '/')


def resource_path(relative_path):
    try:
        path = sys._MEIPASS
    except Exception:
        path = os.path.abspath(".")

    return os.path.join(path, relative_path).replace('\\', '/')


def absolute_path(relative_path=None):
    if not relative_path:
        return str(Path().absolute()).replace('\\', '/')
    else:
        return os.path.join(Path().absolute(), relative_path).replace('\\', '/')


def abs_to_rel(p):
    relative_path = p.replace(absolute_path(), "")

    if relative_path != p:
        return relative_path[1:]
    else:
        return p


def rel_to_abs(p):
    if not os.path.isabs(p):
        return absolute_path(p)
    else:
        return p
