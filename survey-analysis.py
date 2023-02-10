# Analysis of the ADRC Neuropath Survey
from pandas import read_excel, DataFrame
import matplotlib.pyplot as plt
import numpy as np
import re
from collections import Counter
import seaborn as sn
from utils import report_column, plot_landmark_barplots

from os import makedirs
from os.path import join

# global colors to use, color-blind friendly
COLORS = ['#D81B60', '#1E88E5', '#FFC107', '#004D40', '#E9801F', '#A6A717', '#EBE25A', '#000000']

STAIN_MAP = {  # map answer stains to another name
    'p62': 'Other', 'thioflavine-S': 'Other', 'P62': 'Other', 'positive': '', 
    '•\tLuxol-fast-blue and counterstained with hematoxylin and eosin': 'Other',
    'Alpha synuclein added when screening section positive': '', 'Thioflavin-S': 'Other', 'LFB': 'Other',
    'Tau; p62 and synuclein added as needed': '', 'TDP added for FTLD/ALS cases': '',
    'only collected; not stained': '', 'Aβ Stain': 'Aβeta', 'Thio S': 'Other', 'Thioflavin': 'Other', 
    'thioflavin S': 'Other', 'Alpha synuclein added when screening sections positive': '',
    'do not stain for standard dx- collect block only': '', 'thio S': 'Other', 'HELFB': 'Other',
    'Alpha synuclein added if screening sections positive': '', 'Tau Stain': 'Tau', 'Thioflavin S': 'Other',
    'depends on the case': '', 'thioflavin': 'Other', 'LHE': 'Other', 'LHE; PrP': 'Other', 
    'TDP and tau staining done as needed for FTLD and CTE cases': '', 'α-Synuclein': 'α-Syn',
    'P62 added for FTLD/ALS; Alpha synuclein added when screening sections positive': 'Other'
}

SAMPLING_MAP = {  # map sampling answers
    'Sampled before coronal slicing': 'Before Coronal Slicing',
    'Sampled after coronal slicing': 'After Coronal Slicing',
    'Longitudinal section': 'Longitudinal',
    'Transverse section': 'Transverse',
    'Coronal section': 'Coronal',
}
        
    
def main():
    # read survey results
    survey = read_excel('2022-ADRC-NP-Survey_cleaned.xlsx').replace(np.nan, '', regex=True)
    
    # rename region columns for consistency among questions
    survey = survey.rename(columns={
        'Posterior Cingulate Cortex Landmarks': 'Posterior Cingulate Gyrus Landmarks',
        'Posterior Cingulate Cortex Sampling': 'Posterior Cingulate Gyrus Sampling',
        'parietalGyriLandmarks': 'Parietal Gyri Landmarks',
        'Do you target a specific # of Gyri and Sulci for this region; if so how many?': 'Parietal Gyri GS Count',
        'Do you target a specific # of Gyri and Sulci for this region; if so how many?.1': 'Frontal Gyri GS Count',
        'Do you target a specific # of Gyri and Sulci for this region; if so how many?.2': 'Temporal Lobe GS Count',
        'Central Gyri Landmark': 'Central Gyri Landmarks'
    })
    
    # location to save output files such as figures and text files
    save_dir = 'results'
    makedirs(save_dir, exist_ok=True)
    
#     # report the affiliated ADRC and the role of the taker
#     _ = report_column(survey['What ADRC are you affiliated with?'].tolist(), join(save_dir, 'ADRC-affilication.txt'))
#     _ = report_column(survey['What is your role in the ADRC?'].tolist(), join(save_dir, 'role-of-respondent.txt'),
#                       map_dict={'NP Core Co-Leader': 'Neuropathology Core Co-leader'})
    
    # create a combined value list for the three IHC question
    ihc_values = []
    
    ihc_cols = [
        'How do you currently process / counterstain your IHC slides?  Check all that apply. >> Hematoxylin Counter Stain Used',
        'How do you currently process / counterstain your IHC slides?  Check all that apply. >> DAB as chromogen (brown) with no enhancement:',
        'How do you currently process / counterstain your IHC slides?  Check all that apply. >> DAB as chromogen with nickel enhancement'
    ]
    for _, r in survey[ihc_cols].iterrows():
        val = []
        
        if r[ihc_cols[0]] == 'Yes':
            val.append('Hematoxylin Counterstain')
        if r[ihc_cols[1]] == 'Yes':
            val.append('DAB as chromogen (brown) with no enhancement')
        if r[ihc_cols[2]] == 'Yes':
            val.append('DAB as chromogen with nickle enhancement')
            
        ihc_values.append('\n'.join(val))
        
    _ = report_column(ihc_values, join(save_dir, 'ihc-process-counterstain.txt'))
    
    # for brain hemisphere I need to correct some values since an answer of Left\nRight is the same as Both
    hemis = survey['Brain Hemisphere'].tolist()
    
    for i, hemi in enumerate(hemis):
        if hemi in ('Left\nRight', 'Left\nBoth', 'Right\nBoth', 'Left\nRight\nBoth'):
            hemis[i] = 'Both'
            
    _ = report_column(hemis, join(save_dir, 'hemispheres-sampled.txt'))
    
#     # report on the special preparation free-text question
#     _ = report_column(
#         survey['Special Preparation / Additional Info; average cost per slide of IHC?'].tolist(),
#         join(save_dir, 'special-prep.txt')
#         )

    # Average Section thickness in μm: this question was free typed, cleaning up answers after manual inspection
    thickenss = survey['Average Section thickness in μm:'].tolist()

    for i, t in enumerate(thickenss):
        # clean up the string
        t = t.strip()
        t = t.replace('um', '')
        t = t.replace('microns', '')

        if t == 'see above':  # from special prep free text question
            t = '80'
        elif t == '8.0':
            t = '8'
            
        thickenss[i] = t
        
    _ = report_column(thickenss, join(save_dir, 'section-thickness-microns.txt'))
    
    # WSI scanner
    _ = report_column(survey['What type of slide scanner does your ADRC primarily have access to/use ?'].tolist(),
                      join(save_dir, 'wsi-scanners.txt'))
    
    # Report on the antibodies
    _ = report_column(survey['Tau Antibody'].tolist(), join(save_dir, 'tau-antibody.txt'))
    _ = report_column(survey['aBeta Antibody'].tolist(), join(save_dir, 'abeta-antibody.txt'))
    _ = report_column(survey['TDP43 Antibody'].tolist(), join(save_dir, 'tdp43-antibody.txt'))
    _ = report_column(survey['Alpha Synuclein Antibody'].tolist(), join(save_dir, 'aSyn-antibody.txt'))
    
#     # save the vendor info
#     _ = report_column(survey['Tau Vendor / Clone Info'].tolist(), join(save_dir, 'tau-antibody-vendor.txt'))
#     _ = report_column(survey['aBeta Vendor / Clone Info'].tolist(), join(save_dir, 'abeta-antibody-vendor.txt'))
#     _ = report_column(survey['TDP43 Vendor / Clone Info'].tolist(), join(save_dir, 'tdp43-antibody-vendor.txt'))
#     _ = report_column(survey['Alpha Synuclein Vendor / Clone Info'].tolist(), join(save_dir, 'aSyn-antibody-vendor.txt'))

#     # Report who does the sampling / sectioning
#     _ = report_column(survey['Does the same expert / pathologist do most if not all of the blocking?'].tolist(),
#                       join(save_dir, 'blocking.txt'))

    # get list of region names
    regions = []
    splits = (' Landmarks', ' Stains', ' Sampling', ' GS Count')
    
    for col in survey.columns:
        if col.endswith(splits):
            for split in splits:
                col = col.split(split)[0]

            if col not in regions:
                regions.append(col)
                    
    # all figures saved to a single location
    fig_dir = join('figures')
    makedirs(fig_dir, exist_ok=True)
    
    # Plot a stacked bar plot for the sampling approach answers (i.e. before / after coronal slicing)
    sampling_df, s_regions = [], []
    cols = ['After Coronal Slicing', 'Before Coronal Slicing', 'Longitudinal', 'Transverse', 'Coronal', 'Other']
    
    temp = []##
    for region in regions:
        if f'{region} Sampling' not in survey:
            continue
        
        s_regions.append(region)

        # get a list of all the answers for all centers
        sampling_answers = report_column(survey[f'{region} Sampling'].tolist(), map_dict=SAMPLING_MAP)[0]
        
        for i, s in enumerate(sampling_answers):
            if s not in SAMPLING_MAP.values():
                sampling_answers[i] = 'Other'
        
        sampling_answers = Counter(sampling_answers)
        
        row = []
        for c in cols:
            row.append(sampling_answers[c] if c in sampling_answers else 0)

        sampling_df.append(row)

    # compile into a dataframe
    sampling_answers = DataFrame(sampling_df, index=s_regions, columns=cols)
    
    fig, ax = plt.subplots(figsize=(15,10))
    bottom = np.zeros(len(sampling_answers))

    for i, col in enumerate(sampling_answers.columns):
        ax.bar(sampling_answers.index, sampling_answers[col], bottom=bottom, label=col, color=COLORS[i])
        bottom += np.array(sampling_answers[col])

    totals = sampling_answers.sum(axis=1)
    y_offset = 10

    plt.ylim([0, 40])
    fig.set_facecolor('#fffbe7')
    ax.set_facecolor("#fffbe7")

    # Let's put the annotations inside the bars themselves by using a
    # negative offset.
    y_offset = -1
    # For each patch (basically each rectangle within the bar), add a label.
    for bar in ax.patches:
        if bar.get_height() != 0:
            ax.text(
                # Put the text in the middle of each bar. get_x returns the start
                # so we add half the width to get to the middle.
                bar.get_x() + bar.get_width() / 2,
                # Vertically, add the height of the bar to the start of the bar,
                # along with the offset.
                bar.get_height() + bar.get_y() + y_offset,
                # This is actual value we'll show.
                round(bar.get_height()),
                # Center the labels and style them a bit.
                ha='center',
                color='black',
                weight='bold',
                size=18
            )

    ax.tick_params(axis='x', which='major', pad=-15, rotation=90)  # move the tick axis label baseline
    plt.xticks(fontweight='bold', fontsize=16, color='w', verticalalignment='baseline')

    ax.set_title('Region Sampling Approach', fontsize=20, fontweight='bold', y=1.10)
    ax.legend(bbox_to_anchor=(0.75, 1.10), ncol=int(len(cols) / 2), fontsize=14)
    plt.yticks(fontsize=16)

    plt.tick_params(axis='x', which='both', bottom=False, top=False)
    plt.xlabel('Brain Region', fontsize=18, fontweight='bold')
    plt.ylabel('Number of Centers', fontsize=18, fontweight='bold')

    ax.margins(x=0.01)
    # save figure
    plt.savefig(join(fig_dir, 'sampling-stacked-bar-plot.png'), dpi=300, bbox_inches='tight')
    sampling_answers.to_csv(join(fig_dir, 'sampling-stacked-bar-plot.csv'))
    plt.close()
    
    # Landmark bar plots - tailor each one by renaming the landmarks so they fit nicely in the plots
    lm_bar_dir = join('figures/landmark-barplots')
    makedirs(lm_bar_dir, exist_ok=True)
    plot_landmark_barplots(survey[f'{regions[0]} Landmarks'], min_count=3, figsize=(5,5))
    plot_landmark_barplots(survey[f'{regions[1]} Landmarks'], min_count=0, figsize=(6,5),
                           plot_dict={'Motor neurons present on microscopic evaluation': 'MNP', 'BA 4;3;2;1': 'BA 1-4'})
    plot_landmark_barplots(survey[f'{regions[2]} Landmarks'], min_count=3, figsize=(7,5),
                           plot_dict={'BA 39; 40': 'BA 39 & 40', 'MIddle': 'Middle'})
    plot_landmark_barplots(survey[f'{regions[3]} Landmarks'], min_count=0, figsize=(5,5),
                           plot_dict={'collected but only for research': 'Research only', 'Region collected': 'collected'})
    plot_landmark_barplots(survey[f'{regions[4]} Landmarks'], min_count=2, figsize=(5,5),
                           plot_dict={'Collected but only for research': 'for research', 'Region collected': 'collected'})
    plot_landmark_barplots(survey[f'{regions[5]} Landmarks'], min_count=2, figsize=(5,5),
                           plot_dict={'Collected but only for research': 'for research', 'Region collected': 'collected'})
    plot_landmark_barplots(survey[f'{regions[6]} Landmarks'], min_count=2, figsize=(2.5,5),
                           plot_dict={'Line of Gennari (BA17)': 'Line of Gennari\nBA 17', 'Region collected': 'collected'})
    plot_landmark_barplots(
        survey[f'{regions[7]} Landmarks'], min_count=2, figsize=(6,5), plot_dict={'Lateral Geniculate Nucleus': 'LGN', 
        'CA1-4 with dentate gyrus': 'CA1-4 w/\ndentate gyrus', 'Parahippocampal Gyrus': 'Parahippocampal\nGyrus',
        'Occipital Temporal Gyrus': 'Occipital Temporal\nGyrus'}
    )
    plot_landmark_barplots(survey[f'{regions[8]} Landmarks'], min_count=2, figsize=(3.5,5),
                           plot_dict={'Line of gennari (ba17)': 'Line of Gennari\nBa17', 'Region collected': 'collected'})
    plot_landmark_barplots(
        survey[f'{regions[9]} Landmarks'], min_count=2, figsize=(5,5), plot_dict={
            'Line of gennari (ba17)': 'Line of Gennari\nBa17', 
            'Region collected': 'collected', 'BA 17; 18': 'BA 17 & 18'}
    )
    plot_landmark_barplots(survey[f'{regions[10]} Landmarks'], min_count=0, figsize=(2.5,5),
                           plot_dict={'PHG & ITG if will fit': 'PHG & ITG\nif will fit'})
    plot_landmark_barplots(survey[f'{regions[11]} Landmarks'], min_count=0, figsize=(7,5),
                           plot_dict={'Dorsal Motor Nucleus of the Vagus': 'DMV', 'Region collected': 'collected'})
    plot_landmark_barplots(
        survey[f'{regions[12]} Landmarks'], min_count=3, figsize=(9,5), plot_dict={
            'Region Collected': 'collected', 'Anterior Commissure': 'AC'
        })
    plot_landmark_barplots(
        survey[f'{regions[13]} Landmarks'], min_count=3, figsize=(7,5), title='Thalamus & Subthalmaic Nuclei\nLandmarks',
        plot_dict={'Anterior Nucleus of the thalamus': 'Anterior nucleus', 'Mammilo-thalamic Tract': 'MT tract', 
                   'Subthalamic Nucleus': 'Subthalamic\nnucleus'}
    )
    plot_landmark_barplots(survey[f'{regions[14]} Landmarks'], min_count=3, figsize=(6,5), plot_dict={})
    plot_landmark_barplots(survey[f'{regions[15]} Landmarks'], min_count=3, figsize=(3.5,5), 
                           plot_dict={'Entorhinal Cortex': 'EC'})
    plot_landmark_barplots(survey[f'{regions[16]} Landmarks'], min_count=3, figsize=(5,5), plot_dict={})
    plot_landmark_barplots(survey[f'{regions[17]} Landmarks'], min_count=3, figsize=(6,5), 
                           plot_dict={'Superior Cerebellar Peduncle': 'Superior cerebellar\npeduncle'})
    plot_landmark_barplots(survey[f'{regions[18]} Landmarks'], min_count=3, figsize=(5,5), plot_dict={})

    # report on the gyri question - only 4
    for col in survey.columns:
        if 'GS' in col:
            _ = report_column(survey[col].tolist(), save_fp=join(save_dir, re.sub(' +', '-', col) + '.txt'))
            
    # create a heatmap: x axis is the stains, y axis is the brain region
    stains = ('Other', 'Silver', 'CD68', 'TDP-43', 'α-Syn', 'Tau', 'Aβeta', 'H&E')
    
    stain_region_df = []
    for region in regions:
        # report the column
        region_answers = report_column(survey[f'{region} Stains'].tolist(), map_dict=STAIN_MAP)[0]
        region_answers = Counter(region_answers)
        
        row = []
        
        for stain in stains:
            row.append(region_answers[stain] if stain in region_answers else 0)
        
        stain_region_df.append(row)
        
    stain_region_df = DataFrame(stain_region_df, index=regions, columns=stains)
    stain_region_df = stain_region_df.sort_values(by='H&E', ascending=False)
    
    # plot the heatmap
    sn.set(font_scale=1.6)
    fig = plt.figure(figsize=(10,12))
    ax = plt.gca()
    hm = sn.heatmap(data=stain_region_df, annot=True, ax=ax, annot_kws={"fontsize":20}, cbar=True, cmap='BuPu', 
                    linewidths=1, linecolor='black', clip_on=False)
    ax.set_ylabel('Brain Region', labelpad=20, weight='bold', fontsize=24)
    ax.set_xlabel('Stain', labelpad=20, weight='bold', fontsize=24)
    plt.xticks(rotation=70)
    ax.set_title('Region Staining by Centers', fontsize=28, pad=20, weight='bold')
    fig.set_facecolor('#fffbe7')
    ax.set_facecolor("#fffbe7")
    plt.savefig(join(fig_dir, 'brain-stain-heatmap.png'), dpi=300, bbox_inches='tight')
    stain_region_df.to_csv(join(fig_dir, 'brain-stain-heatmap.csv'))
    plt.close()

    
if __name__ == '__main__':
    main()
