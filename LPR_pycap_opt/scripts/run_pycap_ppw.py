import sys
import pyemu
from pycap.analysis_project import Project
from pathlib import Path
import numpy as np
import pandas as pd

# instantiate the project with paths and filenames
datapath = Path('.')
outputdir = datapath/ 'output'
pst = pyemu.Pst(
    datapath / 'pycap.pst'
)
base_pars = pd.Series(index=pst.parameter_data['parnme'].index,
                      data = pst.parameter_data['parval1'])
new_pars = base_pars.copy()
new_pars.values = new_pars.values + np.random.random(len(new_pars)) * 0.01


"""Instantiate the project with paths and filenames."""
# only read out year 5 for time series ::: hard coded
times = range(365*4,365*5+1)

# read in the base depletion names and then the values
bdplobs = pd.read_csv(datapath / 'basedeplobs.dat', header=None)
bdplobs.columns = ['obsname']
bdplobs.index = bdplobs.obsname
bdplobs['obs_values'] = np.nan
# read in the time series depletion names and then the values
output_ts = [i.strip() for i in open(datapath / 'ts_obs.dat', 'r').readlines()]

ts_obs = []
for c_ts in output_ts:
    ts_obs.extend([f'{c_ts}__{i}' for i in times]) 
ts_df = pd.DataFrame(index = ts_obs, data = {'obsname':ts_obs,'obs_values':np.nan})
allout = pd.concat([bdplobs,ts_df])

def get_results(pars, pst, allout, bdplobs, ts_df):
    pst.parameter_data.loc[pars.index, 'parval1'] = pars.values
    pst.write_input_files()

    # Run the pycap model
    ap = Project(datapath/pst.input_files[0])
    ap.report_responses()
    ap.write_responses_csv()

    base_data = pd.read_csv(
        outputdir/f'{yml_file.replace(".yml","")}.table_report.base_stream_depletion.csv', index_col=0)

    for cob in bdplobs.obsname:
        riv,wel,_ = cob.split(':')
        print(cob)
        allout.loc[cob, 'obs_values'] = base_data.loc[wel][riv]


    ts_data = pd.read_csv(
        outputdir/f'{yml_file.replace(".yml","")}.table_report.all_ts.csv', index_col=0) 
    for cob in ts_df.index:
        criv,ctime = cob.split('__')
        allout.loc[cob,'obs_values'] = ts_data.loc[int(ctime)][criv]    

    return allout


    # write out all the observations
    allout['obs_values'].to_csv(datapath / 'allobs.out', sep = ' ', header=None)
if __name__== "__main__":
    allout1 = get_results(base_pars, pst, allout, bdplobs, ts_df)
    print(allout1.head())
    allout2 = get_results(new_pars, pst, allout, bdplobs, ts_df)        
    print(allout2.head())
    
    # allout.to_csv(datapath / 'allobs.out', sep=' ', header=None)
    # print("All observations written to 'allobs.out'")

