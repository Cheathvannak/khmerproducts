import pandas as pd

# Load the Excel file
xl = pd.ExcelFile('ImportTemplate.xlsx')
print('Sheets:', xl.sheet_names)

# Examine each sheet
for sheet in xl.sheet_names:
    df = pd.read_excel('ImportTemplate.xlsx', sheet_name=sheet)
    print(f'\n{sheet} sheet:')
    print(f'Shape: {df.shape}')
    print(f'Columns: {list(df.columns)}')
    print(df.head())
    print('-' * 50)