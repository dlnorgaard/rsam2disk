#!/bin/bash


#pyinstaller -n Rsam2Disk --clean --hidden-import=scipy._lib.messagestream --onefile src/RsamSsam.py --distpath dist
#pyinstaller -n Rsam2Disk --clean --onefile src/RsamSsam.py --distpath dist
pyinstaller Rsam2Disk.spec