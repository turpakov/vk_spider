import inspect
from importlib import import_module
from pkgutil import iter_modules
from analysis.BaseAnalysisTask import BaseAnalysisTask


def walk_modules(path):
    """
    Loads a module and all its submodules from the given module path and
    returns them. If *any* module throws an exception while importing, that
    exception is thrown back.
    For example: walk_modules('scrapy.utils')
    """

    mods = []
    mod = import_module(path)
    mods.append(mod)
    if hasattr(mod, '__path__'):
        for _, subpath, ispkg in iter_modules(mod.__path__):
            fullpath = path + '.' + subpath
            if ispkg:
                mods += walk_modules(fullpath)
            else:
                submod = import_module(fullpath)
                mods.append(submod)
    return mods

def get_classes(module):
    """
    Return list of (name, obj) of subclasses BaseAnalysisTask
    """

    classes = []
    for mod in module:
        for obj in vars(mod).values():
            if inspect.isclass(obj) and issubclass(obj, BaseAnalysisTask):
                if (obj.__name__, obj) not in classes:
                    classes.append((obj.__name__, obj))
    return classes







