"""
Daniel Glover
move pl4 files into local working directory
script converts .pl4 files from ATP ---> Comtrade (.cfg) and Data (.dat) files in ASCII --> float32 format
*must have GTPPL32.exe and .pl4 files in local directory*
*must have cometradeDT.py and pl42com.py f/OEDI repo in local directory*
"""
import os
from pl42com import pl42com


# To identify the pl4 files in the current directory
def id_pl4_cases(address):
    files = os.listdir(address)
    pl4_files = []
    for file in files:
        if '.pl4' in file:
            file = file.replace('.pl4', '')
            pl4_files.append(file)
        else:
            pass
    return pl4_files


# get all the .pl4 files in the current working directory
pl4filenames = id_pl4_cases(os.getcwd())  # list of pl4s


# convert pl4 files
def convert2Comtrade(pl4_list):
    for pl4_file in pl4_list:
        pl42com(pl4_file)


convert2Comtrade(pl4filenames)
