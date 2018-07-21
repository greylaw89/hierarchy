# hierarchy
Hierarchy Dict for Python
Extends Pythons built-in collections.OrderedDict to HierarchyDict, allowing recursive functions that accept (key, value, container) arguments, query by regex, search by string, and acquire by ref id, which is generated based off the KEY_SPLIT constant, defaulted to '/'.

E.g. "USA/CA/Kern/Bakersfield/hart-park" would represent a value referenced by a key (hart-park) contained in a HierarchyDict (Bakersfield), itself contained in another HierarchyDict (Kern), etc until reaching the top level (USA).
