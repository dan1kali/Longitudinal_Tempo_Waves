import os
from natsort import natsorted
import matplotlib.pyplot as plt
from longitudinal_tempo_waves.mixed_micromed_io.mixed_to_mne import create_mne_from_mixed_micromed_recording

# eeg_file = '/Users/macbook/Work/DugueLab/TEMPO_EEG_SAMPLE/20min/PAT_69/EEG_141890.TRC' # 20 min
# eeg_file = '/Users/macbook/Work/DugueLab/TEMPO_EEG_SAMPLE/long_duration/PAT_374/EEG_13619.TRC' # long duration

patient_index = 1
file_index = 1
duration = 'long_duration'  # or '20min or 'long_duration'
folder = '/Users/macbook/Work/DugueLab/Longitudinal_Tempo_Waves/Data'

patient = natsorted([d for d in os.listdir(os.path.join(folder, duration)) if d.startswith('PAT_')])[patient_index-1]
files = natsorted([f for f in os.listdir(os.path.join(folder, duration, patient)) if f.endswith('.TRC')])
eeg_file = os.path.join(folder, duration, patient, files[file_index-1])

mne_data = create_mne_from_mixed_micromed_recording(eeg_file)
mne_data.load_data()
mne_data.plot()


print('\n\n',"Patient:", patient,'\n\n')
# print("Number of channels:", len(mne_data.info['ch_names']),'\n\n')
# print("Channel names:", mne_data.info['ch_names'], '\n\n')
# print("Channel types:", mne_data.get_channel_types(), '\n\n')
total_time_sec = mne_data.n_times / mne_data.info['sfreq']
print(f"Total time: {int(total_time_sec // 60)}m {int(total_time_sec % 60)}s", '\n\n')

plt.show()



# from micromed_io.to_mne import create_mne_from_micromed_recording
# eeg_file = ''
# raw = create_mne_from_micromed_recording(eeg_file)
# raw.load_data()
# raw.plot()
# plt.show()





# all_annotations = []

# for file in glob.glob('/home/anton/Documents/TEST_DATA/*'):

#     try:

#         raw = mne.io.read_raw(file, preload=False)

#         annotations = set(raw.annotations.description.tolist())

#         all_annotations.extend(annotations)

#     except Exception as exc:

#         print(f"Skipped {raw}: {exc}")

# set(all_annotations)
 

# save in a CSV file