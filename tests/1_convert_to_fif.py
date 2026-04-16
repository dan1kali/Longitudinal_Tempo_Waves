# %%
import os
import mne
from longitudinal_tempo_waves.initialize import ObtainEEGFilePaths, TRCtoFIF, removeBadChannels, uniqueChannels
import warnings
import matplotlib.pyplot as plt
from longitudinal_tempo_waves.mixed_micromed_io.mixed_to_mne import create_mne_from_mixed_micromed_recording
warnings.filterwarnings("ignore", category=RuntimeWarning)
mne.set_log_level("ERROR")

################ Specify files and obtain filepaths ################

basePath = '/Volumes/duguelab_general/DugueLab_Research/Current_Projects/DL_Long_Tempo_Waves/Experiments/Experiment/Data/Raw/trc'
eegFileList, patientList = ObtainEEGFilePaths(basePath, patient_index=None, file_index=None)

print(f'\n# TRC files selected for conversion - {len(eegFileList)}','\n')
print(f'\n# Total Patients - {len(patientList)}','\n')

# ####################### Save converted files #######################

# Saves in a folder called "fif" in the same parent directory containing raw file folder
fifFileList = [os.path.splitext(os.sep.join(["fif" if p == "trc" else p for p in path.split(os.sep)]))[0] + "_raw.fif" 
                                             for path in eegFileList]

channelsToRemove = ['PULS+-PULS-', 'SpO2+-SpO2-', 'BEAT+-BEAT-',
                    'thor+-thor-', 'abdo+-abdo-', 'xyz+-xyz-','MKR+-MKR-']
prefixesToRemove = ['el','PNG','dc','SLI','emg']
suffixesToRemove = ['-0','-1']

TRCtoFIF(eegFileList, fifFileList, saveFIF=True, anonymize=True, removeChannels=True, 
         channelsToRemove=channelsToRemove, prefixesToRemove=prefixesToRemove, suffixesToRemove=suffixesToRemove)


# %%

################# Construct channel list for removal #################

# basePath = '/Volumes/duguelab_general/DugueLab_Research/Current_Projects/DL_Long_Tempo_Waves/Experiments/Experiment/Data/Raw/fif'
# patient_index=None
# fifFilesToExamine,patientList = ObtainEEGFilePaths(basePath, patient_index,file_index=1)

# # Examine channel list
# # print(f'\n# Patients selected - {len(patientList)}','\n')
# # unique_chans = uniqueChannels(fifFilesToExamine)
# # print(f"\nUnique channels across all files:\n{unique_chans}\n")

# Determine channels to remove based on above
# channelsToRemove = ['PULS+-PULS-', 'SpO2+-SpO2-', 'BEAT+-BEAT-',
#                     'thor+-thor-', 'abdo+-abdo-', 'xyz+-xyz-','MKR+-MKR-']
# prefixesToRemove = ['el','PNG','dc','SLI','emg','ecg']
# suffixesToRemove = ['-0','-1']

# %%
# ##################### Bulk Remove bad channels #####################

# basePath = '/Volumes/duguelab_general/DugueLab_Research/Current_Projects/DL_Long_Tempo_Waves/Experiments/Experiment/Data/Raw/fif'
# fifFilesToExamine,patientList = ObtainEEGFilePaths(basePath)
# removeBadChannels(fifFilesToExamine, channelsToRemove, prefixesToRemove, suffixesToRemove, replaceCleaned=False)