import os
import time
import mne
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from tqdm import tqdm


def exportTimeMapping(
    fifFileList,
    outputPath=None,
    min_gap_bt_sessions_days=10,
    progressBar=True):
    """
    Build anonymized EEG temporal metadata table from a list of FIF files.

    Parameters
    ----------
    fif_file_list : list[str]
        List of .fif file paths.
    outputPath : str or None
        If provided, writes CSV to this path.
    min_gap_bt_sessions_days : int
        Gap (in days) used to split sessions.
    progressBar : bool
        Show tqdm progress bar.

    Returns
    -------
    pd.DataFrame
        Final anonymized dataframe.
    """

    records = []
    total_start = time.time()

    # -------------------------
    # 1. Extract metadata
    # -------------------------
    iterator = tqdm(fifFileList) if progressBar else fifFileList

    for fpath in iterator:
        try:
            raw = mne.io.read_raw_fif(fpath, preload=False, verbose=False)

            meas_date = pd.to_datetime(raw.info.get("meas_date"), utc=True)
            recording_duration_sec = raw.times[-1] if raw.times is not None else np.nan

            patientID = os.path.basename(os.path.dirname(fpath))
            fileName = os.path.splitext(os.path.basename(fpath))[0]

            records.append({"patient": patientID,
                            "filename": fileName,
                            "meas_date": meas_date,
                            "recording_duration_sec": float(recording_duration_sec)})
            print(f"Extracted time data from {patientID} - {fileName} in {time.time() - total_start:.1f} seconds")

        except Exception as exc:
            print(f"FAILED: {patientID} - {fileName}: {exc}")

    df = pd.DataFrame(records)

    print(f"All data extracted from {len(df)} files in {time.time() - total_start:.1f} seconds! Building time mapping csv...")
    # -------------------------
    # 2. 5-year anonymized block
    # -------------------------
    def year_block(dt):
        y = dt.year
        start = (y // 5) * 5
        return f"{start}-{start+4}"

    df["5_year_block"] = df["meas_date"].apply(year_block)

    # -------------------------
    # 3. time of day
    # -------------------------
    df["time_of_day"] = df["meas_date"].dt.strftime("%H:%M:%S")

    # -------------------------
    # 4. session split
    # -------------------------
    df = df.sort_values(["patient", "meas_date", "filename"]).copy()

    gap = df.groupby("patient")["meas_date"].diff()
    threshold = pd.Timedelta(f"{min_gap_bt_sessions_days}D")

    df["session_id"] = ((gap > threshold) | gap.isna()).groupby(df["patient"]).cumsum().astype(int)

    # -------------------------
    # 5. ordering
    # -------------------------
    df = df.sort_values(["patient", "session_id", "meas_date", "filename"])

    df["session_order"] = df.groupby(["patient", "session_id"]).cumcount() + 1

    # -------------------------
    # 6. session-relative time
    # -------------------------
    df["session_start"] = df.groupby(["patient", "session_id"])["meas_date"].transform("first")

    df["time_elapsed_sec"] = (df["meas_date"] - df["session_start"]).dt.total_seconds()

    df["time_elapsed_hms"] = pd.to_timedelta(df["time_elapsed_sec"], unit="s").astype(str)

    # -------------------------
    # 7. time since last recording
    # -------------------------
    df["time_since_prev_sec"] = df.groupby(["patient", "session_id"])["meas_date"].diff().dt.total_seconds().round(1)

    def sec_to_hms(x):
        if pd.isna(x):
            return pd.NA
        x = int(x)
        h = x // 3600
        m = (x % 3600) // 60
        s = x % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    df["time_since_prev_hms"] = df["time_since_prev_sec"].apply(sec_to_hms)

    # -------------------------
    # 8. duration
    # -------------------------
    df["recording_duration_sec"] = df["recording_duration_sec"].astype(float).round(1)
    df["recording_duration_hms"] = df["recording_duration_sec"].apply(sec_to_hms)

    # -------------------------
    # 9. export table
    # -------------------------
    df_export = df[[
        "patient",
        "filename",
        "5_year_block",
        "session_id",
        "session_order",
        "time_of_day",
        "time_elapsed_hms",
        "time_since_prev_hms",
        "recording_duration_hms",
        "time_elapsed_sec",
        "time_since_prev_sec",
        "recording_duration_sec",]]

    # -------------------------
    # 10. optional units row
    # -------------------------
    units = {
        "patient": "string",
        "filename": "string",
        "5_year_block": "index",
        "session_id": "index",
        "session_order": "index",
        "time_of_day": "hh:mm:ss",
        "recording_duration_hms": "hh:mm:ss",
        "time_elapsed_hms": "hh:mm:ss",
        "time_since_prev_hms": "hh:mm:ss",
        "recording_duration_sec": "seconds",
        "time_elapsed_sec": "seconds",
        "time_since_prev_sec": "seconds"
        }

    units = pd.DataFrame([units])[df_export.columns]
    final_df = pd.concat([units, df_export], ignore_index=True)

    # -------------------------
    # 11. export if requested
    # -------------------------
    if outputPath is not None:
        os.makedirs(os.path.dirname(outputPath), exist_ok=True)
        final_df.to_csv(outputPath, index=False)
    else:
        print("No output path provided. Returning dataframe without saving.")

    print(f"\nAll time data mapped to csv in {time.time() - total_start:.1f} seconds!")
    return final_df


def visualizeRecordingTimeline(
    csvPath,
    patient=None,
    figsize=(12, 6),
    use_session_relative_time=True,
    show=True):
    """
    Visualize EEG recording sessions from patient_time_mapping.csv.

    Parameters
    ----------
    csvPath : str
        Path to CSV file produced by your pipeline.
    
    patient : str or None
        If provided, plots only one patient. Otherwise plots all patients.

    figsize : tuple
        Figure size.

    use_session_relative_time : bool
        If True, uses time_since_session_start_sec.
        If False, uses global time offset within patient.

    show : bool
        If True, calls plt.show() for each patient.
    """

    total_start = time.time()
    # -------------------------
    # LOAD DATA
    # -------------------------
    df = pd.read_csv(csvPath)

    # Remove units row
    df = df[df["patient"] != "string"].copy()

    # Type safety
    df["session_id"] = df["session_id"].astype(int)
    df["recording_duration_sec"] = df["recording_duration_sec"].astype(float).round(1)

    # Specify patients, or all if "None"
    if patient is not None:
        df = df[df["patient"] == patient].copy()

    patients = df["patient"].unique()

    # -------------------------
    # PLOT PER PATIENT
    # -------------------------
    for pat in patients:
        sub = df[df["patient"] == pat].copy()

        plt.figure(figsize=figsize)

        sessions = sorted(sub["session_id"].unique())
        y_map = {s: i for i, s in enumerate(sessions)}

        # Optional global timeline
        if not use_session_relative_time:
            # reconstruct pseudo-global time ordering
            sub = sub.sort_values(["session_id", "session_order"])
            sub["global_start"] = sub.groupby("patient").cumcount() * 10  # fallback spacing

        # Color map per session
        colors = cm.get_cmap("tab10", len(sessions))

        for _, row in sub.iterrows():
            y = y_map[row["session_id"]]

            if use_session_relative_time:
                start = row["time_elapsed_sec"]
            else:
                start = row.get("global_start", 0)

            duration = row["recording_duration_sec"]

            plt.barh(
                y=y,
                width=duration,
                left=start,
                height=0.6,
                color=colors(y))

        plt.yticks(list(y_map.values()), [f"Session {s}" for s in sessions])
        plt.xlabel("Time (seconds)")
        plt.ylabel("Session")
        plt.title(f"Recording Timeline - {pat}")
        plt.grid(True, axis="x", linestyle="--", alpha=0.5)

        plt.tight_layout()

        if show:
            plt.show()
    print(f"\nVisualization completed in {time.time() - total_start:.1f} seconds!")

    return df


def anonymizeFifFiles(fifFileList, overwrite=False):
    """
    Anonymizes FIF files and saves them to a mirrored directory where
    'fif' is replaced with 'fif_rm_chans_anon'

    Processes in bulk for filepaths or for single MNE Raw object (returns object)

    Parameters
    ----------
    fifFileList : list of str
        Paths to input .fif files
    overwrite : bool
        If True, overwrite original files
    """
    total_start = time.time()

    # -- if single filepath --
    if not isinstance(fifFileList, list):
        fifFileList = [fifFileList]
    
    for item in fifFileList:
        file_start = time.time()
        if isinstance(item, mne.io.BaseRaw):
            # -- if object --
            raw = item
            file = None
        else:
            # -- if filepath --
            file = item
            fileName = os.path.splitext(os.path.basename(file))[0]
            patientID = os.path.basename(os.path.dirname(file))
            raw = mne.io.read_raw_fif(file, preload=True)

        try:
            raw.anonymize()

            # -- Exit if passing object through function --
            if file is None:
                print('Processed anonymized file!')
                return raw

            else:
                # -- Create save path --
                if overwrite:
                    save_path = file
                else:
                    parts = file.split(os.sep)
                    save_path = os.sep.join(
                    ["fif_rm_chans_anon" if p == "fif" else p for p in parts])

                    # -- Exit if already saved --
                    if os.path.exists(save_path):
                        print(f"Skipping (already anonymized): {patientID} - {fileName}")
                        continue
                    else:
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # -- Save in directory of choice --
            raw.save(save_path, overwrite=True)
            print(f"Anonymized {patientID} - {fileName} in {time.time() - file_start:.1f} seconds")

        except Exception as exc:
            print(f"Skipped {patientID} - {fileName}: {exc}")

    print(f"\nTotal processing time: {time.time() - total_start:.1f} seconds")