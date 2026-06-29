from longitudinal_tempo_waves.visualize import visualizeAnnotationTimeline, visualizeRecordingTimeline
import os
import pandas as pd
import project.config as config

BasePath = config.raw_dir
# BasePath = '/Users/macbook/Work/DugueLab/Longitudinal_Tempo_Waves/Data/long_duration'
timeMappingCsv = os.path.join(BasePath, "patientTimeMapping.csv")


# %%

#######################################################################
######################### Visualize (optional) ########################
#######################################################################

# -------------- Visual inspection ----------------

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

throw_out = ['PAT_1104', 'PAT_1124', 'PAT_827', 'PAT_829'] # 5

# good: 
# 1200 session 2
# 867 session 1 
# 972 session 1 
# 990 session 1 

# very long: 
# 870 session 2 
# 888 session 2 

# bad:PAT_626
# -------------- Crisis rows ----------------

allAnnotCsvPath = os.path.join(BasePath, "all_annotations.csv")
# annotationDF = loadAnnotationsFromFile(filePath=allAnnotCsvPath, patient_ID=None, filename_list=None)
# crise_rows = annotationDF[annotationDF["annotation"].str.contains("crise", case=False, na=False)]
# unique_patients = crise_rows["patient"].unique()

crisepath = os.path.join(BasePath, "crise_annotations.csv")
# crise_rows.to_csv(savepath, index=False)

annot_rows = pd.read_csv(crisepath)
annot_filtered = annot_rows[annot_rows["patient"].isin(better)]

# -------------- Specify patients by filename or index ----------------

batch_idx = 19
batch_size = 10

start = (batch_idx - 1) * batch_size
end = start + batch_size

patients = sorted(annot_rows["patient"].unique().tolist())[start:end]
# print(f"# Patients with crisis annotations: {len(patients)}") - 185

# patients=[1,2,3,4,6,9,42]

select = better[2]
print(select)


# ----- visualize using one of following functions: -----

# visualizeAnnotationTimeline(file_path=crisepath, patient_ID=select, filename_list=None)
visualizeRecordingTimeline(timeMappingCsv, patient_ID=best[1:9], annotation_df=annot_rows, show=True)

