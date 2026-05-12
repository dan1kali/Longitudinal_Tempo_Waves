import os
import traceback
import mne
import time
from natsort import natsorted
from longitudinal_tempo_waves.mixed_micromed_io.mixed_to_mne import create_mne_from_mixed_micromed_recording

def ObtainEEGFilePaths(basePath, patient_index=None, file_index=None):
    eegFileList = []
    patientList = natsorted([
        d for d in os.listdir(basePath) if d.startswith('PAT_')])

    for p_idx, patient in enumerate(patientList, start=1):
        alFiles = natsorted([
            f for f in os.listdir(os.path.join(basePath, patient))
            if f.startswith('EEG_')])

        for f_idx, file in enumerate(alFiles, start=1):
            if patient_index is not None:
                if isinstance(patient_index, (list, tuple, set)):
                    if p_idx not in patient_index:
                        continue
                else:
                    if p_idx != patient_index:
                        continue
            if file_index is not None and f_idx != file_index:
                continue

            eegFileList.append(os.path.join(basePath, patient, file))

    return eegFileList, patientList

def TRCtoFIF(eegFileList, fifFileList, saveFIF=True, anonymize=True, 
             removeChannels=False, channelsToRemove =[],prefixesToRemove=[], suffixesToRemove=[]):
    
    if not isinstance(eegFileList, list):
        eegFileList = [eegFileList]
        fifFileList = [fifFileList]

    total_start = time.time()
    failedFiles = []

    for f in range(len(eegFileList)):
        file_start = time.time()
        eegFilePath = eegFileList[f]
        fifFilePath = fifFileList[f]

        fileName = os.path.splitext(os.path.basename(eegFilePath))[0]
        patientID = os.path.basename(os.path.dirname(eegFilePath))
        
        try:

            if os.path.exists(fifFilePath):
                print(f"Skipping, already exists: {patientID} - {fileName}")
                continue
            else:
                os.makedirs(os.path.dirname(fifFilePath), exist_ok=True)
                print(f'\nProcessing: {patientID} - {fileName}')

            raw = create_mne_from_mixed_micromed_recording(eegFilePath)
            # raw.load_data()
            # raw.plot()
            # plt.show()
            
            if saveFIF:
                if anonymize:
                    raw.anonymize()
                if removeChannels:
                    raw = removeBadChannels(raw, channelsToRemove, prefixesToRemove, suffixesToRemove)
                raw.save(fifFilePath, overwrite=True)
                print(f'Saved {patientID} - {fileName} as .fif! in {time.time() - file_start:.1f} seconds')
        
        except Exception as e:
            print(f"\nError processing {patientID} - {fileName}: {e}")
            traceback.print_exc()

            failedFiles.append((patientID, fileName, str(e)))
            continue  # move to next file

    print(f"\nTotal processing time: {time.time() - total_start:.1f} seconds")

        # print("Number of channels:", len(fifFile.info['ch_names']),'\n\n')
        # print("Channel names:", fifFile.info['ch_names'], '\n\n')
        # print("Channel types:", fifFile.get_channel_types(), '\n\n')
        # total_time_sec = fifFile.n_times / fifFile.info['sfreq']
        # print(f"Total time: {int(total_time_sec // 60)}m {int(total_time_sec % 60)}s", '\n\n')

    if failedFiles:
        print("\nSummary of failed files:")
        for patientID, fileName, err in failedFiles:
            print(f"- {patientID} - {fileName}: {err}")

def uniqueChannels(fifFileList):
    unique_chans = set()
    for file in fifFileList:
        raw = mne.io.read_raw_fif(file, preload=False)
        unique_chans.update(raw.info['ch_names'])
    return natsorted(unique_chans)

def removeBadChannels(fifFileList, channelsToRemove, prefixesToRemove=[], suffixesToRemove=[], overwrite=False):
    """
    Removes bad channels from .fif files and saves to a directory called 'fif_rm_chans'

    Processes in bulk for filepaths or for single MNE Raw object (returns object)

    Parameters
    ----------
    fifFileList : list of str
        Paths to input .fif files
    bad_channel_list : list of str
        List of channel names to remove
    badChanPrefixes : list of str, optional
        List of prefixes for channels to remove
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
            # -- Determine channels and remove --
            existing_bad_channels = [ch for ch in channelsToRemove if ch in raw.ch_names]
            prefix_channels = [ch for ch in raw.ch_names
                if any(ch.lower().startswith(prefix.lower()) for prefix in prefixesToRemove)]
            suffix_channels = [ch for ch in raw.ch_names
                if any(ch.lower().endswith(suffix.lower()) for suffix in suffixesToRemove)]
            
            existing_bad_channels = natsorted(set(existing_bad_channels + prefix_channels + suffix_channels))
            if not existing_bad_channels:
                print("\nSkipping (no bad channels found)\n")
                continue
            
            raw.drop_channels(existing_bad_channels)

            # -- Exit if passing single object through function --
            if file is None:
                print('Removed extra channels from file!')
                return raw

            # --- Save path ---
            if overwrite:
                save_path = file
            else:
                parts = file.split(os.sep)
                save_path = os.sep.join(["fif_rm_chans" if p == "fif" else p for p in parts])
                
                # -- Exit if already saved --
                if os.path.exists(save_path):
                    print(f"Skipping (already removed channels): {patientID} - {fileName}")
                    continue
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # -- Save in directory of choice --
            raw.save(save_path, overwrite=True)
            print(f'\nRemoved bad channels from {patientID} - {fileName}  in {time.time() - file_start:.1f} seconds\n')

        except Exception as exc:
            print(f"Skipped {patientID} - {fileName}: {exc}")
    
    print(f"\nTotal processing time: {time.time() - total_start:.1f} seconds")
