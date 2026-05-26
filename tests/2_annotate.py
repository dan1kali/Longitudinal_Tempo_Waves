# %%
import json
import os
import mne
import project.config as config
from longitudinal_tempo_waves.initialize import ObtainEEGFilePaths
from longitudinal_tempo_waves.annotate import cleanFifAnnotations, compileAnnotationsFromFilelist, loadAnnotationsFromFile, relabelFifAnnotations, visualizeAnnotationTimeline
import pandas as pd

BasePath = config.raw_dir
BasePath = '/Users/macbook/Work/DugueLab/Longitudinal_Tempo_Waves/Data/long_duration'


# %%
#########################################################################
################ Clean annotations and resave .fif files ################
#########################################################################

# ----------------- Obtain FIF file paths -----------------
# fifBasePath = os.path.join(BasePath, 'fif')
# fifFileList, _ = ObtainEEGFilePaths(fifBasePath,patient_index=None)

# ------------- Get rid of unicode in annotations -------------
# fifSaveFileList = [os.path.splitext(os.sep.join(["fif_fix_annotations" if p == "fif" else p for p in path.split(os.sep)]))[0] + ".fif" for path in fifFileList]
# cleanFifAnnotations(fifFileList, savePathList=fifSaveFileList)


# %%

########################################################################
################# Export annotations from .fif files ###################
########################################################################

# -------------------- Build load and save paths -----------------------
# fifBasePath = os.path.join(BasePath, 'fif_fix_annotations')
# fifFileList, _ = ObtainEEGFilePaths(fifBasePath,patient_index=None)

# csvPath = os.path.join(BasePath, "all_annotations.csv")
# savePath=parquetPath

# ------- Compile all annotations and export to .csv/.parquet ----------
# annotationDF = compileAnnotationsFromFilelist(fifFileList, savePath)


# %%

########################################################################
############## (optional) Visualize Annotation Timeline ################
########################################################################

# ------------------------- Build load paths ---------------------------
csvPath = os.path.join(BasePath, "all_annotations.csv")

# -------------------- Select patients and files -----------------------
patient_ID = [1]
filename_list = None
visualizeAnnotationTimeline(file_path=csvPath, patient_ID=patient_ID, filename_list=filename_list)


# %%

########################################################################
#################### Examine unique annotations ########################
########################################################################

# ------------------------ Build save paths ---------------------------
annotationTxt = os.path.join(BasePath, "annotations_unique.txt")
txtSavePath = annotationTxt

csvLoadPath = os.path.join(BasePath, "all_annotations.csv")
annotationTableCsv = os.path.join(BasePath, "annotations_table.csv")
tableSavePath = annotationTableCsv

# ------- Load the .csv/.parquet and get unique annotations -----------
annotationDF = loadAnnotationsFromFile(filePath=csvLoadPath)
uniqueAnnotations = sorted(annotationDF["annotation"].unique())
# print(uniqueAnnotations)

# ------------------ Save: unique annotations to .txt -----------------
# with open(txtSavePath, "w", encoding="utf-8") as f:
#     for ann in uniqueAnnotations:
#         f.write(str(ann) + "\n")

# ------------- Save: unique annotations to editable table ------------
review_df = pd.DataFrame({"old_label": uniqueAnnotations, "new_label": uniqueAnnotations }) 
review_df.to_csv(tableSavePath, index=False)


# %%

########################################################################
############# Create rename dictionary from edited table ###############
########################################################################

# --------------------- Load file paths ----------------------
reviewLoadPath = annotationTableCsv

review_df = pd.read_csv(annotationTableCsv)

# ---------------- Create dictionary to .json ------------------
renameDict = dict(zip(review_df["old_label"], review_df["new_label"]))

config_path = "/src/project/config.json"
renameConfig = {"rename_dict": renameDict}
with open(config_path, "w") as f:
    json.dump(renameConfig, f, indent=2)


# %%
########################################################################
################ Rename annotations and save new files #################
########################################################################

# ---------------- Load rename dictionary from .json ------------------

# with open(config_path, "r") as f:
#     config = json.load(f)
# renameDict = config["rename_dict"]

# ---------------- Relabel annotations ------------------
# relabelFifAnnotations(fifFileList, renameDict, overwrite=False)
