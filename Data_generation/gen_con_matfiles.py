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

print(os.getcwd())


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
inputfilecur = os.getcwd()

'''!!!!!!!!!it seems the gtppl32.exe only works for the pl4 files in the same folder of the calling
  gtppl32.exe python script, not sure why.'''

# get all the .pl4 files in the inputfilecur directory
pl4filenames = id_pl4_cases(inputfilecur)  # list of pl4s
# loop all the .pl4 files to run gtppl32.exe and get the corresponding .mat files
for ifile in pl4filenames:
    p = subprocess.Popen([r'C:\ATP\gtppl32\GTPPL32.exe ', ifile], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    output, err = p.communicate(b'matlab all \n stop\n')
    print(output.decode('utf-8'))
    # print('error:', err.decode('utf-8'))
    print('Exit code:', p.returncode)
    print('-------------finished run gtppl32.exe for file ' + ifile + '-------------')

time.sleep(3)
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
def convert_mat_files(file_list):
    from oct2py import octave
    octave.restart()
    octave.eval("cd " + inputfilecur)
    print('starting octave conversion')
    for mat_file in file_list:
        octave.eval("load " + str(mat_file))
        octave.eval("save -v6 " + str(mat_file))  # change .mat version, save in local path
    print('finished octave conversion, exiting octave')
    octave.exit()


convert_mat_files(mat_files)

time.sleep(3)
# verify .mat file upgrade - uncomment 3 lines below to read a file and check version, data, etc.
# from scipy.io import loadmat
# test1 = loadmat(inputfilecur + r'\<matfilename>.mat')
# print(test1)


# covert v6 matfiles to HDF5 compressed file
def convertToHDF5():
    matfiles = id_mat_files(os.getcwd())
    data = []  # empty list to store data
    for file in matfiles:
        mat = loadmat(file)
        data.append(mat)
    h5.write(data, path=os.getcwd(), filename='training_data.hdf5')  # name of hdf5 file in cwd


# convertToHDF5()
# read file as python variable
# my_file = h5.read(path=os.getcwd(), filename='training_data.hdf5')
# print('my HDF5 file', my_file)
