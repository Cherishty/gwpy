# coding=utf-8
# Copyright (C) Duncan Macleod (2013)
#
# This file is part of GWpy.
#
# GWpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GWpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GWpy.  If not, see <http://www.gnu.org/licenses/>.

"""Read gravitational-wave frame (GWF) files using the LALFrame API.
"""

from __future__ import division

from astropy.io import registry

try:
    from lalframe import frread
except ImportError:
    raise ImportError("No module named lalframe. LALFrame or frameCPP are "
                      "required in order to read data from GWF-format "
                      "frame files.")

from glue.lal import CacheEntry

from . import identify
from ....detector import Channel
from ....time import Time
from ... import (TimeSeries, StateVector, TimeSeriesDict, StateVectorDict)


def read_timeseries(framefile, channel, start=None, end=None, datatype=None,
                    resample=False, verbose=False, _target=TimeSeries):
    """Read a `TimeSeries` of data from a gravitational-wave frame file

    This method is a thin wrapper around `lalframe.frread.read_timeseries`
    and so can accept any input accepted by that function.

    Parameters
    ----------
    framefile : `str`, :class:`glue.lal.Cache`, :lalsuite:`LALCache`
        data source object, one of:

        - `str` : frame file path
        - :class:`glue.lal.Cache` : pure python cache object
        - :lalsuite:`LALCAche` : C-based cache object

    channel : :class:`~gwpy.detector.channel.Channel`, `str`
        data channel to read from frames
    start : `Time`, :lalsuite:`LIGOTimeGPS`, optional
        start GPS time of desired data
    end : `Time`, :lalsuite:`LIGOTimeGPS`, optional
        end GPS time of desired data
    datatype : `type`, `numpy.dtype`, `str`, optional
        identifier for desired output data type
    resample : `float`, optional
        rate of samples per second at which to resample input TimeSeries.
    verbose : `bool`, optional
        print verbose output

    Returns
    -------
    data : :class:`~gwpy.timeseries.core.TimeSeries`
        a new `TimeSeries` containing the data read from disk
    """
    # parse input arguments
    if isinstance(framefile, CacheEntry):
        framefile = framefile.path
    elif isinstance(framefile, file):
        framefile = framefile.name
    if isinstance(channel, Channel):
        channel = channel.name
    if start and isinstance(start, Time):
        start = start.gps
    if end and isinstance(end, Time):
        end = end.gps
    if start and end:
        duration = float(end - start)
    elif end:
        raise ValueError("If `end` is given, `start` must also be given")
    else:
        duration = None
    lalts = frread.read_timeseries(framefile, channel, start=start,
                                   duration=duration, datatype=datatype,
                                   verbose=verbose)
    out = _target.from_lal(lalts)
    if resample:
        out = out.resample(resample)
    return out


def read_timeseriesdict(framefile, channels, **kwargs):
    """Read data for multiple channels from the given GWF-format
    ``framefile``

    Parameters
    ----------
    framefile : `str`, :class:`glue.lal.Cache`, :lalsuite:`LALCache`
        data source object, one of:

        - `str` : frame file path
        - :class:`glue.lal.Cache` : pure python cache object
        - :lalsuite:`LALCAche` : C-based cache object
    channels : `list`
        list of channel names (or `Channel` objects) to read from frame

    See Also
    --------
    :func:`~gwpy.io.gwf.lalframe.read_timeseries`
        for documentation on keyword arguments

    Returns
    -------
    dict : :class:`~gwpy.timeseries.core.TimeSeriesDict`
        dict of (channel, `TimeSeries`) data pairs
    """
    out = TimeSeriesDict()
    for channel in channels:
        out[channel] = read_timeseries(framefile, channel, **kwargs)
    return out


def read_statevector_dict(source, channels, bitmasks=[], **kwargs):
    """Read a `StateVectorDict` of data from a gravitational-wave
    frame file
    """
    kwargs.setdefault('_target', StateVector)
    svd = StateVectorDict(read_timeseriesdict(source, channels, **kwargs))
    for (channel, bitmask) in zip(channels, bitmasks):
        svd[channel].bitmask = bitmask
    return svd


def read_statevector(source, channel, bitmask=[], **kwargs):
    kwargs.setdefault('_target', StateVector)
    sv = read_timeseries(source, channel, **kwargs).view(StateVector)
    sv.bitmask = bitmask
    return sv

registry.register_reader('lalframe', TimeSeries, read_timeseries)
registry.register_reader('lalframe', StateVector, read_statevector)
registry.register_reader('lalframe', TimeSeriesDict, read_timeseriesdict)
registry.register_reader('lalframe', StateVectorDict, read_statevector_dict)

# force this as the 'gwf' reader
registry.register_reader('gwf', TimeSeries, read_timeseries, force=True)
registry.register_reader('gwf', StateVector, read_statevector, force=True)
registry.register_reader('gwf', TimeSeriesDict, read_timeseriesdict,
                         force=True)
registry.register_reader('gwf', StateVectorDict, read_statevector_dict,
                         force=True)
