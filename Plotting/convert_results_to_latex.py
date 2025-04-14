import pandas as pd
import os

from openpyxl.reader.excel import load_workbook

# Load the Excel file
file_path = "C:/EHubversions/AdOpT-NET0_Julia/Plotting/result_data_long_MPWwoCC.xlsx"
df = pd.read_excel(file_path, sheet_name="Sheet1", header=None)

# Use the first and third rows as headers
top_header = df.iloc[0].ffill()  # Forward fill merged cells
top_header = top_header.replace({"EmissionLimit Greenfield": "Greenfield (Scope 1, 2, and 3)", "EmissionLimit Brownfield": "Brownfield (Scope 1, 2, and 3)",
                                 "EmissionScope Greenfield": "Greenfield (Scope 1 and 2)", "EmissionScope Brownfield":
                                     "Brownfield (Scope 1 and 2)",})
sub_header = df.iloc[2].replace({"2030": "Short-term", "2040": "Mid-term", "2050": "Long-term"})

# sub_header = df.iloc[2].astype(str)  # Convert to string
df.columns = pd.MultiIndex.from_arrays([top_header, sub_header])

# Rename first column header
top_header = top_header.copy()  # Avoid modifying the original header list
top_header.iloc[0] = ""
sub_header.iloc[0] = "Result type"
df = df.iloc[4:].reset_index(drop=True)

# Define the filter criteria
keywords = [
    "size_", "electricity/import_max", "CO2/export_max",
    "methane/import_max", "methane_bio/import_max",
    "CO2_DAC/import_max", "MPW/import_max", "propane/import_max"
]

# Extract first column name
first_column_name = df.columns[0]

# Filter rows based on keywords
filtered_df = df[df[first_column_name].astype(str).str.startswith(tuple(keywords))]

# Remove unwanted rows
filtered_df = filtered_df[
    ~filtered_df[first_column_name].str.contains("mixer|CO2toEmission|WGS|OlefinSeparation", na=False, case=False)]

name_unit_mapping = {
    "size_CrackerFurnace": (r"Conventional cracker", "t naphtha/h"),
    "size_CrackerFurnace_CC": (r"Conventional cracker with \acs{CC}", "t naphtha/h"),
    "size_CrackerFurnace_Electric": (r"Electric cracker", "t naphtha/h"),
    "size_SteamReformer": (r"Conventional reformer", "MW gas"),
    "size_SteamReformer_CC": (r"Conventional reformer with \acs{CC}", "MW gas"),
    "size_ElectricSMR_m": (r"Electric reformer", "MW gas"),
    "size_AEC": (r"\acs{AEC}", "MW electric"),
    "size_HaberBosch": (r"\acs{HB} process", "MW hydrogen"),
    "size_RWGS": ("RWGS", "t \ce{CO2}/h"),
    "size_MeOHsynthesis": (r"Methanol synthesis from syngas", "t syngas/h"),
    "size_DirectMeOHsynthesis": (r"Direct methanol synthesis from \ce{CO2}", "t \ce{CO2}/h"),
    "size_MTO": (r"\acs{MTO}", "t methanol/h"),
    "size_EDH": (r"\acs{EDH}", "t ethanol/h"),
    "size_PDH": (r"\acs{PDH}", "t propane/h"),
    "size_MPW2methanol": (r"\acs{MPW}-to-methanol", "t MPW/h"),
    "size_MPW2methanol_CC": (r"\acs{MPW}-to-methanol with \acs{CC}", "t MPW/h"),
    "size_CO2electrolysis": (r"\ce{CO2} electrolysis", "t \ce{CO2}/h"),
    "size_ASU": (r"\acs{ASU}", "MW electricity"),
    "size_Boiler_Industrial_NG": (r"Gas-fired boiler", "MW gas"),
    "size_Boiler_El": (r"Electric boiler", "MW electricity"),
    # Storage & Import Entries (Keep These at the Bottom)
    "size_Storage_Ammonia": ("Ammonia tank", "tonne"),
    "size_Storage_Battery": ("Li-ion battery", "MWh"),
    "size_Storage_CO2": (r"\ce{CO2} buffer storage", "tonne"),
    "size_Storage_H2": ("Hydrogen tank", "MWh"),
    "size_Storage_Ethylene": ("Ethylene tank", "tonne"),
    "size_Storage_Propylene": ("Propylene tank", "tonne"),
    "electricity/import_max": ("Electricity grid import", "MW (\% of max)"),
    "CO2/export_max": (r"\ce{CO2} T\&S", "t \ce{CO2}/h (\% of max)"),
    "MPW/import_max": ("MPW import", "t MPW/h (\% of max)"),
    "methane/import_max": ("Methane import", "MW gas"),
    "methane_bio/import_max": ("Bio-methane import", "MW gas"),
    "CO2_DAC/import_max": ("DAC-\ce{CO2} import", "t \ce{CO2}/h"),
    "propane/import_max": ("Bio-propane import", "MW"),
}


# Function to rename technologies and format existing ones correctly
def rename_tech(name):
    base_name = name.replace("_existing", "")
    tech_name, unit = name_unit_mapping.get(base_name, (name, "-"))  # Default to '-' if not found
    if "_existing" in name:
        tech_name += " existing"
    return tech_name, unit


# Apply renaming and extract units using .map() for better performance
filtered_df[('', 'Technology')] = filtered_df[first_column_name].map(lambda x: rename_tech(x)[0])
filtered_df[('', 'Unit')] = filtered_df[first_column_name].map(lambda x: rename_tech(x)[1])

# Define order based on LaTeX table
ordered_techs = list(name_unit_mapping.keys())

# Generate a new list of technologies with "existing" tech placed right below the original technology
ordered_techs_with_existing = []
for tech in ordered_techs:
    ordered_techs_with_existing.append(tech)
    if f"{tech}_existing" in filtered_df[first_column_name].values:
        ordered_techs_with_existing.append(f"{tech}_existing")

# Create sorting index to maintain the correct order (with "existing" techs below the original ones)
filtered_df['Order'] = filtered_df[first_column_name].apply(
    lambda x: ordered_techs_with_existing.index(x) if x in ordered_techs_with_existing else len(
        ordered_techs_with_existing))

# Sort the dataframe based on the 'Order' column and remove it
filtered_df = filtered_df.sort_values(by=['Order']).drop(columns=['Order'])


# Round all numeric columns to whole numbers and format nan
def custom_format(x):
    if isinstance(x, float):
        if pd.isna(x):
            return '-'
        return int(x)
    return x


filtered_df = filtered_df.map(custom_format)

# If the index is multi-level, you can access the levels
ordered_columns = [('', 'Technology') , ('', 'Unit')] + [col for col in filtered_df.columns if col not in [('', 'Technology'), ('', 'Unit')]]
filtered_df = filtered_df[ordered_columns]
filtered_df = filtered_df.drop(columns=('Resulttype', 'Interval'))

# Create separate DataFrames for emission limits and emission scopes
df_emission_limit = filtered_df.loc[:, filtered_df.columns.get_level_values(0).str.contains("Scope 1, 2, and 3", na=False)]
df_emission_scope = filtered_df.loc[:, filtered_df.columns.get_level_values(0).str.contains("Scope 1 and 2", na=False)]
df_emission_limit = pd.concat([filtered_df[[('', 'Technology'), ('', 'Unit')]], df_emission_limit], axis=1)
df_emission_scope = pd.concat([filtered_df[[('', 'Technology'), ('', 'Unit')]], df_emission_scope], axis=1)

# Ensure output folder exists and save the filtered data
output_dir = "C:/EHubversions/AdOpT-NET0_Julia/Plotting"
os.makedirs(output_dir, exist_ok=True)  # Ensure output folder exists

filtered_excel_path = os.path.join(output_dir, "filtered_data.xlsx")
filtered_df = filtered_df.reset_index(drop=True)
filtered_df.to_excel(filtered_excel_path, index=True, merge_cells=True)

# Convert the filtered DataFrame to a LaTeX table
latex_table_limit = (
    "\\begin{table}[h!]\n"
    "\\centering\n"
    "\\caption{Installed capacities for Greenfield and Brownfield scenarios including Scope 1, 2, and 3 emissions for "
    "the short, mid, and long-term interval}\n"
    "\\label{tab:results_emission_limit}\n"
    "\\rotatebox{90}{"
    "\\begin{minipage}{0.85\\textheight}"
    + df_emission_limit.to_latex(index=False, escape=False, column_format="lccccccccccccc").replace(
    r'\multicolumn{3}{r}{', r'\multicolumn{3}{c}{')
    + "\end{minipage}}"
    + "\\end{table}"
)

latex_table_scope = (
    "\\begin{table}[h!]\n"
    "\\centering\n"
    "\\caption{Installed capacities for Greenfield and Brownfield scenarios including Scope 1 and 2 emissions for "
    "the short, mid, and long-term interval}\n"
    "\\rotatebox{90}{"
    "\\begin{minipage}{0.85\\textheight}"
    + df_emission_scope.to_latex(index=False, escape=False, column_format="lccccccccccccc").replace(r'\multicolumn{3}{r}{', r'\multicolumn{3}{c}{')
    + "\end{minipage}}"
    + "\\end{table}"
)

#save latex tables
latex_file_path_limit = os.path.join(output_dir, "filtered_data_emission_limit.tex")
with open(latex_file_path_limit, "w") as f:
    f.write(latex_table_limit)

latex_file_path_scope = os.path.join(output_dir, "filtered_data_emission_scope.tex")
with open(latex_file_path_scope, "w") as f:
    f.write(latex_table_scope)


