# This file was automatically generated by SWIG (http://www.swig.org).
# Version 2.0.4
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.



from sys import version_info
if version_info >= (3,0,0):
    new_instancemethod = lambda func, inst, cls: _assoTests.SWIG_PyInstanceMethod_New(func)
else:
    from new import instancemethod as new_instancemethod
if version_info >= (2,6,0):
    def swig_import_helper():
        from os.path import dirname
        import imp
        fp = None
        try:
            fp, pathname, description = imp.find_module('_assoTests', [dirname(__file__)])
        except ImportError:
            import _assoTests
            return _assoTests
        if fp is not None:
            try:
                _mod = imp.load_module('_assoTests', fp, pathname, description)
            finally:
                fp.close()
            return _mod
    _assoTests = swig_import_helper()
    del swig_import_helper
else:
    import _assoTests
del version_info
try:
    _swig_property = property
except NameError:
    pass # Python < 2.2 doesn't have 'property'.
def _swig_setattr_nondynamic(self,class_type,name,value,static=1):
    if (name == "thisown"): return self.this.own(value)
    if (name == "this"):
        if type(value).__name__ == 'SwigPyObject':
            self.__dict__[name] = value
            return
    method = class_type.__swig_setmethods__.get(name,None)
    if method: return method(self,value)
    if (not static):
        self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)

def _swig_setattr(self,class_type,name,value):
    return _swig_setattr_nondynamic(self,class_type,name,value,0)

def _swig_getattr(self,class_type,name):
    if (name == "thisown"): return self.this.own()
    method = class_type.__swig_getmethods__.get(name,None)
    if method: return method(self)
    raise AttributeError(name)

def _swig_repr(self):
    try: strthis = "proxy of " + self.this.__repr__()
    except: strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)

try:
    _object = object
    _newclass = 1
except AttributeError:
    class _object : pass
    _newclass = 0


def _swig_setattr_nondynamic_method(set):
    def set_attr(self,name,value):
        if (name == "thisown"): return self.this.own(value)
        if hasattr(self,name) or (name == "this"):
            set(self,name,value)
        else:
            raise AttributeError("You cannot add attributes to %s" % self)
    return set_attr


class SwigPyIterator(object):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    def __init__(self, *args, **kwargs): raise AttributeError("No constructor defined - class is abstract")
    __repr__ = _swig_repr
    __swig_destroy__ = _assoTests.delete_SwigPyIterator
    def __iter__(self): return self
SwigPyIterator.value = new_instancemethod(_assoTests.SwigPyIterator_value,None,SwigPyIterator)
SwigPyIterator.incr = new_instancemethod(_assoTests.SwigPyIterator_incr,None,SwigPyIterator)
SwigPyIterator.decr = new_instancemethod(_assoTests.SwigPyIterator_decr,None,SwigPyIterator)
SwigPyIterator.distance = new_instancemethod(_assoTests.SwigPyIterator_distance,None,SwigPyIterator)
SwigPyIterator.equal = new_instancemethod(_assoTests.SwigPyIterator_equal,None,SwigPyIterator)
SwigPyIterator.copy = new_instancemethod(_assoTests.SwigPyIterator_copy,None,SwigPyIterator)
SwigPyIterator.next = new_instancemethod(_assoTests.SwigPyIterator_next,None,SwigPyIterator)
SwigPyIterator.__next__ = new_instancemethod(_assoTests.SwigPyIterator___next__,None,SwigPyIterator)
SwigPyIterator.previous = new_instancemethod(_assoTests.SwigPyIterator_previous,None,SwigPyIterator)
SwigPyIterator.advance = new_instancemethod(_assoTests.SwigPyIterator_advance,None,SwigPyIterator)
SwigPyIterator.__eq__ = new_instancemethod(_assoTests.SwigPyIterator___eq__,None,SwigPyIterator)
SwigPyIterator.__ne__ = new_instancemethod(_assoTests.SwigPyIterator___ne__,None,SwigPyIterator)
SwigPyIterator.__iadd__ = new_instancemethod(_assoTests.SwigPyIterator___iadd__,None,SwigPyIterator)
SwigPyIterator.__isub__ = new_instancemethod(_assoTests.SwigPyIterator___isub__,None,SwigPyIterator)
SwigPyIterator.__add__ = new_instancemethod(_assoTests.SwigPyIterator___add__,None,SwigPyIterator)
SwigPyIterator.__sub__ = new_instancemethod(_assoTests.SwigPyIterator___sub__,None,SwigPyIterator)
SwigPyIterator_swigregister = _assoTests.SwigPyIterator_swigregister
SwigPyIterator_swigregister(SwigPyIterator)

class vectorf(object):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __iter__(self): return self.iterator()
    def __init__(self, *args): 
        _assoTests.vectorf_swiginit(self,_assoTests.new_vectorf(*args))
    __swig_destroy__ = _assoTests.delete_vectorf
vectorf.iterator = new_instancemethod(_assoTests.vectorf_iterator,None,vectorf)
vectorf.__nonzero__ = new_instancemethod(_assoTests.vectorf___nonzero__,None,vectorf)
vectorf.__bool__ = new_instancemethod(_assoTests.vectorf___bool__,None,vectorf)
vectorf.__len__ = new_instancemethod(_assoTests.vectorf___len__,None,vectorf)
vectorf.pop = new_instancemethod(_assoTests.vectorf_pop,None,vectorf)
vectorf.__getslice__ = new_instancemethod(_assoTests.vectorf___getslice__,None,vectorf)
vectorf.__setslice__ = new_instancemethod(_assoTests.vectorf___setslice__,None,vectorf)
vectorf.__delslice__ = new_instancemethod(_assoTests.vectorf___delslice__,None,vectorf)
vectorf.__delitem__ = new_instancemethod(_assoTests.vectorf___delitem__,None,vectorf)
vectorf.__getitem__ = new_instancemethod(_assoTests.vectorf___getitem__,None,vectorf)
vectorf.__setitem__ = new_instancemethod(_assoTests.vectorf___setitem__,None,vectorf)
vectorf.append = new_instancemethod(_assoTests.vectorf_append,None,vectorf)
vectorf.empty = new_instancemethod(_assoTests.vectorf_empty,None,vectorf)
vectorf.size = new_instancemethod(_assoTests.vectorf_size,None,vectorf)
vectorf.clear = new_instancemethod(_assoTests.vectorf_clear,None,vectorf)
vectorf.swap = new_instancemethod(_assoTests.vectorf_swap,None,vectorf)
vectorf.get_allocator = new_instancemethod(_assoTests.vectorf_get_allocator,None,vectorf)
vectorf.begin = new_instancemethod(_assoTests.vectorf_begin,None,vectorf)
vectorf.end = new_instancemethod(_assoTests.vectorf_end,None,vectorf)
vectorf.rbegin = new_instancemethod(_assoTests.vectorf_rbegin,None,vectorf)
vectorf.rend = new_instancemethod(_assoTests.vectorf_rend,None,vectorf)
vectorf.pop_back = new_instancemethod(_assoTests.vectorf_pop_back,None,vectorf)
vectorf.erase = new_instancemethod(_assoTests.vectorf_erase,None,vectorf)
vectorf.push_back = new_instancemethod(_assoTests.vectorf_push_back,None,vectorf)
vectorf.front = new_instancemethod(_assoTests.vectorf_front,None,vectorf)
vectorf.back = new_instancemethod(_assoTests.vectorf_back,None,vectorf)
vectorf.assign = new_instancemethod(_assoTests.vectorf_assign,None,vectorf)
vectorf.resize = new_instancemethod(_assoTests.vectorf_resize,None,vectorf)
vectorf.insert = new_instancemethod(_assoTests.vectorf_insert,None,vectorf)
vectorf.reserve = new_instancemethod(_assoTests.vectorf_reserve,None,vectorf)
vectorf.capacity = new_instancemethod(_assoTests.vectorf_capacity,None,vectorf)
vectorf_swigregister = _assoTests.vectorf_swigregister
vectorf_swigregister(vectorf)

class vectori(object):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __iter__(self): return self.iterator()
    def __init__(self, *args): 
        _assoTests.vectori_swiginit(self,_assoTests.new_vectori(*args))
    __swig_destroy__ = _assoTests.delete_vectori
vectori.iterator = new_instancemethod(_assoTests.vectori_iterator,None,vectori)
vectori.__nonzero__ = new_instancemethod(_assoTests.vectori___nonzero__,None,vectori)
vectori.__bool__ = new_instancemethod(_assoTests.vectori___bool__,None,vectori)
vectori.__len__ = new_instancemethod(_assoTests.vectori___len__,None,vectori)
vectori.pop = new_instancemethod(_assoTests.vectori_pop,None,vectori)
vectori.__getslice__ = new_instancemethod(_assoTests.vectori___getslice__,None,vectori)
vectori.__setslice__ = new_instancemethod(_assoTests.vectori___setslice__,None,vectori)
vectori.__delslice__ = new_instancemethod(_assoTests.vectori___delslice__,None,vectori)
vectori.__delitem__ = new_instancemethod(_assoTests.vectori___delitem__,None,vectori)
vectori.__getitem__ = new_instancemethod(_assoTests.vectori___getitem__,None,vectori)
vectori.__setitem__ = new_instancemethod(_assoTests.vectori___setitem__,None,vectori)
vectori.append = new_instancemethod(_assoTests.vectori_append,None,vectori)
vectori.empty = new_instancemethod(_assoTests.vectori_empty,None,vectori)
vectori.size = new_instancemethod(_assoTests.vectori_size,None,vectori)
vectori.clear = new_instancemethod(_assoTests.vectori_clear,None,vectori)
vectori.swap = new_instancemethod(_assoTests.vectori_swap,None,vectori)
vectori.get_allocator = new_instancemethod(_assoTests.vectori_get_allocator,None,vectori)
vectori.begin = new_instancemethod(_assoTests.vectori_begin,None,vectori)
vectori.end = new_instancemethod(_assoTests.vectori_end,None,vectori)
vectori.rbegin = new_instancemethod(_assoTests.vectori_rbegin,None,vectori)
vectori.rend = new_instancemethod(_assoTests.vectori_rend,None,vectori)
vectori.pop_back = new_instancemethod(_assoTests.vectori_pop_back,None,vectori)
vectori.erase = new_instancemethod(_assoTests.vectori_erase,None,vectori)
vectori.push_back = new_instancemethod(_assoTests.vectori_push_back,None,vectori)
vectori.front = new_instancemethod(_assoTests.vectori_front,None,vectori)
vectori.back = new_instancemethod(_assoTests.vectori_back,None,vectori)
vectori.assign = new_instancemethod(_assoTests.vectori_assign,None,vectori)
vectori.resize = new_instancemethod(_assoTests.vectori_resize,None,vectori)
vectori.insert = new_instancemethod(_assoTests.vectori_insert,None,vectori)
vectori.reserve = new_instancemethod(_assoTests.vectori_reserve,None,vectori)
vectori.capacity = new_instancemethod(_assoTests.vectori_capacity,None,vectori)
vectori_swigregister = _assoTests.vectori_swigregister
vectori_swigregister(vectori)

class matrixi(object):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __iter__(self): return self.iterator()
    def __init__(self, *args): 
        _assoTests.matrixi_swiginit(self,_assoTests.new_matrixi(*args))
    __swig_destroy__ = _assoTests.delete_matrixi
matrixi.iterator = new_instancemethod(_assoTests.matrixi_iterator,None,matrixi)
matrixi.__nonzero__ = new_instancemethod(_assoTests.matrixi___nonzero__,None,matrixi)
matrixi.__bool__ = new_instancemethod(_assoTests.matrixi___bool__,None,matrixi)
matrixi.__len__ = new_instancemethod(_assoTests.matrixi___len__,None,matrixi)
matrixi.pop = new_instancemethod(_assoTests.matrixi_pop,None,matrixi)
matrixi.__getslice__ = new_instancemethod(_assoTests.matrixi___getslice__,None,matrixi)
matrixi.__setslice__ = new_instancemethod(_assoTests.matrixi___setslice__,None,matrixi)
matrixi.__delslice__ = new_instancemethod(_assoTests.matrixi___delslice__,None,matrixi)
matrixi.__delitem__ = new_instancemethod(_assoTests.matrixi___delitem__,None,matrixi)
matrixi.__getitem__ = new_instancemethod(_assoTests.matrixi___getitem__,None,matrixi)
matrixi.__setitem__ = new_instancemethod(_assoTests.matrixi___setitem__,None,matrixi)
matrixi.append = new_instancemethod(_assoTests.matrixi_append,None,matrixi)
matrixi.empty = new_instancemethod(_assoTests.matrixi_empty,None,matrixi)
matrixi.size = new_instancemethod(_assoTests.matrixi_size,None,matrixi)
matrixi.clear = new_instancemethod(_assoTests.matrixi_clear,None,matrixi)
matrixi.swap = new_instancemethod(_assoTests.matrixi_swap,None,matrixi)
matrixi.get_allocator = new_instancemethod(_assoTests.matrixi_get_allocator,None,matrixi)
matrixi.begin = new_instancemethod(_assoTests.matrixi_begin,None,matrixi)
matrixi.end = new_instancemethod(_assoTests.matrixi_end,None,matrixi)
matrixi.rbegin = new_instancemethod(_assoTests.matrixi_rbegin,None,matrixi)
matrixi.rend = new_instancemethod(_assoTests.matrixi_rend,None,matrixi)
matrixi.pop_back = new_instancemethod(_assoTests.matrixi_pop_back,None,matrixi)
matrixi.erase = new_instancemethod(_assoTests.matrixi_erase,None,matrixi)
matrixi.push_back = new_instancemethod(_assoTests.matrixi_push_back,None,matrixi)
matrixi.front = new_instancemethod(_assoTests.matrixi_front,None,matrixi)
matrixi.back = new_instancemethod(_assoTests.matrixi_back,None,matrixi)
matrixi.assign = new_instancemethod(_assoTests.matrixi_assign,None,matrixi)
matrixi.resize = new_instancemethod(_assoTests.matrixi_resize,None,matrixi)
matrixi.insert = new_instancemethod(_assoTests.matrixi_insert,None,matrixi)
matrixi.reserve = new_instancemethod(_assoTests.matrixi_reserve,None,matrixi)
matrixi.capacity = new_instancemethod(_assoTests.matrixi_capacity,None,matrixi)
matrixi_swigregister = _assoTests.matrixi_swigregister
matrixi_swigregister(matrixi)

class matrixf(object):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __iter__(self): return self.iterator()
    def __init__(self, *args): 
        _assoTests.matrixf_swiginit(self,_assoTests.new_matrixf(*args))
    __swig_destroy__ = _assoTests.delete_matrixf
matrixf.iterator = new_instancemethod(_assoTests.matrixf_iterator,None,matrixf)
matrixf.__nonzero__ = new_instancemethod(_assoTests.matrixf___nonzero__,None,matrixf)
matrixf.__bool__ = new_instancemethod(_assoTests.matrixf___bool__,None,matrixf)
matrixf.__len__ = new_instancemethod(_assoTests.matrixf___len__,None,matrixf)
matrixf.pop = new_instancemethod(_assoTests.matrixf_pop,None,matrixf)
matrixf.__getslice__ = new_instancemethod(_assoTests.matrixf___getslice__,None,matrixf)
matrixf.__setslice__ = new_instancemethod(_assoTests.matrixf___setslice__,None,matrixf)
matrixf.__delslice__ = new_instancemethod(_assoTests.matrixf___delslice__,None,matrixf)
matrixf.__delitem__ = new_instancemethod(_assoTests.matrixf___delitem__,None,matrixf)
matrixf.__getitem__ = new_instancemethod(_assoTests.matrixf___getitem__,None,matrixf)
matrixf.__setitem__ = new_instancemethod(_assoTests.matrixf___setitem__,None,matrixf)
matrixf.append = new_instancemethod(_assoTests.matrixf_append,None,matrixf)
matrixf.empty = new_instancemethod(_assoTests.matrixf_empty,None,matrixf)
matrixf.size = new_instancemethod(_assoTests.matrixf_size,None,matrixf)
matrixf.clear = new_instancemethod(_assoTests.matrixf_clear,None,matrixf)
matrixf.swap = new_instancemethod(_assoTests.matrixf_swap,None,matrixf)
matrixf.get_allocator = new_instancemethod(_assoTests.matrixf_get_allocator,None,matrixf)
matrixf.begin = new_instancemethod(_assoTests.matrixf_begin,None,matrixf)
matrixf.end = new_instancemethod(_assoTests.matrixf_end,None,matrixf)
matrixf.rbegin = new_instancemethod(_assoTests.matrixf_rbegin,None,matrixf)
matrixf.rend = new_instancemethod(_assoTests.matrixf_rend,None,matrixf)
matrixf.pop_back = new_instancemethod(_assoTests.matrixf_pop_back,None,matrixf)
matrixf.erase = new_instancemethod(_assoTests.matrixf_erase,None,matrixf)
matrixf.push_back = new_instancemethod(_assoTests.matrixf_push_back,None,matrixf)
matrixf.front = new_instancemethod(_assoTests.matrixf_front,None,matrixf)
matrixf.back = new_instancemethod(_assoTests.matrixf_back,None,matrixf)
matrixf.assign = new_instancemethod(_assoTests.matrixf_assign,None,matrixf)
matrixf.resize = new_instancemethod(_assoTests.matrixf_resize,None,matrixf)
matrixf.insert = new_instancemethod(_assoTests.matrixf_insert,None,matrixf)
matrixf.reserve = new_instancemethod(_assoTests.matrixf_reserve,None,matrixf)
matrixf.capacity = new_instancemethod(_assoTests.matrixf_capacity,None,matrixf)
matrixf_swigregister = _assoTests.matrixf_swigregister
matrixf_swigregister(matrixf)

class vectora(object):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __iter__(self): return self.iterator()
    def __init__(self, *args): 
        _assoTests.vectora_swiginit(self,_assoTests.new_vectora(*args))
    __swig_destroy__ = _assoTests.delete_vectora
vectora.iterator = new_instancemethod(_assoTests.vectora_iterator,None,vectora)
vectora.__nonzero__ = new_instancemethod(_assoTests.vectora___nonzero__,None,vectora)
vectora.__bool__ = new_instancemethod(_assoTests.vectora___bool__,None,vectora)
vectora.__len__ = new_instancemethod(_assoTests.vectora___len__,None,vectora)
vectora.pop = new_instancemethod(_assoTests.vectora_pop,None,vectora)
vectora.__getslice__ = new_instancemethod(_assoTests.vectora___getslice__,None,vectora)
vectora.__setslice__ = new_instancemethod(_assoTests.vectora___setslice__,None,vectora)
vectora.__delslice__ = new_instancemethod(_assoTests.vectora___delslice__,None,vectora)
vectora.__delitem__ = new_instancemethod(_assoTests.vectora___delitem__,None,vectora)
vectora.__getitem__ = new_instancemethod(_assoTests.vectora___getitem__,None,vectora)
vectora.__setitem__ = new_instancemethod(_assoTests.vectora___setitem__,None,vectora)
vectora.append = new_instancemethod(_assoTests.vectora_append,None,vectora)
vectora.empty = new_instancemethod(_assoTests.vectora_empty,None,vectora)
vectora.size = new_instancemethod(_assoTests.vectora_size,None,vectora)
vectora.clear = new_instancemethod(_assoTests.vectora_clear,None,vectora)
vectora.swap = new_instancemethod(_assoTests.vectora_swap,None,vectora)
vectora.get_allocator = new_instancemethod(_assoTests.vectora_get_allocator,None,vectora)
vectora.begin = new_instancemethod(_assoTests.vectora_begin,None,vectora)
vectora.end = new_instancemethod(_assoTests.vectora_end,None,vectora)
vectora.rbegin = new_instancemethod(_assoTests.vectora_rbegin,None,vectora)
vectora.rend = new_instancemethod(_assoTests.vectora_rend,None,vectora)
vectora.pop_back = new_instancemethod(_assoTests.vectora_pop_back,None,vectora)
vectora.erase = new_instancemethod(_assoTests.vectora_erase,None,vectora)
vectora.push_back = new_instancemethod(_assoTests.vectora_push_back,None,vectora)
vectora.front = new_instancemethod(_assoTests.vectora_front,None,vectora)
vectora.back = new_instancemethod(_assoTests.vectora_back,None,vectora)
vectora.assign = new_instancemethod(_assoTests.vectora_assign,None,vectora)
vectora.resize = new_instancemethod(_assoTests.vectora_resize,None,vectora)
vectora.insert = new_instancemethod(_assoTests.vectora_insert,None,vectora)
vectora.reserve = new_instancemethod(_assoTests.vectora_reserve,None,vectora)
vectora.capacity = new_instancemethod(_assoTests.vectora_capacity,None,vectora)
vectora_swigregister = _assoTests.vectora_swigregister
vectora_swigregister(vectora)


def fEqual(*args, **kwargs):
  return _assoTests.fEqual(*args, **kwargs)
fEqual = _assoTests.fEqual

def fRound(*args, **kwargs):
  return _assoTests.fRound(*args, **kwargs)
fRound = _assoTests.fRound
class VPlus(object):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self): 
        _assoTests.VPlus_swiginit(self,_assoTests.new_VPlus())
    __swig_destroy__ = _assoTests.delete_VPlus
VPlus_swigregister = _assoTests.VPlus_swigregister
VPlus_swigregister(VPlus)


def initialize():
  return _assoTests.initialize()
initialize = _assoTests.initialize
class RNG(object):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self): 
        _assoTests.RNG_swiginit(self,_assoTests.new_RNG())
    __swig_destroy__ = _assoTests.delete_RNG
RNG.get = new_instancemethod(_assoTests.RNG_get,None,RNG)
RNG_swigregister = _assoTests.RNG_swigregister
RNG_swigregister(RNG)

class BaseLm(object):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    __swig_destroy__ = _assoTests.delete_BaseLm
    def __init__(self, *args): 
        _assoTests.BaseLm_swiginit(self,_assoTests.new_BaseLm(*args))
BaseLm.clone = new_instancemethod(_assoTests.BaseLm_clone,None,BaseLm)
BaseLm.setX = new_instancemethod(_assoTests.BaseLm_setX,None,BaseLm)
BaseLm.clear = new_instancemethod(_assoTests.BaseLm_clear,None,BaseLm)
BaseLm.setY = new_instancemethod(_assoTests.BaseLm_setY,None,BaseLm)
BaseLm.getX = new_instancemethod(_assoTests.BaseLm_getX,None,BaseLm)
BaseLm.replaceCol = new_instancemethod(_assoTests.BaseLm_replaceCol,None,BaseLm)
BaseLm_swigregister = _assoTests.BaseLm_swigregister
BaseLm_swigregister(BaseLm)

class LinearM(BaseLm):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    __swig_destroy__ = _assoTests.delete_LinearM
    def __init__(self, *args): 
        _assoTests.LinearM_swiginit(self,_assoTests.new_LinearM(*args))
LinearM.fit = new_instancemethod(_assoTests.LinearM_fit,None,LinearM)
LinearM.getBeta = new_instancemethod(_assoTests.LinearM_getBeta,None,LinearM)
LinearM.getSEBeta = new_instancemethod(_assoTests.LinearM_getSEBeta,None,LinearM)
LinearM_swigregister = _assoTests.LinearM_swigregister
LinearM_swigregister(LinearM)

class AssoData(object):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self): 
        _assoTests.AssoData_swiginit(self,_assoTests.new_AssoData())
    __swig_destroy__ = _assoTests.delete_AssoData
AssoData.clone = new_instancemethod(_assoTests.AssoData_clone,None,AssoData)
AssoData.setGenotype = new_instancemethod(_assoTests.AssoData_setGenotype,None,AssoData)
AssoData.setX = new_instancemethod(_assoTests.AssoData_setX,None,AssoData)
AssoData.setPhenotype = new_instancemethod(_assoTests.AssoData_setPhenotype,None,AssoData)
AssoData.setMaf = new_instancemethod(_assoTests.AssoData_setMaf,None,AssoData)
AssoData.setMafWeight = new_instancemethod(_assoTests.AssoData_setMafWeight,None,AssoData)
AssoData.meanOfX = new_instancemethod(_assoTests.AssoData_meanOfX,None,AssoData)
AssoData.phenotype = new_instancemethod(_assoTests.AssoData_phenotype,None,AssoData)
AssoData.genotype = new_instancemethod(_assoTests.AssoData_genotype,None,AssoData)
AssoData.raw_genotype = new_instancemethod(_assoTests.AssoData_raw_genotype,None,AssoData)
AssoData.covariates = new_instancemethod(_assoTests.AssoData_covariates,None,AssoData)
AssoData.maf = new_instancemethod(_assoTests.AssoData_maf,None,AssoData)
AssoData.covarcounts = new_instancemethod(_assoTests.AssoData_covarcounts,None,AssoData)
AssoData.samplecounts = new_instancemethod(_assoTests.AssoData_samplecounts,None,AssoData)
AssoData.pvalue = new_instancemethod(_assoTests.AssoData_pvalue,None,AssoData)
AssoData.statistic = new_instancemethod(_assoTests.AssoData_statistic,None,AssoData)
AssoData.se = new_instancemethod(_assoTests.AssoData_se,None,AssoData)
AssoData.setPvalue = new_instancemethod(_assoTests.AssoData_setPvalue,None,AssoData)
AssoData.setStatistic = new_instancemethod(_assoTests.AssoData_setStatistic,None,AssoData)
AssoData.setSE = new_instancemethod(_assoTests.AssoData_setSE,None,AssoData)
AssoData.permuteY = new_instancemethod(_assoTests.AssoData_permuteY,None,AssoData)
AssoData.permuteRawX = new_instancemethod(_assoTests.AssoData_permuteRawX,None,AssoData)
AssoData.permuteX = new_instancemethod(_assoTests.AssoData_permuteX,None,AssoData)
AssoData.sumToX = new_instancemethod(_assoTests.AssoData_sumToX,None,AssoData)
AssoData.binToX = new_instancemethod(_assoTests.AssoData_binToX,None,AssoData)
AssoData.weightX = new_instancemethod(_assoTests.AssoData_weightX,None,AssoData)
AssoData.setSitesByMaf = new_instancemethod(_assoTests.AssoData_setSitesByMaf,None,AssoData)
AssoData.simpleLinear = new_instancemethod(_assoTests.AssoData_simpleLinear,None,AssoData)
AssoData.simpleLogit = new_instancemethod(_assoTests.AssoData_simpleLogit,None,AssoData)
AssoData.multipleLinear = new_instancemethod(_assoTests.AssoData_multipleLinear,None,AssoData)
AssoData.gaussianP = new_instancemethod(_assoTests.AssoData_gaussianP,None,AssoData)
AssoData.studentP = new_instancemethod(_assoTests.AssoData_studentP,None,AssoData)
AssoData_swigregister = _assoTests.AssoData_swigregister
AssoData_swigregister(AssoData)

class BaseAction(object):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self): 
        _assoTests.BaseAction_swiginit(self,_assoTests.new_BaseAction())
    __swig_destroy__ = _assoTests.delete_BaseAction
BaseAction.clone = new_instancemethod(_assoTests.BaseAction_clone,None,BaseAction)
BaseAction.apply = new_instancemethod(_assoTests.BaseAction_apply,None,BaseAction)
BaseAction.name = new_instancemethod(_assoTests.BaseAction_name,None,BaseAction)
BaseAction_swigregister = _assoTests.BaseAction_swigregister
BaseAction_swigregister(BaseAction)

class SumToX(BaseAction):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self): 
        _assoTests.SumToX_swiginit(self,_assoTests.new_SumToX())
    __swig_destroy__ = _assoTests.delete_SumToX
SumToX_swigregister = _assoTests.SumToX_swigregister
SumToX_swigregister(SumToX)

class BinToX(BaseAction):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self): 
        _assoTests.BinToX_swiginit(self,_assoTests.new_BinToX())
    __swig_destroy__ = _assoTests.delete_BinToX
BinToX_swigregister = _assoTests.BinToX_swigregister
BinToX_swigregister(BinToX)

class PermuteX(BaseAction):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self): 
        _assoTests.PermuteX_swiginit(self,_assoTests.new_PermuteX())
    __swig_destroy__ = _assoTests.delete_PermuteX
PermuteX_swigregister = _assoTests.PermuteX_swigregister
PermuteX_swigregister(PermuteX)

class PermuteRawX(BaseAction):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self): 
        _assoTests.PermuteRawX_swiginit(self,_assoTests.new_PermuteRawX())
    __swig_destroy__ = _assoTests.delete_PermuteRawX
PermuteRawX_swigregister = _assoTests.PermuteRawX_swigregister
PermuteRawX_swigregister(PermuteRawX)

class PermuteY(BaseAction):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self): 
        _assoTests.PermuteY_swiginit(self,_assoTests.new_PermuteY())
    __swig_destroy__ = _assoTests.delete_PermuteY
PermuteY_swigregister = _assoTests.PermuteY_swigregister
PermuteY_swigregister(PermuteY)

class SetMaf(BaseAction):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self): 
        _assoTests.SetMaf_swiginit(self,_assoTests.new_SetMaf())
    __swig_destroy__ = _assoTests.delete_SetMaf
SetMaf_swigregister = _assoTests.SetMaf_swigregister
SetMaf_swigregister(SetMaf)

class WeightByAllMaf(BaseAction):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self): 
        _assoTests.WeightByAllMaf_swiginit(self,_assoTests.new_WeightByAllMaf())
    __swig_destroy__ = _assoTests.delete_WeightByAllMaf
WeightByAllMaf_swigregister = _assoTests.WeightByAllMaf_swigregister
WeightByAllMaf_swigregister(WeightByAllMaf)

class SetSites(BaseAction):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self, upper = 1.0, lower = 0.0): 
        _assoTests.SetSites_swiginit(self,_assoTests.new_SetSites(upper, lower))
    __swig_destroy__ = _assoTests.delete_SetSites
SetSites_swigregister = _assoTests.SetSites_swigregister
SetSites_swigregister(SetSites)

class SimpleLinearRegression(BaseAction):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self): 
        _assoTests.SimpleLinearRegression_swiginit(self,_assoTests.new_SimpleLinearRegression())
    __swig_destroy__ = _assoTests.delete_SimpleLinearRegression
SimpleLinearRegression_swigregister = _assoTests.SimpleLinearRegression_swigregister
SimpleLinearRegression_swigregister(SimpleLinearRegression)

class MultipleLinearRegression(BaseAction):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self): 
        _assoTests.MultipleLinearRegression_swiginit(self,_assoTests.new_MultipleLinearRegression())
    __swig_destroy__ = _assoTests.delete_MultipleLinearRegression
MultipleLinearRegression_swigregister = _assoTests.MultipleLinearRegression_swigregister
MultipleLinearRegression_swigregister(MultipleLinearRegression)

class SimpleLogisticRegression(BaseAction):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self): 
        _assoTests.SimpleLogisticRegression_swiginit(self,_assoTests.new_SimpleLogisticRegression())
    __swig_destroy__ = _assoTests.delete_SimpleLogisticRegression
SimpleLogisticRegression_swigregister = _assoTests.SimpleLogisticRegression_swigregister
SimpleLogisticRegression_swigregister(SimpleLogisticRegression)

class GaussianPval(BaseAction):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self, sided = 1): 
        _assoTests.GaussianPval_swiginit(self,_assoTests.new_GaussianPval(sided))
    __swig_destroy__ = _assoTests.delete_GaussianPval
GaussianPval_swigregister = _assoTests.GaussianPval_swigregister
GaussianPval_swigregister(GaussianPval)

class StudentPval(BaseAction):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self, sided = 1): 
        _assoTests.StudentPval_swiginit(self,_assoTests.new_StudentPval(sided))
    __swig_destroy__ = _assoTests.delete_StudentPval
StudentPval_swigregister = _assoTests.StudentPval_swigregister
StudentPval_swigregister(StudentPval)

class BasePermutator(BaseAction):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    __swig_destroy__ = _assoTests.delete_BasePermutator
    def __init__(self, *args): 
        _assoTests.BasePermutator_swiginit(self,_assoTests.new_BasePermutator(*args))
BasePermutator.append = new_instancemethod(_assoTests.BasePermutator_append,None,BasePermutator)
BasePermutator.extend = new_instancemethod(_assoTests.BasePermutator_extend,None,BasePermutator)
BasePermutator.check = new_instancemethod(_assoTests.BasePermutator_check,None,BasePermutator)
BasePermutator_swigregister = _assoTests.BasePermutator_swigregister
BasePermutator_swigregister(BasePermutator)

class AssoAlgorithm(BasePermutator):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self, *args): 
        _assoTests.AssoAlgorithm_swiginit(self,_assoTests.new_AssoAlgorithm(*args))
    __swig_destroy__ = _assoTests.delete_AssoAlgorithm
AssoAlgorithm_swigregister = _assoTests.AssoAlgorithm_swigregister
AssoAlgorithm_swigregister(AssoAlgorithm)

class FixedPermutator(BasePermutator):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self, *args, **kwargs): 
        _assoTests.FixedPermutator_swiginit(self,_assoTests.new_FixedPermutator(*args, **kwargs))
    __swig_destroy__ = _assoTests.delete_FixedPermutator
FixedPermutator_swigregister = _assoTests.FixedPermutator_swigregister
FixedPermutator_swigregister(FixedPermutator)

class VariablePermutator(BasePermutator):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self, *args, **kwargs): 
        _assoTests.VariablePermutator_swiginit(self,_assoTests.new_VariablePermutator(*args, **kwargs))
    __swig_destroy__ = _assoTests.delete_VariablePermutator
VariablePermutator.clone = new_instancemethod(_assoTests.VariablePermutator_clone,None,VariablePermutator)
VariablePermutator_swigregister = _assoTests.VariablePermutator_swigregister
VariablePermutator_swigregister(VariablePermutator)

class Exception(object):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self, *args, **kwargs): 
        _assoTests.Exception_swiginit(self,_assoTests.new_Exception(*args, **kwargs))
    __swig_destroy__ = _assoTests.delete_Exception
Exception.message = new_instancemethod(_assoTests.Exception_message,None,Exception)
Exception_swigregister = _assoTests.Exception_swigregister
Exception_swigregister(Exception)

class StopIteration(Exception):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self, *args, **kwargs): 
        _assoTests.StopIteration_swiginit(self,_assoTests.new_StopIteration(*args, **kwargs))
    __swig_destroy__ = _assoTests.delete_StopIteration
StopIteration_swigregister = _assoTests.StopIteration_swigregister
StopIteration_swigregister(StopIteration)

class IndexError(Exception):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self, *args, **kwargs): 
        _assoTests.IndexError_swiginit(self,_assoTests.new_IndexError(*args, **kwargs))
    __swig_destroy__ = _assoTests.delete_IndexError
IndexError_swigregister = _assoTests.IndexError_swigregister
IndexError_swigregister(IndexError)

class ValueError(Exception):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self, *args, **kwargs): 
        _assoTests.ValueError_swiginit(self,_assoTests.new_ValueError(*args, **kwargs))
    __swig_destroy__ = _assoTests.delete_ValueError
ValueError_swigregister = _assoTests.ValueError_swigregister
ValueError_swigregister(ValueError)

class SystemError(Exception):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self, *args, **kwargs): 
        _assoTests.SystemError_swiginit(self,_assoTests.new_SystemError(*args, **kwargs))
    __swig_destroy__ = _assoTests.delete_SystemError
SystemError_swigregister = _assoTests.SystemError_swigregister
SystemError_swigregister(SystemError)

class RuntimeError(Exception):
    thisown = _swig_property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    def __init__(self, *args, **kwargs): 
        _assoTests.RuntimeError_swiginit(self,_assoTests.new_RuntimeError(*args, **kwargs))
    __swig_destroy__ = _assoTests.delete_RuntimeError
RuntimeError_swigregister = _assoTests.RuntimeError_swigregister
RuntimeError_swigregister(RuntimeError)



