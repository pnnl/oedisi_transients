# -*- coding: utf-8 -*-
"""
Created on Wed Feb 21 19:43:06 2024

@author: corn677
"""

import numpy as np
import scipy as sc
import os
import sys
import h5py

def id_mat_files(address):
    files = os.listdir(address)  # puts all files in current dir into list
    matlab_files = []
    for file in files:
        if '.mat' in file:
            matlab_files.append(os.path.join(address,file))
        else:
            pass
    return matlab_files

def convert_to_array(mat_file, time_limit=0.4):
    ''' Time limit: max number of seconds to save
       '''
    mf_dict = sc.io.loadmat(mat_file)
    # Pre-determine array size for PV###A,B,C,X,Y,Z
    use_keys = [k for k in mf_dict.keys() if 'PV' in k.upper() and \
                k[-1] in ['A', 'B', 'C', 'X', 'Y', 'Z']]
    time_arr = mf_dict['t']
    dt = time_arr[1]-time_arr[0] # Assume uniform time sampling
    len_max = int(time_limit/dt + 1)
    len_arr = min(len(mf_dict[use_keys[0]]), len_max)
    # Loop through keys and fill in data array
    pv_data = np.zeros((len_arr, len(use_keys)))
    for i, key in enumerate(use_keys):
        array = mf_dict[key]
        # Note, we may cut off the initial part of the array to avoid transients and introduce a phase shift
        pv_data[:,i] = array.reshape((len(array),))[-len_arr:]
    return pv_data

def progress_message(pre_message, cnt, cmax):
    sys.stdout.write('\r')
    sys.stdout.write(f'{pre_message} {cnt}/{cmax}')
    sys.stdout.flush()

def get_phase_bus(fname):
    ''' Extracts the phase and bus from a filename assuming input format:
        fname= F[#phases]_[bus][phase(s)][cnt] (possibly with _0001 from matlab conversion)
        Special handling is included for adjacent feeders (ADJ#)
    '''
    str_block = fname.split('_')[1]
    if 'ADJ' in str_block:
        bus = str_block[:4]
        found_bus = True
        str_block = str_block[4:]
    else:
        bus = ''
        found_bus = False
    phase = ''
    found_phase = False
    idx = 0
    while found_bus == False or found_phase == False:
        if not str_block[idx].isalpha() and not found_bus:
            bus += str_block[idx]
        elif str_block[idx].isalpha():
            found_bus = True
            phase += str_block[idx]
        else:
            found_phase = True
        idx += 1
    return phase, bus

# Set directory
feeder_root = "C:\ATP\OEDI_ATP_Models"
feeder = "IEEE13"
feeder_path = os.path.join(feeder_root, feeder, 'results')
if not os.path.isdir(feeder_path):
    feeder_path = os.getcwd()
   
mat_files = id_mat_files(feeder_path)
# Pre-determine output array size
pv_data0 = convert_to_array(mat_files[0])
extr_nofault = 0 # Additional number of no fault cases to add
all_data = np.zeros((len(mat_files)+extr_nofault,*pv_data0.shape))
all_labels = list()
phases = list()
atp_bus = list()
nf_idx = None
for i, mf in enumerate(mat_files):
    progress_message("Loading file", i+1, len(mat_files))
    all_data[i,:,:] = convert_to_array(mf)
    # Save which file is the no fault case (assumes just one for now)
    if 'NoFault' in mf:
        nf_idx = i
        all_labels.append('no_fault')
        phases.append('nan')
        atp_bus.append('nan')
    else:
        all_labels.append('fault')
        phs, bus = get_phase_bus(os.path.split(mf)[-1])
        phases.append(phs)
        atp_bus.append(bus)
print('') # Extra line after progress method  

if extr_nofault > 0:
    # Add on extra no fault cases so we have equal numbers of faults/no faults
    if nf_idx is None:
        raise IndexError(f"Failed to find a no-fault case in the directory {feeder_path}")
    pv_nofault = convert_to_array(mat_files[nf_idx])
    for j in range(extr_nofault):
        all_data[j+len(mat_files),:,:] = pv_nofault
        all_labels.append('no_fault')
        phases.append('nan')
        atp_bus.append('nan')
    
all_labels = np.array(all_labels, dtype=np.string_)
phases = np.array(phases, dtype=np.string_)
atp_bus = np.array(atp_bus, dtype=np.string_)
save_data = {'data':all_data, 'label':all_labels, 'phase':phases, 'bus':atp_bus}
# Save compressed files to npz and/or hdf5
save_npz = True
if save_npz:
    print('saving compressed npz file')
    np.savez_compressed(os.path.join(feeder_path,f'{feeder}_data'), **save_data)
save_hdf5 = True
if save_hdf5:
    print('saving hdf5 file')
    with h5py.File(os.path.join(feeder_path,f'{feeder}_data.hdf5'), 'w') as f:
        for key, arr in save_data.items():
            f.create_dataset(key, data=arr, compression='gzip')
