rem pyinstaller --add-data="site-packages\obspy\imaging\data\*npz;site-packages\obspy\imaging\data" --onedir src\RsamSsam.py --distpath dist2 

pyinstaller -n Rsam2Disk --onefile src\RsamSsam.py --distpath dist