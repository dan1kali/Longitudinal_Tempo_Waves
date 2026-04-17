# %%
import project.config as config
import os
import mne
from longitudinal_tempo_waves.initialize import ObtainEEGFilePaths, TRCtoFIF, uniqueChannels, removeBadChannels
from longitudinal_tempo_waves.anonymize import exportTimeMapping, visualizeRecordingTimeline, anonymizeFifFiles
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
mne.set_log_level("ERROR")

BasePath = config.raw_dir
trcBasePath = os.path.join(BasePath, 'trc')
fifFilePath_preAnonymize = os.path.join(BasePath, 'fif_rmchans_NOT_anon')
outputTimeMappingCsv = os.path.join(BasePath, "patientTimeMapping.csv")


# %%

# (1) ################### CONVERT FROM TRC TO FIF ####################

# -- Specify files and obtain filepaths --
eegFileList, patientList = ObtainEEGFilePaths(trcBasePath, patient_index=None, file_index=None)

print(f'\n# TRC files selected for conversion - {len(eegFileList)}','\n')
print(f'\n# Total Patients - {len(patientList)}','\n')

# -- Save converted files --
fifFileList = [os.path.splitext(os.sep.join(["fif_rmchans_NOT_anon" if p == "trc" else p for p in path.split(os.sep)]))[0] + "_raw.fif" 
                                             for path in eegFileList]

TRCtoFIF(eegFileList, fifFileList, 
         saveFIF=True, anonymize=False, removeChannels=True, 
         channelsToRemove=config.chans_to_remove, 
         prefixesToRemove=config.prefixes_to_remove, 
         suffixesToRemove=config.suffixes_to_remove)


# %%

# (2) ####################### Save time mapping ########################

# -- Save CSV --
fifFileList_toAnonymize, _ = ObtainEEGFilePaths(fifFilePath_preAnonymize, patient_index=None, file_index=None)
exportTimeMapping(fifFileList_toAnonymize, outputPath=outputTimeMappingCsv)

# -- Visualize (optional) --
timeMappingData_csv = os.path.join(BasePath, '___.csv')
visualizeRecordingTimeline(timeMappingData_csv, patient=None)


# %%

# (3) ########################## Bulk anonymize ##########################

anonymizeFifFiles(fifFileList_toAnonymize, overwrite=False)





# %%

################# Construct channel list for removal #################

# Examine channel list --> determine which remove --> fill in config.py

# fifBasePath = os.path.join(rawBasePath, 'fif')
# fifFilesToExamine,patientList = ObtainEEGFilePaths(fifBasePath, patient_index=None,file_index=1)

# unique_chans = uniqueChannels(fifFilesToExamine)

# print(f'\n# Patients selected - {len(patientList)}','\n')
# print(f"\nUnique channels across all files:\n{unique_chans}\n")


# %%
# ##################### Bulk Remove bad channels #####################

# fifBasePath = os.path.join(rawBasePath, 'fif')
# fifFilesToExamine,patientList = ObtainEEGFilePaths(fifBasePath, patient_index=None,file_index=None)

# removeBadChannels(fifFilesToExamine, 
#                   channelsToRemove=config.chans_to_remove, 
#                   prefixesToRemove=config.prefixes_to_remove, 
#                   suffixesToRemove=config.suffixes_to_remove, 
#                   replaceCleaned=False)
