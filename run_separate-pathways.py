import json
from pathlib import Path
from adopt_net0.modelhub import ModelHub
from adopt_net0.result_management.read_results import add_values_to_summary
from adopt_net0.utilities import fix_technology_sizes_zero, installed_capacities_existing, \
    installed_capacities_existing_from_file

#Run Chemelot pathways
execute = 0

if execute == 1:
    # Specify the path to your input data
    casepath = "Z:/AdOpt_NET0/AdOpt_casestudies/MY/MY_Chemelot_2040_pathways"
    resultpath = "Z:/AdOpt_NET0/AdOpt_results/MY/Pathways/CH_2040_scope3"

    config_filepath = Path(casepath) / "ConfigModel.json"
    tech_filepath = Path(casepath + "/" + scenario + "/node_data/" + node + "/Technologies.json")

    co2tax = ['ref']
    scenario = '2040'
    node = 'Chemelot'
    nr_DD_days = 10
    scope3 = 1

    pathways_ammonia = {"conventional_CC": ["SteamReformer", "HaberBosch"],
                        "electric": ["ElectricSMR_m", "WGS_m", "HaberBosch", "ASU"],
                        "electrolyzer": ["AEC", "HaberBosch", "ASU"],
                        }
    pathways_ethylene = {"conventional_CC": ["CrackerFurnace", "OlefinSeparation"],
                         "electric": ["CrackerFurnace_Electric", "OlefinSeparation"],
                         "methanol1": ["AEC", "RWGS", "MeOHsynthesis", "MTO"],
                         "methanol2": ["AEC", "DirectMeOHsynthesis", "MTO"],
                         "methanol3": ["MPW2methanol", "MTO"],
                         "hydrocarbon_upgrading": ["EDH", "PDH"],
                         "CO2electrolysis": ["CO2electrolysis"],
                         }
    pathways_auxiliary = ["Boiler_Industrial_NG", "Boiler_El",
                          "Storage_Ammonia", "Storage_CO2", "Storage_Ethylene", "Storage_H2",
                          "Storage_Battery", "Storage_Propylene",
                          "CO2toEmission", "feedgas_mixer", "naphtha_mixer", "PE_mixer", "CO2_mixer",
                          "HBfeed_mixer", "syngas_mixer"]

    for ammonia_key, ammonia_tech in pathways_ammonia.items():
        for ethylene_key, ethylene_tech in pathways_ethylene.items():
            # Combine ammonia, ethylene, and auxiliary pathways
            combined_tech = ammonia_tech + ethylene_tech + pathways_auxiliary

            for tax in co2tax:
                # change config file
                with open(config_filepath) as json_file:
                    model_config = json.load(json_file)

                model_config['optimization']['typicaldays']['N']['value'] = nr_DD_days
                model_config['optimization']['objective']['value'] = 'costs'

                # Scope 3 analysis yes/no
                model_config['optimization']['scope_three_analysis'] = scope3

                # solver settings
                model_config['solveroptions']['timelim']['value'] = 48
                model_config['solveroptions']['mipgap']['value'] = 0.02
                model_config['solveroptions']['threads']['value'] = 10

                # change save options
                model_config['reporting']['save_summary_path']['value'] = resultpath
                model_config['reporting']['save_path']['value'] = resultpath

                # Write the updated JSON data back to the file
                with open(config_filepath, 'w') as json_file:
                    json.dump(model_config, json_file, indent=4)

                # change technologies
                with open(tech_filepath) as json_file:
                    techs = json.load(json_file)

                techs["new"] = combined_tech

                # Write the updated JSON data back to the file
                with open(tech_filepath, 'w') as json_file:
                    json.dump(techs, json_file, indent=4)

                # Construct and solve the model
                pyhub = ModelHub()
                pyhub.read_data(casepath)

                # change emission factor to correct for scope 3
                if not scope3:
                    if nr_DD_days != 0:
                        pyhub.data.time_series['clustered'][
                            scenario, node, 'CarrierData', 'CO2', 'Export emission factor'] = 0
                        pyhub.data.time_series['clustered'][
                            scenario, node, 'CarrierData', 'naphtha', 'Import emission factor'] = 0
                        pyhub.data.time_series['clustered'][
                            scenario, node, 'CarrierData', 'methane', 'Import emission factor'] = 0
                    pyhub.data.time_series['full'][
                        scenario, node, 'CarrierData', 'CO2', 'Export emission factor'] = 0
                    pyhub.data.time_series['full'][
                        scenario, node, 'CarrierData', 'naphtha', 'Import emission factor'] = 0
                    pyhub.data.time_series['full'][
                        scenario, node, 'CarrierData', 'methane', 'Import emission factor'] = 0

                if tax == 'high':
                    if nr_DD_days != 0:
                        pyhub.data.time_series['clustered'][
                            scenario, node, 'CarbonCost', 'global', 'price'] = 250
                    pyhub.data.time_series['full'][scenario, node, 'CarbonCost', 'global', 'price'] = 250

                #add casename based tech combinition
                if nr_DD_days > 0:
                    pyhub.data.model_config['reporting']['case_name']['value'] = 'DD{0}_a_{1}_e_{2}'.format(
                        str(pyhub.data.model_config['optimization']['typicaldays']['N']['value']), ammonia_key,
                        ethylene_key)
                else:
                    pyhub.data.model_config['reporting']['case_name'][
                        'value'] = 'a_' + ammonia_key + '_e_' + ethylene_key

                #solving
                pyhub.quick_solve()

#Run Chemelot warmstart
execute = 1

if execute == 1:
    # Specify the path to your input data
    casepath = "Z:/AdOpt_NET0/AdOpt_casestudies/MY/Warmstarts/MY_Chemelot_bf_"
    # resultpath = "Z:/AdOpt_NET0/AdOpt_results/MY/tests/"
    resultpath = "Z:/AdOpt_NET0/AdOpt_results/MY/Warmstart Brownfield/"

    # select simulation types
    node = 'Chemelot'
    scope3 = 1
    run_with_emission_limit = 1
    intervals = ['2040', '2050']
    # intervals = ['2030', '2040', '2050']
    interval_emissionLim = {'2030': 1, '2040': 0.5, '2050': 0}
    nr_DD_days = 0
    take_prev_solution = 1
    emission_2030 = 530358.4136
    h5_path_prev = Path("Z:/AdOpt_NET0/AdOpt_results/MY/EmissionLimit Brownfield/Chemelot/20250303182130_2030_minC_DD10-1/optimization_results.h5")
    pyhub = {}

    pathways_ammonia = {"conventional_CC": ["SteamReformer"],
                        "electric": ["ElectricSMR_m", "WGS_m"],
                        "electrolyzer": ["AEC", "HaberBosch"],
                        "storage": ["Storage_Ammonia", "Storage_CO2", "Storage_H2",
                            "Storage_Battery"]
                        }
    pathways_ethylene = {"conventional_CC": ["CrackerFurnace"],
                         "electric": ["CrackerFurnace_Electric"],
                         "methanol1": ["RWGS", "MeOHsynthesis", "MTO"],
                         "methanol2": ["MPW2methanol", "MTO"],
                         "hydrocarbon_upgrading": ["EDH", "PDH"],
                         "advanced": ["DirectMeOHsynthesis", "CO2electrolysis"],
                         "storage": ["Storage_Ethylene", "Storage_Battery", "Storage_Propylene"]
                         }
    pathways_auxiliary = {"Boiler_Industrial_NG", "Boiler_El",
                          "CO2toEmission", "feedgas_mixer", "naphtha_mixer", "PE_mixer", "CO2_mixer",
                          "HBfeed_mixer", "syngas_mixer",
                          "HaberBosch", "ASU", "OlefinSeparation"}

    # Initialize the dictionary, setting all technologies to True
    tech_status = {tech: True for pathway in pathways_ammonia.values() for tech in pathway}
    tech_status.update({tech: True for pathway in pathways_ethylene.values() for tech in pathway})

    # Define the order of pathways to unfix
    unfix_order_pathways = [
        {"ethylene": ["advanced"]},
        {"ethylene": ["storage"], "ammonia": ["storage"]}
    ]
    # unfix_order_pathways = [
    #     {"ethylene": ["advanced", "hydrocarbon_upgrading"]},
    #     {"ethylene": ["methanol1", "methanol2"], "ammonia": ["electric", "electrolyzer"]},
    #     {"ethylene": ["conventional_CC", "electric"], "ammonia": "conventional_CC"}
    # ]

    for i, interval in enumerate(intervals):
        # change config file
        casepath_interval = casepath + interval
        config_filepath = Path(casepath_interval) / "ConfigModel.json"
        with open(config_filepath) as json_file:
            model_config = json.load(json_file)

        model_config['optimization']['typicaldays']['N']['value'] = nr_DD_days

        if interval == '2030':
            model_config['optimization']['objective']['value'] = 'costs'
        else:
            prev_interval = intervals[i - 1]
            model_config['optimization']['objective']['value'] = "costs_emissionlimit"
            if interval == '2040' and take_prev_solution:
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
        model_config['solveroptions']['threads']['value'] = 8

        # change save options
        model_config['reporting']['save_summary_path']['value'] = resultpath + node
        model_config['reporting']['save_path']['value'] = resultpath + node

        # Write the updated JSON data back to the file
        with open(config_filepath, 'w') as json_file:
            json.dump(model_config, json_file, indent=4)

        # Installed capacities
        if interval != '2030':
            if take_prev_solution and interval == '2040':
                if h5_path_prev.exists():
                    installed_capacities_existing_from_file(interval, '2030', node, casepath_interval, h5_path_prev)
            else:
                prev_interval = intervals[i - 1]
                installed_capacities_existing(pyhub, interval, prev_interval, node, casepath_interval)

        # Construct and solve the model
        pyhub[interval] = ModelHub()
        pyhub[interval].read_data(casepath_interval)

        # construct model
        pyhub[interval].construct_model()
        pyhub[interval].construct_balances()

        if interval == '2040':
            # Only existing
            counter = 0
            pyhub[interval].data.model_config['reporting']['case_name']['value'] = interval + '_ws_' + str(
                counter) + '_minC_bf'
            pyhub[interval] = fix_technology_sizes_zero(pyhub[interval], tech_status, node, interval)
            pyhub[interval].solve()

            # Loop over each chemical pathway to unfix
            for pathways in unfix_order_pathways:
                for chemical, pathway in pathways.items():
                    if isinstance(pathway, list):  # If the pathway is a list of multiple pathways
                        for sub_pathway in pathway:
                            tech_list = pathways_ethylene[sub_pathway] if chemical == "ethylene" else pathways_ammonia[
                                sub_pathway]
                            for tech in tech_list:
                                tech_status[tech] = False
                    else:  # Single pathway case
                        tech_list = pathways_ethylene[pathway] if chemical == "ethylene" else pathways_ammonia[pathway]
                        for tech in tech_list:
                            tech_status[tech] = False

                counter += 1
                pyhub[interval].data.model_config['reporting']['case_name']['value'] = interval + '_ws_' + str(
                    counter) + '_minC_bf'

                pyhub[interval] = fix_technology_sizes_zero(pyhub[interval], tech_status, node, interval)
                pyhub[interval].solve()

            for tech in tech_status:
                tech_status[tech] = False
            pyhub[interval].data.model_config['reporting']['case_name']['value'] = interval + '_ws_final_minC_bf'
            pyhub[interval] = fix_technology_sizes_zero(pyhub[interval], tech_status, node, interval)
            pyhub[interval].solve()

        else:
            pyhub[interval].data.model_config['reporting']['case_name']['value'] = interval + '_minC_bf'
            pyhub[interval].solve()
