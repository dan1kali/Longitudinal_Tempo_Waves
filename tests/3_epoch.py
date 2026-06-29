# %%
import os
import mne
from longitudinal_tempo_waves.annotate import loadAnnotationsFromFile
import project.config as config
from longitudinal_tempo_waves.initialize import ObtainEEGFilePaths
from longitudinal_tempo_waves.epoch import epochFifFiles
from pathlib import Path

mne.set_log_level("WARNING")

BasePath = config.raw_dir

########################################################################
########################## Visual inspection ###########################
########################################################################


best = ['PAT_1013', 'PAT_1020',  'PAT_1034', 'PAT_1164', 'PAT_1321'] # 5

better = ['PAT_1069', 'PAT_1085', 'PAT_1117', 'PAT_1123', 'PAT_1139', 
        'PAT_1144', 'PAT_1152', 'PAT_1288', 'PAT_1342', 'PAT_1344', 'PAT_1346', 
        'PAT_1358', 'PAT_1373', 'PAT_420', 'PAT_838', 'PAT_858', 'PAT_863', 'PAT_983', 'PAT_996'] # 19

very_long = ['PAT_1120', 'PAT_1136','PAT_1168', 'PAT_1177', 'PAT_1181', 'PAT_1182', 'PAT_1184',
                'PAT_1197', 'PAT_1198', 'PAT_1202', 'PAT_1214', 'PAT_1240', 'PAT_1251', 'PAT_1252', 
                'PAT_1257', 'PAT_1278', 'PAT_1282', 'PAT_1302', 'PAT_1319', 'PAT_1321','PAT_1322', 
                'PAT_1323', 'PAT_1324', 'PAT_1325', 'PAT_1326', 'PAT_1327', 'PAT_1328', 'PAT_1341', 
                'PAT_1353', 'PAT_1355', 'PAT_1375'] # 31

maybe = ['PAT_1066', 'PAT_1117', 'PAT_1120', 'PAT_1135', 'PAT_1154', 'PAT_1179', 'PAT_1244', 'PAT_1309',
         'PAT_844', 'PAT_851', 'PAT_868', 'PAT_874','PAT_877','PAT_980','PAT_983'] # 15

not_working = set(['PAT_1322', 'PAT_1323', 'PAT_1324', 'PAT_1325', 'PAT_1326', 'PAT_1327', 'PAT_1328'])  

selected = [p for p in (best + better + very_long + maybe) if p not in not_working]


# %%
########################################################################
####################### Epoch and save new files #######################
########################################################################

# ----------------- Obtain FIF file paths -----------------

# files = ['EEG_55673_raw',
#          'EEG_59768_raw', ######
#          'EEG_59765_raw',
#          'EEG_82826_raw',
#          'EEG_115069_raw']

fifBasePath = os.path.join(BasePath, 'fif_relabel_pass1')
fifFileList, _, _ = ObtainEEGFilePaths(fifBasePath,patient_index=None)
filtered_fileList = [f for f in fifFileList if Path(f).parent.name in selected] # use if patient
# filtered_fileList = [f for f in fifFileList if Path(f).stem in fileset]

# ------------- Create event dict to sepectively epoch "crise" only -------------
allAnnotCsvPath = os.path.join(BasePath, "all_annotations.csv")
annotationDF = loadAnnotationsFromFile(filePath=allAnnotCsvPath, patient_ID=selected, filename_list=None)
crise_annotations = (annotationDF.loc[annotationDF["annotation"].str.contains("crise", case=False, na=False),"annotation"].unique())

event_id = {ann: i + 1 for i, ann in enumerate(crise_annotations)}

# ---------------- convert to events and epoch ------------------
timeMappingCsv = os.path.join(BasePath, "patientTimeMapping.csv")
epochFifFiles(filtered_fileList,event_id=event_id,generate_controls_csv=timeMappingCsv)