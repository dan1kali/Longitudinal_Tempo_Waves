import json
import os
import re
import unicodedata
import mne
from natsort import natsorted
import pandas as pd
import time
import numpy as np
from project.helper import resolveSelection
import project.config as config

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



def loadAnnotationsFromFile(filePath, patient_ID=None, filename_list=None):

    if filePath.endswith(".parquet"):
        df = pd.read_parquet(filePath)
    elif filePath.endswith(".csv"):
        df = pd.read_csv(filePath)
    else:
        raise ValueError("Unsupported file format")

    all_patients = natsorted(df["patient"].unique())
    patient_ID = resolveSelection(patient_ID, all_patients, "patient_ID")
    df = df[df["patient"].isin(patient_ID)]

    all_files = natsorted(df["filename"].unique())
    filename_list = resolveSelection(filename_list, all_files, "filename")
    df = df[df["filename"].isin(filename_list)]

    if "original_rec_time" in df.columns:
        df["original_rec_time"] = pd.to_datetime(df["original_rec_time"], errors="coerce")

    if "onset" in df.columns:
        df["onset"] = pd.to_numeric(df["onset"], errors="coerce")

    if "original_rec_time" in df.columns and "onset" in df.columns:
        df["absolute_rec_time"] = df["original_rec_time"] + pd.to_timedelta(df["onset"], unit="s")

    return df


def cleanFifAnnotationsUnicode(fifFileList, savePathList=None):
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



def normalizeSyntax(label):
    # ---- Unicode cleanup (optional but useful for accents consistency) ----
    label = unicodedata.normalize("NFKC", label)

    # ---------------- Strip whitespace ----------------
    label = label.strip()

    # ------------- Replace underscores/hyphens ----------------
    label = label.replace("_", " ")
    label = label.replace("-", " ")

    # ---- Remove unwanted symbols (keep medically relevant punctuation) ----
    label = re.sub(r"[$§@#&*~^`|\\]", "", label)

    # ---------------- Collapse multiple spaces ----------------
    label = re.sub(r"\s+", " ", label)

    # ---------------- Collapse spaces before punctuation ----------------
    label = re.sub(r"\s+([!?.,;:])", r"\1", label)

    # ---------------- Fix repeated punctuation ----------------
    label = re.sub(r"([!?.,;:+\-*/])\1+", r"\1", label)
    label = re.sub(r"[!?]{2,}", lambda m: "?" if "?" in m.group(0) else "!", label)
    
    # ---------------- Lower case ----------------
    label = label.lower()
    
    return label


def normalizeSemantics(label):
    return config.semantic_map.get(label, label)


def generateAnnotationTable(annotationDF, output_csv=None,annotationTxt=None):
    """
    Generate editable annotation review table.

    Parameters
    ----------
    annotationDF : pd.DataFrame
        DataFrame containing an 'annotation' column.

    output_csv : str
        Path to save editable CSV table.

    Returns
    -------
    review_df : pd.DataFrame
    """

    uniqueAnnotations = sorted(annotationDF["annotation"].dropna().unique())

    rows = []

    for old_label in uniqueAnnotations:

        syntax_label = normalizeSyntax(old_label)
        final_label = normalizeSemantics(syntax_label)

        changed = old_label != final_label

        if old_label == syntax_label and syntax_label == final_label:
            source = "unchanged"
        elif old_label != syntax_label and syntax_label == final_label:
            source = "auto-syntax"
        elif syntax_label != final_label:
            source = "auto-semantic"
        else:
            source = "auto-mixed"

        rows.append({
            "old_label": old_label,
            "final_label": final_label,
            "changed": changed,
            "source": source,})

    review_df = pd.DataFrame(rows)

    if output_csv:
        review_df.to_csv(output_csv, index=False)

        print(f"Saved annotation review table:\n{output_csv}")

    if annotationTxt:

        with open(annotationTxt, "w", encoding="utf-8") as f:
            for ann in uniqueAnnotations:
                f.write(str(ann) + "\n")
                
    collapse_count = len(uniqueAnnotations) - len(set(review_df["final_label"]))
    print(f"Normalization collapsed {collapse_count} labels")

    return review_df, collapse_count



def loadEditedAnnotationTable(review_csv, overwrite_csv=True, save_json=False):
    """
    Reload manually edited annotation table and regenerate metadata.

    Parameters
    ----------
    review_csv : str
        Path to edited review CSV.

    overwrite_csv : bool
        If True, overwrite CSV with regenerated metadata.

    Returns
    -------
    review_df : pd.DataFrame

    renameDict : dict
        Dictionary mapping old_label -> final_label
    """

    review_df = pd.read_csv(review_csv)
    review_df = review_df[["old_label", "final_label"]].copy()

    rows = []

    for _, row in review_df.iterrows():

        old_label = str(row["old_label"])
        final_label = str(row["final_label"])

        syntax_label = normalizeSyntax(old_label)

        changed = old_label != final_label

        if old_label == final_label:
            source = "unchanged"

        elif final_label == syntax_label:
            source = "auto-syntax"

        elif final_label == normalizeSemantics(syntax_label):
            source = "auto-semantic"

        else:
            source = "manual"

        rows.append({
            "old_label": old_label,
            "final_label": final_label,
            "changed": changed,
            "source": source,
        })

    updated_df = pd.DataFrame(rows)

    if overwrite_csv:
        updated_df.to_csv(review_csv, index=False)
        print(f"Updated annotation table:\n{review_csv}")

    renameDict = dict(zip(updated_df["old_label"], updated_df["final_label"],))

    if save_json:

        json_path = "/src/project/config.json"
        renameConfig = {"rename_dict": renameDict}
        with open(json_path, "w") as f:
            json.dump(renameConfig, f, indent=2)
        print(f"Saved rename dictionary:\n{json_path}")

        # code to reload from json:
        # ---------------- Load rename dictionary from .json -------------------
        # config_path = "/src/project/config.json"
        # with open(config_path, "r") as f:
        #     config = json.load(f)
        # renameDict = config["rename_dict"]

    n_before = len(set(review_df["old_label"]))
    n_after = len(set(review_df["final_label"]))

    n_manual_collapse = n_before - n_after

    print(f"Manual editing collapsed {n_manual_collapse} labels")

    return updated_df, renameDict, n_manual_collapse




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

    processed_patients = set()
    output_root = None  # <-- track global output root

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

            present = set(raw.annotations.description)

            rename_dict_this_file = {
                old: new
                for old, new in renameDict.items()
                if old in present
            }

            raw.annotations.rename(rename_dict_this_file)

            # Save relabeled file in a mirrored directory structure
            if overwrite:
                save_path = file
            else:
                parts = file.split(os.sep)
                save_path = os.sep.join(["fif_relabeled_syntax" if "fif" in p and not p.endswith(".fif") else p for p in parts])
                if os.path.exists(save_path):
                    print(f"Skipping (already relabeled): {patientID} - {fileName}")
                    continue
                else:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # capture root output directory once
            if output_root is None:
                output_root = os.path.dirname(os.path.dirname(save_path))

            raw.save(save_path, overwrite=True)
            processed_patients.add(patientID)

            print(f"Relabeled {patientID} - {fileName} annotations in {time.time() - file_start:.1f} seconds")

        except Exception as exc:
            print(f"Skipped {patientID} - {fileName}: {exc}")

    print(f"Relabeled {len(processed_patients)} patients to {output_root}")
    print(f"Total processing time: {time.time() - total_start:.1f} seconds")