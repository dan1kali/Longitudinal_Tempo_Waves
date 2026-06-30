# Longitudinal Tempo Waves

Simple package to analyze travelling waves in longitudinal epilepsy EEG data.
Managed with `uv`.

## Setup

1. **Create and activate virtual environment using uv**:

   ```bash
   uv sync
   source .venv/bin/activate
   ```

2. **Install in editable mode**:

   ```bash
   uv pip install -e .
   ```

This allows the test scripts to import modules from `src`.

## Intro

This repository is intended to be used with long-term EEG data of epileptic patients, where multiple recordings are recorded on the same patient over the course of up to 5 days, and has processing steps from the most raw data in the form os .trc files. Using metadata stored within the .trc file, this pipeline allows for recordings to be aligned to each other relative to the 5-day session and for useful visualizations to be drawn of the recording timeline, and within one patient, for annotation data to be extracted and understood across that patient's files, so future analyses can examine more effectively across longitudinal data.

Additionally, data processing steps are able to be performed in bulk by specifying only the parent data folder, which houses patient folders, which house individual data files. Steps include anonymization, annotation relabeling, and epoching around seizure events.

## How to Use

Functions are stored in `src/longitudinal_tempo_waves/` folder and callable in scripts used in `tests/` folder.

All data and `.csv` files containing metadata are saved in subfolder called `Data/`.

1. Update `config.py` file with desired base save path for all data/metadata!!! Recommended path is:

   ```python
   '/path/to/this/repo/Data'
   ```

2. Then simply use scripts from `tests/` to process data. In all scripts, simply the folder that patient

### `1_convert.py`

Convert raw TRC data to FIF using `TRCtoFIF()`, `.trc` files must first live in directory called `trc` saved in the base path from step 1. `.fif` files will save in their on folder in the same path, as will all future intermediates in future steps.

#### `1.1_anonymize.py`

Use this if files are not yet anonymized:

- First, generate longitudinal metadata with `exportTimeMapping()` saved in `.csv` file in base path.
- Optionally visualize.
- Then, bulk anonymize files using `anonymizeFifFiles()`.

### `2_annotate.py`

Use if annotations are messy with unicode:

- Clean unicode from annotations, and reannotates in bulk.
- Generate metadata storing unique list of all annotations, and corresponding patient and file names using `compileAnnotationsFromFilelist()` --> generates `all_annotations.csv`

Use if annotations are not standardized:

- To prepare for relabeling, generate rename dictionary using one of two methods:
  - (1) recommended: (using rules pre-set in def `normalizeFifAnnotations()` in `annotate.py`) using `generateAnnotationTable()` --> saves `annotations_table.csv`
  - (2) manual: simply edit `final_label` column in `annotations_table.csv` yourself
- then bulk relabel using `relabelFifAnnotations()`

#### `2.1_visualize.py`

Visually inspect files (red dot indicates "crise" annotation) using:

1. `visualizeRecordingTimeline()` to see how files are spread throughout time within ~5-day sessions. Specify multiple patients, up to ~9 depending on size of computer screen is recommended, or
2. `visualizeAnnotationTimeline()` to see how annotations are distributed within a single patient and their files.

### `3_epoch.py`

- Generate epochs around seizure events labeled with "crise", and control epochs. Best to first visually examine files and generate a list of specific patients to generate epochs for by specifying best patients or files to examine.
- By default, epochs are generated for 30min preceding the seizure event, and only if uninterrupted by the beginning of the recording, and skips epochs that are within 2 hours of each other (keeps the first).
- For each patient, one or more (or none) control epochs are also generated when `timeMappingCsv.csv` is an input, which generates epochs which correspond to the same time that the seizure event was labeled but on a different day in the entire 5-day recording timeline.
- Files are saved as `-epo.fif` files.

### Other

#### `0.1_figures.py`

- Generate simply figures with statistics about the data.

## Quickstart

1. Convert raw TRC data to FIF using `TRCtoFIF()`
2. Generate longitudinal metadata with `exportTimeMapping()`
3. Visualize recordings or annotations with `visualizeRecordingTimeline()` and `visualizeAnnotationTimeline()`
4. Compile annotations with `compileAnnotationsFromFilelist()`, and `generateAnnotationTable()` --> `relabelFifAnnotations()` to relabel
5. Create epochs and control epochs with `epochFifFiles()`