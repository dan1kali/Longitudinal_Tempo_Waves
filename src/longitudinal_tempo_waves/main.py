# import mne
# from neo.io

import matplotlib.pyplot as plt
from longitudinal_tempo_waves.mixed_micromed_io.mixed_to_mne import create_mne_from_mixed_micromed_recording


# # for the easy to convert ones
# from micromed_io.to_mne import create_mne_from_micromed_recording
# eeg_file = '/Users/macbook/Work/DugueLab/TEMPO_EEG_SAMPLE/20min/PAT_69/EEG_141890.TRC' # 20 min
# # eeg_file = '/Users/macbook/Work/DugueLab/TEMPO_EEG_SAMPLE/long_duration/PAT_374/EEG_13619.TRC' # long duration
# raw = create_mne_from_micromed_recording(eeg_file)
# raw.load_data()
# raw.plot()

# plt.show()


# eeg_file = '/Users/macbook/Work/DugueLab/TEMPO_EEG_SAMPLE/20min/PAT_69/EEG_141890.TRC' # 20 min
eeg_file = '/Users/macbook/Work/DugueLab/TEMPO_EEG_SAMPLE/long_duration/PAT_374/EEG_13619.TRC' # long duration
mne_data = create_mne_from_mixed_micromed_recording(eeg_file)
mne_data.load_data()
mne_data.plot()

print(mne_data.info['ch_names'], '\n')
plt.show()