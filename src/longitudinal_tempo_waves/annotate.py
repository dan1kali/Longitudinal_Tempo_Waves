import os
import re
import unicodedata
import mne
from natsort import natsorted
import pandas as pd
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from project.helper import resolveSelection

def compileAnnotationsFromFilelist(fifFileList, savePath=None):
    rows = []
    for file in fifFileList:
        fileName = os.path.splitext(os.path.basename(file))[0]
        patientID = os.path.basename(os.path.dirname(file))
        
        try:
            raw = mne.io.read_raw(file, preload=False)
            ann = raw.annotations
            
            df = pd.DataFrame({
                "patient": patientID,
                "filename": fileName,
                "annotation": ann.description,
                "onset": ann.onset,
                "recording_duration": raw.times[-1],  # last time point in seconds
                "event_duration": ann.duration,
                "sfreq" : raw.info["sfreq"]})
            if ann.ch_names is not None:
                df["ch_names"] = ann.ch_names
            if ann.orig_time is not None:
                df["original_rec_time"] = ann.orig_time
                df["absolute_rec_time"] = ann.orig_time + pd.to_timedelta(df["onset"], unit="s")
                        
            rows.append(df)

        except Exception as exc:
            print(f"Skipped {patientID} - {fileName}: {exc}")

    combined_df = pd.concat(rows, ignore_index=True)

    if savePath:
        if savePath.endswith(".parquet"):
            combined_df.to_parquet(savePath, engine="pyarrow")
        elif savePath.endswith(".csv"):
            combined_df.to_csv(savePath, index=False)
        else:
            raise ValueError("savePath must end with .parquet or .csv")
        return combined_df
    

def loadAnnotationsFromFile(filePath):

    if filePath.endswith(".parquet"):
        df = pd.read_parquet(filePath)
    elif filePath.endswith(".csv"):
        df = pd.read_csv(filePath)
    else:
        raise ValueError("Unsupported file format")

    if "original_rec_time" in df.columns:
        df["original_rec_time"] = pd.to_datetime(df["original_rec_time"], errors="coerce")

    if "onset" in df.columns:
        df["onset"] = pd.to_numeric(df["onset"], errors="coerce")

    if "original_rec_time" in df.columns and "onset" in df.columns:
        df["absolute_rec_time"] = df["original_rec_time"] + pd.to_timedelta(df["onset"], unit="s")

    return df

def visualizeAnnotationTimeline(
    parquet_path,
    patient_ID=None,
    filename_list=None,
    figsize=(12, 1.2),
    show=True
):
    df = pd.read_parquet(parquet_path)

    # -----------------------
    # UNIVERSES
    # -----------------------
    all_files = natsorted(df["filename"].unique())
    all_patients = natsorted(df["patient"].unique())

    # -----------------------
    # RESOLVE INPUTS
    # -----------------------
    patient_ID = resolveSelection(patient_ID, all_patients, "patient_ID")
    filename_list = resolveSelection(filename_list, all_files, "filename")

    # -----------------------
    # FILTER
    # -----------------------
    df = df[df["patient"].isin(patient_ID)]
    df = df[df["filename"].isin(filename_list)]

    files = natsorted(df["filename"].unique())

    # -----------------------
    # PLOT SETUP
    # -----------------------
    fig, ax = plt.subplots(
        1, 1,
        figsize=(figsize[0], max(figsize[1], 0.5 * len(files)))
    )

    y_map = {f: i for i, f in enumerate(files)}

    ann_types = df["annotation"].astype(str).unique()
    cmap = plt.cm.get_cmap("tab20", len(ann_types))
    ann_color = {a: cmap(i) for i, a in enumerate(ann_types)}

    # -----------------------
    # PLOT
    # -----------------------
    for f in files:
        sub = df[df["filename"] == f]
        y = y_map[f]

        rec_duration_hr = sub["recording_duration"].iloc[0] / 3600

        ax.barh(
            y=y,
            left=0,
            width=rec_duration_hr,
            height=0.6,
            color="lightblue",
            alpha=0.3
        )

        for _, row in sub.iterrows():
            x = row["onset"] / 3600
            color = ann_color.get(row["annotation"], "black")

            ax.scatter(x, y, color=color, s=20, zorder=3)

            if pd.notna(row["event_duration"]) and row["event_duration"] > 0:
                ax.hlines(
                    y=y,
                    xmin=x,
                    xmax=(row["onset"] + row["event_duration"]) / 3600,
                    color=color,
                    linewidth=2,
                    alpha=0.7
                )

    # -----------------------
    # FORMATTING
    # -----------------------
    ax.set_yticks(list(y_map.values()))
    ax.set_yticklabels(files)
    ax.set_xlabel("Time (hours)")
    ax.set_title("Recording + Annotation Timeline")
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    handles = [
        Line2D([0], [0], marker='o', color='w',
               markerfacecolor=ann_color[a],
               label=a, markersize=6)
        for a in ann_types
    ]

    ax.legend(handles=handles, title="Annotations",
              bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()

    if show:
        plt.show()

    return df

def cleanFifAnnotations(fifFileList, savePathList=None):
    """
    In-place cleaning of MNE FIF annotations:
    - removes control characters (\x00, etc.)
    - normalizes unicode
    - strips pure punctuation noise
    - drops empty annotations
    - overwrites original FIF files
    """


    if savePathList is None:
        savePathList = fifFileList


    def clean_label(s: str) -> str:
        if s is None:
            return ""

        s = unicodedata.normalize("NFKC", s)

        # remove null bytes + control chars
        s = s.replace("\x00", " ")
        s = re.sub(r"[\x00-\x1F\x7F]", " ", s)

        # normalize whitespace
        s = re.sub(r"\s+", " ", s).strip()

        # drop pure punctuation / junk
        # if re.fullmatch(r"[\W_]+", s):
            # return ""

        return s

    for in_fname, out_fname in zip(fifFileList, savePathList):
        raw = mne.io.read_raw_fif(in_fname, preload=True)

        if raw.annotations is None:
            continue

        desc, onset, duration = [], [], []

        for d, o, dur in zip(
            raw.annotations.description,
            raw.annotations.onset,
            raw.annotations.duration
        ):
            cd = clean_label(d)
            if cd:  # keep only meaningful labels
                desc.append(cd)
                onset.append(o)
                duration.append(dur)

        raw.set_annotations(
            mne.Annotations(onset=onset, duration=duration, description=desc)
        )

        os.makedirs(os.path.dirname(out_fname), exist_ok=True)
        raw.save(out_fname, overwrite=True)

    return fifFileList


def relabelFifAnnotations(fifFileList, renameDict, overwrite=False):
    """
    Rewrites MNE annotations in FIF files using renameDict and saves
    to a mirrored directory where 'fif' is replaced with 'fif_relabeled'

    Works to process bulk or single files from filepaths only

    Parameters
    ----------
    fifFileList : list of str
        Paths to input .fif files
    renameDict : dict
        Mapping old_annotation to new_annotation
    """
    total_start = time.time()

    if not isinstance(fifFileList, list):
        fifFileList = [fifFileList]

    for file in fifFileList:
        file_start = time.time()
        fileName = os.path.splitext(os.path.basename(file))[0]
        patientID = os.path.basename(os.path.dirname(file))
        try:
            raw = mne.io.read_raw_fif(file, preload=True)

            # Relabel
            if raw.annotations is None or len(raw.annotations) == 0:
                print("Skipping (no annotations)")
                continue

            raw.annotations.rename(renameDict)

            # Save relabeled file in a mirrored directory structure
            if overwrite:
                save_path = file
            else:
                parts = file.split(os.sep)
                save_path = os.sep.join(["fif_relabeled" if p == "fif" else p for p in parts])
                if os.path.exists(save_path):
                    print(f"Skipping (already relabeled): {patientID} - {fileName}")
                    continue
                else:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            raw.save(save_path, overwrite=True)
            print(f"Relabeled {patientID} - {fileName} annotations in {time.time() - file_start:.1f} seconds")

        except Exception as exc:
            print(f"Skipped {patientID} - {fileName}: {exc}")

    print(f"\nTotal processing time: {time.time() - total_start:.1f} seconds")