from operator import sub

from natsort import natsorted
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from project.helper import resolveSelection
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator
import matplotlib.cm as cm
import numpy as np


def visualizeRecordingTimeline(
    csvPath,
    patient_ID=None,
    annotation_df=None,
    show=True,
    figsize=(8, 1),
    use_session_relative_time=False,):
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
        sessionspan_check = set()
        for _, row in sub.iterrows():

            y = y_map[row["session_id"]]

            # event start (row-level)
            if use_session_relative_time:
                start = row["time_elapsed_sec"] / 3600
            else:
                start = (session_first_time.loc[row["session_id"]]
                        + row["time_elapsed_sec"]) / 3600

            duration = row["recording_duration_sec"] / 3600

            # timeline span
            if s not in sessionspan_check:
                start_s, end_s = session_spans[s]
                ax.barh(
                    y=y,
                    width=end_s - start_s,
                    left=start_s,
                    height=(1.6 - 0.2 * len(sessions)) / len(sessions) if len(sessions) > 1 else 1.5,
                    color="lightblue",
                    alpha=0.5,
                    zorder=2)
                sessionspan_check.add(s)

            # recording segments
            ax.barh(
                y=y,
                width=duration,
                left=start,
                height=(1.6 - 0.4 * len(sessions)) / len(sessions) if len(sessions) > 1 else 1,
                color=colors(y),
                zorder=3)

            if annotation_df is not None:
                ann_sub = annotation_df[annotation_df["filename"] == row["filename"]]
                for _, ann in ann_sub.iterrows():
                    ann_x = start + ann["onset"] / 3600
                    ax.scatter(ann_x,
                                y,
                                color='red',
                                s=10,
                                zorder=4)
            
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

        ax.set_ylim(-1, 1) # spacing of y axis
        ax.xaxis.set_major_locator(MultipleLocator(6))
        ax.set_xlim(0, global_xmax)

    plt.xlabel("Time (hours)")
    fig.suptitle("Recording Timeline")

    legend_handles = [Patch(facecolor="lightblue", alpha=0.45, label="Session window"),
                    Patch(facecolor=colors(y), alpha=0.8, label="Recording segments"), # type: ignore
                    Patch(facecolor="lightgray", alpha=0.8, label="Days")]
    

    if annotation_df is not None:
        legend_handles.append( 
            Line2D([0], [0],
                marker='o',
                color='w',
                markerfacecolor='red',
                markersize=5,
                label='Annotations') ) # type: ignore

    fig.legend(handles=legend_handles,
        loc="lower center",
        # bbox_to_anchor=(0.5, 0.0),
        bbox_to_anchor=(0.5, 0),
        ncol=4)

    fig.tight_layout(rect=[0, 0.03, 1, 1]) # type: ignore

    # use with contrained layout
    # plt.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, -0.55), ncol=3,) # spreads legend horizontally )
    
    if show:
        plt.show()

    return df


def visualizeAnnotationTimeline(
    file_path,
    patient_ID=None,
    filename_list=None,
    figsize=(12, 1.2),
    show=True
):
    if file_path.endswith(".parquet"):
        df = pd.read_parquet(file_path)
    elif file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        raise ValueError("Unsupported file format")

    # -----------------------
    # UNIVERSES
    # -----------------------
    all_files = natsorted(df["filename"].unique())
    all_patients = natsorted(df["patient"].unique())

    # -----------------------
    # RESOLVE INPUTS
    # -----------------------
    patient_ID = resolveSelection(patient_ID, all_patients, "patient_ID")
    filename_list = resolveSelection(filename_list, all_files, "filename")

    # -----------------------
    # FILTER
    # -----------------------
    df = df[df["patient"].isin(patient_ID)]
    df = df[df["filename"].isin(filename_list)]

    files = natsorted(df["filename"].unique())

    # -----------------------
    # PLOT SETUP
    # -----------------------
    fig, ax = plt.subplots(
        1, 1,
        figsize=(figsize[0], max(figsize[1], 0.5 * len(files)))
    )

    y_map = {f: i for i, f in enumerate(files)}

    ann_types = df["annotation"].astype(str).unique()
    cmap = plt.cm.get_cmap("tab20", len(ann_types))
    ann_color = {a: cmap(i) for i, a in enumerate(ann_types)}

    # -----------------------
    # PLOT
    # -----------------------
    for f in files:
        sub = df[df["filename"] == f]
        y = y_map[f]

        rec_duration_hr = sub["recording_duration"].iloc[0] / 3600

        ax.barh(
            y=y,
            left=0,
            width=rec_duration_hr,
            height=0.6,
            color="lightblue",
            alpha=0.3
        )

        for _, row in sub.iterrows():
            x = row["onset"] / 3600
            color = ann_color.get(row["annotation"], "black")

            ax.scatter(x, y, color=color, s=20, zorder=3)

            if pd.notna(row["event_duration"]) and row["event_duration"] > 0:
                ax.hlines(
                    y=y,
                    xmin=x,
                    xmax=(row["onset"] + row["event_duration"]) / 3600,
                    color=color,
                    linewidth=2,
                    alpha=0.7
                )

    # -----------------------
    # FORMATTING
    # -----------------------
    ax.set_yticks(list(y_map.values()))
    ax.set_yticklabels(files)
    ax.set_xlabel("Time (hours)")
    ax.set_title("Recording + Annotation Timeline")
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    handles = [
        Line2D([0], [0], marker='o', color='w',
               markerfacecolor=ann_color[a],
               label=a, markersize=6)
        for a in ann_types
    ]

    ax.legend(handles=handles, title="Annotations",
              bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()

    if show:
        plt.show()

    return df