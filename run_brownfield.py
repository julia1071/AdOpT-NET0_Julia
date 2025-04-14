import json
from pathlib import Path
import pandas as pd
import adopt_net0.data_preprocessing as dp
from adopt_net0.modelhub import ModelHub
from adopt_net0.result_management.read_results import add_values_to_summary
from adopt_net0.utilities import fix_installed_capacities, installed_capacities_existing, \
    installed_capacities_existing_from_file

#Run Chemelot emission limit case
execute = 1


if execute == 1:
    # Specify the base path to your input data
    casepath = "Z:/AdOpt_NET0/AdOpt_casestudies/MY/MY_Chemelot_bf_"
    resultpath = "Z:/AdOpt_NET0/AdOpt_results/MY/EmissionLimit Brownfield/"


    # select simulation types
    node = 'Chemelot'
    scope3 = 1
    run_with_emission_limit = 1
    intervals = ['2040', '2050']
    # intervals = ['2030', '2040', '2050']
    interval_emissionLim = {'2030': 1, '2040': 0.5, '2050': 0}
    nr_DD_days = 10
    prev_from_file = 1
    emission_2030 = 522907.4304
    h5_path_prev = Path(
        "Z:/AdOpt_NET0/AdOpt_results/MY/EmissionLimit Brownfield/Chemelot/20250408154656_2030_minC_DD10-1/optimization_results.h5")
    pyhub = {}

    for i, interval in enumerate(intervals):
        casepath_interval = casepath + interval
        json_filepath = Path(casepath_interval) / "ConfigModel.json"

        with open(json_filepath) as json_file:
            model_config = json.load(json_file)

        model_config['optimization']['typicaldays']['N']['value'] = nr_DD_days

        if interval == '2030':
            model_config['optimization']['objective']['value'] = 'costs'
        else:
            prev_interval = intervals[i - 1]
            model_config['optimization']['objective']['value'] = "costs_emissionlimit"
            if interval == '2040' and prev_from_file:
                limit = interval_emissionLim[interval] * emission_2030
            else:
                if nr_DD_days > 0:
                    limit = interval_emissionLim[interval] * pyhub[prev_interval].model[
                        'clustered'].var_emissions_net.value
                else:
                    limit = interval_emissionLim[interval] * pyhub[prev_interval].model['full'].var_emissions_net.value
            model_config['optimization']['emission_limit']['value'] = limit

        # Scope 3 analysis yes/no
        model_config['optimization']['scope_three_analysis'] = scope3

        # solver settings
        model_config['solveroptions']['timelim']['value'] = 24*30
        model_config['solveroptions']['mipgap']['value'] = 0.02
        model_config['solveroptions']['threads']['value'] = 12
        model_config['solveroptions']['nodefilestart']['value'] = 200

        #change save options
        model_config['reporting']['save_summary_path']['value'] = resultpath + node
        model_config['reporting']['save_path']['value'] = resultpath + node

        # Write the updated JSON data back to the file
        with open(json_filepath, 'w') as json_file:
            json.dump(model_config, json_file, indent=4)

        if i != 0:
            prev_interval = intervals[i - 1]
            if prev_from_file and interval == '2040':
                if h5_path_prev.exists():
                    installed_capacities_existing_from_file(interval, '2030', 'Chemelot', casepath_interval,
                                                            h5_path_prev)
            else:
                installed_capacities_existing(pyhub, interval, prev_interval, 'Chemelot', casepath_interval)

        # Construct and solve the model
        pyhub[interval] = ModelHub()
        pyhub[interval].read_data(casepath_interval)

        # Set case name
        if nr_DD_days > 0:
            pyhub[interval].data.model_config['reporting']['case_name'][
                'value'] = (interval + '_minC_' +
                            'DD' + str(pyhub[interval].data.model_config['optimization']['typicaldays']['N']['value']))
            pyhub[interval].data.time_series['clustered'][
                interval, node, 'CarbonCost', 'global', 'price'] = 150.31
        else:
            pyhub[interval].data.model_config['reporting']['case_name'][
                'value'] = interval + '_minC_fullres'

        pyhub[interval].data.time_series['full'][interval, node, 'CarbonCost', 'global', 'price'] = 150.31

        # Start brownfield optimization
        pyhub[interval].construct_model()
        pyhub[interval].construct_balances()
        pyhub[interval].solve()


#Run Chemelot cluster case without emission limit
execute = 0


if execute == 1:
    # Specify the base path to your input data
    casepath = "Z:/AdOpt_NET0/AdOpt_casestudies/MY/MY_Chemelot_bf_"
    resultpath = "Z:/AdOpt_NET0/AdOpt_results/MY/Brownfield/"


    # select simulation types
    node = 'Chemelot'
    objectives = ['costs']
    co2tax = ['ref']
    scope3 = 1
    run_with_emission_limit = 1
    intervals = ['2030', '2040', '2050']
    interval_taxHigh = {'2030': 250, '2040': 400, '2050': 500}
    nr_DD_days = 10
    pyhub = {}

    for obj in objectives:
        for tax in co2tax:
            for i, interval in enumerate(intervals):
                casepath_interval = casepath + interval
                json_filepath = Path(casepath_interval) / "ConfigModel.json"

                with open(json_filepath) as json_file:
                    model_config = json.load(json_file)

                model_config['optimization']['typicaldays']['N']['value'] = nr_DD_days
                model_config['optimization']['objective']['value'] = obj

                # Scope 3 analysis yes/no
                model_config['optimization']['scope_three_analysis'] = scope3

                # solver settings
                model_config['solveroptions']['timelim']['value'] = 24*30
                model_config['solveroptions']['mipgap']['value'] = 0.02
                model_config['solveroptions']['threads']['value'] = 24

                #change save options
                model_config['reporting']['save_summary_path']['value'] = resultpath + node
                model_config['reporting']['save_path']['value'] = resultpath + node
                # Write the updated JSON data back to the file
                with open(json_filepath, 'w') as json_file:
                    json.dump(model_config, json_file, indent=4)

                if i != 0:
                    prev_interval = intervals[i - 1]
                    installed_capacities_existing(pyhub, interval, prev_interval, node, casepath_interval)

                # Construct and solve the model
                pyhub[interval] = ModelHub()
                pyhub[interval].read_data(casepath_interval)

                if obj == 'emissions_minC':
                    # add casename
                    pyhub[interval].data.model_config['reporting']['case_name']['value'] = interval + '_minE_refCO2tax'

                elif obj == 'costs':
                    # add casename
                    if nr_DD_days > 0:
                        pyhub[interval].data.model_config['reporting']['case_name'][
                            'value'] = (interval + '_minC_' + tax + 'CO2tax' +
                                        'DD' + str(pyhub[interval].data.model_config['optimization']['typicaldays']['N']['value']))
                    else:
                        pyhub[interval].data.model_config['reporting']['case_name'][
                            'value'] = (interval + '_minC_' + tax + 'CO2tax_fullres')

                    if tax == 'high':
                        if nr_DD_days != 0:
                            pyhub[interval].data.time_series['clustered'][
                                interval, node, 'CarbonCost', 'global', 'price'] = interval_taxHigh[interval]
                        pyhub[interval].data.time_series['full'][interval, node, 'CarbonCost', 'global', 'price'] = interval_taxHigh[interval]

                # Start brownfield optimization
                pyhub[interval].construct_model()
                pyhub[interval].construct_balances()
                pyhub[interval].solve()

                if interval == '2050' and run_with_emission_limit:
                    casepath_interval = casepath + interval
                    json_filepath = Path(casepath_interval) / "ConfigModel.json"

                    with open(json_filepath) as json_file:
                        model_config = json.load(json_file)

                    model_config['optimization']['objective']['value'] = "costs_emissionlimit"
                    model_config['optimization']['emission_limit']['value'] = 0

                    # Write the updated JSON data back to the file
                    with open(json_filepath, 'w') as json_file:
                        json.dump(model_config, json_file, indent=4)

                    # fix to 2040 capacities
                    prev_interval = intervals[i - 1]
                    installed_capacities_existing(pyhub, interval, prev_interval, node, casepath_interval)

                    # Construct and solve the model
                    pyhub["2050_emissionlimit"] = ModelHub()
                    pyhub["2050_emissionlimit"].read_data(casepath_interval)

                    # add casename
                    if nr_DD_days > 0:
                        pyhub["2050_emissionlimit"].data.model_config['reporting']['case_name'][
                            'value'] = ('2050_emissionlimit_minC_' + tax + 'CO2tax' +
                                        'DD' + str(pyhub["2050_emissionlimit"].data.model_config['optimization']['typicaldays']['N']['value']))
                    else:
                        pyhub["2050_emissionlimit"].data.model_config['reporting']['case_name'][
                            'value'] = ('2050_emissionlimit_minC_' + tax + 'CO2tax_fullres')

                    # Start brownfield optimization
                    pyhub["2050_emissionlimit"].construct_model()
                    pyhub["2050_emissionlimit"].construct_balances()
                    pyhub["2050_emissionlimit"].solve()



#Run Chemelot cluster case with minimum size constraint
execute = 0
nr_DD_days = 0

if execute == 1:
    # Specify the base path to your input data
    casepath = "Z:/AdOpt_NET0/AdOpt_casestudies/MY/MY_Chemelot_bf_"
    resultpath = "Z:/AdOpt_NET0/AdOpt_results/MY/Brownfield/"


    # select simulation types
    node = 'Chemelot'
    objectives = ['costs']
    co2tax = ['ref']
    scope3 = 1
    intervals = ['2030', '2040', '2050']
    pyhub = {}
    set_conv_tech = ["SteamReformer_existing", "HaberBosch_existing", "CrackerFurnace_existing", "OlefinSeparation_existing"]

    for obj in objectives:
        for tax in co2tax:
            for i, interval in enumerate(intervals):
                casepath_interval = casepath + interval
                json_filepath = Path(casepath_interval) / "ConfigModel.json"

                with open(json_filepath) as json_file:
                    model_config = json.load(json_file)

                model_config['optimization']['typicaldays']['N']['value'] = nr_DD_days
                model_config['optimization']['objective']['value'] = obj

                # Scope 3 analysis yes/no
                model_config['optimization']['scope_three_analysis'] = scope3

                #change save options
                model_config['reporting']['save_summary_path']['value'] = resultpath + node
                model_config['reporting']['save_path']['value'] = resultpath + node
                # Write the updated JSON data back to the file
                with open(json_filepath, 'w') as json_file:
                    json.dump(model_config, json_file, indent=4)

                # Construct and solve the model
                pyhub[interval] = ModelHub()
                pyhub[interval].read_data(casepath_interval, start_period=1, end_period=10)

                if obj == 'emissions_minC':
                    # add casename
                    pyhub[interval].data.model_config['reporting']['case_name']['value'] = interval + '_minE_refCO2tax'

                elif obj == 'costs':
                    # add casename
                    pyhub[interval].data.model_config['reporting']['case_name']['value'] = interval + '_minC_' + tax + 'CO2tax'

                    if tax == 'high':
                        if nr_DD_days != 0:
                            pyhub[interval].data.time_series['clustered'][
                                interval, node, 'CarbonCost', 'global', 'price'] = 250
                        pyhub[interval].data.time_series['full'][interval, node, 'CarbonCost', 'global', 'price'] = 250

                # Start brownfield optimization
                pyhub[interval].construct_model()
                pyhub[interval].construct_balances()

                if i != 0:
                    prev_interval = intervals[i - 1]
                    pyhub = fix_installed_capacities(pyhub, interval, prev_interval, node, set_conv_tech)

                pyhub[interval].solve()

                # ref = pyhub['2040'].model[pyhub[interval].info_solving_algorithms["aggregation_model"]].intervals[interval].node_blocks[node].tech_blocks_active['SteamReformer']



