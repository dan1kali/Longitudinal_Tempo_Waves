# Longitudinal Tempo Waves

Simple package to analyze travelling waves in longitudinal epilepsy EEG data. Managed with `uv`.

## Setup

1. **Create and activate a virtual environment using `uv`:**

   ```bash
   uv sync
   source .venv/bin/activate
   ```

2. **Install in editable mode:**

   ```bash
   uv pip install -e .
   ```

This allows the test scripts to import modules from `src`.

---

## Intro

This repository is intended to be used with long-term EEG data of epileptic patients, where multiple recordings are recorded on the same patient over the course of up to 5 days, and has processing steps from the most raw data in the form of `.trc` files. Using metadata stored within the `.trc` file, this pipeline allows for recordings to be aligned to each other relative to the 5-day session and for useful visualizations to be drawn of the recording timeline. Within one patient, annotation data can be extracted and understood across that patient's files so future analyses can examine more effectively across longitudinal data.

Additionally, data processing steps are able to be performed in bulk by specifying only the parent data folder, which houses patient folders, which house individual data files. Steps include anonymization, annotation relabeling, and epoching around seizure events.

---

## How to Use

Functions are stored in `src/longitudinal_tempo_waves/` and are callable from scripts in `tests/`.

All data and `.csv` files containing metadata are saved in the `Data/` subfolder.

### 1. Configure the data directory

Update `config.py` with the desired base save path for all data and metadata.

**Recommended path:**

```python
'/path/to/this/repo/Data'
```

### 2. Run the processing scripts

#### `1_convert.py`

Convert raw TRC data to FIF using `TRCtoFIF`.

- `.trc` files must first live in a directory called `trc` within the base path specified above.
- `.fif` files are saved in their own folder in the same path, along with all future intermediate outputs.

##### `1.1_anonymize.py`

Use this if files are not yet anonymized.

1. Generate longitudinal metadata with `exportTimeMapping`, saved as a `.csv` file in the base path.
2. Optionally visualize the metadata.
3. Bulk anonymize files using `anonymizeFifFiles`.

---

#### `2_annotate.py`

##### If annotations contain Unicode issues

- Clean Unicode from annotations and reannotate files in bulk.
- Generate metadata containing the unique list of annotations, along with the corresponding patient and file names, using `compileAnnotationsFromFilelist`.
- This generates `all_annotations.csv`.

##### If annotations are not standardized

Generate a rename dictionary using one of two methods.

**Method 1 (recommended)**

Use the preset rules in `normalizeFifAnnotations` (defined in `annotate.py`) by running:

`generateAnnotationTable`

This creates `annotations_table.csv`.

**Method 2 (manual)**

Edit the `final_label` column in `annotations_table.csv` yourself.

Then bulk relabel annotations using:

`relabelFifAnnotations`

##### `2.1_visualize.py`

Visually inspect files (red dots indicate `"crise"` annotations).

1. **`visualizeRecordingTimeline`**
   - Displays how recordings are distributed throughout the approximately 5-day session.
   - Multiple patients can be displayed simultaneously (up to approximately 9 is recommended, depending on screen size).

2. **`visualizeAnnotationTimeline`**
   - Displays how annotations are distributed across files for a single patient.

---

#### `3_epoch.py`

Generate epochs around seizure events labeled `"crise"` and corresponding control epochs.

It is recommended to first visually inspect recordings and generate a list of patients or files to analyze.

By default:

- Epochs are generated for the 30 minutes preceding each seizure event.
- Epochs are generated only if uninterrupted by the beginning of the recording.
- Epochs within 2 hours of each other are skipped (the first is kept).

For each patient, one or more (or none) control epochs are also generated when `timeMappingCsv.csv` is provided. These correspond to the same time that the seizure event was labeled but on a different day within the entire 5-day recording timeline.

Epochs are saved as `-epo.fif` files.

---

#### Other scripts

##### `0.1_figures.py`

Generate summary figures with statistics about the dataset.

---

## Quickstart

1. Convert raw TRC data to FIF using `TRCtoFIF`.
2. Generate longitudinal metadata with `exportTimeMapping`.
3. Visualize recordings and annotations using `visualizeRecordingTimeline` and `visualizeAnnotationTimeline`.
4. Compile annotations with `compileAnnotationsFromFilelist`, generate standardized labels with `generateAnnotationTable`, and relabel using `relabelFifAnnotations`.
5. Create seizure and control epochs with `epochFifFiles`.