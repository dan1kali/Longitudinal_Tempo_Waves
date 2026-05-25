import os
import mne
import time

def epochFifFiles(fifFileList,tmin=-0.2,tmax=0.5,baseline=(None, 0),
                  event_id=None,reject=None,resample_sfreq=None,overwrite=False):
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
            epochs = mne.Epochs(raw,
                                events,
                                event_id=event_ids_of_interest,
                                tmin=tmin,
                                tmax=tmax,
                                baseline=baseline,
                                preload=True,
                                reject=reject)

            if resample_sfreq is not None:
                epochs.resample(resample_sfreq)

            if file is None:
                print('Processed epochs!')
                return epochs
            
            else:
                parts = file.split(os.sep)
                save_path = os.sep.join(["fif_epochs" if p == "fif" else p for p in parts])
                save_path = save_path.replace(".fif", "-epo.fif")

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