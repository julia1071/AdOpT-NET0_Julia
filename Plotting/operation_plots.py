import os
import h5py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.colors import to_rgba
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from adopt_net0 import extract_datasets_from_h5group, extract_dataset_from_h5

# Define the data paths
RESULT_FOLDER = "Z:/AdOpt_NET0/AdOpt_results/MY/"
DATA_TO_EXCEL_PATH = 'C:/EHubversions/AdOpT-NET0_Julia//Plotting/operation_flex_import.xlsx'
DATA_TO_EXCEL_PATH1 = 'C:/EHubversions/AdOpT-NET0_Julia/Plotting/operation_flex.xlsx'
DATA_TO_EXCEL_PATH2 = 'C:/EHubversions/AdOpT-NET0_Julia/Plotting/operation_flex_storage.xlsx'
DATAPATH = "C:/EHubversions/AdOpT-NET0_Julia/Plotting"
EL_LOAD_PATH = "Z:/AdOpt_NET0/AdOpt_data/MY/241119_MY_Data_Chemelot/import_data/Electricity_data_MY.xlsx"


def fetch_and_process_data_import(resultfolder, data_to_excel_path, result_types, interval):
    """
    Fetch data from HDF5 files, process it, and save the results to an Excel file.
    """
    # Initialize an empty dictionary to collect DataFrame results
    all_results = []

    for result_type in result_types:
        resultfolder_type = f"{resultfolder}{result_type}"

        # Define the multi-level index for rows
        columns = pd.MultiIndex.from_product(
            [
                [str(result_type)],
                ["Chemelot"],
                [interval]
            ],
            names=["Resulttype", "Location", "Interval"]
        )

        # Create the DataFrame for this result type with NaN values
        result_data = pd.DataFrame(np.nan, index=range(8760), columns=columns)

        # Fill the path column using a loop
        for location in result_data.columns.levels[1]:
            folder_name = f"{location}"
            summarypath = os.path.join(resultfolder_type, folder_name, "Summary.xlsx")

            try:
                summary_results = pd.read_excel(summarypath)
            except FileNotFoundError:
                print(f"Warning: Summary file not found for {result_type} - {location}")
                continue

            for interval in result_data.columns.levels[2]:
                for case in summary_results['case']:
                    if pd.notna(case) and interval in case:
                        h5_path = Path(summary_results[summary_results['case'] == case].iloc[0][
                                           'time_stamp']) / "optimization_results.h5"
                        if h5_path.exists():
                            with h5py.File(h5_path, "r") as hdf_file:
                                ebalance_data = extract_datasets_from_h5group(hdf_file["operation/energy_balance"])
                                df_ebalance_data = pd.DataFrame(ebalance_data)

                                car = "electricity"
                                para = "import"
                                if (interval, location, car, para) in df_ebalance_data.columns:
                                    car_output = df_ebalance_data[interval, location, car, para]
                                    result_data.loc[:, (result_type, location, interval)] = car_output
                                else:
                                    result_data.loc[:, (result_type, location, interval)] = 0

        # Store results for this result_type
        all_results.append(result_data)

    #Data to excel
    all_results = pd.concat(all_results, axis=1)
    all_results.to_excel(data_to_excel_path)


def fetch_and_process_data_operation(resultfolder, data_to_excel_path, result_type, interval):
    """
    Fetch data from HDF5 files, process it, and save the results to an Excel file.
    """
    # Initialize an empty dictionary to collect DataFrame results
    all_results = []

    resultfolder_type = f"{resultfolder}{result_type}"

    # Define the multi-level index for rows
    columns = pd.MultiIndex.from_product(
        [
            [result_type],
            ["Chemelot"],
            [interval],
            ["ElectricSMR_m", "AEC", "MPW", "PDH", "Storage_Battery"]
        ],
        names=["Resulttype", "Location", "Interval", "Tecs"]
    )

    # Create the DataFrame for this result type with NaN values
    result_data = pd.DataFrame(np.nan, index=range(8760), columns=columns)

    # Fill the path column using a loop
    for location in result_data.columns.levels[1]:
        folder_name = f"{location}"
        summarypath = os.path.join(resultfolder_type, folder_name, "Summary.xlsx")

        try:
            summary_results = pd.read_excel(summarypath)
        except FileNotFoundError:
            print(f"Warning: Summary file not found for {result_type} - {location}")
            continue

        for interval in result_data.columns.levels[2]:
            for case in summary_results['case']:
                if pd.notna(case) and interval in case:
                    h5_path = Path(summary_results[summary_results['case'] == case].iloc[0][
                                       'time_stamp']) / "optimization_results.h5"
                    if h5_path.exists():
                        with h5py.File(h5_path, "r") as hdf_file:
                            tec_operation = extract_datasets_from_h5group(hdf_file["operation/technology_operation"])
                            tec_operation = {k: v for k, v in tec_operation.items() if len(v) >= 8670}
                            df_tec_operation = pd.DataFrame(tec_operation)

                            for tec in result_data.columns.levels[3]:
                                para = "electricity_input"
                                if (interval, location, tec, para) in df_tec_operation:
                                    car_output = df_tec_operation[interval, location, tec, para]
                                    result_data.loc[:, (result_type, location, interval, tec)] = car_output
                                else:
                                    result_data.loc[:, (result_type, location, interval, tec)] = 0

        # Store results for this result_type
        all_results.append(result_data)

    # Data to excel
    all_results = pd.concat(all_results, axis=1)
    all_results.to_excel(data_to_excel_path)


def fetch_and_process_data_storage(resultfolder, data_to_excel_path, result_type, interval):
    """
    Fetch data from HDF5 files, process it, and save the results to an Excel file.
    """
    # Initialize an empty dictionary to collect DataFrame results
    all_results = []

    resultfolder_type = f"{resultfolder}{result_type}"

    # Define the multi-level index for rows
    columns = pd.MultiIndex.from_product(
        [
            [result_type],
            ["Chemelot"],
            [interval],
            ["Storage_Ammonia", "Storage_CO2", "Storage_Ethylene",
             "Storage_H2", "Storage_Battery", "Storage_Propylene"]
        ],
        names=["Resulttype", "Location", "Interval", "Tecs"]
    )

    # Create the DataFrame for this result type with NaN values
    result_data = pd.DataFrame(np.nan, index=range(8760), columns=columns)

    # Fill the path column using a loop
    for location in result_data.columns.levels[1]:
        folder_name = f"{location}"
        summarypath = os.path.join(resultfolder_type, folder_name, "Summary.xlsx")

        try:
            summary_results = pd.read_excel(summarypath)
        except FileNotFoundError:
            print(f"Warning: Summary file not found for {result_type} - {location}")
            continue

        for interval in result_data.columns.levels[2]:
            for case in summary_results['case']:
                if pd.notna(case) and interval in case:
                    h5_path = Path(summary_results[summary_results['case'] == case].iloc[0][
                                       'time_stamp']) / "optimization_results.h5"
                    if h5_path.exists():
                        with h5py.File(h5_path, "r") as hdf_file:
                            tec_operation = extract_datasets_from_h5group(hdf_file["operation/technology_operation"])
                            tec_operation = {k: v for k, v in tec_operation.items() if len(v) >= 8670}
                            df_tec_operation = pd.DataFrame(tec_operation)

                            for tec in result_data.columns.levels[3]:
                                para = "storage_level"
                                if (interval, location, tec, para) in df_tec_operation:
                                    car_output = df_tec_operation[interval, location, tec, para]
                                    result_data.loc[:, (result_type, location, interval, tec)] = car_output
                                else:
                                    result_data.loc[:, (result_type, location, interval, tec)] = 0

        # Store results for this result_type
        all_results.append(result_data)

    # Data to excel
    all_results = pd.concat(all_results, axis=1)
    all_results.to_excel(data_to_excel_path)


def configure_matplotlib():
    """
    Configure Matplotlib to use LaTeX for text rendering and set font.
    """
    plt.rcParams.update({
        "text.usetex": True,
        "font.family": "serif",
        "font.serif": ["Computer Modern Roman"],
        "axes.labelsize": 12,
        "font.size": 12,
        "legend.fontsize": 11,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
    })


def extract_profiles(result_data, result_types, interval):
    """
    Extract import profiles from the result data.
    """
    return {
        (result_type, location, interval): result_data.loc[:, (result_type, location, interval)]
        for result_type in result_types
        for location in ["Chemelot"]
    }


def extract_profiles_operation(result_data, result_type, interval):
    """
    Extract import profiles from the result data.
    """
    return {
        (result_type, location, interval, tec): result_data.loc[:, (result_type, location, interval, tec)]
        for location in ["Chemelot"]
        for tec in ["ElectricSMR_m", "AEC", "MPW", "PDH", "Storage_Battery"]
    }


def extract_profiles_storage(result_data, result_type, interval):
    """
    Extract import profiles from the result data.
    """
    return {
        (result_type, location, interval, tec): result_data.loc[:, (result_type, location, interval, tec)]
        for location in ["Chemelot"]
        for tec in ["Storage_Ammonia", "Storage_CO2", "Storage_Ethylene",
                    "Storage_H2", "Storage_Battery", "Storage_Propylene"]
    }


def plot_import_profiles(import_profiles, el_price, el_price2, el_emissionrate,
                         relative=False, overlay=None, colors=None):
    """
    Plot import profiles with optional overlays and custom colors, updated for new result types.
    """
    weeks = {
        'Winter': range(0, 168),
        'Spring': range(168 * 12, 168 * 13),
        'Summer': range(168 * 25, 168 * 26),
        'Fall': range(168 * 38, 168 * 39)
    }

    label_map = {
        "EmissionLimit Greenfield": "Greenfield (Scope 1, 2, and 3)",
        "EmissionLimit Brownfield": "Brownfield (Scope 1, 2, and 3)",
        "EmissionScope Greenfield": "Greenfield (Scope 1 and 2)",
        "EmissionScope Brownfield": "Brownfield (Scope 1 and 2)",
    }

    plt.figure(figsize=(10, 5))

    color_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color'] if colors is None else colors
    legend_handles = []

    for i, (season, week_range) in enumerate(weeks.items(), start=1):
        plt.subplot(2, 2, i)
        ax1 = plt.gca()

        for idx, (key, profile) in enumerate(import_profiles.items()):
            color = color_cycle[idx % len(color_cycle)]
            label = label_map.get(key[0], key[0])  # fall back to key if not in map

            if relative:
                max_import = profile.max()
                line, = ax1.plot(list(week_range), profile.iloc[week_range] / max_import,
                                 label=label, linewidth=0.75, color=color)
            else:
                line, = ax1.plot(list(week_range), profile.iloc[week_range],
                                 label=label, linewidth=0.75, color=color)

            if i == 1:
                legend_handles.append((line, label))

        if overlay:
            ax2 = ax1.twinx()
            if overlay == "el_price":
                line1, = ax2.plot(list(week_range), el_price.iloc[week_range], color='grey',
                                  linestyle='dotted', linewidth=0.8, label='Chemelot Price')
                line2, = ax2.plot(list(week_range), el_price2.iloc[week_range], color='black',
                                  linestyle='dotted', linewidth=0.8, label='Zeeland Price')
                ax2.set_ylabel('Electricity Price [€/MWh]')
                ax2.set_ylim(0, 150)
                if i == 1:
                    legend_handles.extend([(line1, line1.get_label()), (line2, line2.get_label())])
            elif overlay == "emission":
                line1, = ax2.plot(list(week_range), el_emissionrate.iloc[week_range], color='black',
                                  linestyle='dotted', linewidth=0.8, label='Emission Rate')
                ax2.set_ylabel('Emission Rate [t CO$_2$/MWh]')
                ax2.set_ylim(0, 0.25)
                if i == 1:
                    legend_handles.append((line1, line1.get_label()))

        ax1.set_xlabel('Time (hours)')
        ax1.set_ylabel('Electricity import' + (' (Relative)' if relative else ' [MW]'))
        ax1.set_title(f'{season}')
        ax1.set_ylim(0, 1000)
        ax1.grid(True, alpha=0.5)

    # Shared legend
    plt.tight_layout(rect=[0, 0.1, 1, 1])  # leave bottom 7% for legend
    handles, labels = zip(*legend_handles)
    plt.figlegend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.01), ncol=3)


def plot_operation_profiles(operation_profiles, el_price2, el_emissionrate, relative=False, overlay=None, colors=None):
    """
    Plot operation profiles with optional overlays and custom colors
    for one location and one result type (multiple technologies).
    """
    weeks = {
        'Winter': range(0, 168),
        'Spring': range(168 * 12, 168 * 13),
        'Summer': range(168 * 25, 168 * 26),
        'Fall': range(168 * 38, 168 * 39)
    }

    plt.figure(figsize=(10, 5))

    color_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color'] if colors is None else colors

    tech_labels = {
        "ElectricSMR_m": "Electric SMR",
        "AEC": "Electrolyzer (AEC)",
        "MPW": "MPW gasification",
        "PDH": "PDH",
        "Storage_Battery": "Battery Storage"
    }

    legend_handles = []

    for i, (season, week_range) in enumerate(weeks.items(), start=1):
        plt.subplot(2, 2, i)
        ax1 = plt.gca()

        for idx, ((_, _, _, tec), profile) in enumerate(operation_profiles.items()):  # ignore loc, type, interval
            color = color_cycle[idx % len(color_cycle)]
            label = tech_labels.get(tec, tec)
            if relative:
                max_val = profile.max()
                line, = ax1.plot(list(week_range), profile.iloc[week_range] / max_val, label=label,
                                 linewidth=0.75, color=color)
                ax1.set_ylim(0, 1.1)
            else:
                line, = ax1.plot(list(week_range), profile.iloc[week_range], label=label,
                                 linewidth=0.75, color=color)
                ax1.set_ylim(0, 1000)

            if i == 1:
                legend_handles.append((line, label))

        # Overlay: el_price2 or emission
        if overlay:
            ax2 = ax1.twinx()
            if overlay == "el_price":
                line2, = ax2.plot(list(week_range), el_price2.iloc[week_range], color='black', linestyle='dotted',
                                  linewidth=0.8, label='Electricity Price')
                ax2.set_ylabel('Electricity Price [€/MWh]')
                ax2.set_ylim(0, 150)
            elif overlay == "emission":
                line2, = ax2.plot(list(week_range), el_emissionrate.iloc[week_range], color='black',
                                  linestyle='dotted', linewidth=0.8, label='Emission Rate')
                ax2.set_ylabel('Emission Rate [t CO$_2$/MWh]')
                ax2.set_ylim(0, 0.25)

            if i == 1:
                legend_handles.append((line2, line2.get_label()))

        ax1.set_xlabel('Time (hours)')
        ax1.set_ylabel('Electricity consumption\n' + (' (Relative)' if relative else ' [MW]'))
        ax1.set_title(f'{season}')
        ax1.grid(True, alpha=0.5)

    # Legend below all subplots
    plt.tight_layout(rect=[0, 0.1, 1, 1])
    handles, labels = zip(*legend_handles)
    plt.figlegend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.01), ncol=3)


def plot_storage_level(operation_profiles, colors=None, zoom_techs=None):
    """
    Plot storage levels over the full year using area fill,
    one vertically stacked plot per storage technology.
    Optionally adds summer week zoom-in for specified technologies.
    """
    color_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color'] if colors is None else colors
    zoom_techs = zoom_techs or []

    tech_labels = {
        "Storage_Ammonia": "Ammonia tank",
        "Storage_H2": "Hydrogen tank",
        "Storage_Ethylene": "Ethylene tank",
        "Storage_Propylene": "Propylene tank",
        "Storage_Battery": "Battery storage"
    }

    # Filter profiles by matching tech names
    storage_profiles = {
        key: val for key, val in operation_profiles.items()
        if key[3] in tech_labels and val.mean() >= 1
    }

    num_techs = len(storage_profiles)
    fig, axes = plt.subplots(num_techs, 1, figsize=(10, 2 * num_techs), sharex=True)

    # Make sure axes is always iterable
    if num_techs == 1:
        axes = [axes]

    for ax, ((_, _, _, tec), profile), color in zip(axes, storage_profiles.items(), color_cycle):
        label = tech_labels[tec]

        ax.fill_between(range(len(profile)), profile, color=color, alpha=0.6, label=label)

        ax.set_title(label)
        ax.set_ylabel('Storage level [MWh]' if any(x in tec for x in ["Battery", "H2"]) else 'Storage level [ton]')
        ax.grid(True, alpha=0.3)

        # Optional summer zoom inset
        if tec in zoom_techs:
            summer_start = 168 * 25
            summer_end = summer_start + 168
            zoom_ax = inset_axes(ax, width="40%", height="35%", loc='upper right', borderpad=2)
            zoom_ax.fill_between(range(summer_start, summer_end),
                                 profile[summer_start:summer_end],
                                 color=color, alpha=0.6)
            zoom_ax.set_title("Summer week", fontsize=8)
            zoom_ax.tick_params(labelsize=6)
            zoom_ax.grid(True, alpha=0.3)
            zoom_ax.set_xlim(summer_start, summer_end)

    axes[-1].set_xlabel('Time (hours)')

    plt.tight_layout(h_pad=1.5)



def main():
    set_result_types = ['EmissionLimit Greenfield', 'EmissionLimit Brownfield', 'EmissionScope Greenfield',
                        'EmissionScope Brownfield']  # Add multiple result types
    result_type = 'EmissionLimit Greenfield'
    interval = '2030'

    get_data = 0

    if get_data == 1:
        fetch_and_process_data_import(RESULT_FOLDER, DATA_TO_EXCEL_PATH, set_result_types, interval)
        fetch_and_process_data_operation(RESULT_FOLDER, DATA_TO_EXCEL_PATH1, result_type, interval)
        fetch_and_process_data_storage(RESULT_FOLDER, DATA_TO_EXCEL_PATH2, result_type, interval)
        import_data = pd.read_excel(DATA_TO_EXCEL_PATH, index_col=0, header=[0, 1, 2])
        operation_data = pd.read_excel(DATA_TO_EXCEL_PATH1, index_col=0, header=[0, 1, 2, 3])
        storage_data = pd.read_excel(DATA_TO_EXCEL_PATH2, index_col=0, header=[0, 1, 2, 3])
    else:
        import_data = pd.read_excel(DATA_TO_EXCEL_PATH, index_col=0, header=[0, 1, 2])
        operation_data = pd.read_excel(DATA_TO_EXCEL_PATH1, index_col=0, header=[0, 1, 2, 3])
        storage_data = pd.read_excel(DATA_TO_EXCEL_PATH2, index_col=0, header=[0, 1, 2, 3])

    configure_matplotlib()
    el_importdata = pd.read_excel(EL_LOAD_PATH, sheet_name=interval, header=0, nrows=8760)
    el_price = el_importdata.iloc[:, 0]
    el_price2 = el_importdata.iloc[:, 1]
    el_emissionrate = el_importdata.iloc[:, 2]

    import_profiles = extract_profiles(import_data, set_result_types, interval)
    operation_profiles = extract_profiles_operation(operation_data, result_type, interval)
    storage_profiles = extract_profiles_storage(storage_data, result_type, interval)

    # custom_colors_operation = ['#512500', '#7D1D3F', '#9467bd', '#33658A', '#F26419']
    # custom_colors_operation = ['#5D3250', '#94617B', '#A37BA2', '#A0B7BB', '#4A7787']
    custom_colors_operation = ['#422966', '#EEBD6D', '#EEEEFF', '#79AA74', '#28587B']
    custom_colors_import = ['#3F826D', '#E15F51', '#545E75', '#F2D0A4']
    custom_colors_storage = ['#3F826D', '#E15F51', '#545E75', '#F2D0A4']
    overlay = "emission"
    plot = "storage_level"

    if plot == "technology_operation":
        plot_operation_profiles(operation_profiles, el_price2, el_emissionrate, relative=True, overlay=overlay,
                                colors=custom_colors_operation)
        name = f"{interval}_{result_type.replace(' ', '_')}"
    elif plot == "electricity_import":
        plot_import_profiles(import_profiles, el_price, el_price2, el_emissionrate, relative=False, overlay=overlay,
                             colors=custom_colors_import)
        name = f"{interval}"
    elif plot == "storage_level":
        plot_storage_level(storage_profiles, colors=custom_colors_storage, zoom_techs=["Storage_Battery", "Storage_H2"])
        name = f"{interval}_{result_type.replace(' ', '_')}"

    filename = plot + '_' + name

    saveas = 'both'
    if saveas == 'svg':
        savepath = f'C:/Users/5637635/Documents/OneDrive - Universiteit Utrecht/Research/Multiyear Modeling/MY_Plots/{filename}.svg'
        plt.savefig(savepath, format='svg')
    elif saveas == 'pdf':
        savepath = f'C:/Users/5637635/Documents/OneDrive - Universiteit Utrecht/Research/Multiyear Modeling/MY_Plots/{filename}.pdf'
        plt.savefig(savepath, format='pdf')
    elif saveas == 'both':
        savepath = f'C:/Users/5637635/Documents/OneDrive - Universiteit Utrecht/Research/Multiyear Modeling/MY_Plots/{filename}.pdf'
        plt.savefig(savepath, format='pdf')
        savepath = f'C:/Users/5637635/Documents/OneDrive - Universiteit Utrecht/Research/Multiyear Modeling/MY_Plots/{filename}.svg'
        plt.savefig(savepath, format='svg')

    plt.show()


if __name__ == "__main__":
    main()
