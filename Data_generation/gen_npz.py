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

def id_mat_files(address, name_match=None):
    ''' Returns a list of matlab files in a directory with option to match name patters'''
    files = os.listdir(address)  # puts all files in current dir into list
    matlab_files = []
    for file in files:
        if '.mat' in file:
            # Option to skip file if name_match isn't part of the filename
            if name_match is not None:
                if name_match not in file:
                    continue
            matlab_files.append(os.path.join(address,file))
        else:
            pass
    return matlab_files

def convert_to_array(mat_file, time_limit=0.4, tstart=0, vnominal=None, pnominal=None, atpdraw_dict=None):
    ''' Time limit: max number of seconds to save
        vnominal is specified as peak voltage (V L-L *sqrt(2/3) or V L-N *sqrt(2))
        pnominal is specified in kW total (sum of all three phases)
        if atpdraw_dict is specified it helps parse outputs
       '''
    mf_dict = sc.io.loadmat(mat_file)
    # Pre-determine array size for PV###A,B,C,X,Y,Z
    if atpdraw_dict is None:
        use_keys = [k for k in mf_dict.keys() if 'PV' in k.upper() and \
                    k[-1] in ['A', 'B', 'C', 'X', 'Y', 'Z']]
    else:
        name_key = atpdraw_dict['name_key']
        current_format = atpdraw_dict['current_format'] # Either 'XYZ' or 'dash'
        name_list = ['A', 'B', 'C']
        if current_format == 'XYZ':
            name_list += ['X', 'Y', 'Z']
        use_keys = [k for k in mf_dict.keys() if name_key.upper() in k.upper() and \
                    k[-1] in name_list]
        if current_format == 'XYZ':
            use_keys = sorted(use_keys)
        elif current_format == 'dash':
            # Ensuring order is voltage A, B, C then current A, B, C
            ordered_keys = [0 for k in use_keys]
            for k in use_keys:
                first = k[0].upper()
                last = k[-1]
                cnt_dict = {'A':0, 'B':1, 'C':2}
                extra = 0
                if first == 'I':
                    extra += 3
                ordered_keys[cnt_dict[last]+extra] = k
            use_keys = ordered_keys
        else:
            raise ValueError(f'current format {current_format} is not available. Use "XYZ" or "dash"')

    time_arr = mf_dict['t']
    dt = time_arr[1]-time_arr[0] # Assume uniform time sampling
    len_max = int(time_limit/dt + 1)
    len_arr = min(len(mf_dict[use_keys[0]]), len_max)
    # Loop through keys and fill in data array
    pv_data = np.zeros((len_arr, len(use_keys)))
    if tstart != 0:
        textra = np.random.rand()*(1/60.)
        tstart += textra
        sidx = int(tstart/dt)
    for i, key in enumerate(use_keys):
        array = mf_dict[key]
        # Note, we may cut off the initial part of the array to avoid transients and introduce a phase shift
        if tstart == 0:
            pv_data[:,i] = array.reshape((len(array),))[-len_arr:]
        else:
            # Add random cycle shift to start time
            pv_data[:,i] = array.reshape((len(array),))[sidx:sidx+len_max]
    # Now normalize all onto a per-unit scale.
    # If nominal values are not specified, we determine them empirically
    # Note, this assumes voltage/current peak values
    beginning = int(0.15/dt) # We use 0.15 as the start time for the fault
    if vnominal is None:
        vnominal = np.max(pv_data[:beginning,0:3])
    if pnominal is None:
        inominal = np.max(pv_data[:beginning,3:])
    else:
        inominal = 2/3*pnominal/vnominal
    pv_data[:,0:3] /= vnominal
    pv_data[:,3:] /= inominal
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

def set_feeder(fpath=None, feeder=None):
    # Set directory
    if fpath is None:
        feeder_root = "C:\ATP\OEDI_ATP_Models"
    if feeder is None:
        feeder = "IEEE13"
    feeder_path = os.path.join(feeder_root, feeder, 'results')
    if not os.path.isdir(feeder_path):
        print(f'Warning, directory {feeder_path} does not exist')
        print('Defaulting to current working directory')
        feeder_path = os.getcwd()
    return feeder_path

def execute_gen_npz(fpath=None, feeder=None):
    ''' Compresses npz and hdf5 files from faults created by AtpLoopFaults_all_feeders_PV.py '''
    feeder_path = set_feeder(fpath, feeder)
    if feeder is None:
        feeder = "IEEE13"
    
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

def atpdraw_gen_npz(tstart=1.0, twindow=0.4, dt=1e-4, vnominal=None, pnominal=None,
                    merge_with_faults=True, fpath=None, feeder=None):
    ''' Compression algorithm specific to voltage sag events generated in ATPDraw
        This requires matching of ATPDraw parameters and parameters here
    Args:
        tstart(float): the time in seconds at which to start saving for the npz file. Note that
                       this start time will be randomly shifted forward by a fraction of 1 cycle
                       to introduce random phase shifts with time
        twindow(float): the time in seconds to save to the npz file (inclusive of both endpoints)
        dt(float): the time step in seconds
        vnominal(float or None): the nominal peak voltage (V LL * sqrt(2/3))
        pnominal(float or None): the nominal max power output (used for setting current scaling)
        merge_with_faults(bool): if True will attempt to merge with npz file from AtpLoopFaults code
       '''
    feeder_path = set_feeder(fpath, feeder)
    if feeder is None:
        feeder = "IEEE13"
    # The atpdraw dict must match the node name used in atpdraw when generating data
    atpdraw_dict = {'name_key':'N634', 'current_format':'dash'}

    mat_files = id_mat_files(feeder_path, name_match='sag_event')
    # Pre-determine output array size
    pv_data0 = convert_to_array(mat_files[0], time_limit=twindow, tstart=tstart, vnominal=vnominal,
                                pnominal=pnominal, atpdraw_dict=atpdraw_dict)
    all_data = np.zeros((len(mat_files),*pv_data0.shape))
    all_labels = list()
    phases = list()
    atp_bus = list()
    nf_idx = None
    for i, mf in enumerate(mat_files):
        progress_message("Loading file", i+1, len(mat_files))
        all_data[i,:,:] = convert_to_array(mf, time_limit=twindow, tstart=tstart, vnominal=vnominal,
                                           pnominal=pnominal, atpdraw_dict=atpdraw_dict)
        # Save which file is the no fault case (assumes just one for now)
        if 'NoFault' in mf:
            nf_idx = i
            all_labels.append('no_fault')
            phases.append('nan')
            atp_bus.append('nan')
        elif 'sag_event' in mf:
            nf_idx = i
            all_labels.append('sag')
            phases.append('nan')
            atp_bus.append('nan')
        else:
            all_labels.append('fault')
            phs, bus = get_phase_bus(os.path.split(mf)[-1])
            phases.append(phs)
            atp_bus.append(bus)
    print('') # Extra line after progress method  
        
    all_labels = np.array(all_labels, dtype=np.string_)
    phases = np.array(phases, dtype=np.string_)
    atp_bus = np.array(atp_bus, dtype=np.string_)
    save_data = {'data':all_data, 'label':all_labels, 'phase':phases, 'bus':atp_bus}
    # Save compressed files to npz and/or hdf5
    save_npz = True
    if save_npz:
        print('saving compressed npz file')
        if merge_with_faults:
            fault_data = np.load(os.path.join(feeder_path,f'{feeder}_data.npz'))
            # Include new data
            for key in save_data.keys():
                if key == 'data':
                    new_array = np.vstack((fault_data[key],save_data[key]))
                else:
                    new_array = np.hstack((fault_data[key],save_data[key]))
                save_data[key] = new_array
        np.savez_compressed(os.path.join(feeder_path,f'{feeder}_data_sag'), **save_data)
    save_hdf5 = True
    if save_hdf5:
        print('saving hdf5 file')
        with h5py.File(os.path.join(feeder_path,f'{feeder}_data.hdf5'), 'w') as f:
            for key, arr in save_data.items():
                f.create_dataset(key, data=arr, compression='gzip')

if __name__ == '__main__':
    execute_gen_npz()