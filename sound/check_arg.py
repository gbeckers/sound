"""
This module defines type information for often-used variables, such as sampling
rate (fs), time, etc, and functions to check them.

The rationale behind it is that for our purposes python's dynamic typing is not
always a good idea. We want to prevent that variables get unexpected types. Our
classes and functions should do type checking and casting of input arguments.
We also want to be able to check for non-sensical values (i.e. a negative duration).

The dictionary 'argtypes' contains the defined types in our package.

The functions check_arg and check_argarray check for the types and values that
are allowed and may cast to different types.

"""
import numpy as np

from numpy import array, any, float32, float64, floating, integer, isnan, \
    isinf, issubdtype, ndarray, uint8, int8, uint16, int16, uint32, int32, \
    uint64, int64




# FIXME
# The following could be used
# import numbers
# isinstance(n, numbers.Integral)

class DimensionError(Exception): pass


class SizeError(Exception): pass


# np.uint64 creates troubles with cython an indexing
defined_integers = (int, np.uint8, np.int8, np.uint16,
                    np.int16, np.uint32, np.int32, np.int64)

defined_floats = (float, np.float16, np.float32, np.float64)

eps = np.power(2.0, -52.0)

class ArgCheck(object):
    def __init__(self, allowedinputtypes, typedef, failfuncs=()):
        """
        Parameters
        ----------
        allowedinputtypes: sequence of types
        typedef: type
        failfuncs: sequence of functions

        """
        self.allowedinputtypes = allowedinputtypes
        self.typedef = typedef
        self.failfuncs = failfuncs

    def __str__(self):
        s = 'input: %s, ' % str(self.allowedinputtypes)
        s += 'type: %s ' % self.typedef
        s += 'fail: %s ' % str(self.failfuncs)
        return s

    __repr__ = __str__


## define fail functions here

def smaller0(arg):
    """smaller than zero"""
    if any(arg < 0.0): return True


def smallerequal0(arg):
    """smaller than or equal to zero"""
    if any(arg <= 0.0): return True


## define argument types here
## ArgCheck((tuple of inputtypes), outputtype, (tuple of test functions for wrong input values))

argtypes = dict(
    bandwidth=ArgCheck(defined_floats, float64, (isnan, isinf, smaller0)),
    binsize=ArgCheck(defined_integers, int64, (smallerequal0,)),
    channelaxis=ArgCheck(defined_integers, int64, ()),
    copy=ArgCheck((bool,), bool, ()),
    datasize=ArgCheck(defined_integers, int64, (smaller0,)),
    dataoffset=ArgCheck(defined_integers, int64, (smaller0,)),
    duration=ArgCheck(defined_floats, float64, (isnan, isinf, smaller0)),
    endindex=ArgCheck(defined_integers, int64, (smaller0,)),
    epochaxis=ArgCheck(defined_integers, int64, ()),
    fftduration=ArgCheck(defined_floats, float64, (isnan, isinf, smallerequal0)),
    framesize=ArgCheck(defined_integers, int64, (smallerequal0,)),
    frequency=ArgCheck(defined_floats, float64, (isnan, isinf)),
    frequencyaxis=ArgCheck(defined_integers, int64, ()),
    inmemory=ArgCheck((bool,), bool, ()),
    nearest_boundary=ArgCheck((bool,), bool, ()),
    nbits=ArgCheck(defined_integers, int, (smaller0,)),
    nbytes=ArgCheck(defined_integers, int, (smaller0,)),
    nchannels=ArgCheck(defined_integers, int, (smallerequal0,)),
    nepochs=ArgCheck(defined_integers, int64, (smaller0,)),
    nframes=ArgCheck(defined_integers, int64, (smaller0,)),
    nfrequencysamples=ArgCheck(defined_integers, int64, (smaller0,)),
    ntimesamples=ArgCheck(defined_integers, int64, (smaller0,)),
    overwrite=ArgCheck((bool,), bool, ()),
    readonly=ArgCheck((bool,), bool, ()),
    samplingrate=ArgCheck(defined_integers + defined_floats, float64, (isnan, isinf, smallerequal0)),
    scalefactor=ArgCheck(defined_floats, float64, (isnan, isinf)),
    stepduration=ArgCheck(defined_floats, float64, (isnan, isinf, smallerequal0)),
    startindex=ArgCheck(defined_integers, int64, (smaller0,)),
    stepsize=ArgCheck(defined_integers, int64, (smallerequal0,)),
    time=ArgCheck(defined_floats, float64, (isnan, isinf)),
    quantize=ArgCheck((bool,), bool, ()),
    windowduration=ArgCheck(defined_floats, float64, (isnan, isinf, smallerequal0)))


## functions

def check_arg(arg, argname):
    if not argname in argtypes:
        raise ValueError("%s is not a defined argument type" % argname)
    argtype = argtypes[argname]
    # check allowed input
    if not isinstance(arg, argtype.allowedinputtypes):
        raise TypeError("argument type is not valid for %s (input: %s, allowed: %s)" \
                        % (argname, type(arg), argtype.allowedinputtypes))
    # cast
    arg = argtype.typedef(arg)
    # check fail functions
    for func in argtype.failfuncs:
        if func(arg):
            raise ValueError("%s value not allowed (%s, %s)" % (argname, arg, func.__doc__))
    return arg


def check_argarray(argarray, argname, ndim=None, size=None):
    # convert to array if necessary
    if not isinstance(argarray, ndarray):
        argarray = array(argarray, ndmin=1)

    argtype = argtypes[argname]
    # check if dtype is allowed
    if not argarray.dtype in argtype.allowedinputtypes:
        raise TypeError("argument type is not valid for %s (input: %s, allowed: %s)" \
                        % (argname, argarray.dtype, argtype.allowedinputtypes))
    # if allowed but not defined type, convert
    if not argarray.dtype == argtype.typedef:
        argarray = argarray.astype(argtype.typedef)
    # check for conditions not allowed
    for func in argtype.failfuncs:
        if any(func(argarray)):
            raise ValueError("%s value not allowed (%s)" % (argname, func.__doc__))
    # check dimension
    if not ndim is None:
        if argarray.ndim != ndim:
            raise DimensionError("%s dimension not allowed (%s)" \
                                 % (argname, argarray.ndim))
    # check size
    if not size is None:
        if argarray.size != size:
            raise SizeError("%s size not allowed (%s)" \
                            % (argname, argarray.size))
    return argarray


def _checkandconvert(arg, allowedinputtypes, outputtype):
    if not isinstance(arg, allowedinputtypes):
        raise TypeError("argument type is not valid (input: %s, allowed: %s)" \
                        % (type(arg), allowedinputtypes))
    return outputtype(arg)


def check_bool(arg):
    if not isinstance(arg, bool):
        raise TypeError("argument not of bool type")
    return arg


def check_float(arg, positive=True, zero=True, negative=True, nan=True,
                inf=True, cast=float64):
    """
    pass

    """
    for switch in (positive, zero, negative, nan, inf):
        check_bool(switch)
    if not cast in defined_floats:
        raise ValueError("cast argument should be a float type")
    arg = _checkandconvert(arg, defined_floats, cast)
    if (not nan) and isnan(arg): raise ValueError("argument cannot be nan")
    if (not inf) and isinf(arg): raise ValueError("argument cannot be (-)inf")
    if (not positive) and (arg > 0.0): raise ValueError("argument > 0.0")
    if (not zero) and (arg == 0.0): raise ValueError("argument == 0.0")
    if (not negative) and (arg < 0.0): raise ValueError("argument < 0.0")
    return arg


def check_floatarray(arg, positive=True, zero=True, negative=True, nan=True,
                     inf=True, cast=float64, copy=False):
    for switch in (positive, zero, negative, nan, inf, copy):
        check_bool(switch)
    if not cast in defined_floats:
        raise ValueError("cast argument should be a float type")
    if not isinstance(arg, ndarray):
        arg = array(arg, ndmin=1, copy=copy)
    if not issubdtype(arg.dtype, floating):
        raise TypeError("arg is not a float or sequence of defined_floats")
    if arg.dtype != cast:
        arg = arg.astype(cast)
    if (not nan) and any(isnan(arg)): raise ValueError("argument cannot be nan")
    if (not inf) and any(isinf(arg)): raise ValueError("argument cannot be (-)inf")
    if (not positive) and any(arg > 0.0): raise ValueError("argument > 0.0")
    if (not zero) and any(arg == 0.0): raise ValueError("argument == 0.0")
    if (not negative) and any(arg < 0.0): raise ValueError("argument < 0.0")
    return arg


def check_int(arg, positive=True, zero=True, negative=True, cast=int64):
    for switch in (positive, zero, negative):
        check_bool(switch)
    if not cast in defined_integers:
        raise ValueError("cast argument should be an int type")
    if not isinstance(arg, defined_integers) or (type(arg) is bool):
        raise TypeError("argument is not an integer: %s" % type(arg))
    if (not positive) and (arg > 0): raise ValueError("argument > 0")
    if (not zero) and (arg == 0): raise ValueError("argument == 0")
    if (not negative) and (arg < 0): raise ValueError("argument < 0")
    return cast(arg)


def check_intarray(arg, positive=True, zero=True, negative=True, cast=int64,
                   copy=False):
    for switch in (positive, zero, negative, copy):
        check_bool(switch)
    if not cast in defined_integers:
        raise ValueError("cast argument should be an int type")
    if not isinstance(arg, ndarray):
        arg = array(arg, ndmin=1, copy=copy)
    if not issubdtype(arg.dtype, integer):
        raise TypeError("arg is not an int or sequence of defined_integers")
    if arg.dtype != cast:
        arg = arg.astype(cast)
    if (not positive) and any(arg > 0): raise ValueError("argument > 0")
    if (not zero) and any(arg == 0): raise ValueError("argument == 0")
    if (not negative) and any(arg < 0): raise ValueError("argument < 0")
    return arg




