from pathlib import Path
import adopt_net0.data_preprocessing as dp
from adopt_net0.modelhub import ModelHub
from adopt_net0.result_management.read_results import add_values_to_summary
import pandas as pd


#Create data Chemelot cluster without GT
execute = 0

if execute == 1:
    # Specify the path to your input data
    casepath = "Z:/PyHub/PyHub_casestudies/CM/Chemelot_cluster"
    datapath = "Z:/PyHub/PyHub_data/CM/170624_CM"
    resultpath = "Z:/PyHub/PyHub_results/CM/Chemelot_cluster"


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
        dp.fill_carrier_data(casepath, value_or_data=135, columns=['Demand'], carriers=['ammonia'])
        dp.fill_carrier_data(casepath, value_or_data=45, columns=['Demand'], carriers=['CO2'])
        dp.fill_carrier_data(casepath, value_or_data=150, columns=['Demand'], carriers=['ethylene'])
        dp.fill_carrier_data(casepath, value_or_data=27.8, columns=['Demand'], carriers=['steam'])
        dp.fill_carrier_data(casepath, value_or_data=86.4, columns=['Demand'], carriers=['electricity'])
        dp.fill_carrier_data(casepath, value_or_data=6.9, columns=['Demand'], carriers=['crackergas'])

        # No import limit
        dp.fill_carrier_data(casepath, value_or_data=2000, columns=['Import limit'], carriers=['electricity', 'methane', 'naphtha', "CO2"])

        # No export limit
        dp.fill_carrier_data(casepath, value_or_data=2000, columns=['Export limit'], carriers=['nitrogen', 'oxygen', 'heatlowT', 'steam', 'crackergas'])
        dp.fill_carrier_data(casepath, value_or_data=0.203, columns=['Export emission factor'],
                             carriers=['crackergas'])

        # CO2 export
        dp.fill_carrier_data(casepath, value_or_data=115, columns=['Export limit'], carriers=['CO2'])
        dp.fill_carrier_data(casepath, value_or_data=-61.90, columns=['Export price'], carriers=['CO2'])

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


#Create data Chemelot cluster without GT
execute = 1

if execute == 1:
    # Specify the path to your input data
    casepath = "Z:/PyHub/PyHub_casestudies/CM/Chemelot_cluster_GT"
    datapath = "Z:/PyHub/PyHub_data/CM/170624_CM"


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
        dp.fill_carrier_data(casepath, value_or_data=135, columns=['Demand'], carriers=['ammonia'])
        dp.fill_carrier_data(casepath, value_or_data=45, columns=['Demand'], carriers=['CO2'])
        dp.fill_carrier_data(casepath, value_or_data=150, columns=['Demand'], carriers=['ethylene'])
        dp.fill_carrier_data(casepath, value_or_data=27.8, columns=['Demand'], carriers=['steam'])
        dp.fill_carrier_data(casepath, value_or_data=86.4, columns=['Demand'], carriers=['electricity'])
        dp.fill_carrier_data(casepath, value_or_data=6.9, columns=['Demand'], carriers=['crackergas'])

        # No import limit
        dp.fill_carrier_data(casepath, value_or_data=2000, columns=['Import limit'], carriers=['electricity', 'methane', 'naphtha', "CO2"])

        # No export limit
        dp.fill_carrier_data(casepath, value_or_data=2000, columns=['Export limit'],
                             carriers=['nitrogen', 'oxygen', 'heatlowT', 'steam'])


        # CO2 export
        dp.fill_carrier_data(casepath, value_or_data=115, columns=['Export limit'], carriers=['CO2'])
        dp.fill_carrier_data(casepath, value_or_data=-61.90, columns=['Export price'], carriers=['CO2'])

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
