'''
Created on Feb 6, 2017

@author: dnorgaard
'''
import os
import math as M
import numpy as np
from matplotlib import mlab
from obspy.imaging.cm import obspy_sequential
        

filename_format="%s_%d%02d%02d_%s_%d.csv"
date_format="%d-%b-%Y %H:%M:%S"
bands=[0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 8, 10, 15, 20 ]

#===============================================================================
# process - calculate SSAM and write to file
#===============================================================================
def process(stream, station_id, et, config, station_data):
    ssam=calculate(stream)
    missed=station_data['ssam_missed']
    station_data['ssam_missed']=write(ssam, station_id, et, config, missed)
    return station_data  

#===============================================================================
# calculate SSAM values for given frequency bands. 
#===============================================================================
def calculate(stream):    
    stream.merge(method=1)  
    data=np.array([])  
    for tr in stream:
        data=np.append(data, tr.data)
    specgram, freq, time = spectrogram(tr.data, tr.stats.sampling_rate) 
    ssam=[]
    minf=0
    maxf=0
    for i in range(0,len(bands)):
        b=bands[i]
        maxf=b  
        tempsum=0
        count=0
        for j in range(0, len(freq)):
            f=freq[j]
            if minf <= f and f < maxf:
                favg = np.average(specgram[j])
                tempsum += favg
                count += 1
        v=round(tempsum/count)
        #print(i,b,tempsum/count, minf, maxf)
        ssam.append(v)
        minf=b 
    return ssam
    
#===============================================================================
# _nearest_pow_2 - taken from obspy.imaging.spectrogram
#===============================================================================
def _nearest_pow_2(x):
    """
    Find power of two nearest to x

    >>> _nearest_pow_2(3)
    2.0
    >>> _nearest_pow_2(15)
    16.0

    :type x: float
    :param x: Number
    :rtype: Int
    :return: Nearest power of 2 to x
    """
    a = M.pow(2, M.ceil(np.log2(x)))
    b = M.pow(2, M.floor(np.log2(x)))
    if abs(a - x) < abs(b - x):
        return a
    else:
        return b       
         
#===============================================================================
# spectrogram - modified version of obspy.imaging.spectrogram.spectrogram().
#===============================================================================
def spectrogram(data, samp_rate, per_lap=0.9, wlen=None, log=False,
                outfile=None, fmt=None, axes=None, dbscale=False,
                mult=8.0, cmap=obspy_sequential, zorder=None, title=None,
                show=True, sphinx=False, clip=[0.0, 1.0]):
    """
    Computes and plots spectrogram of the input data.

    :param data: Input data
    :type samp_rate: float
    :param samp_rate: Samplerate in Hz
    :type per_lap: float
    :param per_lap: Percentage of overlap of sliding window, ranging from 0
        to 1. High overlaps take a long time to compute.
    :type wlen: int or float
    :param wlen: Window length for fft in seconds. If this parameter is too
        small, the calculation will take forever.
    :type log: bool
    :param log: Logarithmic frequency axis if True, linear frequency axis
        otherwise.
    :type outfile: str
    :param outfile: String for the filename of output file, if None
        interactive plotting is activated.
    :type fmt: str
    :param fmt: Format of image to save
    :type axes: :class:`matplotlib.axes.Axes`
    :param axes: Plot into given axes, this deactivates the fmt and
        outfile option.
    :type dbscale: bool
    :param dbscale: If True 10 * log10 of color values is taken, if False the
        sqrt is taken.
    :type mult: float
    :param mult: Pad zeros to length mult * wlen. This will make the
        spectrogram smoother.
    :type cmap: :class:`matplotlib.colors.Colormap`
    :param cmap: Specify a custom colormap instance. If not specified, then the
        default ObsPy sequential colormap is used.
    :type zorder: float
    :param zorder: Specify the zorder of the plot. Only of importance if other
        plots in the same axes are executed.
    :type title: str
    :param title: Set the plot title
    :type show: bool
    :param show: Do not call `plt.show()` at end of routine. That way, further
        modifications can be done to the figure before showing it.
    :type sphinx: bool
    :param sphinx: Internal flag used for API doc generation, default False
    :type clip: [float, float]
    :param clip: adjust colormap to clip at lower and/or upper end. The given
        percentages of the amplitude range (linear or logarithmic depending
        on option `dbscale`) are clipped.
    """
#     import matplotlib.pyplot as plt
    # enforce float for samp_rate
    samp_rate = float(samp_rate)

    # set wlen from samp_rate if not specified otherwise
    if not wlen:
        wlen = samp_rate / 100.

    npts = len(data)
    # nfft needs to be an integer, otherwise a deprecation will be raised
    # XXX add condition for too many windows => calculation takes for ever
    nfft = int(_nearest_pow_2(wlen * samp_rate))
    if nfft > npts:
        nfft = int(_nearest_pow_2(npts / 8.0))

    if mult is not None:
        mult = int(_nearest_pow_2(mult))
        mult = mult * nfft
    nlap = int(nfft * float(per_lap))

    data = data - data.mean()
#     end = npts / samp_rate

    # Here we call not plt.specgram as this already produces a plot
    # matplotlib.mlab.specgram should be faster as it computes only the
    # arrays
    # XXX mlab.specgram uses fft, would be better and faster use rfft
    specgram, freq, time = mlab.specgram(data, Fs=samp_rate, NFFT=nfft,
                                         pad_to=mult, noverlap=nlap)

    # db scale and remove zero/offset for amplitude
    if dbscale:
        specgram = 10 * np.log10(specgram[1:, :])
    else:
        specgram = np.sqrt(specgram[1:, :])
    freq = freq[1:]

    vmin, vmax = clip
    if vmin < 0 or vmax > 1 or vmin >= vmax:
        msg = "Invalid parameters for clip option."
        raise ValueError(msg)
    _range = float(specgram.max() - specgram.min())
    vmin = specgram.min() + vmin * _range
    vmax = specgram.min() + vmax * _range
#     norm = Normalize(vmin, vmax, clip=True)
    
#     if not axes:
#         fig = plt.figure()
#         ax = fig.add_subplot(111)
#     else:
#         ax = axes

    # calculate half bin width
    halfbin_time = (time[1] - time[0]) / 2.0
    halfbin_freq = (freq[1] - freq[0]) / 2.0

    # argument None is not allowed for kwargs on matplotlib python 3.3
#     kwargs = {k: v for k, v in (('cmap', cmap), ('zorder', zorder))
#               if v is not None}

    if log:
        # pcolor expects one bin more at the right end
        freq = np.concatenate((freq, [freq[-1] + 2 * halfbin_freq]))
        time = np.concatenate((time, [time[-1] + 2 * halfbin_time]))
        # center bin
        time -= halfbin_time
        freq -= halfbin_freq
        # Log scaling for frequency values (y-axis)
#         ax.set_yscale('log')
#         # Plot times
#         ax.pcolormesh(time, freq, specgram, norm=norm, **kwargs)
    else:
        # this method is much much faster!
        specgram = np.flipud(specgram)
        # center bin
#         extent = (time[0] - halfbin_time, time[-1] + halfbin_time,
#                   freq[0] - halfbin_freq, freq[-1] + halfbin_freq)
#         ax.imshow(specgram, interpolation="nearest", extent=extent, **kwargs)


    #fig.close()
    return specgram, freq, time
    
    # **Not sure if I need anything below there yet.  Keep for now.**
    
    
#     # set correct way of axis, whitespace before and after with window
#     # length
#     ax.axis('tight')
#     ax.set_xlim(0, end)
#     ax.grid(False)
# 
#     if axes:
#         return ax
# 
#     ax.set_xlabel('Time [s]')
#     ax.set_ylabel('Frequency [Hz]')
#     if title:
#         ax.set_title(title)
# 
#     if not sphinx:
#         # ignoring all NumPy warnings during plot
#         temp = np.geterr()
#         np.seterr(all='ignore')
#         plt.draw()
#         np.seterr(**temp)
#     if outfile:
#         if fmt:
#             fig.savefig(outfile, format=fmt)
#         else:
#             fig.savefig(outfile)
#     elif show:
#         plt.show()
#     else:
#         return fig
            
#===============================================================================
# write - write SSAM to file
#===============================================================================
def write(ssam, station_id, et, config, missed):
    text=missed+et.strftime(date_format)
    for v in ssam:
        text += " %d"%v
    if config.print_data or config.print_debug:
        print(station_id+"     "+text)
    try:
        station=station_id.replace(":","_")
        filename = filename_format%("SSAM", et.year, et.month, et.day, station, 60)
        subdir=os.path.join(config.ssam_directory, str(60))
        full_filename = os.path.join(subdir, filename)
        f = open(full_filename,"a")
        f.write(text+"\n")
        if config.print_data or config.print_debug:
            print(station_id+"     "+text)
        f.close() 
    except Exception:
        return text + "\n"  
    return ""  

