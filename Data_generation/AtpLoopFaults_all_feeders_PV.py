# -*- coding: utf-8 -*-
"""
Created on Fri Feb 10 17:53:28 2023

@author: chat694 Kaustav Chatterjee PNNL
modified by Matt Cornachione to generate simulations for multiple feeders
"""

import math
import sys
import operator
import subprocess
import os
import shutil
import random
import msvcrt
from pynput.keyboard import Key, Controller
import pandas as pd
import numpy as np
import csv
import time

no_sims = 1000

def run_atp_fault_case(bus, phs, slgf, fname):
    tfault = random.uniform(0.15, 0.15 + 1/60)
    extra_period = np.ceil(1/60./atp_dt) # extra time intervals in one period, rounded up
    extra_time = extra_period*atp_dt*(1+np.random.rand()) # one - two extra periods
    vsrc = '{:.2f}'.format (atp_vpu * source_vbase)
    fp = open (atp_parm, mode='w')
    print ('$PARAMETER', file=fp)
    print ('_FLT_=\'' + bus.ljust(5) + '\'', file=fp)
    print ('__DELTAT   ={:.10f}'.format (atp_dt), file=fp)
    tmax = 0.4 + extra_time # Add time to 1) avoid startup transients 2) vary starting phase angle
    print (f'____TMAX   ={tmax}', file=fp)
    print ('_VSOURCE__ =' + vsrc, file=fp)
    # Vary the starting phase (This doesn't work because ATP always starts at the same phase)
    vary_phase = False
    if vary_phase:
        freq_base = 60 #np.random.rand()*360
        freqa = f'{freq_base:0.3f}'#.rjust(10)
        freqb = f'{freq_base-120:0.3f}'#.rjust(10)
        freqc = f'{freq_base-240:0.3f}'#.rjust(10)
        print(f'__FREQ_A__ ={freqa}', file=fp)
        print(f'__FREQ_B__ ={freqb}', file=fp)
        print(f'__FREQ_C__ ={freqc}', file=fp)
    # Update the _PV.atp file with a random network configuration
    update_network = True
    if update_network:
        load_num = np.random.randint(3)+1
        pv_num = np.random.randint(2)+1
        network_file = f'IEEE13_PV_L{load_num}C{pv_num}_net.atp'
        with open(os.path.join(atp_path,f'{feeder}_PV.atp'), 'r') as f:
            atp_lines = f.readlines()
        for i, line in enumerate(atp_lines):
            if '_net.atp' in line:
                newline = f'$INCLUDE, {network_file}\n'
                atp_lines[i] = newline
        with open(os.path.join(atp_path,f'{feeder}_PV.atp'), 'w') as f:
            f.writelines(atp_lines)
    if slgf == True:  # line-to-gnd fault
        if phs == 'A':
            print ('_TFAULTA__ ={:.5f}'.format (tfault), file=fp)
            # print ('_TFAULTA__ =9.15', file=fp)
            print ('_TFAULTB__ =9.15', file=fp)
            print ('_TFAULTC__ =9.15', file=fp)
            # print ('_TFAULTBC_ =9.15', file=fp)
        elif phs == 'B':
            print ('_TFAULTA__ =9.15', file=fp)
            print ('_TFAULTB__ ={:.5f}'.format (tfault), file=fp)
            # print ('_TFAULTB__ =9.15', file=fp)
            print ('_TFAULTC__ =9.15', file=fp)
            # print ('_TFAULTBC_ =9.15', file=fp)
        else:
            print ('_TFAULTA__ =9.15', file=fp)
            print ('_TFAULTB__ =9.15', file=fp)
            # print ('_TFAULTC__ =9.15', file=fp)
            print ('_TFAULTC__ ={:.5f}'.format (tfault), file=fp)
            # print ('_TFAULTBC_ =9.15', file=fp)
    elif phs == 'AB':
        print ('_TFAULTA__ ={:.5f}'.format (tfault), file=fp)
        print ('_TFAULTB__ ={:.5f}'.format (tfault), file=fp)
        # print ('_TFAULTA__ =9.15', file=fp)
        # print ('_TFAULTB__ =9.15', file=fp)
        print ('_TFAULTC__ =9.15', file=fp)
        # print ('_TFAULTBC_ =9.15', file=fp)
    elif phs == 'BC':
        print ('_TFAULTA__ =9.15', file=fp)
        # print ('_TFAULTB__ =9.15', file=fp)
        # print ('_TFAULTC__ =9.15', file=fp)
        print ('_TFAULTB__ ={:.5f}'.format (tfault), file=fp)
        print ('_TFAULTC__ ={:.5f}'.format (tfault), file=fp)
        # print ('_TFAULTBC_ =9.15', file=fp)
    elif phs == 'AC' :
        # print ('_TFAULTA__ =9.15', file=fp)
        print ('_TFAULTA__ ={:.5f}'.format (tfault), file=fp)
        print ('_TFAULTB__ =9.15', file=fp)
        # print ('_TFAULTC__ =9.15', file=fp)
        print ('_TFAULTC__ ={:.5f}'.format (tfault), file=fp)
        # print ('_TFAULTBC_ =9.15', file=fp)
    elif phs == 'ABC':
        print ('_TFAULTA__ ={:.5f}'.format (tfault), file=fp)
        print ('_TFAULTB__ ={:.5f}'.format (tfault), file=fp)
        print ('_TFAULTC__ ={:.5f}'.format (tfault), file=fp)
    else:
        print ('_TFAULTA__ =9.15', file=fp)
        print ('_TFAULTB__ =9.15', file=fp)
        print ('_TFAULTC__ =9.15', file=fp)
        print ('_TFAULTBC_ =9.15', file=fp)
    print ('BLANK END PARAMETER', file=fp)
    fp.close()        
    
    cmdline = "runtp " + atp_file + " >nul"
    
    p1 = subprocess.Popen(cmdline, cwd=atp_path, shell=True)
    p1.wait()
    
    # move the pl4 file
    print ('moving {:s} to {:s}'.format (atp_pl4, fname))
    shutil.move(atp_pl4, fname)

def check_pv_phase(pv_phase, bus_phase):
    '''
    Checks to see if the pv_phase is included in the bus_phase
    If pv_phase is 'ABC' this always returns true
    Also returns a list of acceptable phases to use
    '''
    pv_set = set(pv_phase)
    if pv_set == set('ABC'):
        return True, ['A', 'B', 'C']
    else:
        ok_phases = []
        for phase in pv_set:
            if phase in set(bus_phase):
                ok_phases.append(phase)
        if len(ok_phases) == 0:
            pv_ok = False
        else:
            pv_ok = True
        return pv_ok, ok_phases

# List of all the feeders to simulate
feeder_names = ['IEEE13'] #['IEEE13'], ['IEEE123']
# Dictionary of the bus location and phases (atp numbering) of the largest PV
largest_pv = {'IEEE13': {'bus':4, 'phases':'ABC'}, 'IEEE123': {'bus':4, 'phases':'ABC'}}
for feeder in feeder_names:
    atp_base = f'{feeder}_PV'
    atp_path = f"C:/ATP/OEDI_ATP_Models/{feeder}/"
    atp_file = atp_base + '.atp'
    atp_list = atp_path + atp_base + '.lis'
    atp_parm = atp_path + atp_base + '.prm'
    atp_pl4 = atp_path + atp_base + '.pl4'
    pl4path = f"C:/ATP/OEDI_ATP_Models/{feeder}/results"
    source_vbase = float(3396.625777) #float(10181.71)
    atp_vpu = float(1.035)
    atp_dt = float(1e-4)
    
    if feeder == 'IEEE123':
        zone_filename = 'zone_info_IEEE123_PV_v2.csv'
    else:
        zone_filename = f'zone_info_{feeder}_PV.csv'
    zones = pd.read_csv(zone_filename)  # read csv from zone classification file
    
    use_zone = 'all'
    if use_zone == 'all':
       zone = np.array(())
       for z in zones.columns:
           zone = np.append(zone, zones[z].dropna().values)
    else:
        if use_zone in zones.columns:
            zone = zones[use_zone]  # zones.zone_35
            zone = zone.dropna()
        else:
            raise ValueError(f"Zone {use_zone} not found in {zone_filename}")
    t_start = time.time()
    for times in range(no_sims):
        phase_ok = False
        # Loop through buses until we find one that includes the PV phase(s)
        while not phase_ok:
            ln=random.choice(zone)
            toks = ln.split('_')
            bus = toks[0]
            atpbus = toks[0]
            nph = len(toks[1])
            phs = toks[1]
            phase_ok, use_phases = check_pv_phase(largest_pv[feeder]['phases'], phs)

        # Limit to a single fault per sim
        phase_ok = False
        while not phase_ok:
            if nph == 3:
                case = random.randint(0, 6)
                phase_list = ['ABC', 'AB', 'BC', 'AC', 'A', 'B', 'C']
                sel_phs = phase_list[case]
            elif nph == 2:
                case = random.randint(0, 2)
                phase_list = [phs] + list(phs)
                sel_phs = phase_list[case]
            else:
                sel_phs = phs
            # Check if the selected fault covers at least one of the PV phases
            phase_ok = not set(use_phases).isdisjoint(sel_phs)
        phs = sel_phs
        
        # Run a no-fault trial for the first half of the simulation
        if times <= int(no_sims/2):
            phs = ''
            
        # Set pl4name and message depending on number of phases
        if phs == '':
            pl4name = pl4path + '/' + 'NoFault' + str(times) + '.pl4'
            print ('running no fault case, output to {:s}'.format (pl4name))
        elif len(phs) == 3:
            pl4name = pl4path + '/' + 'F3_' + atpbus + phs + str(times) + '.pl4'
            print ('running three-phase fault at {:s} ({:s}), output to {:s}'.format (atpbus, bus, pl4name))
        elif len(phs) == 2:
            pl4name = pl4path + '/' + 'F2_' + atpbus + phs + str(times) + '.pl4'
            print ('running two-phase fault at {:s} ({:s}), output to {:s}'.format (atpbus, bus, pl4name))
        else:
            pl4name = pl4path + '/' + 'F1_' + atpbus + phs + str(times) + '.pl4'
            print ('running SLGF on {:s} at {:s} ({:s}), output to {:s}'.format (phs, atpbus, bus, pl4name))
        run_atp_fault_case(atpbus, phs, slgf=(len(phs)==1), fname=pl4name)
    t_end = time.time()
    print(f"Running {no_sims} cases on feeder {feeder} took {t_end-t_start:.3f}s")

# Once done we can run all of the other file generation scripts
# For now just importing them and they will run, but we should
# make this into a proper workflow at some point
convert = True
if convert:
    convert_comtrade=True
    convert_mat=True
    convert_csv=True
    compress=True
    if convert_comtrade:
        print("\nStarting pl4 to Comtrade conversion\n")
        import pl4_to_comtrade
    if convert_csv:
        print("\nStarting Comtrade to csv conversion\n")
        cmdline = f'python comtrade_to_csv -d "{pl4path}"'
        p1 = subprocess.Popen(cmdline, cwd=os.getcwd(), shell=True)
        p1.wait()
    if convert_mat:
        print("\nStarting pl4 to mat conversion\n")
        import gen_con_matfiles
    if compress:
        print("\nStarting npz and hdf5 compression\n")
        import gen_npz
