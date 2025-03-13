import os
from textwrap import dedent
import numpy as np
import matplotlib.pyplot as plt
from .mm import curve
import matplotlib.patches as mpatches


def plot_plate_data(data,
                    exclude_index=None,
                    title=None,
                    ligand_name=None,
                    save_path=None,
                    concs=None,
                    linear_cmap=True,
                    addresses=None,
                    ax=None,
                    ylim=None,
                    legend_text=None,
                    legend=True,
                    ):
    x = data.columns.astype(int)

    if ax is None:
        fig, ax = plt.subplots(figsize=(15, 5))

    # assuming index is concs
    if concs is None:
        concs = data.index

    # linear colormap
    if linear_cmap:
        if concs.argmax() == 0:
            colors = plt.cm.inferno(np.linspace(1, 0, len(concs)))
        else:
            colors = plt.cm.inferno(np.linspace(0, 1, len(concs)))
    else:
        assert concs is not None
        colors = plt.cm.inferno(concs)

    if exclude_index is None:
        exclude_index = np.zeros(len(data))

    for i, (row, exclude) in enumerate(zip(data.index, exclude_index)):
        y = data.loc[row,:]
        ax.plot(x,
                y,
                lw=2,
                color=colors[i],
                linestyle='dashed' if bool(exclude) else 'solid',
                )
    if title is not None:
        ax.set_title(title)

    if ylim is None:
        ax.set_ylim((-0.05,1))
    else:
        ax.set_ylim(ylim)


    ax.set_xticks(x[::50])
    ax.set_xlim((280,800))
    ax.set_xlabel('Wavlength nm')
    ax.set_ylabel('Absorbance')

    if concs is not None:
        if addresses is not None:
            labels = [f'{addr}: {conc:.4g}' for addr, conc in zip(addresses, concs)]
        else:
            labels = [f'{conc:.4g}' for conc in concs]
    else:
        if addresses is not None:
            labels = [f'{addr}: {conc:.4g}' for addr, conc in zip(addresses, concs)]
        else: 
            labels = data.index

    if legend_text is not None:
        handles, _labels = ax.get_legend_handles_labels()
        handles.append(mpatches.Patch(color='none', label=legend_text))
    else:
        handles = None

    if legend:
        ax.legend(labels,
                  title = f'{ligand_name} concentration μM',
                  loc='upper right',
                  handles=handles,
                  )

    if ax is None and save_path is not None:
        assert 'fig' in locals()
        fig.savefig(save_path)

def plot_michaelis_menten(response,
                          concs,
                          vmax,
                          km,
                          r_squared,
                          exclude_index=None,
                          ax=None,
                          title=None,
                          ylim=None,
                          legend_text=None,
                          ):

    x_2 = np.linspace(0, concs.max(), 500)
    y_hat = curve(x_2,
                  vmax,
                  km,
                  )

    if exclude_index is None:
        exclude_index = np.zeros(len(response)).astype(bool)

    plt.set_cmap('inferno')
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.5,5))
    ax.plot(x_2, y_hat, color = '0.1')
    ax.scatter(concs[~exclude_index], response[~exclude_index],  color = 'orange', s = 30)
    ax.scatter(concs[exclude_index], response[exclude_index],  color = 'gray', s = 30)
    ax.set_ylabel('Response')
    ax.set_xlabel('[Substrate] µM')

    if title is not None:
        ax.set_title(title)

    if ylim is None:
        ylim = (-0.1, 1)

    ax.set_ylim(ylim)

    label = dedent(f'''
           $K_d$ = {round(km, 2)}
           $V_{{max}}$ = {round(vmax, 2)}
           $R^2$ = {round(r_squared, 2)}
           ''')
    handles, labels = ax.get_legend_handles_labels()
    handles.append(mpatches.Patch(color='none', label=label))
    if legend_text:
        handles.append(mpatches.Patch(color='none', label=legend_text))
    ax.legend(handles=handles,
              loc='right',
              )

    if title is not None:
        ax.set_title(title)


def plot_traces_nb(data,
                   ax=None,
                   lw=0.5,
                   c='#b4b4b4',
                   colors=None,
                   xlim=(220, 800),
                   ylim=(-0.05, 3.5),
                   legend_dict=None,
                   **kwargs
                   ):

    if ax is None:
        fig, ax = plt.subplots(1, 1, 
                               figsize=(14, 6),
                              )

    if 'tqdm' not in globals():
        tqdm = lambda x: x

    for i in tqdm(range(len(data))):
        row = data.iloc[i, :]
        ax.plot(row,
                lw=lw,
                c=c if colors is None else colors[i],
                alpha=kwargs.get('alpha'),
                )

    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xlabel('Wavelength (nm)')
    ax.set_ylabel('Absorbance')
    if (title:=kwargs.get('title')):
        ax.set_title(title)
    if isinstance(legend_dict, dict):
        patch_props = legend_dict.get('patch_props')
        legend_props = legend_dict.get('legend_props')
        assert all((patch_props, legend_props)), f"expected 'patch_props':list and 'legend_props': dict in legend_dict\nGot {', '.join(legend_dict.keys())}"
        handles, labels = ax.get_legend_handles_labels()
        for patch in patch_props:
            handles.append(mpatches.Patch(**patch))
        ax.legend(handles=handles, **legend_props)
    return ax


def add_cmap(fig, 
             ax, 
             vmin, 
             vmax,
             **kwargs):
    fig.colorbar(
                    plt.matplotlib.cm.ScalarMappable(
                                                    plt.matplotlib.colors.Normalize(vmin=vmin, vmax=vmax),
                                                    plt.colormaps['inferno'],
                                                    ),
                    ax=ax,
                    **kwargs
    )

def plot_group(test_data_raw=None,
               test_data_norm=None,
               test_data_smooth=None,
               control_data_raw=None,
               control_data_norm=None,
               control_data_smooth=None,
               exclude_mask_test=None,
               exclude_mask_control=None,
               corrected_data=None,
               diff_data=None,
               test_well_addresses=None,
               control_well_addresses=None,
               ligand=None,
               response=None,
               vmax=None,
               km=None,
               rsq=None,
               a420_max=None,
               suptitle=None,
               show=None,
               save_path=None,
               legend_text=None,
               table_data=None,
               ):

    n_plots = sum([i is not None for i in [
        test_data_raw,
        control_data_raw,
        test_data_norm,
        test_data_smooth,
        control_data_norm,
        control_data_smooth,
        corrected_data,
        diff_data,
        ligand,
        response,
        table_data,
        ]
                   ])

    fig, axs = plt.subplots(n_plots // 2 + n_plots % 2, 
                            2, 
                            figsize=(16, 4 * (n_plots // 2)),
                            )

    next_ax = iter(axs.flatten())

    if control_data_raw is not None:
        plot_plate_data(control_data_raw,
                        exclude_index=exclude_mask_control,
                        ax=next(next_ax),
                        ligand_name=ligand,
                        addresses=control_well_addresses,
                        title='Control Data',
                        ylim=(-0.1, max(0.3, 1.2 * a420_max) if a420_max else None),
                        )

    if test_data_raw is not None:
        plot_plate_data(test_data_raw,
                        exclude_index=exclude_mask_test,
                        ax=next(next_ax),
                        ligand_name=ligand,
                        title='Raw Test Data',
                        addresses=test_well_addresses,
                        ylim=(-0.1, max(0.3, 1.2 * a420_max)) if a420_max else None,
                        )

    if control_data_norm is not None:
        plot_plate_data(control_data_norm,
                        exclude_index=exclude_mask_control,
                        ax=next(next_ax),
                        ligand_name=ligand,
                        addresses=control_well_addresses,
                        title='Normalized Control Data',
                        ylim=(-0.1, max(0.3, 1.2 * a420_max)) if a420_max else None,
                        )

    if test_data_norm is not None:
        plot_plate_data(test_data_norm,
                        exclude_index=exclude_mask_test,
                        ax=next(next_ax),
                        ligand_name=ligand,
                        addresses=test_well_addresses,
                        title='Normalized Test Data',
                        ylim=(-0.1, max(0.3, 1.2 * a420_max)) if a420_max else None,
                        )


    if control_data_smooth is not None:
        plot_plate_data(control_data_smooth,
                        exclude_index=exclude_mask_control,
                        ax=next(next_ax),
                        ligand_name=ligand,
                        title='Smooth Control Data',
                        addresses=control_well_addresses,
                        ylim=(-0.1, max(0.3, 1.2 * a420_max)) if a420_max else None,
                        )

    if test_data_smooth is not None:
        plot_plate_data(test_data_smooth,
                        exclude_index=exclude_mask_test,
                        ax=next(next_ax),
                        addresses=test_well_addresses,
                        ligand_name=ligand,
                        title='Smooth Test Data',
                        ylim=(-0.1, max(0.3, 1.2 * a420_max)) if a420_max else None,
                        )

    if exclude_mask_test is not None and exclude_mask_control is not None:
        exclude_mask_corrected = exclude_mask_control.values | exclude_mask_test.values
    elif exclude_mask_test is not None:
        exclude_mask_corrected = exclude_mask_test.values
    elif exclude_mask_control is not None:
        exclude_mask_corrected = exclude_mask_control.values
    else:
        exclude_mask_corrected = np.zeros(len(corrected_data)).astype(bool)

    if corrected_data is not None:
        plot_plate_data(corrected_data,
                        exclude_index=exclude_mask_corrected,
                        ax=next(next_ax),
                        ligand_name=ligand,
                        title='Corrected Test Data',
                        ylim=(-0.1, max(0.3, 1.2 * a420_max)) if a420_max else None,
                        )

    if diff_data is not None:
        plot_plate_data(diff_data.sort_index(ascending=False),
                        exclude_index=exclude_mask_corrected,
                        ax=next(next_ax),
                        #concs=concs,
                        ligand_name=ligand,
                        title=r'$\Delta$ Absorbance',
                        ylim=(-0.3, max(0.3, 1.2 * a420_max)) if a420_max else None,
                        )

    if response is not None:
        assert isinstance(vmax, (int, float))
        assert response.dtype == float
        plot_michaelis_menten(response=response,
                              exclude_index=exclude_mask_corrected,
                              concs=corrected_data.index,
                              vmax=vmax,
                              km=km,
                              r_squared=rsq,
                              ax=next(next_ax),
                              ylim=(0, max((vmax * 1.2), max(response) * 1.2)),
                              legend_text=legend_text,
                              title='Response'
                              )
    # else:
    #     if legend_text is not None:
    #         handles, labels = axs[2, 0].get_legend_handles_labels()
    #         handles.append(mpatches.Patch(color='none', label=legend_text))
    #         axs[2, 0].legend(handles=handles,
    #                          loc='right',
    #                          )

    if any(table_data):
        assert isinstance(table_data, dict)
        ax = next(next_ax)
        fmt_labels = lambda s : ' '.join([i.capitalize() for i in s.split('_')])
        ax.table(cellText=[[i] for i in table_data.values()],
                 rowLabels=[fmt_labels(i) for i in table_data.keys()],
                 bbox=[0.4, 0.2, 0.4, 0.6],
                 # colWidths=[0.4],
                 cellLoc='left',
                 # loc='center',
                 edges='TBLR',
                 alpha=0.5,
                 fontsize=14,
                 )
        ax.axis('off')

    for ax in next_ax:
        ax.axis('off')

    if suptitle:
        plt.suptitle(suptitle)
    plt.tight_layout()

    if show:
        plt.show()
    elif save_path is not None:
        assert save_path is not None
        assert os.path.exists(os.path.dirname(save_path))
        plt.savefig(save_path)
        plt.close()
    else:
        return fig
