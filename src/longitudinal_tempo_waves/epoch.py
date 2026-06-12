import os
import mne
import time
import numpy as np
import pandas as pd
from collections import defaultdict

def epochFifFiles(fifFileList,event_id=None, generate_controls_csv=None, tmin=-30*60,tmax=5*60,baseline=(None, 0),
                  reject=None,resample_sfreq=None,overwrite=False):
    """
    Epoch FIF files using MNE annotations and save as -epo.fif files.

    Works to process bulk or single files from filepaths only

    Parameters
    ----------
    fifFileList : list of str
        Input FIF files
    tmin, tmax : float
        Epoch time window (seconds)
    baseline : tuple or None
        Baseline correction window
    event_id : dict or None
        Mapping of annotation descriptions to event IDs
    reject : dict or None
        Rejection thresholds (e.g. {'eeg': 150e-6})
    resample_sfreq : float or None
        If set, resample epochs
    overwrite : bool
        Whether to overwrite existing epoch files
    """

    total_start = time.time()

    if generate_controls_csv is not None:
        timeMapping_df = pd.read_csv(generate_controls_csv)

    if not isinstance(fifFileList, list):
        fifFileList = [fifFileList]

    for item in fifFileList:

        file_start = time.time()

        if isinstance(item, mne.io.BaseRaw):
            raw = item
            file = None
        else:
            file = item
            fileName = os.path.splitext(os.path.basename(file))[0]
            patientID = os.path.basename(os.path.dirname(file))
            raw = mne.io.read_raw_fif(file, preload=True)

        try:
            if raw.annotations is None or len(raw.annotations) == 0:
                print(f"Skipping (no annotations): {patientID} - {fileName}")
                continue

            events, event_ids_of_interest = mne.events_from_annotations(raw,event_id=event_id) # type: ignore

            # Skip epochs that are within 2 hours of each other (keeps first)
            event_times = events[:, 0] / raw.info['sfreq']
            order = np.argsort(event_times)
            event_times = event_times[order]
            events = events[order]
            min_gap = 3600*2  # 2 hours
            kept_events = []
            last_time = -np.inf
            for ev, t in zip(events, event_times):
                if t - last_time >= min_gap:
                    kept_events.append(ev)
                    last_time = t
            events = np.array(kept_events)

            epochs = mne.Epochs(raw,
                                events,
                                event_id=event_ids_of_interest,
                                tmin=tmin,
                                tmax=tmax,
                                baseline=baseline,
                                preload=True,
                                reject=reject)


            # Skip epochs that are close to start of recording
            if len(epochs) == 0:
                print(f"Skipping (0 valid epochs): {patientID} - {fileName}")
                continue

            if resample_sfreq is not None:
                epochs.resample(resample_sfreq)

            if file is None:
                print('Processed epochs!')
                return epochs
            
            else:
                # generate corresponding control epochs
                if generate_controls_csv is not None:
                    filtered_fileList = [f for f in fifFileList if os.path.basename(os.path.dirname(f)) == patientID]
                    filtered_df = timeMapping_df[timeMapping_df["patient"] == patientID]
                    saveControlEpochs(fileName, filtered_fileList, filtered_df, events, 
                                        tmin=tmin,tmax=tmax)

                # save epochs
                parts = file.split(os.sep)
                save_path = os.sep.join(["fif_epochs" if "fif" in p and not p.endswith(".fif") else p for p in parts])
                save_path = save_path.replace("_raw.fif", "_epo.fif")

                if os.path.exists(save_path) and not overwrite:
                    print(f"Skipping (already epoched): {patientID} - {fileName}")
                    continue
                else:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                epochs.save(save_path, overwrite=True)
                print(f"Epochs saved: {patientID} - {fileName} in {time.time() - file_start:.1f} seconds")
                print("Events:", event_ids_of_interest)

        except Exception as exc:
            print(f"Skipped {patientID} - {fileName}: {exc}")
            
    print(f"\nTotal processing time: {time.time() - total_start:.1f} seconds")


def saveControlEpochs(file_name, filtered_fileList, timeMappingDF, events, 
                    tmin=-30*60,tmax=5*60,baseline=(None, 0),overwrite=False):
    start_time = time.time()
    file_map = {os.path.splitext(os.path.basename(f))[0]: f for f in filtered_fileList}
    
    patientID = timeMappingDF['patient'].iloc[0]

    # Get current file metadata
    row = timeMappingDF.loc[timeMappingDF["filename"] == file_name].iloc[0]
    session_id = row["session_id"]
    file_start = pd.to_timedelta(str(row["time_of_day"]))
    # restrict df to current session (in case there are 2+) 
    session_df = timeMappingDF[timeMappingDF["session_id"] == session_id].copy()

    # Compute recording intervals
    session_df["start_td"] = pd.to_timedelta(session_df["time_of_day"])
    session_df["end_td"] = session_df["start_td"] + pd.to_timedelta(
        session_df["recording_duration_sec"].astype(float),unit="s")

    raw = mne.io.read_raw_fif(file_map[file_name], preload=False)
    # For each seizure event, compute clock time
    event_times_sec = events[:, 0] / raw.info["sfreq"]
    event_clock_times = (file_start + pd.to_timedelta(event_times_sec, unit="s"))

    # Find matching control recordings
    control_map = []
    for event_clock in event_clock_times:
        matches = session_df[(session_df["start_td"] <= event_clock)
                            & (session_df["end_td"] > event_clock)]
        # optionally exclude the seizure file itself
        matches = matches[matches["filename"] != file_name]
        if len(matches) == 0:
            continue
        match = matches.iloc[0]

        # Convert clock time into sample position in control recording
        offset_sec = (event_clock - match["start_td"]).total_seconds()

        control_map.append({"event_time": event_clock,
                                    "control_file": match["filename"],
                                    "control_offset_sec": offset_sec})

    grouped = defaultdict(list)
    for m in control_map:
        grouped[m["control_file"]].append(m["control_offset_sec"])

    for control_file, offsets in grouped.items():

        if control_file not in file_map:
            print('Error: File missing from filelist')
            continue

        control_raw = mne.io.read_raw_fif(file_map[control_file], preload=True)
        sfreq = control_raw.info["sfreq"]
        control_events = []

        for off in offsets:
            sample = int(off * sfreq)
            if sample >= 0 and sample < control_raw.n_times:
                control_events.append([sample, 0, 99])

        control_events = np.array(control_events, dtype=int)
        event_id = {"control": 99}

        if len(control_events) == 0:
            continue

        control_epochs = mne.Epochs(control_raw,
                                    control_events,
                                    event_id=event_id,
                                    tmin=tmin,
                                    tmax=tmax,
                                    baseline=baseline,
                                    preload=True)
        
        parts = file_map[control_file].split(os.sep)
        save_path = os.sep.join(["fif_epochs_control" if "fif" in p and not p.endswith(".fif") else p for p in parts])
        save_path = save_path.replace("_raw.fif", "_epo.fif")

        if os.path.exists(save_path) and not overwrite:
            print(f"Skipping (already epoched): {patientID} - {file_name}")
            continue
        else:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

        control_epochs.save(save_path, overwrite=True)
        print(f"Control epochs saved: {patientID} - {file_name} in {time.time() - start_time:.1f} seconds")
        print("Control events:", control_epochs.event_id)
