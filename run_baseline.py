import json
from pathlib import Path
import pandas as pd
import adopt_net0.data_preprocessing as dp
from adopt_net0.modelhub import ModelHub
from adopt_net0.result_management.read_results import add_values_to_summary

#Run Chemelot emission limit
execute = 1

if execute == 1:
    # Specify the path to your input data
    casepath = "Z:/AdOpt_NET0/AdOpt_casestudies/MY/MY_Chemelot_gf_"
    resultpath = "Z:/AdOpt_NET0/AdOpt_results/MY/EmissionLimit Greenfield/"

    # select simulation types
    node = 'Chemelot'
    scope3 = 1
    run_with_emission_limit = 1
    # intervals = ['2040', '2050']
    intervals = ['2030', '2040', '2050']
    interval_emissionLim = {'2030': 1, '2040': 0.5, '2050': 0}
    nr_DD_days = 10
    take_prev_solution = 0
    prev_emission = 540875.012
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
            if interval == '2040' and take_prev_solution:
                limit = interval_emissionLim[interval] * prev_emission
            else:
                if nr_DD_days > 0:
                    limit = interval_emissionLim[interval] * pyhub[prev_interval].model['clustered'].var_emissions_net.value
                else:
                    limit = interval_emissionLim[interval] * pyhub[prev_interval].model['full'].var_emissions_net.value
            model_config['optimization']['emission_limit']['value'] = limit

        # Scope 3 analysis yes/no
        model_config['optimization']['scope_three_analysis'] = scope3

        # solver settings
        model_config['solveroptions']['timelim']['value'] = 24*30
        model_config['solveroptions']['mipgap']['value'] = 0.02
        model_config['solveroptions']['threads']['value'] = 8
        model_config['solveroptions']['nodefilestart']['value'] = 200

        #change save options
        model_config['reporting']['save_summary_path']['value'] = resultpath + node
        model_config['reporting']['save_path']['value'] = resultpath + node

        # Write the updated JSON data back to the file
        with open(json_filepath, 'w') as json_file:
            json.dump(model_config, json_file, indent=4)

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


#Run Chemelot case without emission limit
execute = 0

if execute == 1:
    # Specify the path to your input data
    casepath = "Z:/AdOpt_NET0/AdOpt_casestudies/MY/MY_Chemelot_gf_"
    resultpath = "Z:/AdOpt_NET0/AdOpt_results/MY/Greenfield/"
    json_filepath = Path(casepath) / "ConfigModel.json"

    node = 'Chemelot'
    objectives = ['costs']
    scope3 = 1
    # intervals = ['2040', '2050']
    intervals = ['2030', '2040', '2050']
    run_with_emission_limit = 1
    co2tax = ['ref']
    interval_taxHigh = {'2030': 250, '2040': 400, '2050': 500}
    nr_DD_days = 10

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
                model_config['solveroptions']['timelim']['value'] = 120
                model_config['solveroptions']['mipgap']['value'] = 0.02
                model_config['solveroptions']['threads']['value'] = 24

                #change save options
                model_config['reporting']['save_summary_path']['value'] = resultpath + node
                model_config['reporting']['save_path']['value'] = resultpath + node

                # Write the updated JSON data back to the file
                with open(json_filepath, 'w') as json_file:
                    json.dump(model_config, json_file, indent=4)

                # Construct and solve the model
                pyhub = ModelHub()
                pyhub.read_data(casepath_interval)

                if obj == 'emissions_minC':
                    # add casename
                    pyhub.data.model_config['reporting']['case_name']['value'] = 'minE_refCO2tax'

                    # solving
                    pyhub.quick_solve()

                elif obj == 'costs':
                    # add casename
                    if nr_DD_days > 0:
                        pyhub.data.model_config['reporting']['case_name'][
                            'value'] = (interval + '_minC_' + tax + 'CO2tax' +
                                        'DD' + str(pyhub.data.model_config['optimization']['typicaldays']['N']['value']))
                    else:
                        pyhub.data.model_config['reporting']['case_name'][
                            'value'] = (interval + '_minC_' + tax + 'CO2tax_fullres')

                    if tax == 'high':
                        if nr_DD_days != 0:
                            pyhub.data.time_series['clustered'][
                                interval, node, 'CarbonCost', 'global', 'price'] = interval_taxHigh[interval]
                        pyhub.data.time_series['full'][
                            interval, node, 'CarbonCost', 'global', 'price'] = interval_taxHigh[interval]

                    # solving
                    pyhub.quick_solve()

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

                        # Construct and solve the model
                        pyhub = ModelHub()
                        pyhub.read_data(casepath_interval)

                        # add casename
                        if nr_DD_days > 0:
                            pyhub.data.model_config['reporting']['case_name'][
                                'value'] = ('2050_emissionlimit_minC_' + tax + 'CO2tax' +
                                            'DD' + str(
                                        pyhub["2050_emissionlimit"].data.model_config['optimization']['typicaldays'][
                                            'N']['value']))
                        else:
                            pyhub.data.model_config['reporting']['case_name'][
                                'value'] = ('2050_emissionlimit_minC_' + tax + 'CO2tax_fullres')

                        # Start brownfield optimization
                        pyhub.quick_solve()


