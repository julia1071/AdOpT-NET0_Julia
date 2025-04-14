import os
import h5py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.ticker import PercentFormatter
from adopt_net0 import extract_datasets_from_h5group

# Define the data path
result_types = ['EmissionLimit Greenfield', 'EmissionLimit Brownfield', 'EmissionScope Greenfield', 'EmissionScope Brownfield']  # Add multiple result types

data_to_excel_path = 'C:/EHubversions/AdOpT-NET0_Julia/Plotting/result_data_long.xlsx'

# Initialize an empty dictionary to collect DataFrame results
all_results = []

for result_type in result_types:
    resultfolder = f"Z:/AdOpt_NET0/AdOpt_results/MY/{result_type}"

    # Define the multi-level index for rows
    columns = pd.MultiIndex.from_product(
        [
            [str(result_type)],
            ["Chemelot"],
            ["2030", "2040", "2050"]
        ],
        names=["Resulttype", "Location", "Interval"]
    )

    # Define the index rows
    index = ["path", "costs_interval", "sunk_costs", "costs_tot", "emissions_tot"]

    # Create the DataFrame for this result type with NaN values
    result_data = pd.DataFrame(np.nan, index=index, columns=columns)

    # Fill the path column using a loop
    for location in result_data.columns.levels[1]:
        folder_name = f"{location}"
        summarypath = os.path.join(resultfolder, folder_name, "Summary.xlsx")

        try:
            summary_results = pd.read_excel(summarypath)
        except FileNotFoundError:
            print(f"Warning: Summary file not found for {result_type} - {location}")
            continue

        tec_costs = {}
        total_costs = {}
        for case in summary_results['case']:
            for i, interval in enumerate(result_data.columns.levels[2]):
                if pd.notna(case) and interval in case:
                    h5_path = Path(summary_results.loc[summary_results['case'] == case, 'time_stamp'].iloc[
                                       0]) / "optimization_results.h5"
                    result_data.at["path", (result_type, location, interval)] = h5_path
                    result_data.loc["costs_interval", (result_type, location, interval)] = \
                        summary_results.loc[summary_results['case'] == case, 'total_npv'].iloc[0]
                    result_data.loc["emissions_tot", (result_type, location, interval)] = \
                        summary_results.loc[summary_results['case'] == case, 'emissions_pos'].iloc[0]
                    tec_costs[interval] = summary_results.loc[summary_results['case'] == case, 'cost_capex_tecs'].iloc[0]
                    total_costs[interval] = summary_results.loc[summary_results['case'] == case, 'total_npv'].iloc[
                        0]

                    #Calculate sunk costs for brownfield
                    if 'Brownfield' in result_type and interval != '2030':
                        prev_interval = result_data.columns.levels[2][i - 1]
                        if interval == '2040':
                            result_data.loc["sunk_costs", (result_type, location, interval)] = tec_costs[prev_interval]
                            result_data.loc["costs_tot_interval", (result_type, location, interval)] = tec_costs[prev_interval] + \
                                summary_results.loc[summary_results['case'] == case, 'total_npv'].iloc[0]
                        if interval == '2050':
                            first_interval = result_data.columns.levels[2][i - 2]
                            result_data.loc["sunk_costs", (result_type, location, interval)] = tec_costs[
                                prev_interval] + tec_costs[first_interval]
                            result_data.loc["costs_tot_interval", (result_type, location, interval)] = tec_costs[prev_interval] + \
                                + tec_costs[first_interval] + summary_results.loc[summary_results['case'] == case, 'total_npv'].iloc[0]

                    # Calculate total cumulative costs
                    if 'Brownfield' in result_type:
                        if interval == '2050':
                            result_data.loc["costs_tot_cumulative", (result_type, location, interval)] = sum(total_costs.values()) * 10
                    elif 'Greenfield' in result_type:
                        result_data.loc["costs_tot_cumulative", (result_type, location, interval)] = total_costs[interval] * 30

                    if h5_path.exists():
                        with h5py.File(h5_path, "r") as hdf_file:
                            nodedata = extract_datasets_from_h5group(hdf_file["design/nodes"])
                            df_nodedata = pd.DataFrame(nodedata)

                            for tec in df_nodedata.columns.levels[2]:
                                output_name = f'size_{tec}'
                                if (interval, location, tec, 'size') in df_nodedata.columns:
                                    result_data.loc[output_name, (result_type, location, interval)] = \
                                        df_nodedata[(interval, location, tec, 'size')].iloc[0]
                                else:
                                    result_data.loc[output_name, (result_type, location, interval)] = 0

                            ebalance = extract_datasets_from_h5group(hdf_file["operation/energy_balance"])
                            df_ebalance = pd.DataFrame(ebalance)
                            cars_at_node = df_ebalance[interval, location].columns.droplevel([1]).unique()

                            for car in cars_at_node:
                                parameters = ["import", "export"]
                                for para in parameters:
                                    output_name = f"{car}/{para}_max"
                                    if (interval, location, car, para) in df_ebalance.columns:
                                        car_output = df_ebalance[interval, location, car, para]
                                        result_data.loc[output_name, (result_type, location, interval)] = max(
                                            car_output)
                                    else:
                                        result_data.loc[output_name, (result_type, location, interval)] = 0

    # Store results for this result_type
    all_results.append(result_data)

# Concatenate all result types into a single DataFrame
final_result_data = pd.concat(all_results, axis=1)

# Save to Excel (optional)
final_result_data.to_excel(data_to_excel_path)
