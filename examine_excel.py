#!/usr/bin/env python3
import pandas as pd
import sys

try:
    xls = pd.ExcelFile('Manufacturers.xlsx')
    print('Sheet names:', xls.sheet_names)
    
    for sheet in xls.sheet_names:
        df = pd.read_excel('Manufacturers.xlsx', sheet_name=sheet)
        print(f'\n{sheet} sheet:')
        print(df.head())
        print(f'Shape: {df.shape}')
        print(f'Columns: {list(df.columns)}')
except Exception as e:
    print(f'Error: {e}')