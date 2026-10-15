# -*- coding: utf-8 -*-
"""
Created on Fri Jun 12 14:54:58 2026

@author: MNEREA
"""

# -*- coding: utf-8 -*-
from asammdf import MDF, Signal
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
import re
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import shutil
import os
# =====================================================
# HELPER
# =====================================================
def select_root_folder(default_folder=None):
    """
    Open folder selection dialog and return selected folder as Path.
    """
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    if default_folder is None:
        selected_folder = filedialog.askdirectory(
            title="Select root folder containing MDF/MF4/DAT files"
        )
    else:
        selected_folder = filedialog.askdirectory(
            title="Select root folder containing MDF/MF4/DAT files",
            initialdir=str(default_folder)
        )

    root.destroy()

    if selected_folder == "":
        raise Exception("No folder selected. Script stopped.")

    return Path(selected_folder)

def safe_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return name


def make_img_name(file_stem, t_value, before_after):
 
    if isinstance(t_value, str):
        t_txt = t_value
    else:
        t_txt = f"{t_value:.1f}"

    return f"{file_stem}~(t={t_txt})_{before_after}.png"

def make_axle_img_name(file_stem, axle_name, t_value, before_after):
    if isinstance(t_value, str):
        t_txt = t_value
    else:
        t_txt = f"{t_value:.1f}"

    return f"{file_stem}_{axle_name}~(t={t_txt})_{before_after}.png"

def win_long_path(path):
    """
    Convert normal Windows/UNC path to long-path format.

    Keeps the same final folder and same filename.
    Only changes how Windows accesses the path internally.
    """
    path = str(Path(path))

    # Already long-path format
    if path.startswith("\\\\?\\"):
        return path

    # UNC path: \\server\share\folder -> \\?\UNC\server\share\folder
    if path.startswith("\\\\"):
        return "\\\\?\\UNC\\" + path.lstrip("\\")

    # Local path: C:\folder -> \\?\C:\folder
    return "\\\\?\\" + path
def finish_plot(fig_dir=None, filename=None, show_plots=True):
    plt.grid()
    plt.tight_layout()

    saved_path = None

    if fig_dir is not None and filename is not None:
        fig_dir = Path(fig_dir)

        # Final path keeps exactly your existing naming style
        safe_name = safe_filename(filename)
        saved_path = fig_dir / safe_name

        try:
            # =====================================================
            # 1) Ensure final network folder exists using long path
            # =====================================================
            os.makedirs(win_long_path(fig_dir), exist_ok=True)

            # =====================================================
            # 2) Save first to short local temp path
            #    This avoids matplotlib failing directly on long UNC path.
            # =====================================================
            temp_dir = Path(r"C:\Temp\TorqueCleaner_Plots")
            temp_dir.mkdir(parents=True, exist_ok=True)

            temp_path = temp_dir / safe_name

            plt.savefig(temp_path, dpi=150)

            # =====================================================
            # 3) Copy local file to final UNC path using Windows long path
            # =====================================================
            shutil.copy2(
                str(temp_path),
                win_long_path(saved_path)
            )

            # =====================================================
            # 4) Remove local temp image
            # =====================================================
            try:
                temp_path.unlink()
            except Exception:
                pass

            print("Saved image:", saved_path)

        except Exception as e:
            print("FAILED IMAGE SAVE:", saved_path)
            print("ERROR:", e)
            raise

    if show_plots:
        plt.show()
    else:
        plt.close()

    return saved_path


def save_full_processed_axles_plots(axle_plot_data_all, fig_dir, file_stem, show_plots=False):
    """
    Save one full-range BEFORE and AFTER plot using processed data
    returned from process_axle(), not raw MDF rereading.
    """

    if len(axle_plot_data_all) == 0:
        print("No processed axle data -> skip t=_all plots")
        return []

    # common x/y from processed ORIGINAL signals
    all_t = []
    all_y = []

    for d in axle_plot_data_all:
        all_t.append(d["t"])
        all_y.append(d["y_left_orig"])
        all_y.append(d["y_right_orig"])

    all_t = np.concatenate(all_t)
    all_y = np.concatenate(all_y)

    x_min = np.min(all_t)
    x_max = np.max(all_t)

    y_min = np.min(all_y)
    y_max = np.max(all_y)
    y_margin = 0.05 * (y_max - y_min) if y_max > y_min else 1.0

    common_xlim = (x_min, x_max)
    common_ylim = (y_min - y_margin, y_max + y_margin)

    log_rows = []

    # =====================================================
    # FULL ORIGINAL BEFORE FROM PROCESSED AXLE DATA
    # =====================================================
    plt.figure(figsize=(14, 6))

    for d in axle_plot_data_all:
        plot_with_label(d["t"], d["y_left_orig"],  d["left_color"],  d["left_name"],  alpha=0.7)
        plot_with_label(d["t"], d["y_right_orig"], d["right_color"], d["right_name"], alpha=0.7)

    plt.title("Processed axle(s) - Original signals")
    plt.xlabel("Time [s]")
    plt.ylabel("Torque [Nm]")
    plt.xlim(common_xlim)
    plt.ylim(common_ylim)
    plt.legend()

    img_name_before = make_img_name(file_stem, "_all", "1before")
    finish_plot(fig_dir, img_name_before, show_plots)

    # =====================================================
    # FULL CLEANED AFTER FROM PROCESSED AXLE DATA
    # =====================================================
    plt.figure(figsize=(14, 6))

    for d in axle_plot_data_all:
        plot_with_label(d["t"], d["y_left_clean"],  d["left_color"],  f"{d['left_name']}_CLEAN",  alpha=0.9)
        plot_with_label(d["t"], d["y_right_clean"], d["right_color"], f"{d['right_name']}_CLEAN", alpha=0.9)

    plt.title("Processed axle(s) - Cleaned signals")
    plt.xlabel("Time [s]")
    plt.ylabel("Torque [Nm]")
    plt.xlim(common_xlim)
    plt.ylim(common_ylim)
    plt.legend()

    img_name_after = make_img_name(file_stem, "_all", "2after")
    img_path_after = finish_plot(fig_dir, img_name_after, show_plots)

    log_rows.append({
        "file_name": file_stem,
        "axle": "Processed",
        "window_name": img_name_after,
        "error_type": "All_Cleaned",
        "start_time_s": "",
        "end_time_s": "",
        "image_path": str(img_path_after) if img_path_after else ""
    })

    return log_rows

def save_combined_cleaned_zoom_plot(axle_plot_data_all, fig_dir, file_stem,
                                    t_center, zoom_sec=3.0, show_plots=False):
    """
    Save one combined cleaned zoom plot showing all processed axles together
    in the same time window.

    Used when front and rear both have cleaned faults in the same time range.
    """

    if len(axle_plot_data_all) == 0:
        return None

    # collect all y values for common y-axis
    y_all = []
    for d in axle_plot_data_all:
        y_all.append(d["y_left_orig"])
        y_all.append(d["y_right_orig"])

    y_all = np.concatenate(y_all)
    y_min = np.min(y_all)
    y_max = np.max(y_all)
    y_margin = 0.05 * (y_max - y_min) if y_max > y_min else 1.0
    common_ylim = (y_min - y_margin, y_max + y_margin)

    plt.figure(figsize=(12, 5))

    for d in axle_plot_data_all:
        t = d["t"]
        mask = (t >= t_center - zoom_sec / 2) & (t <= t_center + zoom_sec / 2)

        plot_with_label(
            t[mask], d["y_left_clean"][mask],
            d["left_color"], f"{d['left_name']}_CLEAN"
        )
        plot_with_label(
            t[mask], d["y_right_clean"][mask],
            d["right_color"], f"{d['right_name']}_CLEAN"
        )

    plt.title(f"Both Axles – Cleaned ({t_center:.3f}s)")
    plt.xlabel("Time [s]")
    plt.ylabel("Torque [Nm]")
    plt.ylim(common_ylim)
    plt.legend()

    img_name = f"{file_stem}_BothAxles~(t={t_center:.6f})_2after.png"
    img_path = finish_plot(fig_dir, img_name, show_plots)

    return img_path
def torque_label(ch_name, sig):
    clean_name = ch_name.replace('TQ_', '').replace('Tq_', '')
    return (
        f"{clean_name} torque [Nm] "
        f"(MAX: {np.max(sig):.3f}, MIN: {np.min(sig):.3f}), "
        f"('{ch_name}')"
    )
def plot_with_label(x, y, color, name, alpha=1.0, style='-'):
    plt.plot(
        x,
        y,
        color=color,
        linestyle=style,
        alpha=alpha,
        label=torque_label(name, y)
    )
def get_first_existing_channel(mdf, names):
    all_channels = list(mdf.channels_db.keys())

    for name in names:
        name_low = name.lower()

        # exact / case-insensitive / suffix match
        matches = [
            ch for ch in all_channels
            if ch.lower() == name_low
            or (
                ch.lower().startswith(name_low)
                and len(ch) > len(name)
                and ch[len(name)] in ["_", "-", ".", " ", "[", "("]
            )
        ]

        if matches:
            chosen = sorted(matches, key=len)[0]
            return mdf.get(chosen), chosen

    raise Exception(f"None of these channels found: {names}")
   
def same_shape_behavior(y1, y2, start, end, corr_min=0.70, min_points=5):
    """
    Returns True if y1 and y2 move with similar local shape/slope.
    Used to reject false faults when both signals move together.
    """

    n = len(y1)

    start = max(0, int(start))
    end = min(n, int(end))

    if end - start < min_points:
        return False

    seg1 = y1[start:end]
    seg2 = y2[start:end]

    d1 = np.diff(seg1)
    d2 = np.diff(seg2)

    if len(d1) < 3:
        return False

    if np.std(d1) < 1e-6 or np.std(d2) < 1e-6:
        return False

    corr = np.corrcoef(d1, d2)[0, 1]

    return corr > corr_min
def self_interpolate_slice(y_clean, low, high):
    """
    Clean y_clean[low:high] using linear interpolation
    from the same signal's own neighbours.
    high is exclusive.
    """
    n = len(y_clean)

    low = max(0, int(low))
    high = min(n, int(high))

    if low >= high:
        return y_clean

    left_idx = low - 1
    right_idx = high

    if left_idx >= 0 and right_idx < n:
        y_left = y_clean[left_idx]
        y_right = y_clean[right_idx]

        # avoid invalid interpolation if one boundary is NaN / inf
        if not np.isfinite(y_left) or not np.isfinite(y_right):
            return y_clean

        y_clean[low:high] = np.interp(
            np.arange(low, high),
            [left_idx, right_idx],
            [y_left, y_right]
        )

    elif left_idx >= 0:
        y_left = y_clean[left_idx]

        if not np.isfinite(y_left):
            return y_clean

        y_clean[low:high] = y_left

    elif right_idx < n:
        y_right = y_clean[right_idx]

        if not np.isfinite(y_right):
            return y_clean

        y_clean[low:high] = y_right

    return y_clean

def same_slope_behavior(a, b, corr_min=0.70, range_min=100):
    """
    Returns True if two signals move together / parallel.
    Used to reject false faults when left-right difference is high
    but both signals have similar behaviour.
    """

    if len(a) < 5 or len(b) < 5:
        return False

    da = np.diff(a)
    db = np.diff(b)

    # If both signals are almost constant, correlation is not meaningful
    if np.std(da) < 1e-6 or np.std(db) < 1e-6:
        return False

    slope_corr = np.corrcoef(da, db)[0, 1]

    a_range = np.ptp(a)
    b_range = np.ptp(b)

    return (
        slope_corr > corr_min and
        a_range > range_min and
        b_range > range_min
    )
def should_self_interpolate_fault(y_faulty, low, high, value_threshold):
    """
    Return True if faulty signal before and after the bad interval
    are close to each other.

    low inclusive, high exclusive.
    """
    n = len(y_faulty)

    low = max(0, int(low))
    high = min(n, int(high))

    left_idx = low - 1
    right_idx = high

    if left_idx < 0 or right_idx >= n:
        return False

    before_val = y_faulty[left_idx]
    after_val = y_faulty[right_idx]

    return abs(before_val - after_val) < value_threshold

def get_local_true_bounds(mask_local):
    """
    Return first and last True index inside a local boolean mask.
    Returns None if no True found.
    """
    idx = np.where(mask_local)[0]
    if len(idx) == 0:
        return None
    return idx[0], idx[-1]

def expand_bool_mask(mask, pad):
    """
    Expand True regions by +/- pad samples.
    """
    mask = np.asarray(mask, dtype=bool)
    out = mask.copy()

    for k in range(1, pad + 1):
        out[k:] |= mask[:-k]
        out[:-k] |= mask[k:]

    return out

def bool_mask_to_segments(mask, min_len=1):
    """
    Convert boolean mask to continuous index segments.
    Returns list of (start_idx, end_idx_exclusive).
    """

    segments = []
    in_segment = False
    start = None

    for i, val in enumerate(mask):

        if val and not in_segment:
            start = i
            in_segment = True

        elif not val and in_segment:
            end = i

            if end - start >= min_len:
                segments.append((start, end))

            in_segment = False

    if in_segment:
        end = len(mask)

        if end - start >= min_len:
            segments.append((start, end))

    return segments
def detect_short_plateau_pulses(y, spike_jump, high_torque_threshold,
                                plateau_std_max, max_pulse_samples=20,
                                min_pulse_samples=2):
    """
    Detect short box-like pulses:
    sharp rise/fall with a short high plateau in between.

    Returns list of (start, end) sample intervals.
    """
    n = len(y)
    intervals = []
    i = 1

    while i < n - 2:
        # rising or falling edge
        jump1 = y[i] - y[i-1]

        if abs(jump1) > spike_jump:
            direction = np.sign(jump1)
            j = i + 1

            # allow short plateau / short flat region
            while (
                j < n - 1 and
                (j - i) <= max_pulse_samples and
                abs(y[j] - y[j-1]) < spike_jump * 0.5
            ):
                j += 1

            pulse_len = j - i

            if min_pulse_samples <= pulse_len <= max_pulse_samples:
                plateau = y[i:j]

                # plateau must stay high enough and reasonably flat
                if (
                    len(plateau) >= 2 and
                    abs(np.mean(plateau)) > high_torque_threshold and
                    np.std(plateau) < plateau_std_max
                ):
                    # look for opposite edge
                    if (
                        j < n and
                        abs(y[j] - y[j-1]) > spike_jump and
                        np.sign(y[j] - y[j-1]) == -direction
                    ):
                        intervals.append((i, j))
                        i = j + 1
                        continue

        i += 1

    return intervals
def make_event_mask(t, start_time, end_time, margin_sec=1.5, min_zoom_sec=3.0):
    """
    Create a zoom mask that always covers the full event plus margin.

    If event is short, keep at least min_zoom_sec total window.
    If event is long, expand to event duration + margin before/after.
    """

    start_time = float(start_time)
    end_time = float(end_time)

    if end_time < start_time:
        start_time, end_time = end_time, start_time

    event_duration = end_time - start_time

    # ensure minimum total zoom window
    total_window = max(event_duration + 2 * margin_sec, min_zoom_sec)

    center = (start_time + end_time) / 2.0

    zoom_start = center - total_window / 2.0
    zoom_end = center + total_window / 2.0

    return (t >= zoom_start) & (t <= zoom_end), zoom_start, zoom_end

# =====================================================
# PROCESS ONE AXLE
# =====================================================
def process_axle(mdf, axle_name, left_candidates, right_candidates,
                 other_left_candidates=None, other_right_candidates=None,
                 fig_dir=None, mdf_dir=None, show_plots=True,
                 file_stem="File"):

    print("\n" + "="*60)
    print(f"PROCESSING {axle_name.upper()} AXLE")
    print("="*60)

    # =====================================================
    # CONSTANTS / THRESHOLDS
    # =====================================================
    
    value_threshold = 100        # difference between left/right to start checking
    window_size = 20             # number of samples in detection window
    activity_ratio = 3.0         # one signal must be 3x more dynamic than the other
    spike_jump = 200             # sudden jump threshold
    
    high_torque_threshold = 1500 # high abnormal torque level
    direct_step_abs_min = 3000  # only for clear saturated direct step faults
    low_torque_threshold = 500   # low/normal opposite side level
    step_mean_diff_threshold = 500
    flat_std_threshold = 50
    flat_level_min = 1000       # replaces abs(rr_level) > 1000 / abs(rl_level) > 1000
    plateau_std_max = 100        # max allowed standard deviation inside plateau window
    plateau_range_max = 100      # max allowed max-min range inside plateau w
    opposite_std_threshold = 150
    flat_dynamic_max = 20
    step_extend_samples = 15 #include 10 samples before and 10 samples after
    min_step_samples = 5    #ignore very tiny step regions shorter than 5 samples.
    zoom_sec = 3.0
    common_slope_corr_min = 0.70
    common_movement_range_min = 100

    
    short_pulse_max_samples = 20
    short_pulse_min_samples = 2
    short_pulse_plateau_std_max = 120

    sig_rl, left_name = get_first_existing_channel(mdf, left_candidates)
    sig_rr, right_name = get_first_existing_channel(mdf, right_candidates)

    y_rl = sig_rl.samples
    y_rr = sig_rr.samples
    t_rear = sig_rr.timestamps
    
    log_rows = []
    if mdf_dir is None:
       mdf_dir = fig_dir
    # ✅ Load other axle only for plotting reference
    #Load other axle only for plotting reference, Load is missing, continue with only this axle
    has_other_axle = False
    
    if other_left_candidates is not None and other_right_candidates is not None:
        try:
            sig_ol, other_left_name = get_first_existing_channel(mdf, other_left_candidates)
            sig_or, other_right_name = get_first_existing_channel(mdf, other_right_candidates)
    
            y_ol = sig_ol.samples
            y_or = sig_or.samples
            t_other = sig_or.timestamps
    
            has_other_axle = True
    
        except Exception:
            print(f"{axle_name}: other axle not found, plotting only {axle_name} axle.")
            has_other_axle = False
    

    n = len(y_rr)

    rear_rl_flat  = np.zeros(n, dtype=bool)
    rear_rr_flat  = np.zeros(n, dtype=bool)
    rear_rl_spike = np.zeros(n, dtype=bool)
    rear_rr_spike = np.zeros(n, dtype=bool)
    
    # =====================================================
    # FLAT-TOP DETECTION
    # =====================================================
    
    for i in range(n - window_size):
    
        rl_win = y_rl[i:i+window_size]
        rr_win = y_rr[i:i+window_size]
    
        if np.max(np.abs(rl_win - rr_win)) < value_threshold:
            continue
        # ✅ high difference but same shape/slope = normal movement, not fault
       
        # If RL and RR differ but move together, this is normal behaviour, not fault.
        if same_slope_behavior(
            rl_win,
            rr_win,
            corr_min=common_slope_corr_min,
            range_min=common_movement_range_min
        ):
            continue
    
        rl_dyn = np.std(np.diff(rl_win))
        rr_dyn = np.std(np.diff(rr_win))
    
        rl_ptp = np.ptp(rl_win)
        rr_ptp = np.ptp(rr_win)
    
        rr_smooth = np.all(np.abs(np.diff(rr_win)) < spike_jump * 0.3)
        rl_smooth = np.all(np.abs(np.diff(rl_win)) < spike_jump * 0.3)
    
        rr_level = np.mean(np.abs(rr_win))
        rl_level = np.mean(np.abs(rl_win))
        # ✅ detect sharp edges → this is a STEP, not flat
        rl_edge_left  = abs(y_rl[i] - y_rl[i-1]) if i > 0 else 0
        rl_edge_right = abs(y_rl[i+window_size] - y_rl[i+window_size-1]) if i+window_size < n else 0
        
        rr_edge_left  = abs(y_rr[i] - y_rr[i-1]) if i > 0 else 0
        rr_edge_right = abs(y_rr[i+window_size] - y_rr[i+window_size-1]) if i+window_size < n else 0
        
        # if strong edges exist → skip flat detection
        if (rl_edge_left > spike_jump or rl_edge_right > spike_jump or
            rr_edge_left > spike_jump or rr_edge_right > spike_jump):
            continue
    
        if rr_dyn < flat_dynamic_max and rr_ptp < plateau_range_max and rr_smooth and abs(rr_level) > flat_level_min and rl_dyn > rr_dyn * activity_ratio:
            rear_rr_flat[i:i+window_size] = True
    
        if rl_dyn < flat_dynamic_max and rl_ptp < plateau_range_max and rl_smooth and abs(rl_level) > flat_level_min and rr_dyn > rl_dyn * activity_ratio:
            rear_rl_flat[i:i+window_size] = True
    
    
    # =====================================================
    # MERGE SMALL GAPS
    # =====================================================
    
    def merge_flat(mask, max_gap):
        mask = mask.copy()
        i = 0
        while i < len(mask):
            if not mask[i]:
                j = i
                while j < len(mask) and not mask[j]:
                    j += 1
                if j - i <= max_gap:
                    mask[i:j] = True
                i = j
            else:
                i += 1
        return mask
    
    rear_rr_flat = merge_flat(rear_rr_flat, window_size)
    rear_rl_flat = merge_flat(rear_rl_flat, window_size)
    
        
    def merge_mask_gaps(mask, max_gap):
        mask = mask.copy()
        i = 0
    
        while i < len(mask):
            if not mask[i]:
                j = i
                while j < len(mask) and not mask[j]:
                    j += 1
    
                # fill only small gaps between True regions
                left_true = i > 0 and mask[i-1]
                right_true = j < len(mask) and mask[j]
    
                if left_true and right_true and (j - i) <= max_gap:
                    mask[i:j] = True
    
                i = j
            else:
                i += 1
    
        return mask
    
    # =====================================================
    # =====================================================
    # LONG STUCK / FROZEN CHANNEL DETECTION
    # =====================================================

    opposite_activity_min = 80.0
    near_zero_diff_min = 10.0
    min_stuck_duration_s = 20.0
    
    # Robust stuck parameters
    stuck_level_tol = 35.0          # samples within +/-35 Nm of stuck level
    stuck_fraction_min = 0.80       # at least 80% of samples close to median
    
    stuck_rl_mask = np.zeros(n, dtype=bool)
    stuck_rr_mask = np.zeros(n, dtype=bool)
    
    stuck_rl_reference_side = "right"
    stuck_rr_reference_side = "left"
    
    # Estimate sample time safely
    if len(t_rear) > 2:
        dt_median = np.median(np.diff(t_rear))
        if dt_median <= 0 or not np.isfinite(dt_median):
            dt_median = 0.01
    else:
        dt_median = 0.01
    
    stuck_window_samples = max(10, int(min_stuck_duration_s / dt_median))
    
    
    # =====================================================
    # ROBUST GLOBAL STUCK CHECK
    # This fixes cases like:
    # RL stuck around -3298 Nm but has some small spikes.
    # Normal std/range check fails, so use median + close-sample fraction.
    # =====================================================
    
    rl_med = np.median(y_rl)
    rr_med = np.median(y_rr)
    
    rl_close_frac = np.mean(np.abs(y_rl - rl_med) < stuck_level_tol)
    rr_close_frac = np.mean(np.abs(y_rr - rr_med) < stuck_level_tol)
    
    rl_global_range = np.ptp(y_rl)
    rr_global_range = np.ptp(y_rr)
    
    rl_is_stuck_global = rl_close_frac >= stuck_fraction_min
    rr_is_stuck_global = rr_close_frac >= stuck_fraction_min
  
    
    # =====================================================
    # CASE A: BOTH CHANNELS LOOK STUCK
    # Choose the one closer to zero as reference.
    # Example:
    # FL=-290, FR=-40 -> FL faulty, FR reference.
    # =====================================================
    
    if rl_is_stuck_global and rr_is_stuck_global:
    
        rl_abs_med = abs(rl_med)
        rr_abs_med = abs(rr_med)
    
        if rl_abs_med > rr_abs_med + near_zero_diff_min:
            stuck_rl_mask[:] = True
            stuck_rl_reference_side = "right"
    
           
    
        elif rr_abs_med > rl_abs_med + near_zero_diff_min:
            stuck_rr_mask[:] = True
            stuck_rr_reference_side = "left"
    
    
        else:
            print(
                f"{axle_name}: BOTH STUCK but similar level. "
                f"No substitution applied."
            )
    
    
    # =====================================================
    # CASE B: ONE CHANNEL STUCK, OTHER CHANNEL ACTIVE
    # =====================================================
    
    else:
    
        if rl_is_stuck_global and rr_global_range > opposite_activity_min:
            stuck_rl_mask[:] = True
            stuck_rl_reference_side = "right"
    
           
        if rr_is_stuck_global and rl_global_range > opposite_activity_min:
            stuck_rr_mask[:] = True
            stuck_rr_reference_side = "left"
    
    
    
    # =====================================================
    # PARTIAL LONG STUCK CHECK
    # Only if no global stuck was found.
    # =====================================================
    
    if not np.any(stuck_rl_mask) and not np.any(stuck_rr_mask):
    
        for i in range(0, n - stuck_window_samples):
    
            rl_win = y_rl[i:i + stuck_window_samples]
            rr_win = y_rr[i:i + stuck_window_samples]
    
            rl_med_win = np.median(rl_win)
            rr_med_win = np.median(rr_win)
    
            rl_close_frac_win = np.mean(np.abs(rl_win - rl_med_win) < stuck_level_tol)
            rr_close_frac_win = np.mean(np.abs(rr_win - rr_med_win) < stuck_level_tol)
    
            rl_range_win = np.ptp(rl_win)
            rr_range_win = np.ptp(rr_win)
    
            rl_stuck_win = rl_close_frac_win >= stuck_fraction_min
            rr_stuck_win = rr_close_frac_win >= stuck_fraction_min
    
            # both stuck in window -> choose near-zero as reference
            if rl_stuck_win and rr_stuck_win:
    
                if abs(rl_med_win) > abs(rr_med_win) + near_zero_diff_min:
                    stuck_rl_mask[i:i + stuck_window_samples] = True
                    stuck_rl_reference_side = "right"
    
                elif abs(rr_med_win) > abs(rl_med_win) + near_zero_diff_min:
                    stuck_rr_mask[i:i + stuck_window_samples] = True
                    stuck_rr_reference_side = "left"
    
            # left stuck, right active
            elif rl_stuck_win and rr_range_win > opposite_activity_min:
                stuck_rl_mask[i:i + stuck_window_samples] = True
                
    
            # right stuck, left active
            elif rr_stuck_win and rl_range_win > opposite_activity_min:
                stuck_rr_mask[i:i + stuck_window_samples] = True
                
    
        stuck_rl_mask = merge_mask_gaps(stuck_rl_mask, max_gap=stuck_window_samples)
        stuck_rr_mask = merge_mask_gaps(stuck_rr_mask, max_gap=stuck_window_samples)
    
        stuck_rl_mask = expand_bool_mask(stuck_rl_mask, pad=step_extend_samples)
        stuck_rr_mask = expand_bool_mask(stuck_rr_mask, pad=step_extend_samples)
    
    
    # =====================================================
    # PROTECT LONG STUCK CHANNELS FROM STEP / PLATEAU DETECTION
    # Important:
    # StepPlateau must not see the long frozen channel as a step fault.
    # =====================================================
    
    y_rl_step = y_rl.copy()
    y_rr_step = y_rr.copy()
    
    if np.any(stuck_rl_mask):
        y_rl_step[stuck_rl_mask] = 0.0
    
    if np.any(stuck_rr_mask):
        y_rr_step[stuck_rr_mask] = 0.0
    # =====================================================
    # STEP DETECTION
    # =====================================================
    
    # Use magnitude envelope so opposite-sign channels do not cancel each other
    y_ref = np.maximum(np.abs(y_rr_step), np.abs(y_rl_step))

    
    starts = []
    ends = []
    
    i = 1
    while i < n:
    
        if abs(y_ref[i] - y_ref[i-1]) > spike_jump:
            direction = np.sign(y_ref[i] - y_ref[i-1])
    
            start = i
    
            # ✅ extend start backward
            k = i
            while k > 1 and abs(y_ref[k] - y_ref[k-1]) < spike_jump * 0.5:
                k -= 1
            
            start = k
            j = i + 1
            found = False
    
            while j < n:
                if (np.sign(y_ref[j] - y_ref[j-1]) == -direction and
                    abs(y_ref[j] - y_ref[j-1]) > spike_jump):
    
                    end = j
                    # ✅ extend end forward (capture full falling edge plateau)
                    k = j
                    while k < n-2 and abs(y_ref[k] - y_ref[k-1]) < spike_jump * 0.5:
                        k += 1
                    
                    end = k
                    #segment = y_ref[start:end]
                    mid = (start + end) // 2
                    segment = y_ref[mid-10:mid+10]
    
                    if len(segment) >= window_size and np.std(segment) < 500 and abs(np.mean(segment)) > 800:
                        starts.append(start)
                        ends.append(end)
    
                    found = True
                    i = j
                    break
    
                j += 1
    
            if not found:
                i += 1
            else:
                continue
    
        else:
            i += 1
    
    # =====================================================
    # ✅ VERY IMPORTANT: build step mask
    # =====================================================
    step_mask = np.zeros(n, dtype=bool)
    
    # ✅ mark step from y_ref (existing)
    for s, e in zip(starts, ends):
        s_ext = max(0, s - step_extend_samples)
        e_ext = min(n, e + step_extend_samples)
        step_mask[s_ext:e_ext] = True
    
    
    # ✅ EXISTING plateau logic
    for i in range(1, n):
        rr_std_local = np.std(y_rr_step[max(0, i-10):min(n, i+10)])
        rl_std_local = np.std(y_rl_step[max(0, i-10):min(n, i+10)])
    
        if abs(y_rr_step[i]) > high_torque_threshold and rr_std_local < flat_std_threshold:
            step_mask[i] = True
    
        if abs(y_rl_step[i]) > high_torque_threshold and rl_std_local < flat_std_threshold:
            step_mask[i] = True
    
    

    # ✅ INSERT THIS BLOCK HERE
    for i in range(10, n-10):
        rr_win = y_rr_step[i-10:i+10]
        rl_win = y_rl_step[i-10:i+10]
       
     
        # ✅ Case 1: Right high plateau, left low Works for positive OR negative plateau
        rr_mean = np.mean(rr_win)
        rl_mean = np.mean(rl_win)
        
        rr_std = np.std(rr_win)
        rl_std = np.std(rl_win)
        
        mean_diff = abs(rr_mean - rl_mean)
        
        # ✅ Case 1: Right side has high flat plateau
        # Works even if left side is not near zero, as long as RR differs strongly from RL
        if (
            rr_std < plateau_std_max and
            abs(rr_mean) > high_torque_threshold and
            (
                abs(rl_mean) < low_torque_threshold or
                mean_diff > step_mean_diff_threshold
            )
        ):
            step_mask[i-10:i+10] = True
        
        # ✅ Case 2: Left side has high flat plateau
        # Works even if right side is not near zero, as long as RL differs strongly from RR
        if (
            rl_std < plateau_std_max and
            abs(rl_mean) > high_torque_threshold and
            (
                abs(rr_mean) < low_torque_threshold or
                mean_diff > step_mean_diff_threshold
            )
        ):
            step_mask[i-10:i+10] = True
        
        # ✅ Case 3: Opposite-sign simultaneous plateau
        rr_mean = np.mean(rr_win)
        rl_mean = np.mean(rl_win)
    
        rr_std = np.std(rr_win)
        rl_std = np.std(rl_win)
    
        if (
            abs(rr_mean) > high_torque_threshold and
            abs(rl_mean) > high_torque_threshold and
            np.sign(rr_mean) != np.sign(rl_mean) and
            rr_std < opposite_std_threshold and
            rl_std < opposite_std_threshold
        ):
            step_mask[i-10:i+10] = True
    
    
    # This catches sharp opposite-sign faults even if the window std test fails.
    opposite_fault_mask = (
        (np.abs(y_rr_step) > high_torque_threshold) &
        (np.abs(y_rl_step) > high_torque_threshold) &
        (np.sign(y_rr_step) != np.sign(y_rl_step))
    )
    
    step_mask[opposite_fault_mask] = True

    # =====================================================
    # DIRECT ONE-SIDE HIGH PLATEAU DETECTION
    # catches clear cases like:
    # RR near 4500 Nm, RL near 0 Nm, long flat plateau
    # This does not depend on edge-based starts/ends.
    # =====================================================

    direct_plateau_win = 20

    for i in range(direct_plateau_win, n - direct_plateau_win):

        rr_win = y_rr_step[i - direct_plateau_win:i + direct_plateau_win]
        rl_win = y_rl_step[i - direct_plateau_win:i + direct_plateau_win]

        rr_mean = np.mean(rr_win)
        rl_mean = np.mean(rl_win)

        rr_std = np.std(rr_win)
        rl_std = np.std(rl_win)

        rr_abs_mean = np.mean(np.abs(rr_win))
        rl_abs_mean = np.mean(np.abs(rl_win))

        mean_diff = abs(rr_mean - rl_mean)

        # RR high plateau fault
        if (
            rr_abs_mean > high_torque_threshold and
            mean_diff > step_mean_diff_threshold and
            rr_abs_mean > rl_abs_mean * 3.0 and
            rr_std < 300
        ):
            step_mask[i - direct_plateau_win:i + direct_plateau_win] = True

        # RL high plateau fault
        if (
            rl_abs_mean > high_torque_threshold and
            mean_diff > step_mean_diff_threshold and
            rl_abs_mean > rr_abs_mean * 3.0 and
            rl_std < 300
        ):
            step_mask[i - direct_plateau_win:i + direct_plateau_win] = True
            
    # ✅ THEN ADD merge step gaps HERE
    step_mask = merge_mask_gaps(step_mask, max_gap=window_size)
    # ✅ THEN BUILD STEP SEGMENTS HERE
    step_segments = []
    in_step = False
    
    for i in range(n):
        if step_mask[i] and not in_step:
            step_start = i
            in_step = True
    
        elif not step_mask[i] and in_step:
            step_end = i
    
            if step_end - step_start >= min_step_samples:
                step_segments.append((step_start, step_end))
    
            in_step = False
    
    if in_step:
        step_segments.append((step_start, n-1))
    
    
    # =====================================================
    # ✅ FILTER FALSE STEP EVENTS CAUSED BY COMMON RL/RR MOTION
    # =====================================================
    
    filtered_step_segments = []
    
    for s, e in step_segments:

        rl_seg = y_rl_step[s:e+1]
        rr_seg = y_rr_step[s:e+1]
    
        if len(rl_seg) < 5:
            continue
        
        max_abs_fault_level = max(
            np.max(np.abs(rl_seg)),
            np.max(np.abs(rr_seg))
        )
        
        # reject normal high torque driving events
        # real step/plateau faults in your data are saturated around ±4500 Nm
        if max_abs_fault_level < direct_step_abs_min:
            continue

        mean_diff = abs(np.mean(rr_seg) - np.mean(rl_seg))
    
        # If RR and RL are not strongly different, this is not a fault step.
        if mean_diff < step_mean_diff_threshold:
            continue
        
        # ✅ reject common movement / parallel behaviour
        if same_slope_behavior(
            rl_seg,
            rr_seg,
            corr_min=common_slope_corr_min,
            range_min=common_movement_range_min
        ):
            continue
    
        filtered_step_segments.append((s, e))
    
    # =====================================================
    # MERGE STEP / PLATEAU EVENTS CLOSE IN TIME
    #
    # Important:
    # Do NOT generate one plot per small separated piece.
    # If Step/Plateau events occur within 3 seconds of each other,
    # treat them as one engineering event and make one zoom plot.
    # =====================================================
    
    step_segments = sorted(filtered_step_segments, key=lambda x: x[0])
    
    merged_step_segments = []
    merge_step_gap_sec = 3.0
    
    for s, e in step_segments:
    
        s = int(s)
        e = int(e)
    
        if not merged_step_segments:
            merged_step_segments.append([s, e])
            continue
    
        last_s, last_e = merged_step_segments[-1]
    
        last_end_time = t_rear[min(last_e, n - 1)]
        this_start_time = t_rear[min(s, n - 1)]
    
        # Merge if next event starts within 3 seconds after previous event ends
        if this_start_time - last_end_time <= merge_step_gap_sec:
            merged_step_segments[-1][1] = max(last_e, e)
        else:
            merged_step_segments.append([s, e])
        
    # =====================================================
        
    step_segments = [(s, e) for s, e in merged_step_segments]
    
    print(
        f"{axle_name}: merged Step/Plateau plot events -> "
        f"{len(step_segments)}"
    )
    
    # ✅ rebuild step_mask from merged step_segments
    step_mask = np.zeros(n, dtype=bool)
    
    for s, e in step_segments:
        step_mask[s:e+1] = True
        
    # =====================================================
    # =====================================================
    # =====================================================
    # BUILD SIDE-SPECIFIC STEP MASKS
    # Needed when one side has step/plateau and the other side has spike inside it
    # =====================================================
    step_mask_rr_side = np.zeros(n, dtype=bool)
    step_mask_rl_side = np.zeros(n, dtype=bool)
    
    for s, e in step_segments:
        rr_seg = y_rr[s:e+1]
        rl_seg = y_rl[s:e+1]
        rr_seg = y_rr_step[s:e+1]
        rl_seg = y_rl_step[s:e+1]
    
        rr_high = np.abs(rr_seg) > high_torque_threshold
        rl_high = np.abs(rl_seg) > high_torque_threshold
    
        rr_diff = np.abs(rr_seg - rl_seg) > step_mean_diff_threshold
        rl_diff = np.abs(rl_seg - rr_seg) > step_mean_diff_threshold
    
        # RR side faulty when RR is high and clearly different from RL
        rr_fault_local = rr_high & rr_diff
    
        # RL side faulty when RL is high and clearly different from RR
        rl_fault_local = rl_high & rl_diff
    
        if np.any(rr_fault_local):
            step_mask_rr_side[s:e+1][rr_fault_local] = True
    
        if np.any(rl_fault_local):
            step_mask_rl_side[s:e+1][rl_fault_local] = True
    
    # expand side masks slightly to include rising/falling edges
    step_mask_rr_side = expand_bool_mask(step_mask_rr_side, step_extend_samples)
    step_mask_rl_side = expand_bool_mask(step_mask_rl_side, step_extend_samples)
    # Do not allow StepPlateau cleaning on long stuck/frozen channels
    step_mask_rl_side[stuck_rl_mask] = False
    step_mask_rr_side[stuck_rr_mask] = False
    
    # =====================================================
    # SHORT PLATEAU / MICRO-STEP DETECTION
    # =====================================================
    rr_short_pulses = detect_short_plateau_pulses(
        y_rr,
        spike_jump=spike_jump,
        high_torque_threshold=high_torque_threshold,
        plateau_std_max=short_pulse_plateau_std_max,
        max_pulse_samples=short_pulse_max_samples,
        min_pulse_samples=short_pulse_min_samples
    )

    rl_short_pulses = detect_short_plateau_pulses(
        y_rl,
        spike_jump=spike_jump,
        high_torque_threshold=high_torque_threshold,
        plateau_std_max=short_pulse_plateau_std_max,
        max_pulse_samples=short_pulse_max_samples,
        min_pulse_samples=short_pulse_min_samples
    )

    # remove pulses already covered by large step_mask
    rr_short_pulses = [
        (s0, e0) for s0, e0 in rr_short_pulses
        if not np.any(step_mask_rr_side[s0:e0+1])
    ]

    rl_short_pulses = [
        (s0, e0) for s0, e0 in rl_short_pulses
        if not np.any(step_mask_rl_side[s0:e0+1])
    ]
    
    # =====================================================
    # FILTER EVENTS
    # =====================================================
    
    filtered_s = []
    filtered_e = []
    
    for s, e in zip(starts, ends):
        if (e - s) >= window_size:
            filtered_s.append(s)
            filtered_e.append(e)
    
    starts = filtered_s
    ends = filtered_e
    
    # =====================================================
    # =====================================================
    # SPIKE DETECTION
    # =====================================================

    offset_spike_centers_rr = set()
    offset_spike_centers_rl = set()

    for i in range(1, n - 1):

        # skip anything inside detected step/plateau region
        # Do not skip whole axle step_mask here.
        # A spike on one side can exist inside a step fault on the other side.
        inside_rr_step_here = step_mask_rr_side[i]
        inside_rl_step_here = step_mask_rl_side[i]

        # skip detected flat windows only
        if rear_rr_flat[i] or rear_rl_flat[i]:
            continue

        # =====================================================
        # 1) ORIGINAL POINT-SPIKE DETECTION
        # catches true one-sample sharp spikes only
        # rejects normal movement when both signals have similar shape/slope
        # rejects ramp/level transition using before-after return check
        # =====================================================

        # ---------- RR point-spike candidate ----------
        # ---------- RR point-spike candidate ----------
        if (
            not inside_rr_step_here and
            abs(y_rr[i] - y_rr[i - 1]) > spike_jump and
            abs(y_rr[i + 1] - y_rr[i]) > spike_jump
        ):
            rr_base_left = y_rr[max(0, i - 8):max(0, i - 3)]
            rr_base_right = y_rr[min(n, i + 3):min(n, i + 8)]

            rl_base_left = y_rl[max(0, i - 8):max(0, i - 3)]
            rl_base_right = y_rl[min(n, i + 3):min(n, i + 8)]

            if (
                len(rr_base_left) > 0 and
                len(rr_base_right) > 0 and
                len(rl_base_left) > 0 and
                len(rl_base_right) > 0
            ):
                rr_left_level = np.median(rr_base_left)
                rr_right_level = np.median(rr_base_right)
                rr_return_ok = abs(rr_left_level - rr_right_level) < spike_jump

                rr_base = np.median(np.concatenate([rr_base_left, rr_base_right]))
                rl_base = np.median(np.concatenate([rl_base_left, rl_base_right]))

                rr_dev = abs(y_rr[i] - rr_base)
                rl_dev_same_time = abs(y_rl[i] - rl_base)

                rr_cross_diff = abs(y_rr[i] - y_rl[i])

                rr_range_local = np.ptp(y_rr[max(0, i - 4):min(n, i + 5)])
                rl_range_local = np.ptp(y_rl[max(0, i - 4):min(n, i + 5)])

                shape_same_rr = same_shape_behavior(
                    y_rr,
                    y_rl,
                    i - 4,
                    i + 5,
                    corr_min=0.60
                )

                rr_isolated_point_spike = (
                    rr_dev > spike_jump and
                    rr_cross_diff > value_threshold and
                    rr_dev > rl_dev_same_time * 3.0 and
                    rr_range_local > rl_range_local * 2.0 and
                    rr_return_ok and
                    not shape_same_rr
                )

                if rr_isolated_point_spike:
                    rear_rr_spike[i] = True

        # ---------- RL point-spike candidate ----------
        if (
            not inside_rl_step_here and
            abs(y_rl[i] - y_rl[i - 1]) > spike_jump and
            abs(y_rl[i + 1] - y_rl[i]) > spike_jump
        ):
            rl_base_left = y_rl[max(0, i - 8):max(0, i - 3)]
            rl_base_right = y_rl[min(n, i + 3):min(n, i + 8)]

            rr_base_left = y_rr[max(0, i - 8):max(0, i - 3)]
            rr_base_right = y_rr[min(n, i + 3):min(n, i + 8)]

            if (
                len(rl_base_left) > 0 and
                len(rl_base_right) > 0 and
                len(rr_base_left) > 0 and
                len(rr_base_right) > 0
            ):
                rl_left_level = np.median(rl_base_left)
                rl_right_level = np.median(rl_base_right)
                rl_return_ok = abs(rl_left_level - rl_right_level) < spike_jump

                rl_base = np.median(np.concatenate([rl_base_left, rl_base_right]))
                rr_base = np.median(np.concatenate([rr_base_left, rr_base_right]))

                rl_dev = abs(y_rl[i] - rl_base)
                rr_dev_same_time = abs(y_rr[i] - rr_base)

                rl_cross_diff = abs(y_rl[i] - y_rr[i])

                rl_range_local = np.ptp(y_rl[max(0, i - 4):min(n, i + 5)])
                rr_range_local = np.ptp(y_rr[max(0, i - 4):min(n, i + 5)])

                shape_same_rl = same_shape_behavior(
                    y_rl,
                    y_rr,
                    i - 4,
                    i + 5,
                    corr_min=0.60
                )

                rl_isolated_point_spike = (
                    rl_dev > spike_jump and
                    rl_cross_diff > value_threshold and
                    rl_dev > rr_dev_same_time * 3.0 and
                    rl_range_local > rr_range_local * 2.0 and
                    rl_return_ok and
                    not shape_same_rl
                )

                if rl_isolated_point_spike:
                    rear_rl_spike[i] = True

        # =====================================================
        # 2) OFFSET-AWARE SPIKE DETECTION WITH SHAPE/SLOPE CHECK
        # Handles spike with small slope/offset before or after peak.
        # Rejects normal movement when both signals have similar shape/slope.
        # Rejects ramp/level transition using before-after return check.
        # =====================================================

        local_pad = 8

        low_i = max(0, i - local_pad)
        high_i = min(n, i + local_pad + 1)

        rr_local = y_rr[low_i:high_i]
        rl_local = y_rl[low_i:high_i]

        # =====================================================
        # RR / right-side offset spike candidate
        # =====================================================
        if len(rr_local) >= 3:
            rr_center_local = np.argmax(np.abs(rr_local - np.median(rr_local)))
            rr_center = low_i + rr_center_local

            if not step_mask_rr_side[rr_center]:
                rr_base_left = y_rr[max(0, rr_center - 12):max(0, rr_center - 5)]
                rr_base_right = y_rr[min(n, rr_center + 5):min(n, rr_center + 12)]

                rl_base_left = y_rl[max(0, rr_center - 12):max(0, rr_center - 5)]
                rl_base_right = y_rl[min(n, rr_center + 5):min(n, rr_center + 12)]

                if (
                    len(rr_base_left) > 0 and
                    len(rr_base_right) > 0 and
                    len(rl_base_left) > 0 and
                    len(rl_base_right) > 0
                ):
                    rr_left_level = np.median(rr_base_left)
                    rr_right_level = np.median(rr_base_right)
                    rr_return_ok = abs(rr_left_level - rr_right_level) < spike_jump

                    rr_baseline = np.median(
                        np.concatenate([rr_base_left, rr_base_right])
                    )

                    rl_baseline = np.median(
                        np.concatenate([rl_base_left, rl_base_right])
                    )

                    rr_dev = abs(y_rr[rr_center] - rr_baseline)
                    rl_dev_near_rr = abs(y_rl[rr_center] - rl_baseline)

                    rr_cross_diff = abs(y_rr[rr_center] - y_rl[rr_center])

                    rr_range_local = np.ptp(y_rr[low_i:high_i])
                    rl_range_local = np.ptp(y_rl[low_i:high_i])

                    shape_same_rr = same_shape_behavior(
                        y_rr,
                        y_rl,
                        rr_center - local_pad,
                        rr_center + local_pad + 1,
                        corr_min=0.60
                    )

                    rr_isolated_spike = (
                        rr_dev > spike_jump and
                        rr_cross_diff > value_threshold and
                        rr_dev > rl_dev_near_rr * 3.0 and
                        rr_range_local > rl_range_local * 2.0 and
                        rr_return_ok and
                        not shape_same_rr
                    )

                    if rr_isolated_spike:
                        if rr_center not in offset_spike_centers_rr:
                            offset_spike_centers_rr.add(rr_center)

                            rear_rr_spike[rr_center] = True

                            s_off = max(0, rr_center - local_pad)
                            e_off = min(n - 1, rr_center + local_pad)

                            rr_short_pulses.append((s_off, e_off))

        # =====================================================
        # RL / left-side offset spike candidate
        # =====================================================
        if len(rl_local) >= 3:
            rl_center_local = np.argmax(np.abs(rl_local - np.median(rl_local)))
            rl_center = low_i + rl_center_local

           
            if not step_mask_rl_side[rl_center]:
                rl_base_left = y_rl[max(0, rl_center - 12):max(0, rl_center - 5)]
                rl_base_right = y_rl[min(n, rl_center + 5):min(n, rl_center + 12)]

                rr_base_left = y_rr[max(0, rl_center - 12):max(0, rl_center - 5)]
                rr_base_right = y_rr[min(n, rl_center + 5):min(n, rl_center + 12)]

                if (
                    len(rl_base_left) > 0 and
                    len(rl_base_right) > 0 and
                    len(rr_base_left) > 0 and
                    len(rr_base_right) > 0
                ):
                    rl_left_level = np.median(rl_base_left)
                    rl_right_level = np.median(rl_base_right)
                    rl_return_ok = abs(rl_left_level - rl_right_level) < spike_jump

                    rl_baseline = np.median(
                        np.concatenate([rl_base_left, rl_base_right])
                    )

                    rr_baseline = np.median(
                        np.concatenate([rr_base_left, rr_base_right])
                    )

                    rl_dev = abs(y_rl[rl_center] - rl_baseline)
                    rr_dev_near_rl = abs(y_rr[rl_center] - rr_baseline)

                    rl_cross_diff = abs(y_rl[rl_center] - y_rr[rl_center])

                    rl_range_local = np.ptp(y_rl[low_i:high_i])
                    rr_range_local = np.ptp(y_rr[low_i:high_i])

                    shape_same_rl = same_shape_behavior(
                        y_rl,
                        y_rr,
                        rl_center - local_pad,
                        rl_center + local_pad + 1,
                        corr_min=0.60
                    )

                    rl_isolated_spike = (
                        rl_dev > spike_jump and
                        rl_cross_diff > value_threshold and
                        rl_dev > rr_dev_near_rl * 3.0 and
                        rl_range_local > rr_range_local * 2.0 and
                        rl_return_ok and
                        not shape_same_rl
                    )

                    if rl_isolated_spike:
                        if rl_center not in offset_spike_centers_rl:
                            offset_spike_centers_rl.add(rl_center)

                            rear_rl_spike[rl_center] = True

                            s_off = max(0, rl_center - local_pad)
                            e_off = min(n - 1, rl_center + local_pad)

                            rl_short_pulses.append((s_off, e_off))
    # =====================================================
    # FILTER FALSE SHORT/THIN AND SPIKE EVENTS
    # Reject normal torque movement where left/right have similar shape
    # and the event is not strongly isolated.
    # =====================================================

    def keep_isolated_short_event(side, s0, e0):
        """
        Return True only for clear isolated short/thin faults.

        side = "RR" or "RL"
        """

        s0 = max(0, int(s0))
        e0 = min(n - 1, int(e0))

        if e0 <= s0:
            return False

        pad = 8
        a = max(0, s0 - pad)
        b = min(n, e0 + pad + 1)

        rr_seg = y_rr[a:b]
        rl_seg = y_rl[a:b]

        if len(rr_seg) < 5 or len(rl_seg) < 5:
            return False

        # Reject if both signals move with similar shape/slope
        if same_shape_behavior(
            y_rl,
            y_rr,
            a,
            b,
            corr_min=0.55
        ):
            return False

        rr_range = np.ptp(rr_seg)
        rl_range = np.ptp(rl_seg)
        cross_diff_max = np.max(np.abs(rr_seg - rl_seg))

        rr_abs_max = np.max(np.abs(rr_seg))
        rl_abs_max = np.max(np.abs(rl_seg))

        # before/after return check
        rr_left = np.median(y_rr[max(0, s0 - 8):max(0, s0 - 3)])
        rr_right = np.median(y_rr[min(n, e0 + 3):min(n, e0 + 8)])

        rl_left = np.median(y_rl[max(0, s0 - 8):max(0, s0 - 3)])
        rl_right = np.median(y_rl[min(n, e0 + 3):min(n, e0 + 8)])

        rr_return_ok = abs(rr_left - rr_right) < spike_jump
        rl_return_ok = abs(rl_left - rl_right) < spike_jump

        if side == "RR":
            # RR must show a clear isolated change relative to RL.
            # Do not require absolute torque above 1500 Nm because a valid
            # spike can occur from a normal baseline, for example -140 to -1080 Nm.
            return (
                rr_range > spike_jump and
                cross_diff_max > value_threshold and
                rr_range > max(rl_range * 2.0, spike_jump) and
                rr_return_ok
            )
        
        if side == "RL":
            # RL must show a clear isolated change relative to RR.
            return (
                rl_range > spike_jump and
                cross_diff_max > value_threshold and
                rl_range > max(rr_range * 2.0, spike_jump) and
                rl_return_ok
            )

        return False


    # Filter short/thin pulse intervals before cleaning
    rr_short_pulses = [
        (s0, e0) for s0, e0 in rr_short_pulses
        if keep_isolated_short_event("RR", s0, e0)
    ]

    rl_short_pulses = [
        (s0, e0) for s0, e0 in rl_short_pulses
        if keep_isolated_short_event("RL", s0, e0)
    ]

    # Also remove spike center points that are not isolated enough
    for i in range(n):

        if rear_rr_spike[i] and not keep_isolated_short_event("RR", max(0, i - 3), min(n - 1, i + 3)):
            rear_rr_spike[i] = False

        if rear_rl_spike[i] and not keep_isolated_short_event("RL", max(0, i - 3), min(n - 1, i + 3)):
            rear_rl_spike[i] = False
            
    # =====================================================
    # ✅ CLEANING
    # =====================================================
    
    y_rr_clean = y_rr.copy()
    y_rl_clean = y_rl.copy()
    
    # ✅ track step/plateau fault side
    step_fault_is_rr = np.zeros(n, dtype=bool)
    step_fault_is_rl = np.zeros(n, dtype=bool)

    spike_fault_is_rr = np.zeros(n, dtype=bool)
    spike_fault_is_rl = np.zeros(n, dtype=bool)

    
        
    # =====================================================
    # DIRECT FALLBACK CLEANING FOR MISSED ONE-SIDE HIGH PLATEAUS
    # This catches clear cases missed by step_segments:
    # one side very high, opposite side normal, strong difference.
    # Example: RR around +4500 Nm while RL around 0 Nm.
    # =====================================================

    direct_rr_fault = (
        (np.abs(y_rr) > direct_step_abs_min) &
        (np.abs(y_rr - y_rl) > step_mean_diff_threshold) &
        (~stuck_rr_mask)
    )
    
    direct_rl_fault = (
        (np.abs(y_rl) > direct_step_abs_min) &
        (np.abs(y_rl - y_rr) > step_mean_diff_threshold) &
        (~stuck_rl_mask)
    )

    # Expand so edges are included
    direct_rr_fault = expand_bool_mask(direct_rr_fault, step_extend_samples)
    direct_rl_fault = expand_bool_mask(direct_rl_fault, step_extend_samples)
    
    direct_step_segments = []

    def clean_direct_mask(mask, y_clean, fault_side_name):
        intervals = []
        in_fault = False

        # =====================================================
        # 1) Build intervals from mask
        # =====================================================
        for k in range(n):
            if mask[k] and not in_fault:
                s_direct = k
                in_fault = True

            elif not mask[k] and in_fault:
                e_direct = k - 1
                if e_direct - s_direct + 1 >= min_step_samples:
                    intervals.append((s_direct, e_direct))
                in_fault = False

        if in_fault:
            e_direct = n - 1
            if e_direct - s_direct + 1 >= min_step_samples:
                intervals.append((s_direct, e_direct))

        # =====================================================
        # 2) Clean only real direct step faults
        # =====================================================
        for s_direct, e_direct in intervals:

            # Add margin around direct interval
            s_clean = max(0, s_direct - step_extend_samples)
            e_clean = min(n - 1, e_direct + step_extend_samples)

            # =====================================================
            # REJECT NORMAL COMMON MOVEMENT
            # If RL and RR move with similar shape/slope, it is NOT a step fault.
            # This prevents false Step/Plateau around normal high torque peaks.
            # =====================================================
            rl_seg_check = y_rl[s_clean:e_clean + 1]
            rr_seg_check = y_rr[s_clean:e_clean + 1]

            if len(rl_seg_check) >= 5 and len(rr_seg_check) >= 5:

                common_shape = same_shape_behavior(
                    y_rl,
                    y_rr,
                    s_clean,
                    e_clean + 1,
                    corr_min=0.55
                )

                rl_peak_abs = np.max(np.abs(rl_seg_check))
                rr_peak_abs = np.max(np.abs(rr_seg_check))

                rl_peak_value = rl_seg_check[np.argmax(np.abs(rl_seg_check))]
                rr_peak_value = rr_seg_check[np.argmax(np.abs(rr_seg_check))]

                both_sides_high = (
                    rl_peak_abs > direct_step_abs_min and
                    rr_peak_abs > direct_step_abs_min
                )

                same_peak_direction = np.sign(rl_peak_value) == np.sign(rr_peak_value)

                # If both sides are high, same direction, and same shape -> normal torque event
                if common_shape and both_sides_high and same_peak_direction:
                    continue

            # =====================================================
            # 3) Clean accepted direct fault
            # =====================================================
            y_clean = self_interpolate_slice(y_clean, s_clean, e_clean + 1)

            direct_step_segments.append((s_clean, e_clean))

            if fault_side_name == "RR":
                step_fault_is_rr[s_clean:e_clean + 1] = True
                step_mask_rr_side[s_clean:e_clean + 1] = True


            elif fault_side_name == "RL":
                step_fault_is_rl[s_clean:e_clean + 1] = True
                step_mask_rl_side[s_clean:e_clean + 1] = True


        return y_clean

    y_rr_clean = clean_direct_mask(direct_rr_fault, y_rr_clean, "RR")
    y_rl_clean = clean_direct_mask(direct_rl_fault, y_rl_clean, "RL")

    
    # Add direct-cleaned step intervals to step_segments so they also get zoom plots/logs
    if len(direct_step_segments) > 0:
        step_segments = sorted(step_segments + direct_step_segments, key=lambda x: x[0])
    
        # rebuild global step mask including direct events
        step_mask = np.zeros(n, dtype=bool)
        for s_dir, e_dir in step_segments:
            step_mask[s_dir:e_dir + 1] = True
    
    # =====================================================
    # =====================================================
    # ✅ 1. STEP / PLATEAU CLEANING - SIDE SPECIFIC
    # =====================================================
    # y_rl/y_rr are generic left/right signals:
    #   Front axle -> y_rl = FL, y_rr = FR
    #   Rear axle  -> y_rl = RL, y_rr = RR
    #
    # This fixes cases where BOTH sides are faulty:
    #   FL = -4000 plateau
    #   FR = +4000 plateau
    
    for s, e in step_segments:
    
        s = int(s)
        e = int(e)
    
        if e <= s:
            continue
    
        left_seg = y_rl_step[s:e + 1]
        right_seg = y_rr_step[s:e + 1]
    
        diff_seg = np.abs(left_seg - right_seg)
    
        # =====================================================
        # Detect LEFT side fault independently
        # =====================================================
        left_fault_local = (
            (np.abs(left_seg) > direct_step_abs_min) &
            (diff_seg > step_mean_diff_threshold)
        )
    
        # =====================================================
        # Detect RIGHT side fault independently
        # =====================================================
        right_fault_local = (
            (np.abs(right_seg) > direct_step_abs_min) &
            (diff_seg > step_mean_diff_threshold)
        )
    
        # Include existing side-specific masks for this segment
        left_fault_local = left_fault_local | step_mask_rl_side[s:e + 1]
        right_fault_local = right_fault_local | step_mask_rr_side[s:e + 1]
    
        # =====================================================
        # Reject only normal common movement
        # Do NOT reject opposite-sign saturation.
        # =====================================================
        if len(left_seg) >= 5 and len(right_seg) >= 5:
    
            common_shape = same_shape_behavior(
                y_rl_step,
                y_rr_step,
                s,
                e + 1,
                corr_min=0.55
            )
    
            left_peak_abs = np.max(np.abs(left_seg))
            right_peak_abs = np.max(np.abs(right_seg))
    
            left_peak_value = left_seg[np.argmax(np.abs(left_seg))]
            right_peak_value = right_seg[np.argmax(np.abs(right_seg))]
    
            both_sides_high = (
                left_peak_abs > direct_step_abs_min and
                right_peak_abs > direct_step_abs_min
            )
    
            same_peak_direction = (
                np.sign(left_peak_value) == np.sign(right_peak_value)
            )
    
            # Normal high torque event:
            # both high, same direction, same shape
            if common_shape and both_sides_high and same_peak_direction:
                continue
    
        # =====================================================
        # Convert local masks to full-length masks
        # =====================================================
        left_fault_global = np.zeros(n, dtype=bool)
        right_fault_global = np.zeros(n, dtype=bool)
    
        left_fault_global[s:e + 1] = left_fault_local
        right_fault_global[s:e + 1] = right_fault_local
    
        # Expand edges
        left_fault_global = expand_bool_mask(left_fault_global, step_extend_samples)
        right_fault_global = expand_bool_mask(right_fault_global, step_extend_samples)
    
        # =====================================================
        # Clean LEFT side independently
        # =====================================================
        left_segments = bool_mask_to_segments(
            left_fault_global,
            min_len=min_step_samples
        )
    
        for ls, le in left_segments:
    
            ls = max(0, int(ls))
            le = min(n, int(le))
    
            y_rl_clean = self_interpolate_slice(
                y_rl_clean,
                ls,
                le
            )
    
            step_fault_is_rl[ls:le] = True
            step_mask_rl_side[ls:le] = True
    
        # =====================================================
        # Clean RIGHT side independently
        # =====================================================
        right_segments = bool_mask_to_segments(
            right_fault_global,
            min_len=min_step_samples
        )
    
        for rs, re in right_segments:
    
            rs = max(0, int(rs))
            re = min(n, int(re))
    
            y_rr_clean = self_interpolate_slice(
                y_rr_clean,
                rs,
                re
            )
    
            step_fault_is_rr[rs:re] = True
            step_mask_rr_side[rs:re] = True
    
        # =====================================================
        # Fallback if side-specific masks found nothing
        # =====================================================
        if len(left_segments) == 0 and len(right_segments) == 0:
    
            mean_diff = abs(np.mean(left_seg) - np.mean(right_seg))
    
            if mean_diff > step_mean_diff_threshold:
    
                if abs(np.mean(left_seg)) > abs(np.mean(right_seg)):
    
                    y_rl_clean = self_interpolate_slice(
                        y_rl_clean,
                        s,
                        e + 1
                    )
    
                    step_fault_is_rl[s:e + 1] = True
                    step_mask_rl_side[s:e + 1] = True
    
                else:
    
                    y_rr_clean = self_interpolate_slice(
                        y_rr_clean,
                        s,
                        e + 1
                    )
    
                    step_fault_is_rr[s:e + 1] = True
                    step_mask_rr_side[s:e + 1] = True
    # =====================================================
    # ✅ 1B. SHORT PLATEAU / MICRO-STEP CLEANING
    # =====================================================
    for s0, e0 in rr_short_pulses:
        y_rr_clean = self_interpolate_slice(y_rr_clean, s0, e0 + 1)
        spike_fault_is_rr[s0:e0 + 1] = True

    for s0, e0 in rl_short_pulses:
        y_rl_clean = self_interpolate_slice(y_rl_clean, s0, e0 + 1)
        spike_fault_is_rl[s0:e0 + 1] = True
 
    # BUILD SHORT/THIN EVENT LIST FOR ZOOM PLOTTING
    #
    # IMPORTANT:
    # Do NOT plot every micro-sample as separate fault.
    # Merge ShortThin events that are close in time.
    # Example:
    #   1898.77, 1898.78, 1898.79, 1899.2, 1900.6
    # becomes:
    #   one event from first start to last end
    # =====================================================
    
    short_events = []
    
    for s0, e0 in rl_short_pulses:
        short_events.append({
            "start": int(s0),
            "end": int(e0),
            "left_fault": True,
            "right_fault": False
        })
    
    for s0, e0 in rr_short_pulses:
        short_events.append({
            "start": int(s0),
            "end": int(e0),
            "left_fault": False,
            "right_fault": True
        })
    
    # Sort by start index
    short_events = sorted(short_events, key=lambda d: d["start"])
    
    # =====================================================
    # MERGE SHORT/THIN EVENTS CLOSE IN TIME
    # Merge if next event starts within 3 seconds from previous event end.
    # =====================================================
    
    merged_short_events = []
    merge_short_gap_sec = 3.0
    
    for ev in short_events:
    
        if not merged_short_events:
            merged_short_events.append(ev)
            continue
    
        last = merged_short_events[-1]
    
        last_end_time = t_rear[min(last["end"], n - 1)]
        ev_start_time = t_rear[min(ev["start"], n - 1)]
    
        # If event is close to previous event, merge into one zoom plot
        if ev_start_time - last_end_time <= merge_short_gap_sec:
    
            last["end"] = max(last["end"], ev["end"])
            last["left_fault"] = last["left_fault"] or ev["left_fault"]
            last["right_fault"] = last["right_fault"] or ev["right_fault"]
    
        else:
            merged_short_events.append(ev)
    
    short_events = merged_short_events
    
    print(
        f"{axle_name}: merged ShortThin plot events -> "
        f"{len(short_events)}"
    )
    
    # =====================================================
    # ✅ 2. PREPARE SPIKE PROCESSING
    # =====================================================
    # Remove spikes only if the spike is on the SAME side as the step fault
    for i in range(n):
    
        if step_mask_rr_side[i]:
            rear_rr_spike[i] = False
    
        if step_mask_rl_side[i]:
            rear_rl_spike[i] = False
            
    # =====================================================
    # ✅ CLEAN & REBUILD SPIKE INDICES (FINAL FIX)
    # =====================================================
    
    rear_spike_clean = np.zeros(n, dtype=bool)

    for i in range(n):
    
        if rear_rr_spike[i] and not step_mask_rr_side[i]:
            rear_spike_clean[i] = True
    
        if rear_rl_spike[i] and not step_mask_rl_side[i]:
            rear_spike_clean[i] = True
    
    # final spike indices
    rear_spike_indices = np.where(rear_spike_clean)[0]
    
    
    # ✅ protect flat regions
    flat_mask = np.zeros(n, dtype=bool)
    for s, e in step_segments:
        flat_mask[s:e+1] = True
    

    
    # =====================================================
    # ✅ 3. SPIKE CLEANING (SEPARATE!)
    # =====================================================
    for idx in rear_spike_indices:
    
    
        # ✅ skip flat segments only if this detected spike is not already valid
        if flat_mask[idx] and not (rear_rr_spike[idx] or rear_rl_spike[idx]):
            continue
    
        # ✅ safe slicing
        low_chk = max(0, idx - 5)
        high_chk = min(n, idx + 5)
    
        if np.any(rear_rr_flat[low_chk:high_chk]) or np.any(rear_rl_flat[low_chk:high_chk]):
            continue
    
        # ✅ avoid edges
        if idx < 2 or idx > n - 3:
            continue
    
        # ✅ compute reference from cleaned signals
        rr_ref = (y_rr_clean[idx-2] + y_rr_clean[idx-1] +
                  y_rr_clean[idx+1] + y_rr_clean[idx+2]) / 4
    
        rl_ref = (y_rl_clean[idx-2] + y_rl_clean[idx-1] +
                  y_rl_clean[idx+1] + y_rl_clean[idx+2]) / 4
    
        rr_dev = abs(y_rr[idx] - rr_ref)
        rl_dev = abs(y_rl[idx] - rl_ref)
    
        cross_diff = abs(y_rl[idx] - y_rr[idx])
        # ✅ if both signals have same local spike/movement shape, do not clean
        if same_shape_behavior(
            y_rl,
            y_rr,
            idx - 4,
            idx + 5,
            corr_min=common_slope_corr_min
        ):
            continue
    
        # ✅ window for fixing spike (Reject common movement
        if same_shape_behavior(
            y_rl,
            y_rr,
            idx - 4,
            idx + 5,
            corr_min=common_slope_corr_min
        ):
            continue
        
        # Clean only the detected spike and one sample on each side
        low = max(0, idx - 1)
        high = min(n, idx + 2)
        
        # Continue with your existing final decision below
        # ✅ decision
        # =====================================================
        # ✅ FINAL DECISION (FIXED LOGIC)
        # =====================================================
        
        # ✅ CASE 1: strong RR step → NOT a fault
        # ✅ CASE 1: skip only if spike is on the same side as step fault
        if rear_rr_spike[idx] and step_mask_rr_side[idx]:
            continue

        if rear_rl_spike[idx] and step_mask_rl_side[idx]:
            continue
        # ✅ CASE 2: signals close → no fault
        elif cross_diff < spike_jump:
            continue
        
        # ✅ CASE 3: RL clearly deviates MUCH more
        elif rl_dev > rr_dev * 2.0:
            # RL is faulty
        
            if should_self_interpolate_fault(y_rl, low, high, value_threshold):
                y_rl_clean = self_interpolate_slice(y_rl_clean, low, high)
            else:
                y_rl_clean[low:high] = y_rr[low:high]
        
            spike_fault_is_rl[idx] = True
        # ✅ CASE 4: RR clearly deviates MUCH more
        elif rr_dev > rl_dev * 2.0:
            # RR is faulty
        
            if should_self_interpolate_fault(y_rr, low, high, value_threshold):
                y_rr_clean = self_interpolate_slice(y_rr_clean, low, high)
            else:
                y_rr_clean[low:high] = y_rl[low:high]
        
            spike_fault_is_rr[idx] = True

        # ✅ CASE 5: unclear → DO NOTHING
        else:
            continue
    
    # =====================================================
    # MERGE SPIKE EVENTS FOR PLOTTING ONLY
    #
    # Cleaning above still uses all rear_spike_indices.
    # This block only reduces repeated zoom plots.
    # If spike detections are within 3 seconds, only one plot is created.
    # =====================================================
    
    rear_spike_plot_indices = []
    merge_spike_plot_gap_sec = 3.0
    
    last_plot_time = -np.inf
    
    for idx in rear_spike_indices:
    
        idx = int(idx)
    
        # Only consider spikes that were actually cleaned
        if not (spike_fault_is_rl[idx] or spike_fault_is_rr[idx]):
            continue
    
        # If this spike is close to the last plotted spike, do not plot again
        if t_rear[idx] - last_plot_time <= merge_spike_plot_gap_sec:
            continue
    
        rear_spike_plot_indices.append(idx)
        last_plot_time = t_rear[idx]
    
    rear_spike_plot_indices = np.array(rear_spike_plot_indices, dtype=int)
    
    print(
        f"{axle_name}: merged Spike plot events -> "
        f"{len(rear_spike_plot_indices)}"
    )
    # =====================================================
    # =====================================================
    # CLEAN GLOBAL LONG STUCK / FROZEN CHANNEL FAULTS BY SUBSTITUTION
    # =====================================================
    
    global_stuck_events = []
    
    global_flat_range_max = 35.0
    global_flat_std_max = 8.0
    active_range_min = 80.0
    near_zero_diff_min = 80.0
    
    far_from_zero_abs_min = 1000.0
    far_stuck_tol = 35.0
    far_stuck_fraction_min = 0.80
    
    
    def global_stuck_info(y):
        y = np.asarray(y)
    
        med = np.median(y)
        mean = np.mean(y)
        std = np.std(y)
        full_range = np.ptp(y)
    
        close_frac = np.mean(np.abs(y - med) < far_stuck_tol)
    
        # Normal stuck: almost constant full signal
        flat = (
            std < global_flat_std_max and
            full_range < global_flat_range_max
        )
    
        # Far stuck: stuck far from zero, but may contain small spikes/noise
        far_stuck = (
            abs(med) > far_from_zero_abs_min and
            close_frac >= far_stuck_fraction_min
        )
    
        stuck = flat or far_stuck
    
        active = (
            full_range > active_range_min and
            not stuck
        )
    
        return {
            "mean": mean,
            "median": med,
            "std": std,
            "range": full_range,
            "close_frac": close_frac,
            "flat": flat,
            "far_stuck": far_stuck,
            "stuck": stuck,
            "active": active
        }
    
    
    left_info = global_stuck_info(y_rl)
    right_info = global_stuck_info(y_rr)
    
    
    file_duration_s = t_rear[-1] - t_rear[0] if len(t_rear) > 1 else 0.0
    
    if file_duration_s >= min_stuck_duration_s:
    
        # =====================================================
        # =====================================================
        # CASE 1: BOTH SIDES STUCK/FLAT
        #
        # Use the side closer to zero as reference.
        # This fixes:
        #   Rear: RL +24 Nm, RR -83 Nm -> RR = RL
        #   Front: FL -292 Nm, FR -41 Nm -> FL = FR
        # =====================================================
        if left_info["stuck"] and right_info["stuck"]:

            left_abs = abs(left_info["median"])
            right_abs = abs(right_info["median"])

            # Minimum separation only to avoid changing two almost identical flat channels
            both_flat_zero_diff_min = 10.0

            if left_abs > right_abs + both_flat_zero_diff_min:

                # LEFT is farther from zero, RIGHT is reference
                y_rl_clean[:] = y_rr_clean[:]
                spike_fault_is_rl[:] = True

                global_stuck_events.append({
                    "start": 0,
                    "end": n,
                    "left_fault": True,
                    "right_fault": False,
                    "error_type": "GlobalStuck_Left_from_Right"
                })

                print(
                    f"{axle_name}: BOTH STUCK -> LEFT farther from zero. "
                    f"LEFT substituted from RIGHT."
                )

            elif right_abs > left_abs + both_flat_zero_diff_min:

                # RIGHT is farther from zero, LEFT is reference
                y_rr_clean[:] = y_rl_clean[:]
                spike_fault_is_rr[:] = True

                global_stuck_events.append({
                    "start": 0,
                    "end": n,
                    "left_fault": False,
                    "right_fault": True,
                    "error_type": "GlobalStuck_Right_from_Left"
                })

                print(
                    f"{axle_name}: BOTH STUCK -> RIGHT farther from zero. "
                    f"RIGHT substituted from LEFT."
                )

            else:
                print(
                    f"{axle_name}: BOTH STUCK but levels are too close. "
                    f"No global stuck substitution applied."
                )
    
        # =====================================================
        # CASE 2: LEFT STUCK, RIGHT ACTIVE
        # =====================================================
        elif left_info["stuck"] and right_info["active"]:
    
            y_rl_clean[:] = y_rr_clean[:]
            spike_fault_is_rl[:] = True
    
            global_stuck_events.append({
                "start": 0,
                "end": n,
                "left_fault": True,
                "right_fault": False,
                "error_type": "GlobalStuck_Left_from_Right"
            })
    
    
        # =====================================================
        # CASE 3: RIGHT STUCK, LEFT ACTIVE
        # =====================================================
        elif right_info["stuck"] and left_info["active"]:
    
            y_rr_clean[:] = y_rl_clean[:]
            spike_fault_is_rr[:] = True
    
            global_stuck_events.append({
                "start": 0,
                "end": n,
                "left_fault": False,
                "right_fault": True,
                "error_type": "GlobalStuck_Right_from_Left"
            })
  
 
    # =====================================================
    # FINAL SANITIZE CLEANED SIGNALS BEFORE PLOTTING/SAVING
    # =====================================================
    y_rl_clean = np.nan_to_num(y_rl_clean, nan=0.0, posinf=0.0, neginf=0.0)
    y_rr_clean = np.nan_to_num(y_rr_clean, nan=0.0, posinf=0.0, neginf=0.0)
    
    # =====================================================
    # IF NO CLEANED FAULT IN THIS AXLE, RETURN NOTHING
    # =====================================================

    has_cleaned_fault = (
        np.any(step_fault_is_rr) or
        np.any(step_fault_is_rl) or
        np.any(spike_fault_is_rr) or
        np.any(spike_fault_is_rl)
    )
    
    # =====================================================
    # ALWAYS PREPARE AXLE PLOT DATA FOR FULL t=_all PLOTS
    # Even if this axle has no cleaned fault.
    # Important for AWD:
    # Rear may have faults while Front has no faults, but Front must still appear
    # in full original/cleaned before-after plots.
    # =====================================================
    
    if axle_name.lower() == "rear":
        left_color = "blue"
        right_color = "red"
    else:
        left_color = "cyan"
        right_color = "orange"
    
    axle_plot_data = {
        "axle": axle_name,
        "t": t_rear,
    
        "left_name": left_name,
        "right_name": right_name,
    
        "y_left_orig": y_rl,
        "y_right_orig": y_rr,
    
        "y_left_clean": y_rl_clean,
        "y_right_clean": y_rr_clean,
    
        "left_color": left_color,
        "right_color": right_color
    }
    
    if not has_cleaned_fault:
        print(f"{axle_name}: no cleaned fault -> no cleaned channels, but return plot data")
        return [], [], axle_plot_data
        
    # =====================================================
    # PLOTTING
    # =====================================================
    
    # =====================================================
    # COMMON Y-AXIS LIMITS FOR ZOOM PLOTS
    # =====================================================
    
    y_all = np.concatenate([
        y_rl,
        y_rr
    ])
        
    if has_other_axle:
        y_all = np.concatenate([
            y_all,
            y_ol,
            y_or
        ])
    
    y_min = np.min(y_all)
    y_max = np.max(y_all)
    
    y_margin = 0.05 * (y_max - y_min) if y_max > y_min else 1.0
    
    common_ylim = (y_min - y_margin, y_max + y_margin)
    
    
 

    # =====================================================
    # ✅ FLAT-TOP ERRORS
    # =====================================================
    
    for start, end in step_segments:
    
    
        # center of flat-top
        t_center = (t_rear[start] + t_rear[end]) / 2
    
        # ---------------------------
        # ✅ BEFORE VIEW
        # ---------------------------
        event_start_time = t_rear[start]
        event_end_time = t_rear[end]
        
        mask, zoom_start, zoom_end = make_event_mask(
            t_rear,
            event_start_time,
            event_end_time,
            margin_sec=1.5,
            min_zoom_sec=3.0
        )
        zoom_sec = zoom_end - zoom_start
        t_center = (zoom_start + zoom_end) / 2.0
        if has_other_axle:
            mask_other = (t_other >= zoom_start) & (t_other <= zoom_end)
        plt.figure(figsize=(12, 5))
    
        plot_with_label(t_rear[mask], y_rl[mask], 'blue', left_name)
        plot_with_label(t_rear[mask], y_rr[mask], 'red',  right_name)
        if has_other_axle:
            plot_with_label(t_other[mask_other], y_ol[mask_other], 'cyan', other_left_name)
            plot_with_label(t_other[mask_other], y_or[mask_other], 'orange', other_right_name)
        plt.title(f"{axle_name} axle - Before Step/Plateau ({t_rear[start]:.3f} → {t_rear[end]:.3f})")
        plt.xlabel("Time [s]")
        plt.ylabel("Torque [Nm]")
        plt.ylim(common_ylim)
        plt.legend()
        
     
        img_name = make_axle_img_name(file_stem, axle_name, t_center, "1before")
        img_path = finish_plot(fig_dir, img_name, show_plots)
        
        
        zoom_mf4_path = ""
        
        # ---------------------------
        # ✅ CLEANED VIEW
        # ---------------------------
        event_start_time = t_rear[start]
        event_end_time = t_rear[end]
        
        mask, zoom_start, zoom_end = make_event_mask(
            t_rear,
            event_start_time,
            event_end_time,
            margin_sec=1.5,
            min_zoom_sec=3.0
        )
        zoom_sec = zoom_end - zoom_start
        t_center = (zoom_start + zoom_end) / 2.0
        if has_other_axle:
            mask_other = (t_other >= zoom_start) & (t_other <= zoom_end)
        
        plt.figure(figsize=(12, 5))
    
        # ✅ SHOW FLAT CLEANING (this was missing!)
        seg_len = max(1, end - start + 1)

        rr_fault_ratio = np.sum(step_fault_is_rr[start:end+1]) / seg_len
        rl_fault_ratio = np.sum(step_fault_is_rl[start:end+1]) / seg_len

        # ✅ Plot right side: faulty+cleaned if faulty, otherwise original
        # ✅ AFTER plot must always show cleaned processed axle signals
        # If no cleaning happened, clean == original, so this is safe.
        plot_with_label(
            t_rear[mask],
            y_rl_clean[mask],
            'blue',
            f"{left_name}_CLEAN"
        )
        
        plot_with_label(
            t_rear[mask],
            y_rr_clean[mask],
            'red',
            f"{right_name}_CLEAN"
        )
        
        # ✅ Always show other axle as reference
        if has_other_axle:
            plot_with_label(t_other[mask_other], y_ol[mask_other], 'cyan', other_left_name)
            plot_with_label(t_other[mask_other], y_or[mask_other], 'orange', other_right_name)
       
        
        # ✅ FIX TITLE
        plt.title(f"{axle_name} Step/Plateau – Cleaned ({t_rear[start]:.3f} → {t_rear[end]:.3f})")
        
        plt.xlabel("Time [s]")
        plt.ylabel("Torque [Nm]")
        plt.ylim(common_ylim)
        plt.legend()

        img_name = make_axle_img_name(file_stem, axle_name, t_center, "2after")
        img_path = finish_plot(fig_dir, img_name, show_plots)
        
        zoom_mf4_path = ""

        
        log_rows.append({
            "file_name": file_stem,
            "axle": axle_name,
            "window_name": img_name,
            "view": "2after",
            "error_type": "StepPlateau",
            "t_value": f"{t_center:.1f}",
            "start_time_s": f"{t_rear[start]:.6f}",
            "end_time_s": f"{t_rear[end]:.6f}",
            "center_time_s": f"{t_center:.6f}",
            "sample_start": start,
            "sample_end": end,
            "image_path": str(img_path) if img_path else "",
            "zoom_mf4_path": str(zoom_mf4_path) if zoom_mf4_path else ""
        })

    
    # =====================================================
    # ✅ SPIKE ERRORS
    # =====================================================
    
    for idx in rear_spike_plot_indices:
    
        
        # Do not skip whole axle step_mask here.
        # A spike on one side can exist inside a step on the other side.
        if rear_rr_spike[idx] and step_mask_rr_side[idx]:
             continue

        if rear_rl_spike[idx] and step_mask_rl_side[idx]:
            continue

    
        # ✅ only plot spikes that were actually cleaned
        if not (spike_fault_is_rl[idx] or spike_fault_is_rr[idx]):
            continue
    
    
        t_center = t_rear[idx]
    
        # ---------------------------
        # ✅ BEFORE VIEW
        # ---------------------------
        zoom_sec = 3.0
        mask = (t_rear >= t_center - zoom_sec/2) & (t_rear <= t_center + zoom_sec/2)
    
        plt.figure(figsize=(12, 5))

        plot_with_label(t_rear[mask], y_rl[mask], 'blue', left_name)
        plot_with_label(t_rear[mask], y_rr[mask], 'red',  right_name)
        
        # Show other axle as reference if available
        if has_other_axle:
            mask_other = (
                (t_other >= t_center - zoom_sec / 2) &
                (t_other <= t_center + zoom_sec / 2)
            )
        
            plot_with_label(t_other[mask_other], y_ol[mask_other], 'cyan', other_left_name)
            plot_with_label(t_other[mask_other], y_or[mask_other], 'orange', other_right_name)
        
        plt.title(f"{axle_name} axle - Before Spike ({t_center:.3f}s)")
        plt.xlabel("Time [s]")
        plt.ylabel("Torque [Nm]")
        plt.ylim(common_ylim)
        plt.legend()

        img_name = make_axle_img_name(file_stem, axle_name, t_center, "1before")
        img_path = finish_plot(fig_dir, img_name, show_plots)
        
        zoom_mf4_path = ""
        
        # ---------------------------
        # ✅ CLEANED VIEW
        # ---------------------------
        zoom_sec = 3.0
        mask = (t_rear >= t_center - zoom_sec/2) & (t_rear <= t_center + zoom_sec/2)
    
    
        plt.figure(figsize=(12, 5))

        if spike_fault_is_rl[idx]:
            # RL/left-side faulty
            plot_with_label(t_rear[mask], y_rl_clean[mask], 'blue', f"{left_name}_CLEAN")
            plot_with_label(t_rear[mask], y_rr[mask], 'red', right_name)
        
        else:
            # RR/right-side faulty
            plot_with_label(t_rear[mask], y_rr_clean[mask], 'red', f"{right_name}_CLEAN")
            plot_with_label(t_rear[mask], y_rl[mask], 'blue', left_name)
        
        # Show other axle as reference if available
        if has_other_axle:
            mask_other = (
                (t_other >= t_center - zoom_sec / 2) &
                (t_other <= t_center + zoom_sec / 2)
            )
        
            plot_with_label(t_other[mask_other], y_ol[mask_other], 'cyan', other_left_name)
            plot_with_label(t_other[mask_other], y_or[mask_other], 'orange', other_right_name)
            
      
        # ✅ correct title
        plt.title(f"{axle_name} axle - Spike – Cleaned ({t_center:.3f}s)")
    
        plt.xlabel("Time [s]")
        plt.ylabel("Torque [Nm]")
        plt.ylim(common_ylim)
        plt.legend()

        img_name = make_axle_img_name(file_stem, axle_name, t_center, "2after")
        img_path = finish_plot(fig_dir, img_name, show_plots)
        
        zoom_mf4_path = ""
        
        log_rows.append({
            "file_name": file_stem,
            "axle": axle_name,
            "window_name": img_name,
            "view": "2after",
            "error_type": "Spike",
            "t_value": f"{t_center:.1f}",
            "start_time_s": f"{t_center - zoom_sec/2:.6f}",
            "end_time_s": f"{t_center + zoom_sec/2:.6f}",
            "center_time_s": f"{t_center:.6f}",
            "sample_start": idx,
            "sample_end": idx,
            "image_path": str(img_path) if img_path else "",
            "zoom_mf4_path": str(zoom_mf4_path) if zoom_mf4_path else ""
        })
 
    # =====================================================
    # ✅ SHORT / THIN ERROR ZOOM PLOTS
    # =====================================================
    short_zoom_sec = 0.2   # much smaller zoom for thin events

    for ev in short_events:
        start = ev["start"]
        end = ev["end"]

        # only plot if actually cleaned
        left_cleaned_here = np.any(spike_fault_is_rl[start:end+1])
        right_cleaned_here = np.any(spike_fault_is_rr[start:end+1])

        if not (left_cleaned_here or right_cleaned_here):
            continue

        t_center = (t_rear[start] + t_rear[end]) / 2

        mask = (
            (t_rear >= t_center - short_zoom_sec / 2) &
            (t_rear <= t_center + short_zoom_sec / 2)
        )

        if has_other_axle:
            mask_other = (
                (t_other >= t_center - short_zoom_sec / 2) &
                (t_other <= t_center + short_zoom_sec / 2)
            )

        # ---------------------------
        # ✅ BEFORE VIEW
        # ---------------------------
        plt.figure(figsize=(12, 5))

        plot_with_label(t_rear[mask], y_rl[mask], 'blue', left_name)
        plot_with_label(t_rear[mask], y_rr[mask], 'red', right_name)

        if has_other_axle:
            plot_with_label(t_other[mask_other], y_ol[mask_other], 'cyan', other_left_name)
            plot_with_label(t_other[mask_other], y_or[mask_other], 'orange', other_right_name)

        plt.title(
            f"{axle_name} axle - Before Short/Thin Error "
            f"({t_rear[start]:.6f} → {t_rear[end]:.6f})"
        )
        plt.xlabel("Time [s]")
        plt.ylabel("Torque [Nm]")
        plt.ylim(common_ylim)
        plt.legend()

        
        img_name = f"{file_stem}_{axle_name}~(t={t_center:.6f})_ShortThin_1before.png"
        img_path = finish_plot(fig_dir, img_name, show_plots)

        zoom_mf4_path = ""

        # ---------------------------
        # ✅ CLEANED VIEW
        # ---------------------------
        plt.figure(figsize=(12, 5))

        if left_cleaned_here:
            plot_with_label(t_rear[mask], y_rl_clean[mask], 'blue', f"{left_name}_CLEAN")
        else:
            plot_with_label(t_rear[mask], y_rl[mask], 'blue', left_name)

        if right_cleaned_here:
            plot_with_label(t_rear[mask], y_rr_clean[mask], 'red', f"{right_name}_CLEAN")
        else:
            plot_with_label(t_rear[mask], y_rr[mask], 'red', right_name)

        if has_other_axle:
            plot_with_label(t_other[mask_other], y_ol[mask_other], 'cyan', other_left_name)
            plot_with_label(t_other[mask_other], y_or[mask_other], 'orange', other_right_name)

        

        plt.title(
            f"{axle_name} axle - Short/Thin Error – Cleaned "
            f"({t_rear[start]:.6f} → {t_rear[end]:.6f})"
        )
        plt.xlabel("Time [s]")
        plt.ylabel("Torque [Nm]")
        plt.ylim(common_ylim)
        plt.legend()

        img_name = f"{file_stem}_{axle_name}~(t={t_center:.6f})_ShortThin_2after.png"
        img_path = finish_plot(fig_dir, img_name, show_plots)

        zoom_mf4_path = ""

        log_rows.append({
            "file_name": file_stem,
            "axle": axle_name,
            "window_name": img_name,
            "view": "2after",
            "error_type": "ShortThin",
            "t_value": f"{t_center:.6f}",
            "start_time_s": f"{t_rear[start]:.6f}",
            "end_time_s": f"{t_rear[end]:.6f}",
            "center_time_s": f"{t_center:.6f}",
            "sample_start": start,
            "sample_end": end,
            "image_path": str(img_path) if img_path else "",
            "zoom_mf4_path": str(zoom_mf4_path) if zoom_mf4_path else ""
        })
    # =====================================================
    
    # RETURN CLEANED SIGNALS AND LOG ROWS
    # =====================================================

    cleaned_signals = []
    # remove any NaN / inf before saving
    y_rl_clean = np.nan_to_num(y_rl_clean, nan=0.0, posinf=0.0, neginf=0.0)
    y_rr_clean = np.nan_to_num(y_rr_clean, nan=0.0, posinf=0.0, neginf=0.0)
    
    sig_left_clean = Signal(
        samples=y_rl_clean,
        timestamps=t_rear,
        name=left_name,      # same original channel name
        unit=getattr(sig_rl, "unit", "Nm"),
        comment=f"Cleaned version of {left_name}"
    )
    
    sig_right_clean = Signal(
        samples=y_rr_clean,
        timestamps=t_rear,
        name=right_name,     # same original channel name
        unit=getattr(sig_rr, "unit", "Nm"),
        comment=f"Cleaned version of {right_name}"
    )

    cleaned_signals.append(sig_left_clean)
    cleaned_signals.append(sig_right_clean)
    
    return cleaned_signals, log_rows, axle_plot_data


# =====================================================
# RUN AXLES
# Works for AWD, RWD, FWD
# =====================================================

# =====================================================
# RECURSIVE BATCH PROCESSING
# =====================================================
default_root_folder = Path(
    r"\\GBW9061113.got.volvocars.net\proj\9413-shr-vcc26400\97770_Dim\RLD\Personal_Folders\Mulubrhan_A"
)

root_folder = select_root_folder(default_root_folder)

# =====================================================
# CREATE EDITED ROOT FOLDER
# Example:
# Measurement -> Measurement_Edited
# =====================================================
edited_root_folder = root_folder.parent / f"{root_folder.name}_Edited"
edited_root_folder.mkdir(parents=True, exist_ok=True)

print("Original root folder:", root_folder)
print("Edited root folder  :", edited_root_folder)

# =====================================================
# FIND MEASUREMENT FILES ONLY FROM ORIGINAL ROOT
# =====================================================
measurement_files = (
    list(root_folder.rglob("*.mdf")) +
    list(root_folder.rglob("*.MDF")) +
    list(root_folder.rglob("*.mf4")) +
    list(root_folder.rglob("*.MF4")) +
    list(root_folder.rglob("*.dat")) +
    list(root_folder.rglob("*.DAT"))
)

# remove duplicates
measurement_files = list(dict.fromkeys(measurement_files))

# skip already edited / zoom / image / ML files if they exist inside original
measurement_files = [
    p for p in measurement_files
    if "_edited" not in p.stem.lower()
    and "~(t=" not in p.stem.lower()
    and p.parent.name.lower() not in ["images_edited", "ml_next"]
    and "_edited" not in str(p.parent).lower()
]

measurement_files = sorted(measurement_files)

print("Measurement files found:", len(measurement_files))

# =====================================================
# PROCESS FILES
# =====================================================
for file_path in measurement_files:

    print("\n" + "#" * 100)
    print("PROCESSING FILE:", file_path)
    print("#" * 100)

    try:
        file_stem = file_path.stem

        drive_text = str(file_path).upper()
        is_rwd = "RWD" in drive_text
        is_fwd = "FWD" in drive_text
        is_awd = "AWD" in drive_text

        mdf = MDF(str(file_path))

        # =====================================================
        # MIRROR ORIGINAL SUBFOLDER STRUCTURE INTO Edited ROOT
        # =====================================================
        relative_parent = file_path.parent.relative_to(root_folder)
        output_dir = edited_root_folder / relative_parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # PNG images
        fig_dir = output_dir / "Images_Edited"
        fig_dir.mkdir(parents=True, exist_ok=True)

        cleaned_signals_all = []
        file_log_rows = []
        axle_plot_data_all = []

        # =====================================================
        # REAR AXLE
        # =====================================================
        if not is_fwd:
            try:
                cleaned_rear, log_rear, plot_rear = process_axle(
                    mdf,
                    "Rear",
                    ["TQ_RL", "Tq_RL"],
                    ["TQ_RR", "Tq_RR"],
                    other_left_candidates=["TQ_FL", "Tq_FL"],
                    other_right_candidates=["TQ_FR", "Tq_FR"],
                    fig_dir=fig_dir,
                    show_plots=False,
                    file_stem=file_stem
                )

                cleaned_signals_all += cleaned_rear
                file_log_rows += log_rear

                if plot_rear is not None:
                    axle_plot_data_all.append(plot_rear)

            except Exception as e:
                print("Rear axle not available or failed:", e)

        else:
            print("FWD file detected -> skipping Rear processing")

        # =====================================================
        # FRONT AXLE
        # =====================================================
        if not is_rwd:
            try:
                cleaned_front, log_front, plot_front = process_axle(
                    mdf,
                    "Front",
                    ["TQ_FL", "Tq_FL"],
                    ["TQ_FR", "Tq_FR"],
                    other_left_candidates=["TQ_RL", "Tq_RL"],
                    other_right_candidates=["TQ_RR", "Tq_RR"],
                    fig_dir=fig_dir,
                    show_plots=False,
                    file_stem=file_stem
                )

                cleaned_signals_all += cleaned_front
                file_log_rows += log_front

                if plot_front is not None:
                    axle_plot_data_all.append(plot_front)

            except Exception as e:
                print("Front axle not available or failed:", e)

        else:
            print("RWD file detected -> skipping Front processing")

        print("Cleaned signals count:", len(cleaned_signals_all))
        print("Axle plot data count :", len(axle_plot_data_all))
        print("Log rows count       :", len(file_log_rows))

        # =====================================================
        # IF NO CLEANED FAULTS IN THIS FILE
        # SAVE ORIGINAL AS NORMAL MF4 INSIDE Edited ROOT
        # =====================================================
        if len(cleaned_signals_all) == 0:

            normal_output_file = output_dir / f"{file_stem}.mf4"

            if normal_output_file.exists():
                print("No cleaned faults -> original MF4 already exists, skipped:", normal_output_file)

            else:
                if file_path.suffix.lower() == ".mf4":
                    shutil.copy2(file_path, normal_output_file)
                    print("No cleaned faults -> copied original MF4:", normal_output_file)

                else:
                    mdf_original = mdf.convert(version="4.10")
                    mdf_original.save(str(normal_output_file), overwrite=True)
                    print("No cleaned faults -> saved original as MF4:", normal_output_file)

            continue

        # =====================================================
        # OUTPUT FILE PATHS
        # =====================================================
        output_file = output_dir / f"{file_stem}_Edited.mf4"
        log_file = output_dir / f"{file_stem}_Edited_Log.xlsx"

        # =====================================================
        # SAVE FULL-RANGE BEFORE/AFTER PLOTS FIRST
        # Important:
        # If MF4 save fails later, full _all images are still saved.
        # =====================================================
        try:
            full_log_rows = save_full_processed_axles_plots(
                axle_plot_data_all=axle_plot_data_all,
                fig_dir=fig_dir,
                file_stem=file_stem,
                show_plots=False
            )

            file_log_rows += full_log_rows

            print("Saved full-range before/after plots for:", file_stem)

        except Exception as e:
            print("FAILED to save full-range plots:", e)

        # =====================================================
        # SAVE EXCEL LOG BEFORE MF4 SAVE
        # Important:
        # If MF4 save fails, log still exists.
        # =====================================================
        wanted_columns = [
            "file_name",
            "axle",
            "window_name",
            "error_type",
            "start_time_s",
            "end_time_s",
            "image_path"
        ]

        try:
            if len(file_log_rows) > 0:
                df_log = pd.DataFrame(file_log_rows)
                df_log = df_log.reindex(columns=wanted_columns)
                df_log.to_excel(log_file, index=False, engine="openpyxl")
                print("Saved Excel log:", log_file)

        except Exception as e:
            print("FAILED to save Excel log:", e)

        # =====================================================
        # SAVE FULL EDITED MF4
        # keep all original non-torque signals
        # replace torque channels with cleaned torque channels
        # =====================================================
        try:
            cleaned_torque_names = set()

            for sig in cleaned_signals_all:
                cleaned_torque_names.add(sig.name.lower())

            channels_to_keep = []

            for ch_name, occurrences in mdf.channels_db.items():

                # Skip original torque channels that will be replaced
                if ch_name.lower() in cleaned_torque_names:
                    continue

                # Keep every exact occurrence by group/index
                for group_index, channel_index in occurrences:
                    channels_to_keep.append((ch_name, group_index, channel_index))

            # Keep all original non-cleaned channels
            mdf_out = mdf.filter(channels_to_keep)

            # Append cleaned torque channels using original names
            mdf_out.append(cleaned_signals_all)

            # Save as MDF4
            mdf_out = mdf_out.convert(version="4.10")
            mdf_out.save(str(output_file), overwrite=True)

            print("Saved cleaned full MF4 with original torque names:", output_file)
            print("Saved full edited MF4:", output_file)

        except Exception as e:
            print("FAILED to save cleaned full MF4:", output_file)
            print("MF4 SAVE ERROR:", e)

    except Exception as e:
        print("FAILED FILE:", file_path)
        print("ERROR:", e)