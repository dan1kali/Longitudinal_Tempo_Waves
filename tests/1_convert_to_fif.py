# %%
import os
import mne
from longitudinal_tempo_waves.initialize import ObtainEEGFilePaths, TRCtoFIF, removeBadChannels, uniqueChannels
import warnings
import matplotlib.pyplot as plt
from longitudinal_tempo_waves.mixed_micromed_io.mixed_to_mne import create_mne_from_mixed_micromed_recording
warnings.filterwarnings("ignore", category=RuntimeWarning)
mne.set_log_level("ERROR")

# %%
################ Specify files and obtain filepaths ################

basePath = '/Users/macbook/Work/DugueLab/Longitudinal_Tempo_Waves/Data/long_duration/trc'
patient_index=None # use none for all patients
file_index=1
eegFileList, patientList = ObtainEEGFilePaths(basePath, patient_index, file_index)

print(f'\n# TRC files selected for conversion - {len(eegFileList)}','\n')

# %%
####################### Save converted files #######################

# Saves in a folder called "fif" in the same parent directory containing raw file folder
fifFileList = [os.path.splitext(os.sep.join(["fif" if p == "trc" else p for p in path.split(os.sep)]))[0] + "_raw.fif" 
                                             for path in eegFileList]
TRCtoFIF(eegFileList, fifFileList)

# # %%
###################### Visually examine 1 file #####################

basePath = '/Users/macbook/Work/DugueLab/Longitudinal_Tempo_Waves/Data/long_duration/trc'
eegFileList, _ = ObtainEEGFilePaths(basePath, patient_index=1, file_index=1)

raw = create_mne_from_mixed_micromed_recording(eegFileList[0])
raw.load_data()
raw.plot()
plt.show()

# %%
################# Examine channel list for removal #################

basePath = '/Users/macbook/Work/DugueLab/Longitudinal_Tempo_Waves/Data/long_duration/fif'
patient_index=None
fifFilesToExamine,patientList = ObtainEEGFilePaths(basePath, patient_index,file_index=1)

print(f'\n# Patients selected - {len(patientList)}','\n')

unique_chans = uniqueChannels(fifFilesToExamine)
print(f"\nUnique channels across all files:\n{unique_chans}\n")

# # %%
# ######################## Remove bad channels #######################

# Construct channels to remove based on above
channelsToRemove = ['PULS+-PULS-', 'SpO2+-SpO2-', 'BEAT+-BEAT-',
                    'thor+-thor-', 'abdo+-abdo-', 'xyz+-xyz-','MKR+-MKR-']
prefixesToRemove = ['el','PNG','dc','SLI','emg','ecg']
suffixesToRemove = ['-0','-1']

removeBadChannels(fifFilesToExamine, channelsToRemove, prefixesToRemove, suffixesToRemove, replaceCleaned=False)