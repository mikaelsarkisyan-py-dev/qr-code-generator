# Team project

import pandas as pd
from tkinter.messagebox import showerror, showinfo
import matplotlib.pyplot as plt
from datetime import datetime
import uuid
import os

LOG_FILE = "qr_generation_log.csv"

LOG_COLUMNS = [
    "timestamp",
    "id",
    "text_content",
    "version",
    "error_correction_level",
    "mask_pattern",
    "user_options",
    "inverted",
    "success"
]


def _ensure_log_file():
    """
    Ensure the CSV log file exists with the proper columns.
    """
    if not os.path.exists(LOG_FILE):
        df = pd.DataFrame(columns=LOG_COLUMNS)
        df.to_csv(LOG_FILE, index=False)


def log_qr_generation(
    text_content: str,
    version: int,
    ecl: str,
    mask_pattern: int,
    user_options: dict,
    inverted: bool,
    success: bool
):
    """
    Log a QR generation attempt.
    """
    _ensure_log_file()

    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "id": str(uuid.uuid4()),
        "text_content": text_content + " ",
        "version": version,
        "error_correction_level": ecl,
        "mask_pattern": mask_pattern,
        "user_options": str(user_options),
        "inverted": inverted,
        "success": success
    }

    df = pd.read_csv(LOG_FILE)
    df.loc[len(df)] = entry
    df.to_csv(LOG_FILE, index=False)


def load_logs() -> pd.DataFrame:
    """
    Load logs as a pandas DataFrame.
    """
    _ensure_log_file()
    return pd.read_csv(LOG_FILE)


def clear_logs():
    """
    Clear the CSV log file completely.
    """
    df = pd.DataFrame(columns=LOG_COLUMNS)
    df.to_csv(LOG_FILE, index=False)
    showinfo("Success", message="Log file cleared successfully!")


# ------------------------------
# Analytics visualisations
# ------------------------------

def show_ecl_frequency():
    """
    Display a bar chart of ECC usage frequency.
    Shows only this figure.
    """
    df = load_logs()
    if df.empty:
        showerror("Error", message="Log file is empty!")
        return

    counts = df["error_correction_level"].value_counts()

    fig, ax = plt.subplots()
    ax.bar(counts.index, counts.values, color='skyblue')
    ax.set_title("Error Correction Level Usage Frequency")
    ax.set_xlabel("Error Correction Level")
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.show()


def show_success_failure_over_time():
    """
    Display a minute-by-minute line chart of success vs failure QR generations.
    Success and failure are plotted with crosses and connected with lines.
    Shows only this figure.
    """
    df = load_logs()
    if df.empty:
        showerror("Error", message="Log file is empty!")
        return

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    # Round timestamps to the nearest minute
    df["minute"] = df["timestamp"].dt.floor("min")  # floor to minute

    # Group by minute and success/failure
    grouped = df.groupby(["minute", "success"]).size().unstack(fill_value=0)

    # Ensure both success and failure columns exist
    if True not in grouped.columns:
        grouped[True] = 0
    if False not in grouped.columns:
        grouped[False] = 0

    grouped = grouped.sort_index()

    fig, ax = plt.subplots()
    # Plot failure first
    ax.plot(grouped.index, grouped[False], 'r-x', label="Failure", markersize=6)
    # Plot success
    ax.plot(grouped.index, grouped[True], 'g-x', label="Success", markersize=6)

    ax.set_title("QR Generation Success vs Failure Over Time (Minute-by-Minute)")
    ax.set_xlabel("Time")
    ax.set_ylabel("Count")
    ax.legend()
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    fig.show()
