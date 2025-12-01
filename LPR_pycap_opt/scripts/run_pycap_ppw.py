import sys, os
import pyemu
from pycap.analysis_project import Project
from pathlib import Path
import numpy as np
import pandas as pd

def instantiate():
    # instantiate the project with paths and filenames
    datapath = Path('.')
    outputdir = datapath/ 'output'
    pst_name = str(datapath / 'prior_mc.pst')
    pst = pyemu.Pst(
        pst_name
    )
    base_pars = pd.Series(index=pst.parameter_data['parnme'].index,
                        data = pst.parameter_data['parval1'])




    """Instantiate the project with paths and filenames."""
    # only read out year 5 for time series ::: hard coded
    times = range(365*4,365*5+1)

    # read in the base depletion names 
    bdplobs = [i.strip() for i in open(datapath / 'basedeplobs.dat', 'r').readlines()]

    # read in the time series depletion names 
    output_ts = [i.strip() for i in open(datapath / 'ts_obs.dat', 'r').readlines()]


def get_results(pars, pst, bdplobs, output_ts):
    
    pst.parameter_data.loc[pars.index, 'parval1'] = pars.values
    pst.write_input_files()
    yml_file= pst.input_files[0]
    # Run the pycap model
    ap = Project(datapath/yml_file)
    ap.report_responses()
    ap.write_responses_csv()

    bdf = pd.read_csv(outputdir /
        "LPR_Redux.table_report.base_stream_depletion.csv", index_col=0).rename(
            columns={"LPR":"value"})
    bdf.index=[f"LPR:{i}:bdpl" for i in bdf.index]
    bdf = bdf.loc[bdplobs]
    bdf['variable']=bdf.index
    tsdf = pd.read_csv(outputdir / 
                       "LPR_Redux.table_report.all_ts.csv", index_col=0)

    tsdf = tsdf.loc[times][output_ts].melt(ignore_index=False)
    tsdf.index=[f"{j}__{i}" for i,j in zip(tsdf.index,tsdf.variable)]
    allout  = pd.concat([bdf[['variable','value']],
                        tsdf])
    return allout

def ppw_worker_pycap(pst_name, host, port):
    """Worker function for parallel processing."""
    print(os.getcwd())
    instantiate()
    ppw = pyemu.os_utils.PyPestWorker(pst_name,host,port, verbose=False)
    
    while True:
        pvals = ppw.get_parameters()
        if pvals is None:
            break
        allout = get_results(pvals, pst, bdplobs, output_ts)
        ppw.send_observations(allout.loc[ppw.obs_names].values)
     




if __name__== "__main__":
    instantiate()
    allout1 = get_results(base_pars, pst,bdplobs, output_ts)
    print(allout1.head())

    
    # allout.to_csv(datapath / 'allobs.out', sep=' ', header=None)
    # print("All observations written to 'allobs.out'")

