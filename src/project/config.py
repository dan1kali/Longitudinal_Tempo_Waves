import os

# Directories
base_output_dir = 'insert_here'
# base_output_dir = '/Volumes/duguelab_general/DugueLab_Research/Current_Projects/DL_Long_Tempo_Waves/Experiments/Experiment/Data'
# base_output_dir = '/Users/macbook/Work/DugueLab/Longitudinal_Tempo_Waves/Data/long_duration'

raw_dir = os.path.join(base_output_dir, 'raw')
trc_raw_dir = os.path.join(raw_dir, 'trc')
fif_raw_dir = os.path.join(raw_dir, 'fif')

# Channel removal directories
chans_to_remove = ['SpO2+-SpO2-', 
                   'thor+-thor-', 
                   'abdo+-abdo-', 
                   'xyz+-xyz-']
prefixes_to_remove = ['el',     # electrode labels like el1, el2...
                    'PNG',    # artifact/image-related channels if present
                    'dc',     # DC channels
                    'emg']    # EMG channels

suffixes_to_remove = [] #['-0','-1']

# Dictionary to rename annotations
rename_dict = {
    'Stim 1': 'stimulus',
    'stim_1': 'stimulus',
    'STIM-1': 'stimulus',
    'noise': 'artifact',
    'BAD_artifact': 'artifact'}

semantic_map = {
                # "Ecg": "Cardiac",
                # "Resp": "Respiration",
                # "Eyes Closed": "Rest Eyes Closed",
            }

epoch_t_min_epoch = -0.2
epoch_t_max_epoch = 0.5
epoch_baseline = (None, 0)

