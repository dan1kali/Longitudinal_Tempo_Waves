import os
import mne
import pandas as pd


def printAnnotations(fifFileList, saveCSV=False):
    rows = []
    for file in fifFileList:
        fileName = os.path.splitext(os.path.basename(file))[0]
        patientID = os.path.basename(os.path.dirname(file))
        
        try:
            raw = mne.io.read_raw(file, preload=False)
            ann = raw.annotations
            
            # print('\n\n', ann, '\n\n')

            df = pd.DataFrame({
                "patient": patientID,
                "filename": fileName,
                "onset": ann.onset,
                "duration": ann.duration,
                "annotation": ann.description,
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

    if saveCSV:
        combined_df.to_csv("annotations.csv", index=False)

    return combined_df

def relabelFifAnnotations(fifFileList, renameDict):
    """
    Rewrites MNE annotations in FIF files using rename_dict and saves
    to a mirrored directory where 'fif' is replaced with 'fif_relabeled'

    Parameters
    ----------
    fifFileList : list of str
        Paths to input .fif files
    rename_dict : dict
        Mapping old_annotation to new_annotation
    """
    if not isinstance(fifFileList, list):
        fifFileList = [fifFileList]

    for file in fifFileList:
        fileName = os.path.splitext(os.path.basename(file))[0]
        patientID = os.path.basename(os.path.dirname(file))
        try:
            raw = mne.io.read_raw_fif(file, preload=True)

            # Relabel
            if raw.annotations is None or len(raw.annotations) == 0:
                print(f"Skipping (no annotations): {patientID} - {fileName}")
                continue
            raw.annotations.rename(renameDict)

            # Save relabeled file in a mirrored directory structure
            parts = file.split(os.sep)
            save_path = os.sep.join(["fif_relabeled" if p == "fif" else p for p in parts])
            if os.path.exists(save_path):
                print(f"Skipping (already relabeled): {patientID} - {fileName}")
                continue
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            raw.save(save_path, overwrite=True)
            print('\n',"Relabeled ", patientID, ' - ', fileName," annotations",'\n')

        except Exception as exc:
            print(f"Skipped {patientID} - {fileName}: {exc}")
