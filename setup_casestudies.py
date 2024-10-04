import json
from pathlib import Path
import adopt_net0.data_preprocessing as dp
from adopt_net0.modelhub import ModelHub
from adopt_net0.result_management.read_results import add_values_to_summary
import pandas as pd

#Create data Chemelot cluster short term
execute = 1

if execute == 1:
    # Specify the path to your input data
    casepath = Path("Z:/PyHub/PyHub_casestudies/MY/MY_Chemelot_2030")
    datapath = Path("Z:/PyHub/PyHub_data/MY/MY_Data_241003")

    firsttime = 0
    if firsttime == 1:
        # Create template files
        dp.create_optimization_templates(casepath)
        dp.create_montecarlo_template_csv(casepath)

        # Change topology
        topology_file = casepath / "Topology.json"
        config_file = casepath / "ConfigModel.json"

        topology_template = {
            "nodes": ["Chemelot"],
            "carriers": ["electricity", "methane", "methane_bio", "hydrogen", "CO2", "CO2_DAC", "CO2_bio", "nitrogen",
                         "ammonia", "naphtha", "naphtha_bio", "steam", "ethylene", "propylene", "crackergas", "gas",
                         "heatlowT", "oxygen", "methanol", "methanol_bio", "ethanol_bio", "LPG", "LPG_bio", "propane",
                         "benzene"],
            "investment_periods": ["2030"],
            "start_date": "2022-01-01 00:00",
            "end_date": "2022-12-31 23:00",
            "resolution": "1h",
            "investment_period_length": 5,
        }

        with open(topology_file, "w") as f:
            json.dump(topology_template, f, indent=4)
        # with open(config_file, "w") as f:
            # json.dump(configuration_template, f, indent=4)

        # Node location
        file_path = casepath / 'NodeLocations.csv'
        data = pd.read_csv(file_path, delimiter=';')

        # Set the price to 150.31 and subsidy to 0 for all rows
        data['lon'] = 50.968263253252445
        data['lat'] = 5.803275217879619
        data['alt'] = 10

        # Save the modified CSV file
        data.to_csv(file_path, index=False, sep=';')

        # Create folder structure
        dp.create_input_data_folder_template(casepath)

    else:
        set_tecs = ["KBRreformer", "KBRreformer_CC", "eSMR", "AEC", "HaberBosch",
                        "NaphthaCracker", "NaphthaCracker_Electric", "NaphthaCracker_CC",
                        "ASU", "Boiler_Industrial_NG", "Boiler_El",
                        "MeOHsynthesis", "MTO", "EDH", "PDH",
                        "Storage_Ammonia", "Storage_CO2", "Storage_Ethylene", "Storage_H2", "Storage_Battery",
                        "CO2toEmission", "gasmixer", "LPGseparator"]

        json_file_path = casepath / "Topology.json"
        with open(json_file_path, "r") as json_file:
            topology = json.load(json_file)

        for period in topology["investment_periods"]:
            for node_name in topology["nodes"]:
                # Read the JSON technology file
                json_tec_file_path = (
                        casepath / period / "node_data" / node_name / "Technologies.json"
                )
                with open(json_tec_file_path, "r") as json_tec_file:
                    json_tec = json.load(json_tec_file)

                json_tec['new'] = set_tecs
                with open(json_tec_file_path, "w") as json_tec_file:
                    json.dump(json_tec, json_tec_file, indent=4)

        # Copy technology and network data into folder
        dp.copy_technology_data(casepath, datapath)

        # Read climate data and fill carried data
        dp.load_climate_data_from_api(casepath)
        dp.fill_carrier_data(casepath, value_or_data=0)

        # Demand data
        dp.fill_carrier_data(casepath, value_or_data=135, columns=['Demand'], carriers=['ammonia'])
        dp.fill_carrier_data(casepath, value_or_data=44, columns=['Demand'], carriers=['CO2'])
        dp.fill_carrier_data(casepath, value_or_data=150, columns=['Demand'], carriers=['ethylene'])
        dp.fill_carrier_data(casepath, value_or_data=0, columns=['Demand'], carriers=['steam'])
        dp.fill_carrier_data(casepath, value_or_data=81.8, columns=['Demand'], carriers=['electricity'])
        dp.fill_carrier_data(casepath, value_or_data=6.9, columns=['Demand'], carriers=['crackergas'])

        # No import limit
        dp.fill_carrier_data(casepath, value_or_data=2000, columns=['Import limit'],
                             carriers=["electricity", "methane", "methane_bio", "CO2", "CO2_DAC", "CO2_bio",
                                       "naphtha", "naphtha_bio", "ethylene", "propylene", "methanol_bio",
                                       "ethanol_bio", "LPG_bio"])

        # No export limit
        dp.fill_carrier_data(casepath, value_or_data=2000, columns=['Export limit'],
                             carriers=["nitrogen", "steam", "ethylene", "propylene", "crackergas", "heatlowT",
                                       "oxygen", "methanol", "methanol_bio", "ethanol_bio", "LPG", "LPG_bio", "propane"])
        dp.fill_carrier_data(casepath, value_or_data=0.203, columns=['Export emission factor'],
                             carriers=['crackergas'])

        # CO2 export
        dp.fill_carrier_data(casepath, value_or_data=115, columns=['Export limit'], carriers=['CO2'])
        dp.fill_carrier_data(casepath, value_or_data=-63.78, columns=['Export price'], carriers=['CO2'])

        # Constant prices
        dp.fill_carrier_data(casepath, value_or_data=100, columns=['Import price'], carriers=['methane'])
        dp.fill_carrier_data(casepath, value_or_data=732, columns=['Import price'], carriers=['naphtha'])

        # Electricity price from file
        el_load_path = Path(datapath) / 'import_data' / 'Electricity_data_CM.csv'
        el_importdata = pd.read_csv(el_load_path, sep=';', header=0, nrows=8760)
        el_price = el_importdata.iloc[:, 0]
        el_emissionrate = el_importdata.iloc[:, 3]

        dp.fill_carrier_data(casepath, value_or_data=el_price, columns=['Import price'], carriers=['electricity'])
        dp.fill_carrier_data(casepath, value_or_data=el_emissionrate, columns=['Import emission factor'], carriers=['electricity'])


        #carbon tax
        file_path = Path(casepath) / 'period1' / "node_data" / 'Chemelot' / 'CarbonCost.csv'
        data = pd.read_csv(file_path, delimiter=';')

        # Set the price to 150.31 and subsidy to 0 for all rows
        data['price'] = 150.31
        data['subsidy'] = 0

        # Save the modified CSV file
        data.to_csv(file_path, index=False, sep=';')

#Create data Chemelot cluster longterm
execute = 1

if execute == 1:
    # Specify the path to your input data
    casepath = Path("Z:/PyHub/PyHub_casestudies/MY/MY_Chemelot")
    datapath = Path("Z:/PyHub/PyHub_data/MY/MY_Data_241003")

    firsttime = 0
    if firsttime == 1:
        # Create template files
        dp.create_optimization_templates(casepath)
        dp.create_montecarlo_template_csv(casepath)

        # Change topology
        topology_file = casepath / "Topology.json"
        config_file = casepath / "ConfigModel.json"

        topology_template = {
            "nodes": ["Chemelot"],
            "carriers": ["electricity", "methane", "methane_bio", "hydrogen", "CO2", "CO2_DAC", "CO2_bio", "nitrogen",
                         "ammonia", "naphtha", "naphtha_bio", "steam", "ethylene", "propylene", "crackergas", "gas",
                         "heatlowT", "oxygen", "methanol", "methanol_bio", "ethanol_bio", "LPG", "LPG_bio", "propane"],
            "investment_periods": ["2030", "2035", "2040", "2045", "2050"],
            "start_date": "2022-01-01 00:00",
            "end_date": "2022-12-31 23:00",
            "resolution": "1h",
            "investment_period_length": 5,
        }

        with open(topology_file, "w") as f:
            json.dump(topology_template, f, indent=4)
        # with open(config_file, "w") as f:
            # json.dump(configuration_template, f, indent=4)

        # Node location
        # carbon tax
        file_path = casepath / 'NodeLocations.csv'
        data = pd.read_csv(file_path, delimiter=';')

        # Set the price to 150.31 and subsidy to 0 for all rows
        data['lon'] = 50.968263253252445
        data['lat'] = 5.803275217879619
        data['alt'] = 10

        # Save the modified CSV file
        data.to_csv(file_path, index=False, sep=';')

        # Create folder structure
        dp.create_input_data_folder_template(casepath)

    else:
        set_tecs = ["KBRreformer", "KBRreformer_CC", "eSMR", "HaberBosch",
                        "AEC", "ASU", "NaphthaCracker", "NaphthaCracker_Electric",
                        "NaphthaCracker_CC", "Boiler_Industrial_NG", "Boiler_El", "Storage_Ammonia",
                        "Storage_CO2", "Storage_Ethylene", "Storage_H2", "Storage_Battery",
                        "CO2toEmission", "gasmixer"]

        json_file_path = casepath / "Topology.json"
        with open(json_file_path, "r") as json_file:
            topology = json.load(json_file)

        for period in topology["investment_periods"]:
            for node_name in topology["nodes"]:
                # Read the JSON technology file
                json_tec_file_path = (
                        casepath / period / "node_data" / node_name / "Technologies.json"
                )
                with open(json_tec_file_path, "r") as json_tec_file:
                    json_tec = json.load(json_tec_file)

                json_tec['new'] = set_tecs
                with open(json_tec_file_path, "w") as json_tec_file:
                    json.dump(json_tec, json_tec_file, indent=4)

        # Copy technology and network data into folder
        dp.copy_technology_data(casepath, datapath)

        # Read climate data and fill carried data
        dp.load_climate_data_from_api(casepath)
        dp.fill_carrier_data(casepath, value_or_data=0)

        # Demand data
        dp.fill_carrier_data(casepath, value_or_data=135, columns=['Demand'], carriers=['ammonia'])
        dp.fill_carrier_data(casepath, value_or_data=44, columns=['Demand'], carriers=['CO2'])
        dp.fill_carrier_data(casepath, value_or_data=150, columns=['Demand'], carriers=['ethylene'])
        dp.fill_carrier_data(casepath, value_or_data=0, columns=['Demand'], carriers=['steam'])
        dp.fill_carrier_data(casepath, value_or_data=81.8, columns=['Demand'], carriers=['electricity'])
        dp.fill_carrier_data(casepath, value_or_data=6.9, columns=['Demand'], carriers=['crackergas'])

        # No import limit
        dp.fill_carrier_data(casepath, value_or_data=2000, columns=['Import limit'],
                             carriers=['electricity', 'methane', 'naphtha', "CO2"])

        # No export limit
        dp.fill_carrier_data(casepath, value_or_data=2000, columns=['Export limit'],
                             carriers=['nitrogen', 'oxygen', 'heatlowT', 'steam', 'crackergas'])
        dp.fill_carrier_data(casepath, value_or_data=0.203, columns=['Export emission factor'],
                             carriers=['crackergas'])

        # CO2 export
        dp.fill_carrier_data(casepath, value_or_data=115, columns=['Export limit'], carriers=['CO2'])
        dp.fill_carrier_data(casepath, value_or_data=-63.78, columns=['Export price'], carriers=['CO2'])

        # Constant prices
        dp.fill_carrier_data(casepath, value_or_data=100, columns=['Import price'], carriers=['methane'])
        dp.fill_carrier_data(casepath, value_or_data=732, columns=['Import price'], carriers=['naphtha'])

        # Electricity price from file
        el_load_path = Path(datapath) / 'import_data' / 'Electricity_data_CM.csv'
        el_importdata = pd.read_csv(el_load_path, sep=';', header=0, nrows=8760)
        el_price = el_importdata.iloc[:, 0]
        el_emissionrate = el_importdata.iloc[:, 3]

        dp.fill_carrier_data(casepath, value_or_data=el_price, columns=['Import price'], carriers=['electricity'])
        dp.fill_carrier_data(casepath, value_or_data=el_emissionrate, columns=['Import emission factor'], carriers=['electricity'])


        #carbon tax
        file_path = Path(casepath) / 'period1' / "node_data" / 'Chemelot' / 'CarbonCost.csv'
        data = pd.read_csv(file_path, delimiter=';')

        # Set the price to 150.31 and subsidy to 0 for all rows
        data['price'] = 150.31
        data['subsidy'] = 0

        # Save the modified CSV file
        data.to_csv(file_path, index=False, sep=';')

#Create data Zeeland cluster
execute = 0

if execute == 1:
    # Specify the path to your input data
    casepath = "Z:/PyHub/PyHub_casestudies/CM/Zeeland_cluster"
    datapath = "Z:/PyHub/PyHub_data/CM/240624_CM"

    firsttime = 0
    if firsttime == 1:
        # Create template files
        dp.create_optimization_templates(casepath)
        dp.create_montecarlo_template_csv(casepath)

        # Create folder structure
        dp.create_input_data_folder_template(casepath)

        # # Copy technology and network data into folder
        dp.copy_technology_data(casepath, datapath)

        # Read climate data and fill carried data
        dp.load_climate_data_from_api(casepath)
        dp.fill_carrier_data(casepath, value_or_data=0)

        # Demand data
        dp.fill_carrier_data(casepath, value_or_data=208, columns=['Demand'], carriers=['ammonia'])
        dp.fill_carrier_data(casepath, value_or_data=111, columns=['Demand'], carriers=['CO2'])
        dp.fill_carrier_data(casepath, value_or_data=208, columns=['Demand'], carriers=['ethylene'])
        dp.fill_carrier_data(casepath, value_or_data=546.7, columns=['Demand'], carriers=['steam'])
        dp.fill_carrier_data(casepath, value_or_data=93.2, columns=['Demand'], carriers=['electricity'])

        # No import limit
        dp.fill_carrier_data(casepath, value_or_data=3000, columns=['Import limit'],
                             carriers=['electricity', 'methane', 'naphtha', "CO2"])

        # No export limit
        dp.fill_carrier_data(casepath, value_or_data=2000, columns=['Export limit'],
                             carriers=['nitrogen', 'oxygen', 'heatlowT', 'steam', 'crackergas'])
        dp.fill_carrier_data(casepath, value_or_data=0.203, columns=['Export emission factor'],
                             carriers=['crackergas'])

    # CO2 export
    dp.fill_carrier_data(casepath, value_or_data=171, columns=['Export limit'], carriers=['CO2'])
    dp.fill_carrier_data(casepath, value_or_data=-54.56, columns=['Export price'], carriers=['CO2'])

    # # Constant prices
    # dp.fill_carrier_data(casepath, value_or_data=100, columns=['Import price'], carriers=['methane'])
    # dp.fill_carrier_data(casepath, value_or_data=732, columns=['Import price'], carriers=['naphtha'])
    #
    # # Electricity price from file
    # el_load_path = Path(datapath) / 'import_data' / 'Electricity_data_CM.csv'
    # el_importdata = pd.read_csv(el_load_path, sep=';', header=0, nrows=8760)
    # el_price = el_importdata.iloc[:, 1]
    # el_emissionrate = el_importdata.iloc[:, 3]
    #
    # dp.fill_carrier_data(casepath, value_or_data=el_price, columns=['Import price'], carriers=['electricity'])
    # dp.fill_carrier_data(casepath, value_or_data=el_emissionrate, columns=['Import emission factor'], carriers=['electricity'])
    #
    #
    # #carbon tax
    # file_path = Path(casepath) / 'period1' / "node_data" / 'Zeeland' / 'CarbonCost.csv'
    # data = pd.read_csv(file_path, delimiter=';')
    #
    # # Set the price to 150.31 and subsidy to 0 for all rows
    # data['price'] = 150.31
    # data['subsidy'] = 0
    #
    # # Save the modified CSV file
    # data.to_csv(file_path, index=False, sep=';')