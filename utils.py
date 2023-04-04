# Utilities 
from os.path import join, basename
from collections import Counter
import pandas as pd
import re
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


def map_values(values: list, mapping: dict) -> list:
    """Apply a mapping to a list of value answers. Note that there may be multiple answers in a single value so this
    functions separates those and applies it to each separately before re-combining.
    
    Args:
        values: Reponses for a survey question for all submitted surveys.
        mapping: Defaults to None. Dictionary to map values to another variation of it.
    
    """
    for i, val in enumerate(values):
        if '\n' in val:
            # split the answers
            val = val.split('\n')
            
            for j, v in enumerate(val):
                if v in mapping:
                    val[j] = mapping[v]
                
            values[i] = '\n'.join(val)
        else:
            if val in mapping:
                values[i] = mapping[val]
        
    return values


def format_responses(responses: list) -> list:
    """Format survey responses to be in the format that the answer(s) are separated by a new line char for each survey.
    Will convert answers in the CHECKED/UNCHECKED format into this format.
    
    Args:
        responses: responses to a survey question
        
    """
    for i, resp in enumerate(responses):
        resp = resp.strip()
        
        # format this version: remove UNCHECKED asnwers, and add the CHECKED answers separated by a new line character
        if resp.startswith(('CHECKED: ', 'UNCHECKED: ')):
            responses[i] = []
            for val in resp.split('\n'):
                val = val.strip()
                
                if val.startswith('CHECKED: '):
                    responses[i].append(val.split('CHECKED: ')[-1].strip())
            responses[i] = '\n'.join(responses[i])  # rejoin
        else:
            responses[i] = '\n'.join([val.strip() for val in resp.split('\n') if len(val.strip())])
        
    return responses


def report_column(values: list, save_fp: str = '', map_dict: dict = None) -> (list, list, str, int):
    """Analyze the results of a column of the survey, reporting various counts, fractions, etc.
    
    Args:
        values: Reponses for a survey question for all submitted surveys.
        save_fp: File path to save the report of this column, saves a text file.
        map_dict: Defaults to None. Dictionary to map values to another variation of it. Useful for 
            correcting spelling errors or group multiple values that mean the same thing.
    
    Returns:
        all_answers: The values after separating multiple answers into their own entries.
        values: The values after re-mapping.
        results: Results of the column in string format.
        total_entries: Number of entries in the survey, not the number of completed answers.
        
    """
    total_entries = len(values)  # including missing entries
    results = f'save file name: \"{basename(save_fp)}\"\n\n'
    results += f'  * Total entries: {total_entries}\n'
    
    # format responses
    values = format_responses(values)
    
    # re-map values to rename
    if map_dict is not None:
        values = map_values(values, map_dict)
    
    # remove missing entries
    for i, val in enumerate(values):
        # remove any missing entries in a multiple answers 
        val = [v.strip() for v in val.split('\n') if v]
        values[i] = '\n'.join(val)
        
    values = [val.strip() for val in values if len(val)]
    
    results += f'  * Number of answers: {len(values)}\n'
        
    # report entries that have multiple values
    mults = {}
    all_answers = []
    
    for val in values:
        if '\n' in val:
            val = val.split('\n')
            all_answers.extend(val)
            
            k = ' + '.join(val)
            
            if k not in mults:
                mults[k] = 0
            mults[k] += 1
        else:
            all_answers.append(val)
            
    # report the counts of each unique value
    results += f'\nAnswer count:\n'
    for k, v in Counter(all_answers).items():
        results += f'  - {k}  (n={v})\n'
    
    if len(mults):
        results += f'\nMultiple answers:\n'
        for k, v in mults.items():
            results += f'  - {k}  (n={v})\n'
    
    if save_fp:
        with open(save_fp, 'w') as fh:
            fh.write(results.strip())
        
    return all_answers, values, results, total_entries


def plot_landmark_barplots(
        values: pd.Series, map_dict: dict = None, min_count: int = 0, plot_dict: dict = None, rotate_xticks: int = 45, 
        title: str = None, title_size: int = 24, figsize: (int, int) = (10,7), font_size: int = 22, 
        save_dir: str = 'figures/landmark-barplots', show_plot: bool = True
    ):
    """For each region landmark answers (a list) plot / save a bar plot figure.
    
    Args:
        values: Landmark answers for a region.
        map_dict: Dictionary to remap spelling of answers.
        min_count: Group answers with few occurences (i.e. less than this value) into an Other category.
        plot_dict: Dictionary to remap for the figure bar plots.
        rotate_xticks: Rotate the bar labels by this degree.
        title: Overwrite the title, the default is when None is passed and is taken as the name of the values
            parameter Series name.
        title_size: Size of title.
        figsize: Width & height of the figure.
        font_size: Size of all other text in the figure.
        save_dir: Directory to save figure and the results text file to. The filename is the name of the Series.
    
    """
    # get path to save path
    fp = join(save_dir, re.sub(' +', '-', values.name.split(' Landmarks')[0])) + '.'
    
    if title is None:
        title = values.name  # series name
    
    # call report column
    values, unformatted_values, results, N = report_column(values.tolist(), map_dict=map_dict)
    
    # re-map names for plotting
    if plot_dict is not None:
        for i, val in enumerate(values):
            if val in plot_dict:
                values[i] = plot_dict[val]
                
    if plot_dict is not None:
        results += '\nPlot re-mapping:\n'
        
        for k, v in plot_dict.items():
            results += f'  - {k}  -->  {v}\n'
    
    values = Counter(values)
    
    # create an 'Other' group if a minimum was set
    if min_count > 0:
        # track the Other groups in results
        results += '\nOthers bar:\n'
        
        if 'Other' in values:
            results += f"  - Other  (n={values['Other']})\n"
        else:
            values['Other'] = 0
            
        for val in list(values.keys()):
            count = values[val]
            if val != 'Other' and count < min_count:
                values['Other'] += count
                
                results += f'  - {val}  (n={count})\n'
                del values[val]
                
        if not values['Other']:
            del values['Other']
            
    # create bar plot
    answers, counts = list(values.keys()), list(values.values())
    
    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(answers, counts, edgecolor='black', linewidth=4, color='white', width=.6, capsize=.3)
    
    if rotate_xticks is not None:
        ticks_loc = list(ax.get_xticks())
        ax.xaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
        ax.set_xticklabels(answers, rotation=rotate_xticks, ha='right')
        
    for bar in ax.patches:
        ax.text(
            # Put the text in the middle of each bar. get_x returns the start
            # so we add half the width to get to the middle.
            bar.get_x() + bar.get_width() / 2,
            # Vertically, add the height of the bar to the start of the bar,
            # along with the offset.
            bar.get_height() + bar.get_y() + .5,
            # This is actual value we'll show.
            round(bar.get_height()),
            # Center the labels and style them a bit.
            ha='center',
            color='black',
            weight='bold',
            size=font_size
        )
        
    # make the bar plot more journal ready
    count_max = max(counts)
    ymax = int((int(count_max / 5) * 5))

    if count_max % 5:
        ymax += 10
    else:
        ymax += 5
    
    plt.ylim([0, N])
    plt.yticks(np.arange(0, 41, 5))
    plt.axhline(y = N, linestyle = '--', linewidth=3, color='k')
    plt.axhline(y = len(unformatted_values), linestyle = 'dotted', linewidth=3, color='k')
    plt.ylabel(f'# of Centers (N={len(unformatted_values)})', weight='bold', size=font_size)
    plt.yticks(fontweight='bold', fontsize=font_size)
    plt.xticks(fontweight='bold', fontsize=font_size)
    ax.tick_params(axis='both', which='both', direction='out', length=10, width=3)
    
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_linewidth(4)
    ax.spines['left'].set_linewidth(4)
        
    if title:
        plt.title(title, fontsize=title_size, fontweight='bold', y=1.1)
    
    plt.savefig(fp + 'png', dpi=300, bbox_inches='tight')
        
    # modify the first row of results
    results = results.split('\n')
    txt_fp = fp + 'txt'
    results[0] = f'save file name: \"{txt_fp}\"'
    with open(txt_fp, 'w') as fh:
        fh.write('\n'.join(results))
        
    if show_plot:
        plt.show()
    else:
        plt.close()
