#------------------------------------------------------------------------------#
# Headers
#------------------------------------------------------------------------------#

__appname__ = "skeleton-app"         #App Name (the whole operation)
__packagename__ = "skeleton-package" #Package Name (this package)
__modulename__ = "skeleton"          #Module Name (this file)
__version__ = "0.0.1"                #Version (semver)
__date__ = "20180625-2330"

__authors__ = ["Kristoffer Law"]     #Primary Authors
__credits__ = ["Kristoffer Law"]     #Bugfix submissions, minor authors
__copyright__ = "Kristoffer Law"
__license__ = "Apache 2.0"

__maintainer__ = "Kristoffer Law"
__email__ = "klaw@kslaw.me"
__status__ = "Prototype"            #Prototype, Developer, Production

#------------------------------------------------------------------------------#
# Imports
#------------------------------------------------------------------------------#
import collections
import os

import re

import hierarchy
import helpers
#------------------------------------------------------------------------------#
# Constants
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
# Functions
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
# Classes
#------------------------------------------------------------------------------#
class FSType(object):
    FOLDERS = 1
    FILES = 2
    ALL = 3

class FSObject(object):
    WINDOWS_INVALID_CHARS = re.compile(r"""[<>:"|?*]+""")
    WINDOWS_INVALID_FILE_CHARS = re.compile(r"""[/\\]+""")
    @staticmethod
    def _keyword_parser(name):
        """Locates keywords (Blah), keyvalues ((key value)), and
        description (all text after a second '-') in file or directory names."""
        assert type(name) == str, \
               """<name> must be string!"""
        
        base = ""
        keywords = []
        keyvalues = collections.OrderedDict()
        description = ""
        ext = None
        
        if os.path.extsep in name:
            ext = os.path.extsep + name.split(os.path.extsep)[-1]
            name = name[0:name.rindex(os.path.extsep)]

        pattern = r"""(\(\S* [^\(]*\))"""
        pattern = re.compile(pattern)
        
        if not '-' in name:
            base = name.strip()
            return (base,keywords,keyvalues,description,ext)
        
        name_parts = name.split('-')
        base = name_parts[0].strip()

        if len(name_parts) > 2:
            description = "-".join(name_parts[2:])
            description = description.strip()

        components = helpers.compress_spaces(name_parts[1])
        components = components.strip()
        
        for match in pattern.finditer(components):
            match = match.group(0)
            components = components.replace(match, "")
            match = match.replace('(', "")
            match = match.replace(')', "")
            match_parts = match.split(' ')
            keyvalues[match_parts[0]] = " ".join(match_parts[1:])
            continue

        components = components.strip()
        keywords = components.split(' ')

        return (base,keywords,keyvalues,description,ext)
        
    def __init__(self, path, exists = True):
        assert type(path) in [str], \
               """<path> must be string!"""
        assert not FSObject.WINDOWS_INVALID_CHARS.match(path), \
               """Invalid characters detected in <path>!"""
        basename = os.path.basename(path)
        assert not FSObject.WINDOWS_INVALID_FILE_CHARS.match(basename), \
               """Invalid characters detected in <path> (filename)!"""
        
        if exists:
            assert os.path.exists(path), \
                   """<path> not found!"""
        else:
            assert not os.path.exists(path), \
                   """<path> exists!"""

        self.path = path
        self.full_name = basename
        self.folder = os.path.dirname(path)
        self.subclass_hooks = {}

        metadata = FSObject._keyword_parser(self.full_name)
        self.core_name = metadata[0]
        self.key_words = metadata[1]
        self.key_values = metadata[2]
        self.description = metadata[3]
        self.ext = metadata[4]

        return None

    def exists(self):
        if os.path.exists(self.path):
            return True
        return False

class WalkClassifier(object):
    def __init__(self, folder_classes, file_classes):
        CLASS_HOOK_TOKEN = "_{0}__CLASS_HOOKS"

        self.folder_classes = folder_classes
        self.file_classes = file_classes

        self.folder_hooks = collections.OrderedDict()
        self.file_hooks = collections.OrderedDict()

        for cls in folder_classes:
            cls_hook_name = CLASS_HOOK_TOKEN.format(cls.__name__)
            cls_hooks = getattr(cls,cls_hook_name,())
            cls_hooks = {k:cls for k in cls_hooks}
            self.folder_hooks.update(cls_hooks)
            continue

        for cls in file_classes:
            cls_hook_name = CLASS_HOOK_TOKEN.format(cls.__name__)
            cls_hooks = getattr(cls,cls_hook_name,())
            cls_hooks = {k:cls for k in cls_hooks}
            self.file_hooks.update(cls_hooks)
            continue
        
        return None
    
    def __call__(self, path):
        if os.path.isfile(path):
            for hook, cls in self.file_hooks.items():
                if hasattr(hook, "__call__"):
                    if hook(path):
                        return cls
                    pass
                if hasattr(hook, "match"):
                    if hook.match(path):
                        return cls
                    pass
                if hook in path:
                    return cls
                continue
        if os.path.isdir(path):
            for hook, cls in self.folder_hooks.items():
                if hasattr(hook, "__call__"):
                    if hook(path):
                        return cls
                    pass
                if hasattr(hook, "match"):
                    if hook.match(path):
                        return cls
                    pass
                if hook in path:
                    return cls
                continue
        return None
        

class File(FSObject):
    def __init__(self, path, exists = True):
        cls = self.__class__
        FSObject.__init__(self, path, exists)

        self.file_name = self.core_name
        if self.ext:
            self.file_ext = self.ext.replace(os.path.extsep, "")
        else:
            self.file_ext = ""
            
        return None

    def __repr__(self):
        return "<{0} {1}/>".format(self.__class__.__name__, self.core_name)

class Folder(FSObject, hierarchy.HierarchyDict):
    def __init__(self, path, exists = True):
        FSObject.__init__(self, path, exists)
        hierarchy.HierarchyDict.__init__(self, self.full_name)
        
        return None

    def __repr__(self):
        return_ = hierarchy.HierarchyDict.__repr__(self)
        return_ = return_.replace("nodes", "folders")
        return_ = return_.replace("contents", "files")
        return return_

    def create(self):
        assert not os.path.exists(self.path), \
               """Folder instance already exists!"""
        os.mkdir(self.path)
        self.exists = True
        return True

    def create_subfolder(self, name):
        """Creates a subfolder with <name>. Must not already exist in filesystem."""
        assert os.path.exists(self.path), \
               """Folder instance does not exist, cannot creat subfolder!"""
        sub_folder_path = os.path.join(self.path, name)
        assert not os.path.exists(sub_folder_path), \
               """<name> already exists!"""
        sub_folder = Folder(sub_folder_path, False)
        sub_folder.container = self
        sub_folder.create()
        return sub_folder
        
    def scan(self, walk_classifier = None):
        """Scans only top folder, only loading files, not folders."""
        assert self.exists(), \
               "Must exist before scanning!"
        
        for obj in os.listdir(self.path):
            path = os.path.join(self.path, obj)
            if os.path.isfile(path):
                if walk_classifier:
                    cls = walk_classifier(path)
                    if cls is None: cls = File
                else:
                    cls = File
                file_ = cls(path)
                self[file_.full_name] = file_
                continue
            if os.path.isdir(path):
                if walk_classifier:
                    cls = walk_classifier(path)
                    if cls is None: cls = Folder
                else:
                    cls = Folder
                folder = cls(path)
                self[folder.full_name] = folder
                continue
        return None

    def walk(self, walk_classifier = None):
        assert self.exists(), \
               """Must exist before walking!"""
        
        self.scan(walk_classifier)
        subfolders = [i for i in self.values() if isinstance(i, Folder)]
        for subfolder in subfolders:
            subfolder.walk(walk_classifier)
        
        return None

    def gather_file_exts(self):
        """Gathers all file extensions present in sub folders into a list."""
        def gather_exts_(key, value, container):
            if not isinstance(value, File):
                return None
            return value.file_ext
        results = self.recurse(gather_exts_)
        results = list(set(results.values()))
        return results

    def purge(self, file_types):
        """Purges all files from sub folders if not file.file_ext in <file_types>"""
        assert type(file_types) == list, \
               "<file_types> must be list!"
        def purge_(key, value, container):
            if not isinstance(value, File):
                return None
            if not value.file_ext in file_types:
                container.pop(key)
                return True
            return None
        results = self.recurse(purge_)
        return results
        
        
    
#------------------------------------------------------------------------------#
# Globals
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
# Main
#------------------------------------------------------------------------------#
if __name__ == "__main__":
    pass
