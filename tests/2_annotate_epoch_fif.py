# %%
import os
import mne
import project.config as config
from longitudinal_tempo_waves.initialize import ObtainEEGFilePaths
from longitudinal_tempo_waves.epoch import printAnnotations, relabelFifAnnotations, epochFifFiles

BasePath = config.raw_dir

# %%

###################### Obtain FIF file paths #######################

# fifBasePath = '/Users/macbook/Work/DugueLab/Longitudinal_Tempo_Waves/Data/long_duration/fif'

fifBasePath = os.path.join(BasePath, 'fif')
fifFileList = ObtainEEGFilePaths(fifBasePath,patient_index=None)

# %%

#################### Examine unique annotations ####################

annotationDF = printAnnotations(fifFileList, saveCSV=False)

print(annotationDF[['patient', 'filename', 'annotation','onset', 'original_rec_time']],'\n\n')
print(annotationDF["annotation"].unique())

# visualize them
# --> create rename dict in config.py

# %%

############## Rename annotations and save new files ###############

relabelFifAnnotations(fifFileList, renameDict=config.rename_dict)




############## Epoch and save new files ###############

# convert to events and epoch

epochFifFiles(fifFileList,
                  tmin=config.epoch_t_min_epoch,
                  tmax=config.epoch_t_max_epoch,
                  baseline=config.epoch_baseline,
                  event_id=None,
                  reject=None,
                  resample_sfreq=None,
                  overwrite=False)


# events, event_id = mne.events_from_annotations(raw)
# events, event_id = mne.events_from_annotations(
#     raw,
#     event_id={"stim": 1, "response": 2})


