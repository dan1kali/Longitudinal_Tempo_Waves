# %%
import os
import project.config as config
from longitudinal_tempo_waves.initialize import ObtainEEGFilePaths
from longitudinal_tempo_waves.annotate import cleanFifAnnotationsUnicode, compileAnnotationsFromFilelist, generateAnnotationTable, loadAnnotationsFromFile, loadEditedAnnotationTable, relabelFifAnnotations
from longitudinal_tempo_waves.visualize import visualizeAnnotationTimeline
import pandas as pd

BasePath = config.base_output_dir

# %%

#########################################################################
######## Clean unicode from annotations and resave .fif files ###########
#########################################################################

# ------------------------- Obtain FIF file paths -----------------------
# fifBasePath = os.path.join(BasePath, 'fif')
# fifFileList, _ = ObtainEEGFilePaths(fifBasePath,patient_index=None)

# ------------- Get rid of unicode in annotations -------------
# fifSaveFileList = [os.path.splitext(os.sep.join(["fif_fix_annotations" if p == "fif" else p for p in path.split(os.sep)]))[0] + ".fif" for path in fifFileList]
# cleanFifAnnotationsUnicode(fifFileList, savePathList=fifSaveFileList)


# %%

########################################################################
############### Export annotations from all .fif files #################
########################################################################

# -------------------- Build load and save paths -----------------------
# fifBasePath = os.path.join(BasePath, 'fif_fix_annotations')
# fifFileList, _ = ObtainEEGFilePaths(fifBasePath,patient_index=None)

# allAnnotCsvPath = os.path.join(BasePath, "all_annotations.csv")

# ------- Compile all annotations and export to .csv/.parquet ----------
# annotationDF = compileAnnotationsFromFilelist(fifFileList, allAnnotCsvPath)


# %%

########################################################################
############## (optional) Visualize Annotation Timeline ################
########################################################################

# ------------------------- Build load paths ---------------------------
# allAnnotCsvPath = os.path.join(BasePath, "all_annotations.csv")

# # -------------------- Select patients and files -----------------------
# patient_ID = [1]
# filename_list = None
# visualizeAnnotationTimeline(file_path=allAnnotCsvPath, patient_ID=patient_ID, filename_list=filename_list)


# %%

########################################################################
###################### Create rename dictionary ########################
########################################################################

# ----------------------- Load all annotations -------------------------
allAnnotCsvPath = os.path.join(BasePath, "all_annotations.csv")
# patient_ID = [1]
annotationDF = loadAnnotationsFromFile(filePath=allAnnotCsvPath, patient_ID=None, filename_list=None)

# --------------- (Optional) Get unique annotations --------------------
# uniqueAnnotations = sorted(annotationDF["annotation"].unique())
# print(uniqueAnnotations)

# ------------------------ Generate save paths -------------------------
annotationTxt = os.path.join(BasePath, "annotations_unique.txt")
annotationTableCsv = os.path.join(BasePath, "annotations_table.csv")

# ------------------------------------------------------------- 
# IF AUTOMATICALLY EDIT: 
#   
# Edit rules in:
#   def normalizeFifAnnotations in annotate.py 
# 
# Then run:
review_df, collapse_count = generateAnnotationTable(annotationDF, output_csv=None, annotationTxt=None)
# -------------------------------------------------------------

# Examine all changed labels:
# print(review_df[review_df["changed"]])

# Examine number of unique labels changed:
# n_original = annotationDF["annotation"].nunique() # should be 6208
# print("Unique original labels:", n_original)
# changed_unique_final = review_df["final_label"].nunique()
# print("Unique final labels:", changed_unique_final)
# print("Labels collapsed:", n_original - changed_unique_final)
# print("Labels collapsed counted:", collapse_count)

# # Examine one label:
# idx = 1  # change this
# selected_final = review_df["final_label"][idx]
# subset = review_df[review_df["final_label"] == selected_final]
# print("New Label:", selected_final)
# print("Count:", len(subset))
# print("Old Labels:\n",subset["old_label"].to_string(index=False))



# Save to csv:
df = review_df.copy()
summary = (df.groupby("final_label")
            .agg(status=("changed", lambda x: "changed" if x.any() else "unchanged"),
                num_old_labels=("old_label", "nunique"),
                old_labels=("old_label", lambda x: ", ".join(sorted(set(x)))))
            .reset_index()
            .rename(columns={"final_label": "new_label"}))

summary = summary.sort_values(by="status",
    key=lambda s: s.map({"changed": 0, "unchanged": 1})).reset_index(drop=True)

summary = summary[["status", "new_label", "num_old_labels", "old_labels"]]

summary.to_csv(os.path.join(BasePath, "changed_labels.csv"), index=False)

print(summary)

# ------------------------------------------------------------- 
# IF MANUALLY EDIT: 
# 
# Edit: 
#   final_label column in annotations_table.csv
# 
# Then run:
# loadEditedAnnotationTable(annotationTableCsv, overwrite_csv=True)
# -------------------------------------------------------------

# %%

########################################################################
#################### Relabel annotations and save .fif #################
########################################################################

# -------------------------- Build save paths --------------------------
# fifBasePath = os.path.join(BasePath, 'fif_fix_annotations')
# fifFileList, _ = ObtainEEGFilePaths(fifBasePath,patient_index=None)

# ---------------- Load rename dictionary from .csv --------------------
# review_df = pd.read_csv(annotationTableCsv)
# renameDict = dict( zip( review_df["old_label"], review_df["final_label"] ) )

# ----------------------- Relabel annotations --------------------------
# relabelFifAnnotations(fifFileList, renameDict, overwrite=False)







# reusable:

# def inspect_final_label(review_df, final_label):
#     subset = review_df[review_df["final_label"] == final_label]

#     print("FINAL:", final_label)
#     print("COUNT:", len(subset))
#     print("\nOLD LABELS:")
#     print(subset["old_label"].to_string(index=False))

#     return subset