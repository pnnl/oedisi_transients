"""
Daniel Glover
move pl4 files into local directory
script converts .pl4 files from ATP ---> .mat files v4 ---> .mat files v6
*must have GNU Octave installed on local machine and oct2py in local environment
*GTPPL32.exe must be in local directory
"""

import os
import subprocess
import time
import h5py
import hdf5storage as h5
from scipy.io import loadmat
import shutil


# To identify the pl4 files in the current directory
def id_pl4_cases(address):
    files = os.listdir(address)
    pl4_files = []
    for file in files:
        if '.pl4' in file:
            pl4_files.append(file)
        else:
            pass
    return pl4_files


outputfilecur = os.getcwd()
feeder_root = "C:\ATP\OEDI_ATP_Models"
feeder = "IEEE13"
# feeder = "IEEE123"
inputfilecur = os.path.join(feeder_root, feeder, 'results')
# inputfilecur = 'Examples'
if not os.path.isdir(inputfilecur):
    inputfilecur = os.getcwd()

# get all the .pl4 files in the inputfilecur directory
pl4filenames = id_pl4_cases(inputfilecur)  # list of pl4s
# loop all the .pl4 files to run gtppl32.exe and get the corresponding .mat files
skip_pl4_conversion = False
if not skip_pl4_conversion:
    for ifile in pl4filenames:
        # rename file since gtppl32 replaces the last two bytes with 01 (sometimes it appends?)
        ifile2 = ifile.split('.')[:-1] 
        ifile2[-1] += '_00' 
        ifile2 += [ifile.split('.')[-1]]
        ifile2 = '.'.join(ifile2)
        shutil.copyfile(os.path.join(inputfilecur,ifile), os.path.join(inputfilecur, ifile2))
        p = subprocess.Popen([r'C:\ATP\gtppl32\GTPPL32.exe ', ifile2], cwd=inputfilecur, shell=True,
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = p.communicate(b'matlab all \n stop\n')
        print(output.decode('utf-8'))
        print('error:', err.decode('utf-8'))
        print('Exit code:', p.returncode)
        os.remove(os.path.join(inputfilecur, ifile2))
        print('-------------finished run gtppl32.exe for file ' + ifile + '-------------')
    
    time.sleep(1)
    print('finished converting .pl4 to .mat')


# now gather .mat files in list for conversion to v6 using octave
def id_mat_files(address):
    files = os.listdir(address)  # puts all files in current dir into list
    matlab_files = []
    for file in files:
        if '.mat' in file:
            matlab_files.append(file)
        else:
            pass
    return matlab_files


mat_files = id_mat_files(inputfilecur)

# must have GNU Octave (GUI) installed on local machine with octave.exe path in environment variable path!!
def convert_mat_files(file_list, inputfilecur):
    from oct2py import octave
    octave.restart()
    octave.eval("cd " + inputfilecur)
    print('starting octave conversion')
    for mat_file in file_list:
        octave.eval("load " + str(mat_file))
        octave.eval("save -v6 " + str(mat_file))  # change .mat version, save in local path
    print('finished octave conversion, exiting octave')
    octave.exit()

skip_mat_version = False
if not skip_mat_version:
    convert_mat_files(mat_files, inputfilecur)

time.sleep(1)
# verify .mat file upgrade - uncomment 3 lines below to read a file and check version, data, etc.
# from scipy.io import loadmat
# test1 = loadmat(inputfilecur + r'\<matfilename>.mat')
# print(test1)


# covert v6 matfiles to HDF5 compressed file
def convertToHDF5(inputfilecur):
    matfiles = id_mat_files(inputfilecur)
    data = []  # empty list to store data
    for file in matfiles:
        print("Loading", os.path.join(inputfilecur,file))
        mat = loadmat(os.path.join(inputfilecur,file))
        data.append(mat)
    print("Writing hdf5 file.")
    h5.write(data, path=inputfilecur, filename='training_data.hdf5')  # name of hdf5 file in cwd

convert_to_hdf5 = False
if convert_to_hdf5:
    convertToHDF5(inputfilecur)
    # read file as python variable
    my_file = h5.read(path='Examples', filename='training_data.hdf5')
    print('my HDF5 file', my_file)
