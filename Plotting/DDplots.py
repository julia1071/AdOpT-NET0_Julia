import h5py
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.ticker import PercentFormatter
from adopt_net0 import extract_datasets_from_h5group

# Define the data path
run_for = 'bf'
interval = '2030'
resultfolder = "Z:/AdOpt_NET0/AdOpt_results/MY/DesignDays/CH_2030_" + run_for

# Define reference case ('fullres' or 'DD..' and technologies
# tecs = ['AEC', 'MTO', 'Storage_Ammonia']
tecs = ['AEC']
reference_case = 'fullres'

# Extract the relevant data
summarypath = Path(resultfolder) / 'Summary.xlsx'
summary_results = pd.read_excel(summarypath)

# full resolution reference
reference_case_results = {
    'costs': summary_results[summary_results['case'] == reference_case].iloc[0]['total_npv'],
    'emissions': summary_results[summary_results['case'] == reference_case].iloc[0]['emissions_pos'],
    'computation time': summary_results[summary_results['case'] == reference_case].iloc[0]['time_total']
}
reference_case_path_h5 = Path(summary_results[summary_results['case'] == reference_case].iloc[0]['time_stamp']) / "optimization_results.h5"

#get capacities from h5 files
if reference_case_path_h5.exists():
    with h5py.File(reference_case_path_h5, "r") as hdf_file:
        df = extract_datasets_from_h5group(hdf_file["design/nodes"])
        for tec in tecs:
            output_name = 'size_' + tec
            reference_case_results[output_name] = df[(interval, 'Chemelot', tec, 'size')][0]


#now collect data to plot
data = []
for case in summary_results['case']:
    if pd.notna(case) and case != reference_case:
        case_data = {
            'case': case,
            'DD': int(case[2:]),
            'costs': summary_results.loc[summary_results['case'] == case, 'total_npv'].iloc[0],
            'emissions': summary_results.loc[summary_results['case'] == case, 'emissions_pos'].iloc[0],
            'computation time': summary_results.loc[summary_results['case'] == case, 'time_total'].iloc[0]
        }

        #collect sizes from h5
        case_path_h5 = Path(
            summary_results[summary_results['case'] == case].iloc[0]['time_stamp']) / "optimization_results.h5"

        if reference_case_path_h5.exists():
            with h5py.File(reference_case_path_h5, "r") as hdf_file:
                df = extract_datasets_from_h5group(hdf_file["design/nodes"])
                for tec in tecs:
                    output_name = 'size_' + tec
                    case_data[output_name] = df[(interval, 'Chemelot', tec, 'size')][0]

        data.append(case_data)

# Convert the list of dictionaries into a DataFrame
clustered_results = pd.DataFrame(data)
clustered_results.set_index('case', inplace=True)

# difference
columns_of_interest = ['costs', 'emissions', 'computation time']
columns_of_interest.extend(['size_' + tec for tec in tecs])
for column in columns_of_interest:
    clustered_results[f'{column}_diff'] = ((clustered_results[column] - reference_case_results[column]) / reference_case_results[column]) * 100

# Configure Matplotlib to use LaTeX for text rendering and set font
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ["Computer Modern Roman"],
    "axes.labelsize": 12,
    "font.size": 12,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
})

# Define custom colors
# colors = ['#9fa0c3', '#8b687f', '#7b435b', '#4C4D71', '#B096A7']
colors = ['#639051', '#E4F0D0', '#5277B7', '#FFBC47']
markers = ['o', '*', 'D', '^']

# Choose the plot type: 'diff' for percentage differences, 'absolute' for absolute values
plot_type = 'diff'  # Can be changed to 'diff' and 'absolute'

# Create a new figure
fig, ax1 = plt.subplots(figsize=(5, 4))

# Scatter plots for differences (left y-axis in %)
for i, column in enumerate(columns_of_interest):
    if plot_type == 'diff' or (plot_type == 'absolute' and column != 'computation time'):  # Only the other columns get percentage differences
        for tec in tecs:
            label = f'Size Difference {tec}' if column == f'size_{tec}' else f'{column.capitalize()} Difference'
            ax1.scatter(clustered_results['DD'], clustered_results[f'{column}_diff'], color=colors[i], label=label, marker=markers[i])

# Set labels for the left y-axis (percentage)
ax1.set_xlabel('Number of Design Days')
ax1.set_ylabel('Difference with Full Resolution')
ax1.yaxis.set_major_formatter(PercentFormatter(decimals=0))


# Create a second y-axis for the absolute computation time
if plot_type == 'absolute':
    ax2 = ax1.twinx()
    computation_time_in_hours = clustered_results['computation time'] / 3600
    ax2.scatter(clustered_results['DD'], computation_time_in_hours, color='black', label='Computation Time', marker='x')
    ax1.set_ylim(-1, 10)
    ax2.set_ylim(-10, 100)

    # Set labels for the right y-axis (absolute values in hours)
    ax2.set_ylabel('Computation Time (hours)')
    handles2, labels2 = ax2.get_legend_handles_labels()
    handles, labels = ax1.get_legend_handles_labels()
    # Combine the legends from both axes
    ax1.legend(handles + handles2, labels + labels2, loc='upper left')
else:
    ax1.set_ylim(-100, 10)
    handles, labels = ax1.get_legend_handles_labels()
    ax1.legend(handles, labels, loc='center left')
    xmin, xmax = ax1.get_xlim()
    ax1.set_xticks(range(int(xmin), int(xmax) + 1, 10))

# Add grid and combine legends
ax1.grid(True, alpha=0.2)

# # Save and show plot
savepath = 'C:/Users/5637635/Documents/OneDrive - Universiteit Utrecht/Research/Multiyear Modeling/MY_Plots/'

plt.tight_layout()  # Apply before saving (optional, still helps with layout)

plt.savefig(f"{savepath}complexity_{run_for}_{plot_type}.pdf", format='pdf', bbox_inches='tight', pad_inches=0.05)
plt.savefig(f"{savepath}complexity_{run_for}_{plot_type}.svg", format='svg', bbox_inches='tight', pad_inches=0.05)

plt.show()


# Show the plot
# plt.show()
