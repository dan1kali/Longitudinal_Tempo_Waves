import os
from re import sub
import time
from turtle import lt
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator
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
        "patient": "units",
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
    patient_ID=None,
    figsize=(12, 1),
    use_session_relative_time=False,
    show=True):
    """
    Visualize EEG recording sessions from patient_time_mapping.csv.

    Parameters
    ----------
    csvPath : str
        Path to CSV file produced by your pipeline.
    
    patient_ID : str or None
        If provided, plots only one patient. Otherwise plots all patients.

    figsize : tuple
        Figure size.

    use_session_relative_time : bool
        If True, uses time_since_session_start_sec.
        If False, uses global time offset within patient.

    show : bool
        If True, calls plt.show() for each patient.
    """

    # -------------------------
    # LOAD DATA
    # -------------------------
    df = pd.read_csv(csvPath)

    # Remove units row
    df = df[~df["patient"].isin(["string", "units"])].copy()

    # Type safety
    df["session_id"] = df["session_id"].astype(int)
    df["session_order"] = df["session_order"].astype(int)

    df["time_elapsed_sec"] = df["time_elapsed_sec"].astype(float).round(1)
    df["time_since_prev_sec"] = df["time_since_prev_sec"].astype(float).round(1)
    df["recording_duration_sec"] = df["recording_duration_sec"].astype(float).round(1)

    # Optional patient filtering if selected, else selects all
    patients = sorted(df["patient"].dropna().unique())

    if patient_ID is not None:
        # multiple inputs
        if isinstance(patient_ID, (list, tuple, set)):
            if len(patient_ID) == 0:
                patient_ids = patients
            else:
                first = patient_ID[0]  # type: ignore
                if isinstance(first, str):
                    patient_ids = list(patient_ID)
                else:
                    patient_ids = [patients[i - 1] for i in patient_ID]
        elif isinstance(patient_ID, str):
            patient_ids = [patient_ID]
        elif isinstance(patient_ID, int):
            patient_ids = [patients[patient_ID - 1]]
    else:
        patient_ids = patients

    df = df[df["patient"].isin(patient_ids)].copy()

    # -------------------------
    # PLOT 
    # -------------------------

    n_patients = len(patient_ids)

    fig, axes = plt.subplots(
        n_patients,
        1,
        figsize=(figsize[0], max(2, n_patients * figsize[1])),
        # constrained_layout=True,
        sharex=True  # enforce shared x-axis
    )

    if n_patients == 1:
        axes = [axes]

    # compute global xmax
    global_xmax = 0

    for pat in patient_ids:
        sub = df[df["patient"] == pat]

        if not use_session_relative_time:
            def hms_to_seconds(t):
                h, m, s = map(int, t.split(':'))
                return h * 3600 + m * 60 + s

            first_time_sec = hms_to_seconds(sub["time_of_day"].iloc[0])

            end = (
                first_time_sec
                + (sub["time_elapsed_sec"] + sub["recording_duration_sec"]).max()
            ) / 3600
        else:
            end = (
                sub["time_elapsed_sec"]
                + sub["recording_duration_sec"]
            ).max() / 3600

        global_xmax = np.ceil(max(global_xmax, end) / 12) * 12

    # Plotting
    for ax, pat in zip(axes, patient_ids):

        sub = df[df["patient"] == pat].copy()

        sessions = sorted(sub["session_id"].unique())
        y_positions = np.linspace(-1.2, 1.2, len(sessions) + 2)[1:-1]
        y_map = {s: y_positions[i] for i, s in enumerate(sessions)}

        colors = cm.get_cmap("tab10", len(sessions))

        # session-level time conversion helper
        def hms_to_seconds(t):
            h, m, s = map(int, t.split(':'))
            return h * 3600 + m * 60 + s

        session_first_time = (
            sub.groupby("session_id")["time_of_day"]
            .first()
            .apply(hms_to_seconds)
        )

        # ---------------------------------------------------------
        # BUILD SESSION SPANS
        # ---------------------------------------------------------
        session_spans = {}

        for s in sessions:
            g = sub[sub["session_id"] == s]
            first_time_sec = session_first_time.loc[s]

            if use_session_relative_time:
                start_s = g["time_elapsed_sec"].min() / 3600
                end_s = (g["time_elapsed_sec"] + g["recording_duration_sec"]).max() / 3600
            else:
                start_s = (first_time_sec + g["time_elapsed_sec"].min()) / 3600
                end_s = (first_time_sec + (g["time_elapsed_sec"] + g["recording_duration_sec"]).max()) / 3600

            session_spans[s] = (start_s, end_s)

        # ---------------------------------------------------------
        # ROW-LEVEL PLOTTING
        # ---------------------------------------------------------
        for _, row in sub.iterrows():

            y = y_map[row["session_id"]]

            # event start (row-level)
            if use_session_relative_time:
                start = row["time_elapsed_sec"] / 3600
            else:
                start = (
                    session_first_time.loc[row["session_id"]]
                    + row["time_elapsed_sec"]
                ) / 3600

            duration = row["recording_duration_sec"] / 3600

            # timeline span
            start_s, end_s = session_spans[row["session_id"]]

            ax.barh(
                y=y,
                width=end_s - start_s,
                left=start_s,
                height=(1.6 - 0.2 * len(sessions)) / len(sessions) if len(sessions) > 1 else 1.5,
                color="lightblue",
                alpha=0.25,
                zorder=2)

            # recording segments
            ax.barh(
                y=y,
                width=duration,
                left=start,
                height=(1.6 - 0.4 * len(sessions)) / len(sessions) if len(sessions) > 1 else 1,
                color=colors(y),
                zorder=3)

        # formatting
        ax.set_yticks(list(y_map.values()))
        ax.set_yticklabels([str(s) for s in sessions])
        ax.set_title(f"{pat}",fontsize=10)
        ax.grid(True, axis="x", linestyle="--", alpha=0.5)

        # day shading
        for i, day_start in enumerate(np.arange(24, global_xmax + 24, 24)):
            if i % 2 == 0:
                ax.axvspan(
                    day_start,
                    day_start + 24,
                    color="gray",
                    alpha=0.2,
                    zorder=0)

        # ax.set_ylim(-0.1, len(sessions) - 0.9) # spacing of y axis
        ax.set_ylim(-1, 1) # spacing of y axis
        ax.xaxis.set_major_locator(MultipleLocator(6))
        ax.set_xlim(0, global_xmax)

    plt.xlabel("Time (hours)")
    fig.suptitle("Recording Timeline")

    legend_handles = [Patch(facecolor="lightblue", alpha=0.45, label="Session window"),
                    Patch(facecolor=colors(y), alpha=0.8, label="Recording segments"), # type: ignore
                    Patch(facecolor="lightgray", alpha=0.8, label="Days")]

    fig.legend(handles=legend_handles,
        loc="lower center",
        # bbox_to_anchor=(0.5, 0.0),
        bbox_to_anchor=(0.5, 0),
        ncol=3)

    fig.tight_layout(rect=[0, 0.03, 1, 1]) # type: ignore

    # use with contrained layout
    # plt.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, -0.55), ncol=3,) # spreads legend horizontally )
    
    if show:
        plt.show()

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