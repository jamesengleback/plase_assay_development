import logging
import pandas as pd


def bmg(path: str) -> pd.DataFrame | None:
    try:
        # find header
        with open(path, 'r') as f:
            for row_num, row in enumerate(f):
                # if len(row.split(',')) > 500 or 'Well Row' in row:
                if '800' in row:
                    break
        df = pd.read_csv(path, skiprows=row_num)
        if 'Well Row' in df.columns:
            df.index = [f'{i}{j}'.replace('.0', '') for i, j in zip(df['Well Row'],
                                                                    df['Well Col'])
                        ]
            df.columns = df.columns.str.extract('([0-9]+)')[0]
            df = df.dropna()
            df = df.loc[:, df.columns.dropna()]

        elif "Well" in df.columns:
            wells = [f'{i}{int(j) if j.isnumeric() else None}' for i, j in zip(
                                    df['Well'].str.extract('([A-Z])')[0],
                                    df['Well'].str.extract('([0-9]+)').astype(str)[0]
                                              )
                        ]
            wavelengths = df.iloc[0, :].astype(str).str.extract('([0-9]+)')[0]

            df.index = wells
            df.columns = wavelengths
            df = df.iloc[1:, 2:]
        else:
            if df.iloc[:, 0].str.contains('[A-Z]').all() and df.iloc[:, 1].dtype == int:
                df.index = [f'{i}{j}' for i, j in zip(df.iloc[:, 0], df.iloc[:, 1])]

        # drop 'Unnamed' column
        df = df.loc[:, df.columns.str.contains('Unnamed') == False]
        df = df.loc[:, df.columns.str.contains('^[0-9]+$')]
        df.columns = df.columns.astype(int)
        return df
    except Exception as e:
        # df = df.dropna(axis=0) # drop empty rows
        logging.warn(f'parse.bmg({path}):\n{e}')


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
        logging.warn(f'parse.varian({path}):\n{e}')
