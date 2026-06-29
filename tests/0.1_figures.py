# %%

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
import project.config as config

##########################################################################
######################### Figures: Time Mapping ##########################
##########################################################################

BasePath = config.raw_dir
outputCsv = os.path.join(BasePath, "patientTimeMapping.csv")

df = pd.read_csv(outputCsv)

# remove units row
df = df[df["patient"] != "units"].copy()

# convert numeric columns
num_cols = [
    "session_id",
    "session_order",
    "time_elapsed_sec",
    "time_since_prev_sec",
    "recording_duration_sec"
]
for c in num_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce")


# %% ######### Number of recordings per patient ######

# patient_counts = df.groupby("patient")["filename"].count().sort_values()

# plt.figure(figsize=(10, 5))
# sns.histplot(patient_counts, bins=30)
# plt.title("Number of recordings per patient")
# plt.xlabel("Number of files")
# plt.ylabel("Number of patients")
# plt.tight_layout()
# plt.show()

# # %% Top 20 patients by number of recordings

# top = patient_counts.tail(20)

# plt.figure(figsize=(10, 6))
# top.plot(kind="barh")
# plt.title("Top 20 patients by number of recordings")
# plt.xlabel("Number of files")
# plt.tight_layout()
# plt.show()


# %% ######## Distribution of files per session #######

# session_counts = df.groupby(["patient", "session_id"])["filename"].count()

# plt.figure(figsize=(8, 5))
# sns.histplot(session_counts, bins=30)
# plt.title("Number of files per session")
# plt.xlabel("Files per session")
# plt.ylabel("Count")
# plt.tight_layout()
# plt.show()

# %%

# sessions_per_patient = df.groupby("patient")["session_id"].nunique()

# plt.figure(figsize=(10, 5))
# sns.histplot(sessions_per_patient, bins=30)
# plt.title("Number of sessions per patient")
# plt.xlabel("Sessions per patient")
# plt.ylabel("Count")
# plt.xlim(0.8, 4)
# plt.tight_layout()
# plt.show()

# %%  ####### Recording duration distribution ######

plt.figure(figsize=(10, 5))
# sns.histplot(df["recording_duration_sec"], bins=50, kde=True)
# sns.histplot(df["recording_duration_sec"], bins=50)
sns.histplot(df["recording_duration_sec"] / 3600, bins=50) # type: ignore
plt.xlim(0, 7)
plt.title("Recording duration")
plt.xlabel("Duration (hours)")
plt.ylabel("Count")
plt.tight_layout()
plt.show()


# %%  ####### Recording duration distribution zoom in######

plt.figure(figsize=(10, 5))
# sns.histplot(df["recording_duration_sec"], bins=50, kde=True)
# sns.histplot(df["recording_duration_sec"], bins=50)
sns.histplot(df["recording_duration_sec"] / 3600, bins=500) # type: ignore
plt.xlim(0, 1)
plt.title("Recording duration")
plt.xlabel("Duration (hours)")
plt.ylabel("Count")
plt.tight_layout()
plt.show()


##########################################################################
####################### Figures: Annotation Mapping ######################
##########################################################################

parquetPath = os.path.join(BasePath, "all_annotations.parquet")
ann = pd.read_parquet(parquetPath)

# basic cleanup
ann = ann.copy()

# ensure numeric
ann["onset"] = pd.to_numeric(ann["onset"], errors="coerce")
ann["event_duration"] = pd.to_numeric(ann["event_duration"], errors="coerce")
ann["sfreq"] = pd.to_numeric(ann["sfreq"], errors="coerce")

# %% ######### Number of annotations per recording ######### wrong

ann_counts = ann.groupby(["patient", "filename"]).size()

plt.figure(figsize=(10, 5))
# sns.histplot(x=ann_counts, bins=50)
sns.histplot(x=ann_counts, bins="auto")
plt.xlim(0, ann_counts.quantile(0.95))  # zoom into main mass
plt.title("Number of annotations per recording")
plt.xlabel("Annotations per file")
plt.ylabel("Count")
plt.tight_layout()
plt.show()

# %% Most common annotation types 

# top_events = ann["annotation"].value_counts().head(20)

# plt.figure(figsize=(10, 6))
# top_events.plot(kind="barh")
# plt.title("Top 20 annotation types")
# plt.xlabel("Count")
# plt.tight_layout()
# plt.show()

# %% ####### Onset distribution #######

plt.figure(figsize=(7, 5))
sns.histplot(x=ann["onset"]/3600, bins=80)
plt.title("Distribution of annotation onsets (within recording)")
plt.xlim(0, 20000/3600)  # zoom into main mass
plt.xlabel("hours from start")
plt.show()


# %% ####### Onset distribution zoom in #######

plt.figure(figsize=(7, 5))
sns.histplot(x=ann["onset"]/3600, bins=1000)
plt.title("Distribution of annotation onsets (within recording)")
plt.xlim(0, 0.5)  # zoom into main mass
plt.xlabel("hours from start")
plt.show()


# %% ####### Per-file annotations histogram #######
patient_events = ann.groupby("filename").size()

plt.figure(figsize=(7, 5))
sns.histplot(x=patient_events, bins="fd")

upper = patient_events.quantile(0.99)
plt.xlim(0, upper)

plt.title("Annotations per file")
plt.xlabel("Number of annotations")
plt.ylabel("Number of files")

plt.tight_layout()
plt.show()



# %% ####### Annotation timing patterns (inside session dynamics) #######

sample = ann[ann["patient"] == ann["patient"].value_counts().index[0]]

plt.figure(figsize=(10, 5))
sns.histplot(sample["onset"], bins=80)
plt.title("Annotation onset pattern (sample patient)")
plt.show()