# %%
import project.config as config
import os
from longitudinal_tempo_waves.initialize import ObtainEEGFilePaths
from longitudinal_tempo_waves.anonymize import exportTimeMapping, visualizeRecordingTimeline, anonymizeFifFiles

BasePath = config.raw_dir

# %%

# ######################################################################
# ######################### Save time mapping ##########################
# ######################################################################

# ----------------- Specify files and obtain filepaths -----------------
fifFolder_preAnon = os.path.join(BasePath, 'fif_rmchans_NOT_anon')
fifFileList_toAnonymize, _ = ObtainEEGFilePaths(fifFolder_preAnon, patient_index=None, file_index=None)
outputCsv = os.path.join(BasePath, "patientTimeMapping.csv")

# ------------------- Export time mapping metadata ---------------------
exportTimeMapping(fifFileList_toAnonymize, outputCsv)


# %%

#######################################################################
######################### Visualize (optional) ########################
#######################################################################

# -------------- Specify patients by filename or index ----------------
patients=[1,2,3,4,6,9,42]
visualizeRecordingTimeline(outputCsv, patient_ID=patients)


# %%

#######################################################################
############################ Bulk anonymize ###########################
#######################################################################

# ----------------- Specify folder to load files from -----------------
fifFolder_preAnon = os.path.join(BasePath, 'fif_rmchans_NOT_anon')
fifFileList_toAnonymize, _ = ObtainEEGFilePaths(fifFolder_preAnon, patient_index=None, file_index=None)

# ------------------------ Anonymize files ----------------------------
anonymizeFifFiles(fifFileList_toAnonymize, overwrite=False)