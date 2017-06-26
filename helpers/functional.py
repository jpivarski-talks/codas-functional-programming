#### Please ignore the man behind the curtain...
#### This is just a hack to add new methods to Python's built-in types.

import ctypes

if hasattr(ctypes.pythonapi, "Py_InitModule4_64"):
    Py_ssize_t = ctypes.c_int64
else:
    Py_ssize_t = ctypes.c_int

class PyObject(ctypes.Structure): pass
PyObject._fields_ = [("ob_refcnt", Py_ssize_t), ("ob_type", ctypes.POINTER(PyObject))]

class SlotsPointer(PyObject):
    _fields_ = [("dict", ctypes.POINTER(PyObject))]

def proxy_builtin(cls):
    name = cls.__name__
    slots = getattr(cls, "__dict__", name)

    pointer = SlotsPointer.from_address(id(slots))
    namespace = {}

    ctypes.pythonapi.PyDict_SetItem(
        ctypes.py_object(namespace),
        ctypes.py_object(name),
        pointer.dict
    )

    return namespace[name]
    
#### Define and attach functional methods to the Python "list" type.

def sizer(lst):
    """
    Return the length of the list.
    
    Example: [1, 2, 3, 4, 5].size == 5
    
    (For convenience, since everything else is attached at the end of a chain of methods.)
    """
    return len(lst)

def taker(lst):
    """
    Return the first n elements of the list or generator.
    
    Example: [1, 2, 3, 4, 5].take(3) == [1, 2, 3]
    """
    if isinstance(lst, list):
        out = lambda n: lst[:n]
    else:
        def gen(n):
            for i, x in enumerate(lst):
                yield x
                if i + 1 >= n: break
        out = lambda n: list(gen(n))
    out.func_name = "[...].take"
    out.__doc__ = taker.__doc__
    return out

def mapper(lst):
    """
    Apply a given function to each element of this list or generator.
    
    The function must take one argument.
    
    Examples: [1, 2, 3, 4, 5].map(f) == [f(1), f(2), f(3), f(4), f(5)]
              [1, 2, 3, 4, 5].map(lambda x: x + 100) == [101, 102, 103, 104, 105]
    """
    if isinstance(lst, list):
        out = lambda f: [f(x) for x in lst]
    else:
        out = lambda f: (f(x) for x in lst)
    out.func_name = "[...].map"
    out.__doc__ = mapper.__doc__
    return out

def flattener(lst):
    """
    Turn a list-of-lists into a list of all elements. Only reduces one level of structure.
        
    Examples: [[1, 2], [3, 4, 5]].flatten == [1, 2, 3, 4, 5]
              [[1, 2], [3, [4, 5]]].flatten == [1, 2, 3, [4, 5]
    """
    if isinstance(lst, list):
        return sum(lst, [])
    else:
        def gen():
            for x in lst:
                for y in x:
                    yield y
        return gen()

def flatmapper(lst):
    """
    Same as [...].map(f).flatten, but these two operations are frequently done together.
    
    The function must take one argument.
    
    In general: [...].flatmap(f) == [...].map(f).flatten
    
    Example: [1, 2, 3, 4, 5].flatmap(lambda x: [x, x + 100]) == [1, 101, 2, 102, 3, 103, 4, 104, 5, 105]
    
    Flatmap is a very general operation. You can use it to expand a table, as above, or to map and filter
    at the same time. (In the theory of monads, "flatmap" is the fundamental "bind" operation.)
    
    Example: [1, 2, 3, 4, 5].flatmap(lambda x: [100 + x] if x > 2 else []) == [103, 104, 105]
    
    You might encounter this when you want to compute something for all particles in each event, but also
    handle the case when there are no particles after cuts. In that case, "flatmap" instead of "map" and
    return a singleton list [result] when you have a result and an empty list [] when you don't.
    """
    if isinstance(lst, list):
        out = lambda f: sum((f(x) for x in lst), [])
    else:
        def gen(f):
            for x in lst:
                for y in f(x):
                    yield y
        out = gen
    out.func_name = "[...].flatmap"
    out.__doc__ = flatmapper.__doc__
    return out

def filterer(lst):
    """
    Apply a given function to each element of the list and return only those that return True.
    
    The function must take one argument and return True or False.
    
    Example: [1, 2, 3, 4, 5].filter(lambda x: x > 2) == [3, 4, 5]
    """
    if isinstance(lst, list):
        out = lambda f: [x for x in lst if f(x)]
    else:
        def gen(f):
            for x in lst:
                if f(x):
                    yield x
        out = gen
    out.func_name = "[...].filter"
    out.__doc__ = filterer.__doc__
    return out
    
def reducer(lst):
    """
    Apply a given function to each element and a running tally to produce a single result.
    
    The function must take two arguments. The first may be an element from the list or a tally.
    The second will always be from the list.
    
    Examples: [1, 2, 3, 4, 5].reduce(f) == f(f(f(f(1, 2), 3), 4), 5)
              [1, 2, 3, 4, 5].reduce(lambda x, y: x + y) == 15
    """
    out = lambda f: reduce(f, lst)
    out.func_name = "[...].reduce"
    out.__doc__ = reducer.__doc__
    return out

def aggregator(lst):
    """
    Same as reduce, except start the aggregation on a given zero element.
    
    The function must take two arguments. The first will always be a tally and the second from the list.
    
    Examples: [1, 2, 3, 4, 5].aggregate(f, 0) == f(f(f(f(f(0, 1), 2), 3), 4), 5)
              [1, 2, 3, 4, 5].aggregate(lambda x, y: x + y, 0) == 15
              ["a", "b", "c"].aggregate(lambda x, y: x + y, "") == "abc"
    """
    out = lambda f, zero: reduce(f, lst, zero)
    out.func_name = "[...].aggregate"
    out.__doc__ = aggregator.__doc__
    return out

def reducerright(lst):
    """
    Same as reduce, except start the nesting on the right and work left.
    
    The function must take two arguments. The second may be an element from the list or a tally.
    The first will always be from the list.
    
    Example: [1, 2, 3, 4, 5].reduceright(f) == f(1, f(2, f(3, f(4, 5))))
    """
    out = lambda f: reduce(lambda a, b: f(b, a), reversed(lst))
    out.func_name = "[...].reduceright"
    out.__doc__ = reducerright.__doc__
    return out

def aggregatorright(lst):
    """
    Same as aggregate, except start the nesting on the right and work left.
    
    The function must take two arguments. The second will always be a tally and the first from the list.
    
    Example: [1, 2, 3, 4, 5].aggregateright(f, 0) == f(1, f(2, f(3, f(4, f(5, 0)))))
    """
    out = lambda f, zero: reduce(lambda a, b: f(b, a), reversed(lst), zero)
    out.func_name = "[...].aggregateright"
    out.__doc__ = aggregatorright.__doc__
    return out

def pairser(lst):
    """
    Apply a given function to pairs of elements without repetition (in either order) or duplicates.
    
    The function must take two arguments. Both will always be elements from the list.
    
    If you think of the input list as a vector X, this acts on the upper trianglular part of the
    outer product of X with X (not including diagonal).
    
    Alternatively, it's what you would get from these nested loops:
    
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):   # j starts at i + 1
                f(lst[i], lst[j])
    
    Example: [1, 2, 3, 4, 5].pairs(lambda x, y: [x, y]) == [[1, 2], [1, 3], [1, 4], [1, 5],
                                                                    [2, 3], [2, 4], [2, 5],
                                                                            [3, 4], [3, 5],
                                                                                    [4, 5]]
    
    Use this when you want to loop over pairs of distinct pairs of elements from a single list.
    
    Contrast with "table", which is like a nested loop over several lists, for all elements.
    """
    out = lambda f: [f(x, y) for i, x in enumerate(lst) for y in lst[i + 1:]]
    out.func_name = "[...].pairs"
    out.__doc__ = pairser.__doc__
    return out

def tabler(lsts):
    """
    Apply a given function to all combinations of elements from all input lists.
    
    The function must take as many arguments as you have lists, and each will be an element from
    each list.
    
    If you think of the input lists as vectors X, Y, Z, etc., this acts on each element of the
    outer product of X with Y with Z, etc.
    
    Alternatively, it's what you would get from these nested loops:
    
        for x in lst_x:
            for y in lst_y:
                for z in lst_z:
                    f(x, y, z)
    
    Examples: [[100, 200], [1, 2, 3]].table(lambda x, y: x + y) == [101, 102, 103, 201, 202, 203]
    
              [[100, 200], [10, 20], [1, 2]].table(lambda x, y, z: x + y + z) == [
                  111, 112, 121, 122, 211, 212, 221, 222]

    To illustrate the difference between table and pairs, consider the following:

        [1, 2, 3].pairs(lambda x, y: [x, y]) == [[1, 2], [1, 3],
                                                         [2, 3]]
        
        [[1, 2, 3], [1, 2, 3]].table(lambda x, y: [x, y]) == [[1, 1], [1, 2], [1, 3],
                                                              [2, 1], [2, 2], [2, 3],
                                                              [3, 1], [3, 2], [3, 3]]
    """
    def buildargs(first, *rest):
        if len(rest) == 0:
            return [[x] for x in first]
        else:
            return [[x] + y for x in first for y in buildargs(*rest)]

    if len(lsts) < 2:
        raise TypeError("table requires at least two arguments")
    else:
        first = lsts[0]
        rest = lsts[1:]
        out = lambda f: [f(*args) for args in buildargs(first, *rest)]
    out.func_name = "[[...], [...], ...].table"
    out.__doc__ = tabler.__doc__
    return out

def zipper(lsts):
    """
    Apply a function to the ith element of each list, for all i.
    
    The function must take as many arguments as there are lists, and each will be an element from
    each list.
    
    This works just like the built-in Python zip, but applies the function to its results:
    
        for x, y, z in zip(lst_x, lst_y, lst_z):
            f(x, y, z)
    
    Example: [[1, 2, 3], ["a", "b", "c"], [101, 102, 103]].zip(lambda x, y, z: (x, y, z)) == [
                 (1, "a", 101), (2, "b", 102), (3, "c", 103)]
    """
    if len(lsts) < 2:
        raise TypeError("zip requires at least two arguments")
    else:
        out = lambda f: [f(*args) for args in zip(*lsts)]
    out.func_name = "[[...], [...], ...].zip"
    out.__doc__ = zipper.__doc__
    return out

# attach the methods                                               force Python to notice
proxy_builtin(list)["size"] = property(sizer);                     hasattr([], "size")
proxy_builtin(list)["take"] = property(taker);                     hasattr([], "take")
proxy_builtin(list)["map"] = property(mapper);                     hasattr([], "map")
proxy_builtin(list)["flatten"] = property(flattener);              hasattr([], "flatten")
proxy_builtin(list)["flatmap"] = property(flatmapper);             hasattr([], "flatmap")
proxy_builtin(list)["filter"] = property(filterer);                hasattr([], "filter")
proxy_builtin(list)["reduce"] = property(reducer);                 hasattr([], "reduce")
proxy_builtin(list)["aggregate"] = property(aggregator);           hasattr([], "aggregate")
proxy_builtin(list)["reduceright"] = property(reducerright);       hasattr([], "reduceright")
proxy_builtin(list)["aggregateright"] = property(aggregatorright); hasattr([], "aggregateright")
proxy_builtin(list)["pairs"] = property(pairser);                  hasattr([], "pairs")
proxy_builtin(list)["table"] = property(tabler);                   hasattr([], "table")
proxy_builtin(list)["zip"] = property(zipper);                     hasattr([], "zip")

# Verify that they all work (and provide examples of their use).

assert [1, 2, 3, 4, 5].take(3) == [1, 2, 3]

assert [1, 2, 3, 4, 5].map(lambda x: 100 + x) == [101, 102, 103, 104, 105]

assert [[1, 2], [3, 4, 5]].flatten == [1, 2, 3, 4, 5]
assert [[1, 2], [3, [4, 5]]].flatten == [1, 2, 3, [4, 5]]

assert [1, 2, 3, 4, 5].map(lambda x: [x, x + 100]) == [[1, 101], [2, 102], [3, 103], [4, 104], [5, 105]]
assert [1, 2, 3, 4, 5].map(lambda x: [x, x + 100]).flatten == [1, 101, 2, 102, 3, 103, 4, 104, 5, 105]
assert [1, 2, 3, 4, 5].flatmap(lambda x: [x, x + 100]) == [1, 101, 2, 102, 3, 103, 4, 104, 5, 105]
assert [1, 2, 3, 4, 5].flatmap(lambda x: [100 + x] if x > 2 else []) == [103, 104, 105]

assert [1, 2, 3, 4, 5].filter(lambda x: x > 2) == [3, 4, 5]

assert [1, 2, 3, 4, 5].reduce(lambda x, y: x + y) == 15
assert [1, 2, 3, 4, 5].reduce(lambda x, y: [x, y]) == [[[[1, 2], 3], 4], 5]

assert ["a", "b", "c"].aggregate(lambda x, y: x + y, "") == "abc"
assert [1, 2, 3, 4, 5].aggregate(lambda x, y: [x, y], []) == [[[[[[], 1], 2], 3], 4], 5]

assert [1, 2, 3, 4, 5].reduceright(lambda x, y: [x, y]) == [1, [2, [3, [4, 5]]]]

assert [1, 2, 3, 4, 5].aggregateright(lambda x, y: [x, y], []) == [1, [2, [3, [4, [5, []]]]]]

assert [1, 2, 3, 4, 5].pairs(lambda x, y: [x, y]) == [[1, 2], [1, 3], [1, 4], [1, 5], [2, 3],
                                                      [2, 4], [2, 5], [3, 4], [3, 5], [4, 5]]

assert [[100, 200], [1, 2, 3]].table(lambda x, y: x + y) == [101, 102, 103, 201, 202, 203]
assert [[100, 200], [10, 20], [1, 2]].table(lambda x, y, z: x + y + z) == [111, 112, 121, 122, 211, 212, 221, 222]
assert [[1, 2, 3, 4, 5], ["a", "b"]].table(lambda x, y: [x, y]) == [
    [1, "a"], [1, "b"], [2, "a"], [2, "b"], [3, "a"], [3, "b"], [4, "a"], [4, "b"], [5, "a"], [5, "b"]]
assert [1, 2, 3].pairs(lambda x, y: [x, y]) == [[1, 2], [1, 3], [2, 3]]
assert [[1, 2, 3], [1, 2, 3]].table(lambda x, y: [x, y]) == [[1, 1], [1, 2], [1, 3],
                                                             [2, 1], [2, 2], [2, 3],
                                                             [3, 1], [3, 2], [3, 3]]

assert [[1, 2, 3], ["a", "b", "c"], [101, 102, 103]].zip(lambda x, y, z: [x, y, z]) == [
    [1, "a", 101], [2, "b", 102], [3, "c", 103]]

def example_generator():
    yield None

example_generator = example_generator()

proxy_builtin(type(example_generator))["take"] = property(taker);         hasattr(example_generator, "take")
proxy_builtin(type(example_generator))["map"] = property(mapper);         hasattr(example_generator, "map")
proxy_builtin(type(example_generator))["flatten"] = property(flattener);  hasattr(example_generator, "flatten")
proxy_builtin(type(example_generator))["flatmap"] = property(flatmapper); hasattr(example_generator, "flatmap")
proxy_builtin(type(example_generator))["filter"] = property(filterer);    hasattr(example_generator, "filter")

from histogrammar import *
from histogrammar.tutorial import cmsdata
import threading

class Events(object):
    class Iterator(object):
        def __init__(self, parent):
            self.parent = parent
            self.index = 0
        
        def __next__(self):
            if self.index >= len(self.parent.generated):
                raise StopIteration
            self.index += 1
            return self.parent.generated[self.index - 1]
        
        next = __next__
    
    class Filler(threading.Thread):
        def __init__(self, parent):
            super(Events.Filler, self).__init__()
            self.parent = parent
            self.daemon = True
        
        def run(self):
            event_fields = ("jets", "muons", "electrons", "photons", "met", "numPrimaryVertices")
            jet_fields = ("px", "py", "pz", "p", "pt", "mass", "eta", "phi", "E", "btag")
            muon_fields = ("px", "py", "pz", "p", "pt", "mass", "eta", "phi", "E", "q", "iso")
            electron_fields = ("px", "py", "pz", "p", "pt", "mass", "eta", "phi", "E", "q", "iso")
            photon_fields = ("px", "py", "pz", "p", "pt", "mass", "eta", "phi", "E", "iso")
            met_fields = ("px", "py", "pt")
            while len(self.parent.generated) < 100000:
                event = next(self.parent.generator)
                event.fields = event_fields
                for jet in event.jets:
                    jet.fields = jet_fields
                for muon in event.muons:
                    muon.fields = muon_fields
                for electron in event.electrons:
                    electron.fields = electron_fields
                for photon in event.photons:
                    photon.fields = photon_fields
                event.met.fields = met_fields
                self.parent.generated.append(event)
    
    def __init__(self):
        self.generator = cmsdata.EventIterator()
        self.generated = []
        self.filler = self.Filler(self)
        self.filler.start()

    def __iter__(self):
        return self.Iterator(self)
    
    @property
    def take(self):
        return taker(self)
    
    @property
    def map(self):
        return mapper(self)
    
    @property
    def flatten(self):
        return flattener(self)
    
    @property
    def flatmap(self):
        return flatmapper(self)
    
    @property
    def filter(self):
        return filterer(self)

events = Events()

def MoreEvents():
    return cmsdata.EventIterator()

def histogrammarMethod(cls):
    def generatorProperty(lst):
        def hargs(*args, **kwds):
            h = cls(*args, **kwds)
            for x in lst:
                h.fill(x)
            return h
        hargs.func_name = "[...]." + cls.__name__.replace("UntypedLabel", "Bundle")
        hargs.__doc__ = cls.__doc__.replace("UntypedLabel", "Bundle")
        return hargs
    return generatorProperty

# rename UntypedLabel as "Bundle" because that's what it will be in Histogrammar specification 2.0
Bundle = UntypedLabel

proxy_builtin(list)["Average"] = property(histogrammarMethod(Average));                hasattr(list, "Average")
proxy_builtin(list)["Bin"] = property(histogrammarMethod(Bin));                        hasattr(list, "Bin")
proxy_builtin(list)["Categorize"] = property(histogrammarMethod(Categorize));          hasattr(list, "Categorize")
proxy_builtin(list)["CentrallyBin"] = property(histogrammarMethod(CentrallyBin));      hasattr(list, "CentrallyBin")
proxy_builtin(list)["Label"] = property(histogrammarMethod(Label));                    hasattr(list, "Label")
proxy_builtin(list)["Bundle"] = property(histogrammarMethod(Bundle));                  hasattr(list, "Bundle")
proxy_builtin(list)["Index"] = property(histogrammarMethod(Index));                    hasattr(list, "Index")
proxy_builtin(list)["Branch"] = property(histogrammarMethod(Branch));                  hasattr(list, "Branch")
proxy_builtin(list)["Count"] = property(histogrammarMethod(Count));                    hasattr(list, "Count")
proxy_builtin(list)["Deviate"] = property(histogrammarMethod(Deviate));                hasattr(list, "Deviate")
proxy_builtin(list)["Fraction"] = property(histogrammarMethod(Fraction));              hasattr(list, "Fraction")
proxy_builtin(list)["IrregularlyBin"] = property(histogrammarMethod(IrregularlyBin));  hasattr(list, "IrregularlyBin")
proxy_builtin(list)["Minimize"] = property(histogrammarMethod(Minimize));              hasattr(list, "Minimize")
proxy_builtin(list)["Maximize"] = property(histogrammarMethod(Maximize));              hasattr(list, "Maximize")
proxy_builtin(list)["Select"] = property(histogrammarMethod(Select));                  hasattr(list, "Select")
proxy_builtin(list)["SparselyBin"] = property(histogrammarMethod(SparselyBin));        hasattr(list, "SparselyBin")
proxy_builtin(list)["Stack"] = property(histogrammarMethod(Stack));                    hasattr(list, "Stack")
proxy_builtin(list)["Sum"] = property(histogrammarMethod(Sum));                        hasattr(list, "Sum")
