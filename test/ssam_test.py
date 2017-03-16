'''
Created on Feb 6, 2017

@author: dnorgaard
'''

import math as M
import numpy as np
from matplotlib import mlab
        
    
    
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
         
def spectrogram(data, samp_rate, per_lap=0.9, wlen=None, log=False, dbscale=False, mult=8.0):
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
    :type dbscale: bool
    :param dbscale: If True 10 * log10 of color values is taken, if False the
        sqrt is taken.
    :type mult: float
    :param mult: Pad zeros to length mult * wlen. This will make the
        spectrogram smoother.
    """
    # enforce float for samp_rate
    samp_rate = float(samp_rate)

    # set wlen from samp_rate if not specified otherwise
    if not wlen:
        wlen = samp_rate / 100.

#     print("sample rate: ",samp_rate)
#     print("wlen: ",wlen)
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

#     print("nlap: ",nlap)
#     print("nfft: ",nfft)
#     print("mult: ",mult)

    # Here we call not plt.specgram as this already produces a plot
    # matplotlib.mlab.specgram should be faster as it computes only the
    # arrays
    # XXX mlab.specgram uses fft, would be better and faster use rfft
    #specgram, freq, time = mlab.specgram(data, Fs=samp_rate, NFFT=nfft, 
    #                                      pad_to=mult, noverlap=nlap, detrend='linear', mode='psd')
    nfft=1024
    specgram, freq, time = mlab.specgram(data, Fs=samp_rate, NFFT=nfft, scale_by_freq=False, detrend='linear', mode='psd')
    
    

    # db scale and remove zero/offset for amplitude
    if dbscale:
        specgram = 10 * np.log10(specgram[1:, :])
    else:
        specgram = np.sqrt(specgram[1:, :])

    return freq, specgram, time

#===============================================================================
# calculate128
#===============================================================================
def calculate(freq, time, specgram):
    ssam=[]
    for spec in specgram:
        ssam.append("%05d"%np.average(spec))
    return ssam
           
    #===========================================================================
    # test_ssam
    #===========================================================================
#    def test_ssam():

bands=[0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 8, 10, 15, 20 ]
def calculate_custom(freq, time, specgram):
    #bands=[0.5, 1, 1.5, 2 ]
    ssam=[]
    minf=0
    maxf=0
    for x in range(0,len(bands)):
        b=bands[x]
        maxf=b  
        tempsum=0
        count=0
        #print("***Band=",b, " min=", minf, " max=", maxf)
        for i in range(0, len(freq)):
            f=freq[i]
            if minf <= f and f < maxf:
                #print(specgram[i])
                favg = np.average(specgram[i])
                #print("Freq=",f," avg=", favg)
                tempsum += favg
                count += 1
        v=tempsum/count
        #print("Band=",b, " SSAM=",tempsum/count)
        #print(x,b,tempsum/count, minf, maxf)
        ssam.append(v)
        minf=b
    return ssam


from obspy.clients.earthworm import Client
from obspy.core.utcdatetime import UTCDateTime
import os, time
now = UTCDateTime()
et = now - (now.timestamp % 60) 
st = et - 80
network="UW"
station="RER"
channel="EHZ"
location=""
filename_format="%s_%d%02d%02d_%s_%d.dat"
date_format="%d-%b-%Y %H:%M"
subdir="D:\Data\SSAM2017\Test"
client=Client("127.0.0.1", 16030)  
while True:   
    response = client.get_availability(network, station, location, channel)
    if(len(response)==0 or response[-1][5] < et):    # if available end time is before desired end time, wait a bit and then check again
        continue 
    stream=client.get_waveforms(network,station,location,channel, st, et) 
    sample_rate=stream[0].stats.sampling_rate
    npts=stream[0].stats.npts
#     print(sample_rate)
#     print(npts)
    data=np.array([])
    for tr in stream:
        data=np.append(data, tr.data)
        data=data[~np.isnan(data)]

    #print("Start=",start,"End=",end)

    freq, specgram, stime= spectrogram(data, sample_rate)  
    #print("Length specgram: "+str(len(specgram))+"x"+str(len(specgram[0])))
    #print(str(specgram))
    #print("*** freq ***")
    #print("Length freq: "+str(len(freq)))
    #print(str(freq))
    #print("*** time ***")
    #print("Length time: "+str(len(time)))
    #print(time)
    ssam=calculate_custom(freq, time, specgram)
    
    #filename = filename_format%("SSAMTEST", et.year, et.month, et.day, station, 60)
    #full_filename = os.path.join(subdir, filename)
    #f = open(full_filename,"a")
    text=et.strftime(date_format)
    for v in ssam:
        text += " %05d"%v
    #f.write(text+"\n")
    print(text)
    #f.close() 
    
    st += 60
    et += 60
    time.sleep(5)

        
            
            
            
    
