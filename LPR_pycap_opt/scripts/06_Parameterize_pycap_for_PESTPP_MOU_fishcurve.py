#!/usr/bin/env python
# coding: utf-8

# # Set up Pycap LPR to operate with PEST++ for optimization using fish response curves

import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import pyemu
import geopandas as gp
import matplotlib.pyplot as plt
import os, shutil, platform, zipfile
from ipywidgets import interact
import dash
from dash import html, dcc, Input, Output
import plotly.express as px
import folium
from shapely.geometry import MultiPoint
import matplotlib
import matplotlib.colors as mcolors


def prepare_MOU_files():

    #### PyCap Run Name is what all your outputs will have as a name. 
    pycap_run_name = "LPR_Redux"

    #### Base directory for runs
    parent_run_path = Path("../pycap_runs")

    #### depletion potential calculations directory
    base_run_path = parent_run_path / "pycap_base"
    pest_path = parent_run_path / "pycap_pest"
    template_path = pest_path / "pycap_mou_fish_template"
    fish_path = Path('../Inputs/fish_curves')
    # assume that if run_mou is false, it's already been run
    if template_path.exists():
        shutil.rmtree(template_path)
    template_path.mkdir(parents=True)

    #### finally define the scripts directory
    script_path = Path("../scripts")

    #### Path at which to run MOU
    MASTER_path = pest_path / "MASTER_mou_fish"


    # ### Let's check out the fish curves 
    ref_q = 8.6

    # # Parameterization for PEST++ 


    if not template_path.exists():
        template_path.mkdir(parents=True)


    # #### let's load up the configuration file


    with open(base_run_path / f"{pycap_run_name}.yml", 'r') as ifp:
            indat = yaml.safe_load(ifp)


    # #### and now parameterize inputs to vary in optimization. This will only be pumping rates for now
    # 
    # First we set up template (`TPL`) files that allow PEST++ to update model input values by name. We do this by reading in the input (`YML`) file and replacing numeric values with updated values being changed by the algorithm.

    # well-by-well pumping rates
    well_keys = [i for i in indat.keys() if i.startswith('well_')]
    pending_wells = [i for i in well_keys if 'pending' in indat[i]['status']]

    pars = list()
    parvals = list()

    # then again for pumping rate Q
    for k in well_keys:
        cpar = f'{k}__q'
        pars.append(cpar)
        parvals.append(indat[k]['Q'])
        indat[k]['Q'] = f'~{cpar:^45}~'


    # save out tpl file
    with open(template_path / f"{pycap_run_name}.yml.tpl", 'w') as ofp:
        ofp.write('ptf ~\n')
        documents = yaml.dump(indat, ofp, default_flow_style = False, sort_keys = False)


    # create DataFrame of parameters
    pars_df = pd.DataFrame(index = pars, data= {'parval1':parvals})


    # ### Next we need to be able to read in model ouputs to PEST++
    # Now we write an instruction file (`INS`) that can navigate model output and read it into PEST++

    # make ins file and external forward run file
    # set base case depletion observations
    basedeplobs = [f"{indat[k]['name']}:bdpl" for k in indat.keys() if 'stream' in k]

    # get list of unique stream names used in the run
    unique_rivers = list(set([i.split(':')[0] for i in basedeplobs]))

    # add in the totals/sums of proposed/existing/combined depletions for each stream
    basedeplobs.extend([f'{i}:{j}:bdpl' for i in unique_rivers for j in ['total_proposed','total_existing','total_combined']])

    with open(template_path / 'basedeplobs.dat','w') as ofp:
        [ofp.write(i + '\n') for i in basedeplobs]


    # ### Now read in the base case observation values for depletion data

    base_data = pd.read_csv(base_run_path/"output" / f'{pycap_run_name}.table_report.base_stream_depletion.csv', index_col=0)
    # read in the observation names and make a DataFrame to keep the results in
    bdplobs = pd.read_csv(template_path/'basedeplobs.dat', header=None)
    bdplobs.columns =['obsname']
    bdplobs.index = bdplobs.obsname
    bdplobs['obs_values'] = np.nan

    # now map the actual output values to the DataFrame
    for cob in bdplobs.obsname:
        riv,wel,_ = cob.split(':')
        bdplobs.loc[cob, 'obs_values'] = base_data.loc[wel][riv]
    bdplobs.loc['fish_prob'] = ['fish_prob',100.0]


    # ### We can combine all the outputs into a single dataframe and make the instruction file we'll need to read in the results


    bdplobs['obs_values'].to_csv(template_path / 'allobs.out', sep = ' ', header=None)

    with open(template_path / 'allobs.out.ins', 'w') as ofp:
        ofp.write('pif ~\n')
        [ofp.write(f'l1 w !{i}!\n') for i in bdplobs.index]


    # ### Now we need to make a PEST control file to orchestrate everything. Luckily, `pyemu` makes this straightforward now that we have made the `tpl` and `ins` files 

    cwd = os.getcwd()
    os.chdir(template_path)
    pst = pyemu.Pst.from_io_files(*pyemu.utils.parse_dir_for_io_files('.'))
    os.chdir(cwd)

    pars = pst.parameter_data
    obs = pst.observation_data


    # # let's clean up some of the data and add important values
    # name paramter groups according to the type of parameter
    pars.loc[pars.parnme.str.endswith("q"), "pargp"] = "pumping"
    # set initial values
    pars.loc[pars_df.index,'parval1'] = pars_df.parval1

    del_pump = .2 #(as a fraction)
    # set upper and lower bounds on pumping rates as well - initially allow wells to go down to 0 or increase to 1.2x
    pars.loc[pars.pargp=="pumping","parlbnd"] = 0 
    pars.loc[pars.pargp=="pumping", "parubnd"] = pars.loc[pars.pargp=="pumping", "parval1"]*(1+del_pump)
    pars.partrans = 'none'

    # ### We need to make some definitions for multi-objective optimization algorithm (MOU)

    # ### first, optionally, we can consider only the wells greater than a specified depletion potential threshold be managed.
    # ### Do this by setting the variable `dp_thresh`

    dp = gp.read_file(base_run_path / 'depletion_potential.json')
    dp.set_index('index', inplace=True)
    dp_thresh = 0.01



    dp.loc[dp.Depletion_Potential>= dp_thresh].explore(column="Depletion_Potential",
                    vmin=0,vmax=1,
                    style_kwds={"style_function":
                                    lambda x: 
                                    {"radius":x["properties"]["Depletion_Potential"]*15}})


    # ### now let's assign only the wells exceeding the depletion potential threshold to be adjustable (e.g. "decision variables" or "decvars")

    pars["wellname"] = [i.split("__")[0] for i in pars.index]
    pars.loc[pars.wellname.isin(dp.loc[dp.Depletion_Potential >= dp_thresh].index),'pargp'] = 'decvars'
    # we need to "fix" (e.g. make unadjustable) the pumping rates that are not decision variables
    pars.loc[pars.pargp=="pumping", "partrans"] = "fixed"
    pars.sample(5)


    # ### we need to sample a prior population of pumping rates, centered reasonably closely to the initial pumping rates. To do this, we assume we can temporarily set the upper and lower bounds to, say, +/1 10% of the initial value
    pars.loc[pars.pargp=="decvars", "parlbnd"] = pars.loc[pars.pargp=="decvars", "parval1"]*0.8
    pars.loc[pars.pargp=="decvars", "parubnd"] = pars.loc[pars.pargp=="decvars", "parval1"]*1.2

    # we start with about 2x the number of decision variables as the population size
    num_reals = 170
    # sample decision variables from a uniform distribution
    dvpop = pyemu.ParameterEnsemble.from_uniform_draw(pst,num_reals=num_reals)

    # record to external file for PESTPP-MOU
    dvpop.to_csv(template_path / "initial_dvpop.csv")
    # tell PESTPP-MOU about the new file
    pst.pestpp_options["mou_dv_population_file"] = 'initial_dvpop.csv'
    # reset the decision variable bounds
    pars['parlbnd'] = 0
    pars['parubnd'] = pars['parval1'] *(1+del_pump)


    # ### now we need to identify the (competing) objectives. This will be total pumping in all the decision variables and total depletion
    # first create a prior information equation aggregating all the pumping int he decision variables
    pst.add_pi_equation(pars.loc[pars.pargp=='decvars','parnme'], # parameter names to include in the equation
                        pilbl="obj_well",  # the prior information equation name
                        obs_group="greater_than_pumping") # note the "greater_" prefix.   

    # next identify the total depletion as a distinct observation group
    obs.loc[obs.index.str.contains("fish_prob"), "obgnme"] = "greater_than_fishprob"
    # now reset all weights except this one to be 0
    obs.weight = 0
    obs.loc[obs.obgnme=="greater_than_fishprob", "weight"] = 1.0

    pst.pestpp_options["mou_objectives"] = ["obj_well",
                                            "fish_prob"]

    # some additional PESTPP-MOU options:
    pst.pestpp_options["mou_population_size"] = num_reals #twice the number of decision variables
    pst.pestpp_options["mou_save_population_every"] = 1 # save lots of files! 
                                                        # but this way we can inspect how MOU progressed    


    pst.control_data.noptmax = 50
    pst.model_command = ['python run_pycap_standalone_opt_mou_fish.py']

    pst.write(str(template_path / "mou_fish.pst"), version=2)

    # Copy over directories
    if MASTER_path.exists():
        shutil.rmtree(MASTER_path)
    # copy over the binaries into template first so they get distributed


    #copy over the correct binary
    if "window" in platform.platform().lower():
        shutil.copy2('../../binaries/PESTPP/windows/pestpp-mou.exe', template_path / 'pestpp-mou.exe')
    elif "linux" in platform.platform().lower():
        shutil.copy2('../../binaries/PESTPP/linux/pestpp-mou', template_path / 'pestpp-mou')
    elif "mac" in platform.platform().lower():
        shutil.copy2('../../binaries/PESTPP/mac/pestpp-mou', template_path / 'pestpp-mou')

    # we also need the forward run script
    shutil.copy2(script_path / 'run_pycap_standalone_opt_mou_fish.py', 
                template_path / 'run_pycap_standalone_opt_mou_fish.py')

    # and we need the base yml file
    shutil.copy2(base_run_path / 'LPR_Redux.yml',
                template_path / 'LPR_Redux.yml')

    # we need the fish file
    shutil.copy2(fish_path / 'Brook.csv',
                template_path / 'Brook.csv')   

    # finally populate the MASTER path with the template_path files
    shutil.copytree(template_path, MASTER_path)
    os.remove(MASTER_path / 'allobs.out')

