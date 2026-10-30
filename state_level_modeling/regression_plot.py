"""Plot S10 coefficients and S13 margins from the fitted 38-state model."""
from pathlib import Path
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator,FuncFormatter


RED,BLUE,INK,GRAY='#C74343','#286DB4','#273746','#AAB5BD'
S10='FigS10_38州最终模型'
S13='全州实际与预测票差对比图_38州最终模型'
ABBREVIATIONS={'extreme bias right':'ER','left leaning':'LL','center':'C',
               'left':'L','right leaning':'RL','right':'R','extreme bias left':'EL'}
PRED='predicted_margin_pp'
VARIANT='有asinh'
_RELEASE_ROOT = Path(__file__).resolve().parents[1]
if str(_RELEASE_ROOT) not in sys.path:
    sys.path.insert(0, str(_RELEASE_ROOT))
from runtime_config import project_path

def configure_fonts():

    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'pdf.fonttype':42,
        'axes.unicode_minus':False,'text.color':INK,'axes.labelcolor':INK,
        'xtick.color':INK,'ytick.color':INK,'savefig.facecolor':'white'})

def save_figure(fig,output):
    for extension in ['png','pdf']:
        fig.savefig(output/(S13+'.'+extension),dpi=240)
    plt.close(fig)

def draw_s10(table,out):

    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'pdf.fonttype':42,
                         'axes.unicode_minus':False,'text.color':INK,'axes.labelcolor':INK,
                         'xtick.color':INK,'ytick.color':INK,'savefig.facecolor':'white'})
    fig=plt.figure(figsize=(13.5,6.2))
    bottom,height=.235,.55


    labels=fig.add_axes([.015,bottom,.11,height])
    effects=fig.add_axes([.15,bottom,.57,height])
    frequency=fig.add_axes([.755,bottom,.13,height])
    consistency=fig.add_axes([.920,bottom,.065,height])
    panels=[labels,effects,frequency,consistency]
    for ax in panels:

        ax.set_ylim(6.6,-.6)
        ax.set_yticks([])
        for spine in ax.spines.values():spine.set_visible(False)
    for ax in [labels,consistency]:ax.set_xlim(0,1);ax.set_xticks([])
    for i,r in table.iterrows():
        color=RED if r.coefficient>=0 else BLUE
        label='-'.join(ABBREVIATIONS[part] for part in r.term.split('-'))
        labels.text(.99,i,label,ha='right',va='center',fontsize=11.3)
        effects.barh(i,r.coefficient,height=.50,color=color,alpha=.94,zorder=3)

        sign=1 if r.coefficient>=0 else -1
        if r.coefficient < -1:
            effects.text(r.coefficient+.075,i-.32,f'{r.coefficient:+.2f}',
                         ha='left',va='bottom',fontsize=11.3,color='black',zorder=4)
        else:
            effects.text(r.coefficient+sign*.055,i,f'{r.coefficient:+.2f}',
                         ha='left' if sign>0 else 'right',va='center',fontsize=11.3)

        frequency.barh(i,r.selection_frequency*100,height=.35,color='#A7B7C4',zorder=2)
        frequency.text(r.selection_frequency*100+4,i,f'{r.selection_frequency*100:.1f}%',ha='left',va='center',fontsize=10.5)
        consistency.text(.5,i,f'{r.direction_consistency*100:.1f}%',ha='center',va='center',fontsize=11.3)
    effects.set_xlim(-2.2,2.95)
    effects.set_xticks([-2,-1,0,1,2])
    effects.tick_params(axis='x',labelsize=10.5,length=3,pad=7,color='#9AA7B2')
    effects.grid(axis='x',color='#E8EDF1',lw=.65)
    effects.set_axisbelow(True)
    effects.axvline(0,color='#7D8D99',lw=1.2,zorder=1)
    effects.spines['bottom'].set_visible(True);effects.spines['bottom'].set_color('#AEBBC5')
    effects.set_xlabel('OLS coefficient (asinh scale)',fontsize=12.5,labelpad=13)
    frequency.set_xlim(0,148)
    frequency.set_xticks([50],['50%'])
    frequency.tick_params(axis='x',length=0,labelsize=9,pad=8)

    frequency.axvline(50,color='#6C7B87',lw=1,ls=(0,(3,2)),zorder=3)
    fig.text(.027,.866,'Interaction pattern',fontsize=11,color='#596D7B')
    fig.text(.82,.866,'Inclusion\nfrequency',fontsize=10.8,ha='center',va='center',color='#596D7B',linespacing=1.35)
    fig.text(.952,.866,'Direction\nconsistency',fontsize=10.8,ha='center',va='center',color='#596D7B',linespacing=1.35)


    zero=.15+.57*(2.2/5.15)
    fig.add_artist(FancyArrowPatch((zero-.012,.068),(.170,.068),transform=fig.transFigure,
                                  arrowstyle='-|>',mutation_scale=11,lw=1,color=BLUE))
    fig.add_artist(FancyArrowPatch((zero+.012,.068),(.700,.068),transform=fig.transFigure,
                                  arrowstyle='-|>',mutation_scale=11,lw=1,color=RED))
    fig.text(.175,.106,'More Democratic',fontsize=10.5,color=BLUE)
    fig.text(.695,.106,'More Republican',fontsize=10.5,color=RED,ha='right')
    for ext in ['png','pdf']:fig.savefig(out/(S10+'.'+ext),dpi=300)
    plt.close(fig)

def tick_label(x, pos=None):
    return '0' if x == 0 else f'{x:+.0f}'.replace('-', '−')

def party_color(actual):

    return RED if actual > 0 else BLUE

def party_legend():
    return [Line2D([], [], marker='o', linestyle='none', color=RED, label='Republican states'),
            Line2D([], [], marker='o', linestyle='none', color=BLUE, label='Democratic states')]

def draw_all_states(table, output):

    data = table.sort_values('actual_margin_pp', kind='stable').reset_index(drop=True)
    n = len(data)
    fig = plt.figure(figsize=(10, 16.5))
    grid = fig.add_gridspec(1, 2, width_ratios=[1.85, 6.0],
                           left=.035, right=.96, top=.86, bottom=.055, wspace=.065)
    labels, ax = [fig.add_subplot(grid[0, k]) for k in range(2)]
    for panel in [labels, ax]:
        panel.set_ylim(n - .5, -.7)
        panel.set_yticks([])
        for spine in panel.spines.values():
            spine.set_visible(False)
    for panel in [labels]:
        panel.set_xlim(0, 1)
        panel.set_xticks([])
    ax.spines['bottom'].set_visible(True)
    ax.spines['bottom'].set_color('#9AA7B2')

    ax.set_xlim(-100, 100)
    ax.xaxis.set_major_locator(FixedLocator([-100, -50, 0, 50, 100]))
    ax.xaxis.set_minor_locator(FixedLocator([-75, -25, 25, 75]))
    ax.xaxis.set_major_formatter(FuncFormatter(tick_label))
    ax.grid(axis='x', which='major', color='#DFE5EB', lw=.7)
    ax.grid(axis='x', which='minor', color='#EEF1F4', lw=.5)
    ax.axvline(0, color='#85939E', lw=1.2, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel('Vote share difference', labelpad=10, fontsize=12)
    arrows = []
    in_range = 0
    for i, row in data.iterrows():
        truth, estimate = row.actual_margin_pp, row[PRED]
        color = party_color(truth)

        state_label = ('* ' if np.sign(estimate) != np.sign(truth) else '') + row.State
        labels.text(.97, i, state_label, ha='right', va='center', fontsize=10.5)
        ax.scatter([truth], [i], s=21, marker='o', color=color, zorder=4)

        if abs(estimate) <= 100:
            ax.plot([truth, estimate], [i, i], color=GRAY, lw=1, zorder=1)
            ax.scatter([estimate], [i], s=47, marker='D', facecolor='none', edgecolor=color,
                       linewidths=1.35, zorder=5)
            in_range += 1
        else:


            direction = 1 if estimate > 100 else -1
            ax.plot([truth, direction * 100], [i, i], color=GRAY, lw=1, ls=(0, (3, 2)), zorder=1)
            ax.annotate('', xy=(direction * 102, i), xytext=(direction * 94, i),
                        arrowprops={'arrowstyle': '-|>', 'color': color, 'lw': 1.4,
                                    'mutation_scale': 13, 'shrinkA': 0, 'shrinkB': 0},
                        annotation_clip=False, zorder=5)
            arrows.append({'State': row.State, 'direction': direction})
    labels.text(.97, 1.014, 'State', transform=labels.transAxes, ha='right', fontsize=11, color='#627382')
    fig.text(.045, .963, 'Actual and predicted vote margins by state', fontsize=22, fontweight='bold')

    legend = party_legend() + [
        Line2D([], [], marker='o', linestyle='none', color=INK, markersize=5, label='Actual'),
        Line2D([], [], marker='D', linestyle='none', markerfacecolor='none', markeredgecolor=INK, markersize=6, label='Predicted'),
        Line2D([], [], marker='>', markevery=[1], linestyle='--', color=INK, markersize=7, label='|Predicted margin| > 100')]
    if VARIANT == '有asinh':
        legend.append(Line2D([], [], marker='$*$', linestyle='none', color=INK,
                             markersize=12, label='Incorrect winning-party prediction'))
    fig.legend(handles=legend, loc='upper left', bbox_to_anchor=(.033, .919), ncol=3,
               frameon=False, fontsize=10.5, handletextpad=.5, columnspacing=1.5)
    assert len(ax.collections) == n + in_range
    save_figure(fig, output)
    return {'states': n, 'in_range_prediction_points': in_range, 'arrows': arrows,
            'state_order': data.State.tolist()}

def draw_figures(input_dir, output_dir=None):
    """Plot exported predictions without refitting or rescaling the model."""
    input_dir = Path(input_dir)
    out = Path(output_dir) if output_dir is not None else input_dir
    tables = (
        input_dir / "最终38州模型_S10指标.csv",
        input_dir / "7变量38州_asinh_全州明细.csv",
    )
    table = pd.read_csv(tables[0]).sort_values(
        "selection_frequency", ascending=False
    ).reset_index(drop=True)
    data = pd.read_csv(tables[1])
    outputs = [out / (name + "." + ext)
               for name in (S10, S13) for ext in ("png", "pdf")]
    existing = [str(path) for path in outputs if path.exists()]
    if existing:
        raise FileExistsError(
            "Choose a new --output-dir; figure files already exist: "
            + ", ".join(existing)
        )
    out.mkdir(parents=True, exist_ok=True)
    draw_s10(table, out)
    configure_fonts()
    info = draw_all_states(data, out)
    print(f"S10: {len(table)} coefficients; S13: {info['states']} states, "
          f"{len(info['arrows'])} out-of-range arrows.")
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    input_dir = args.input_dir or Path(
        project_path("outputs", "state_level_modeling/regression")
    )
    draw_figures(input_dir, args.output_dir)


if __name__ == "__main__":
    main()
