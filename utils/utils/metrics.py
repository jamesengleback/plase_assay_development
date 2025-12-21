import numpy as np
import pandas as pd
import scipy


def scattering(data: pd.DataFrame):
    # fit x**-4 curve 
    pass


def scatter(w, k):
    return k * (1 / w**4)


def fit_scatter(data: pd.DataFrame):
    wavelengths = data.columns.astype(float).values
    k_values = []
    for _, row in data.iterrows():
        try:
            (k,), _ = scipy.optimize.curve_fit(lambda w, k: k / w**4, wavelengths, row.values)
            k_values.append(k)
        except:
            k_values.append(np.nan)
    return np.array(k_values)


def linear_fit(x):
    # 1d array 
    (m, c), cov = scipy.optimize.curve_fit(lambda x, m, c: x*m + c,
                                           xdata=range(len(x)),
                                           ydata=x
                                           )
    return m, c

def dd_soret(diff_data: pd.DataFrame, start=390, end=420):
    between = diff_data.loc[:, start:end].values
    slopes = []
    for row in between:
        m, c = linear_fit(row)
        slopes.append(m)
    return np.array(slopes)

def auc(data: pd.DataFrame, start=350, end=800):
    return np.trapz(data.loc[:, start:end], axis=1, dx=1)

def std_405(data: pd.DataFrame, wavelength=405):
    return data.loc[:, wavelength]
