import os
import numpy as np
import h5py
import shutil
import subprocess

if __name__ == '__main__':
    # Set directories
    emtp_path = 'C:\EMTP\\atpdraw\\results'
    emtp_name = 'OEDI_IEEE13_with_Gen_and_PV_Variables_save_PV.pl4'

    feeder_root = "C:\ATP\OEDI_ATP_Models"
    feeder = "IEEE13"
    feeder_path = os.path.join(feeder_root, feeder, 'results')
    if not os.path.isdir(feeder_path):
        feeder_path = os.getcwd()

    # Copy ATPDraw results into the feeder results folder
    nmax = None # Option to limit the number of simulation results
    rdirs = sorted([rd for rd in os.listdir(emtp_path) if os.path.isdir(os.path.join(emtp_path,rd))])
    if nmax is not None:
        rdirs = rdirs[:(nmax-1)]
    # Move the '0' pl4 file in emtp_path
    copy = True
    if copy:
        shutil.copy(os.path.join(emtp_path,emtp_name),os.path.join(feeder_path,f'sag_event0.pl4'))
        # Now move all of the results from the simulation folders
        for i, rd in enumerate(rdirs):
            shutil.copy(os.path.join(emtp_path,rd,emtp_name), os.path.join(feeder_path,f'sag_event{i+1}.pl4'))

    # Now run the file conversions
    convert = True
    if convert:
        convert_comtrade = True
        convert_mat = True
        convert_csv = True
        compress = True
        if convert_comtrade:
            print("\nStarting pl4 to Comtrade conversion\n")
            import pl4_to_comtrade
        if convert_csv:
            print("\nStarting Comtrade to csv conversion\n")
            cmdline = f'python comtrade_to_csv.py -d "{feeder_path}"'
            p1 = subprocess.Popen(cmdline, cwd=os.getcwd(), shell=True)
            p1.wait()
        if convert_mat:
            print("\nStarting pl4 to mat conversion\n")
            import gen_con_matfiles
        if compress:
            print("\nStarting npz and hdf5 compression\n")
            import gen_npz
            vnominal = 480*np.sqrt(2/3) # peak voltage
            pnominal = 240 # kW
            gen_npz.atpdraw_gen_npz(vnominal=vnominal, pnominal=pnominal)
    