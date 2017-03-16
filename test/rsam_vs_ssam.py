'''
Created on Feb 27, 2017

@author: dnorgaard
'''
import numpy as np
import os, math

## USER CONFIG ####
oldssam="D:\Data\SSAM\\16channel\FMW_\\20170225_FMW_EHZ_UW.dat"
newssam="D:\Data\SSAM2017\\60\SSAM_20170225_FMW_EHZ_UW__60.dat"
newrsam="D:\Data\RSAM2017\\60\RSAM_20170225_FMW_EHZ_UW__60.csv"
outdir="D:\Data\SSAM2017\Comparison\\RSAMvsSSAM"
### END USER CONFIG ####
os.makedirs(outdir, exist_ok=True)

def parse_filename(filename):
    filename=os.path.basename(filename) # strip out directory
    filename=filename.replace(".dat","")
    parts=filename.split("_")
    if parts[0]=="RSAM":    # assume file being read was created from this module.
        version="RSAM"
        date=parts[1]
        station=parts[2]
        channel=parts[3]
        network=parts[4]
        location=parts[5]
        duration=parts[6]   # not used
    else:                   # assume file being read is from old SSAM2Disk output
        version="Legacy_RSAM"
        date=parts[0]
        station=parts[1]
        channel=parts[2]
        network=parts[3]
        location=""
        duration=60
    return [version, date, station, channel, network, location, duration]

foldssam=open(oldssam)
fnewssam=open(newssam)
fnewrsam=open(newrsam)
ost=[]  # old ssam time
osd=[]  # old ssam data (avg)
nst=[]  # new ssam time
nsd=[]  # new ssam data
nrt=[]  # new rsam time
nrd=[]  # new rsam data
for line in foldssam:        
    row=line.split(" ")
    row[-1]=row[-1].rstrip()
    ost.append(row[1].replace(":",""))
    numdata=[int(d) for d in row[2:]]
    #savg=np.mean(numdata)
    #osd.append(int(savg))
    ssum=np.sum(numdata)
    osd.append(ssum)
for line in fnewssam:        
    row=line.split(" ")
    row[-1]=row[-1].rstrip()
    t=row[1].replace(":","")
    if t in ost:
        nst.append(t)
        numdata=[int(d) for d in row[2:]]
        #savg=np.mean(numdata)
        #nsd.append(int(savg))
        ssum=np.sum(numdata)
        nsd.append(ssum)
for line in fnewrsam:        
    row=line.split(",")
    row[-1]=row[-1].rstrip()
    dt=row[0].split(" ")
    t=dt[1][0:5].replace(":","")
    if t in ost:
        nrt.append(t)
        nrd.append(int(row[1]))
        
outfile=""
info=parse_filename(newrsam)
for i in info:
    outfile+="%s_"%i
outfile=outfile.replace(".csv","")

outfile=os.path.join(outdir,"%svsSSAM.txt"%(outfile))
f=open(outfile,"w")
#print(len(ost), len(osd), len(nst), len(nsd), len(nrt), len(nrd))
for i in range(0,len(ost)):
    if ost[i] != nst[i] or ost[i] != nrt[i]:
        print("ERROR - TIMES DO NOT MATCH!!")
        print(ost[i], nst[i], nrt[i])
        break
    print(ost[i], osd[i], nsd[i], nrd[i])
    f.write("%s %s %s %s\n"%(ost[i], osd[i], nsd[i], nrd[i]))
f.close()
foldssam.close()
fnewssam.close()
fnewrsam.close()
    
    
