#------------------------------------------------------------------------------#
# Headers
#------------------------------------------------------------------------------#

__appname__ = "azdevio-library"      #App Name (the whole operation)
__packagename__ = "azdevio-library"  #Package Name (this package)
__modulename__ = "hierarchy"         #Module Name (this file)
__version__ = "0.0.1"                #Version (semver)
__date__ = "20180714-2133"

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
import copy
import collections

import re
#------------------------------------------------------------------------------#
# Constants
#------------------------------------------------------------------------------#
KEY_SPLIT = '/'
#------------------------------------------------------------------------------#
# Classes
#------------------------------------------------------------------------------#
class HierarchyDict(collections.OrderedDict, object):
    empty_is_falsy = False #Breaks stuff if changed    
    
    def __init__(self, id_, container = None, **kwargs):
        assert type(id_) == str or hasattr(id_, "name"), \
               """<id_> must be string or have <id_>.name attribute!"""
        assert isinstance(container, HierarchyDict) or container is None, \
               """<container> must be HierarchyDict or None!"""
        
        self.__id_ = id_
        self._container = None
        self.metadata = kwargs

        if type(id_) == str:
            self._id_ = id_
        else:
            self._id_ = id_.name

        if container:
            self._container = container
            container[self._id_] = self
        
        collections.OrderedDict.__init__(self)
        
        return None

    #GETTERS AND SETTERS
    @property
    def _id(self):
        return self._id_

    @_id.setter
    def _id(self, id_):
        self.__id_ = id_
        self._id_ = id_
        return None
    
    @property
    def _ref_id(self):
        
        _ref_id = ""
            
        if self._container is None:
            _ref_id = self._id_
        else:
            _ref_id = KEY_SPLIT.join([self._container._ref_id, self._id_])
            
        return _ref_id

    @property
    def ref_id(self):
        return self._ref_id

    @property
    def container(self):
        return self._container

    @container.setter
    def container(self, container):
        assert isinstance(container, HierarchyDict) or container is None, \
               """<container> must be HierarchyDict or None!"""
        
        if self._container:
            del self._container[self._id_]

        if container is None:
            self._container = None
            return None
            
        container[self._id_] = self
        self._container = container
        return None

    @property
    def nodes(self):
        return tuple([i for i in self.values() if isinstance(i, HierarchyDict)])

    @nodes.setter
    def nodes(self, nodes):
        assert type(nodes) in [list], \
               """<nodes> must be a list!"""
        for node in self.nodes:
            node.container = None
        for node in nodes:
            node.container = self
        return None

    @property
    def contents(self):
        return tuple([i for i in self.values() if not isinstance(i, HierarchyDict)])

    #OVERRIDE OPERATORS
    def __nonzero__(self):
        if HierarchyDict.empty_is_falsy:
            if len(self.values()) < 1:
                return False
        return True
    
    def __bool__(self):
        return __nonzero__(self)

    def __copy__(self):
        #TODO
        copy_ = HierarchyDict(self._id_, self._container, **self.metadata)
        for node in self.nodes:
            continue
        return copy_

    def __deepcopy__(self):
        #TODO
        return None

    def __setitem__(self, key, item):
        if isinstance(item, HierarchyDict):
            if key != item._id_:
                raise Exception("Key must match <item>._id_")
            item._container = self
        super(HierarchyDict, self).__setitem__(key, item)
        return None

    def __delitem__(self, key):
        item = self.get(key)
        if isinstance(item, HierarchyDict):
            item._container = None
        super(HierarchyDict, self).__delitem__(key)
        return None

    def __repr__(self):
        cls = self.__class__
        nodes = [i for i in self.values() if isinstance(i, HierarchyDict)]
        values = [i for i in self.values() if not isinstance(i, HierarchyDict)]
        return "<{0} {1} nodes:{2} contents:{3}/>".format(cls.__name__, self._ref_id, len(nodes), len(values))

    #OVERRIDE METHODS
    def clear(self):
        for node in self.values():
            node.container = None
        super(HierarchyDict, self).clear()
        return None

    def copy(self):
        return self.__copy__()

    #CORE METHODS
    def _recurse(self, function, _accumulator = collections.OrderedDict()):
        """Recursive function that accumulates result values from a given function
        for all child nodes and values. <function> takes 3 arguments, (key, value, and container)
        <_accumulator> is passed recursively.
        WARNING: Should not be called directly. <_accumulator> is a mutable default value, use
        self.recurse instead."""

        _accumulator[self._ref_id] = function(self._ref_id, self, self.container)
        
        values = [i for i in self.items() if not isinstance(i[-1], HierarchyDict)]
        nodes = [i for i in self.values() if isinstance(i, HierarchyDict)]

        for value in values:
            key = KEY_SPLIT.join([self._ref_id, value[0]])
            _accumulator[key] = function(value[0], value[-1], self)

        for node in nodes:
            node._recurse(function, _accumulator)

        return _accumulator

    def recurse(self, function, compress = True):
        """Inverts and optionally compresses results from _recurse."""
        assert hasattr(function, "__call__"), \
               "<function> must have __call__ attribute!"
        
        results = self._recurse(function, _accumulator = collections.OrderedDict())
        
        if not compress:
            return results
        items = results.items()
        for item in items:
            if item[-1] is None:
                results.pop(item[0])
            continue
        return results

    def query(self, query):
        """Scans hierarchy by regex query."""
        assert hasattr(query, "match"), \
               "<query> must be regex!"
        def query_(key, value, container):
            if query.match(key):
                return value
            return None
        results = self.recurse(query_)
        return results

    def acquire(self, query):
        """Aquires specified key indiciated by <query>.
        Key must match in entirety."""
        assert type(query) == str, \
               "<query> must be string!"

        _query = query
        query = "^{0}$".format(query)
        query = re.compile(query, re.IGNORECASE)

        results = self.query(query)
            
        if len(results) == 1:
            return results.values()[0]
        elif results:
            return results.values()
        else:
            return None

    def search(self, query):
        """Searches the hierarchy for keys matching <query>.
        Wildcards are '*' for any character."""
        assert type(query) == str, \
               "<query> must be string!"
        
        _query = query
        query = query.replace('*', ".*")
        query = re.compile(query, flags = re.IGNORECASE)
        
        results = self.query(query)
        
        return results
        

    #CONVENIENCE METHODS
    def get_content_ref_id(self, key):
        """Convienence method for getting ref_id from inside recursive function for contents."""
        return KEY_SPLIT.join([self.ref_id, key])
    
    def create_node(self, id_, **kwargs):
        sub_node = HierarchyDict(id_, container = self, **kwargs)
        self[id_] = sub_node
        return sub_node

    def remove_node(self, id_):
        del self[id_]
        return None

    def add_node(self, node):
        assert isinstance(node, HierarchyDict), \
               """<node> must be HierarchyDict or subclass!"""
        self[node._id_] = node
        return None
    
    pass
#------------------------------------------------------------------------------#
# Functions
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
# Globals
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
# Main
#------------------------------------------------------------------------------#
if __name__ == "__main__":
    pass
