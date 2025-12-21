import logging
import pandas as pd


def bmg(path: str) -> pd.DataFrame | None:
    try:
        # find header
        with open(path, 'r') as f:
            for row_num, row in enumerate(f):
                # if len(row.split(',')) > 500 or 'Well Row' in row:
                if 'Well Row' in row or 'Well' in row:
                    break
        df = pd.read_csv(path, skiprows=row_num)
        df = df.dropna(axis=1, how='all')
        if 'Well Row' in df.columns:
            if len(df) > 0 and str(df.iloc[0, 2]).strip() == 'Wavelength [nm]':
                wavelengths = df.iloc[0, 3:].astype(str).str.extract(r'(\d+)')[0]
                df.columns = ['Well Row', 'Well Col', 'Content'] + list(wavelengths.dropna())
                df = df.iloc[1:]
            df['Well Row'] = df['Well Row'].astype(str)
            df['Well Col'] = df['Well Col'].astype(str)
            df.index = [f'{i}{j}'.replace('.0', '') for i, j in zip(df['Well Row'],
                                                                    df['Well Col'])
                        ]
            df.columns = df.columns.str.extract('([0-9]+)')[0]
            df = df.dropna()
            df = df.loc[:, df.columns.dropna()]
            df = df.loc[:, df.columns.str.contains('Unnamed') == False]
            df = df.loc[:, df.columns.str.contains('^[0-9]+$')]
            df.columns = df.columns.astype(int)
            df = df.loc[:, (df.columns >= 220) & (df.columns <= 800)]

        elif "Well" in df.columns:
            df['Well'] = df['Well'].astype(str)
            wells = [f'{i}{int(j) if j.isnumeric() else None}' for i, j in zip(
                                    df['Well'].str.extract('([A-Z])')[0],
                                    df['Well'].str.extract('([0-9]+)').astype(str)[0]
                                              )
                        ]
            wavelengths = df.iloc[0, :].astype(str).str.extract('([0-9]+)')[0]
            df.index = wells
            df.columns = wavelengths
            df = df.iloc[1:, 2:]
            df = df.loc[:, df.columns.str.contains('Unnamed') == False]
            df = df.loc[:, df.columns.str.contains('^[0-9]+$')]
            df.columns = df.columns.astype(int)
            df = df.loc[:, (df.columns >= 220) & (df.columns <= 800)]
        else:
            df.iloc[:, 0] = df.iloc[:, 0].astype(str)
            df.iloc[:, 1] = df.iloc[:, 1].astype(str)
            if all(any(c.isalpha() for c in str(x)) for x in df.iloc[:, 0]) and df.iloc[:, 1].dtype == int:
                df.index = [f'{i}{j}' for i, j in zip(df.iloc[:, 0], df.iloc[:, 1])]
                df.columns = df.columns.str.extract('([0-9]+)')[0]
                df = df.loc[:, df.columns.notna()]

        # drop 'Unnamed' column
        df.columns = df.columns.astype(str)
        df = df.loc[:, df.columns.str.contains('Unnamed') == False]
        df = df.loc[:, df.columns.str.contains('^[0-9]+$')]
        df.columns = df.columns.astype(int)
        # Filter to wavelength columns only (220-800 nm)
        df = df.loc[:, (df.columns >= 220) & (df.columns <= 800)]
        return df
    except Exception as e:
        # df = df.dropna(axis=0) # drop empty rows
        logging.warning(f'parse.bmg({path}):\n{e}')
        return None


def varian(path: str) -> pd.DataFrame | None:
    try:
        # clean df
        df = pd.read_csv(path)# dataframe object from csv
        headers = df.columns # save column headers
        df = df.iloc[1:,:] # trim top row
        df.columns = headers # replace with old headers
        df.index = df.iloc[:,0]
        ## remove wavelength cols
        df = df.iloc[:,1::2]
        ## remove machine info (remove nan rows)
        df = df.dropna()
        ## get sample names from headers
        ## col headers to sample names
        df.columns = headers[::2][:-1]
        # round wavelenths
        df.index = [round(float(i)) for i in df.index]
        return df.astype(float)

    except Exception as e:
        logging.warning(f'parse.varian({path}):\n{e}')
