import numpy as np
import pandas as pd
import os

from matplotlib import pyplot as plt
from openpyxl.reader.excel import load_workbook

# Load the Excel file
file_path = "C:/EHubversions/AdOpT-NET0_Julia/Plotting/result_data_long.xlsx"
df = pd.read_excel(file_path, sheet_name="Sheet1", header=None)

# Use the first and third rows as headers
top_header = df.iloc[0].ffill()  # Forward fill merged cells
# top_header = top_header.replace({"EmissionLimit Greenfield": "Greenfield (Scope 1, 2, and 3)", "EmissionLimit Brownfield": "Brownfield (Scope 1, 2, and 3)",
#                                  "EmissionScope Greenfield": "Greenfield (Scope 1 and 2)", "EmissionScope Brownfield":
#                                      "Brownfield (Scope 1 and 2)",})
sub_header = df.iloc[2].ffill()
# sub_header = df.iloc[2].replace({"2030": "Short-term", "2040": "Mid-term", "2050": "Long-term"})

# sub_header = df.iloc[2].astype(str)  # Convert to string
df.columns = pd.MultiIndex.from_arrays([top_header, sub_header])

# Rename first column header
top_header = top_header.copy()  # Avoid modifying the original header list
top_header.iloc[0] = ""
sub_header.iloc[0] = "Result type"
df = df.iloc[4:].reset_index(drop=True)

# Define the filter criteria
keywords = [
    "costs_interval", "sunk_costs", "costs_tot_interval", "costs_tot_cumulative", "emissions_tot"
]

# Extract first column name
first_column_name = df.columns[0]

# Filter rows based on keywords
filtered_df = df[df[first_column_name].astype(str).str.startswith(tuple(keywords))]

# Prepare figure
fig, ax = plt.subplots(figsize=(10, 5))

# Bar positions
x = np.arange(8)
bar_width = 0.8

# Colors
colors = ["#4C72B0", "#55A868", "#C44E52", "#8172B2"]
brownfield_color = "#DD8452"

# Labels
x_labels = ['Greenfield\n2030', 'Greenfield\n2040', 'Greenfield\n2050', 'Brownfield',
            'Greenfield\n2030', 'Greenfield\n2040', 'Greenfield\n2050', 'Brownfield']
section_titles = ['EmissionLimit', 'EmissionScope']


# --- Extract values from your multiindex dataframe ---
# Helper function to get data
def get_val(df, label, year, cost_type):
    try:
        first_column_name = df.columns[0]
        return float(df.loc[df[first_column_name] == cost_type, (label, year)].values[0])
    except:
        return 0


# Build values
greenfield_limit = [get_val(filtered_df, 'EmissionLimit Greenfield', year, "costs_tot_cumulative") for year in
                    ['2030', '2040', '2050']]
brownfield_limit = [get_val(filtered_df, 'EmissionLimit Brownfield', year, "costs_tot_interval") * 10 for year in
                    ['2030', '2040', '2050']]
brownfield_limit_sum = sum(brownfield_limit)

greenfield_scope = [get_val(filtered_df,'EmissionScope Greenfield', year, "costs_tot_cumulative") for year in
                    ['2030', '2040', '2050']]
brownfield_scope = [get_val(filtered_df,'EmissionScope Brownfield', year, "costs_tot_interval") * 10 for year in
                    ['2030', '2040', '2050']]
brownfield_scope_sum = sum(brownfield_scope)

# --- Plot bars ---
# EmissionLimit section
bars1 = ax.bar(x[:3], greenfield_limit, color=colors, label='Greenfield')
bar1b = ax.bar(x[3], brownfield_limit[0], color=brownfield_color)
bar1b2 = ax.bar(x[3], brownfield_limit[1], bottom=brownfield_limit[0], color='lightgray')
bar1b3 = ax.bar(x[3], brownfield_limit[2], bottom=brownfield_limit[0] + brownfield_limit[1], color='darkgray')

# EmissionScope section
bars2 = ax.bar(x[4:7], greenfield_scope, color=colors, label='Greenfield')
bar2b = ax.bar(x[7], brownfield_scope[0], color=brownfield_color)
bar2b2 = ax.bar(x[7], brownfield_scope[1], bottom=brownfield_scope[0], color='lightgray')
bar2b3 = ax.bar(x[7], brownfield_scope[2], bottom=brownfield_scope[0] + brownfield_scope[1], color='darkgray')

# --- Add dashed line separator ---
ax.axvline(x=3.5, color='black', linestyle='dashed')

# --- Labels and formatting ---
ax.set_xticks(x)
ax.set_xticklabels(x_labels)
ax.set_ylabel("System costs [M€]")
# ax.set_title("Total system costs under different emission targets")

# Annotate section titles
ax.text(1.5, ax.get_ylim()[1] * 1.02, "Scope 1, 2 & 3", ha='center', fontsize=10)
ax.text(5.5, ax.get_ylim()[1] * 1.02, "Scope 1 & 2", ha='center', fontsize=10)

# Legend
custom_legend = [
    plt.Rectangle((0, 0), 1, 1, color=colors[0], label='Greenfield'),
    plt.Rectangle((0, 0), 1, 1, color=brownfield_color, label='Brownfield (2030)'),
    plt.Rectangle((0, 0), 1, 1, color='lightgray', label='Brownfield (2040)'),
    plt.Rectangle((0, 0), 1, 1, color='darkgray', label='Brownfield (2050)'),
]
ax.legend(handles=custom_legend, loc='upper left')

plt.tight_layout()
filename = 'TC_baseline'
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
