#!/usr/bin/env python3
"""
Windows System Backup Utility v1.0.0

Interactive Windows backup utility.

Run:
    python windows_system_backup_utility.py
"""

from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import json
import os
import platform
import shutil
import socket
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional


VERSION = "v1.0.0"
PROJECT_NAME = "Windows System Backup Utility"

DEFAULT_EXCLUDED_FOLDER_NAMES = {
    "node_modules",
    ".next",
    "dist",
    "build",
    "target",
    "bin",
    "obj",
    ".venv",
    "__pycache__",
    "Temp",
    "tmp",
    "$Recycle.Bin",
    "System Volume Information",
}

DRIVE_REMOVABLE = 2
DRIVE_FIXED = 3

TRANSCRIPT_LINES: List[str] = []


def log(message: str = "") -> None:
    print(message)
    TRANSCRIPT_LINES.append(str(message))


def input_logged(prompt: str) -> str:
    answer = input(prompt)
    TRANSCRIPT_LINES.append(prompt + answer)
    return answer


def print_section(title: str) -> None:
    log()
    log("=" * 60)
    log(title)
    log("=" * 60)


def format_bytes(size: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:,.2f} {unit}"
        value /= 1024
    return f"{size:,.2f} B"


def normalize_drive(drive: str) -> str:
    drive = drive.strip().replace("/", "\\")
    if len(drive) == 1:
        drive += ":"
    if not drive.endswith("\\"):
        drive += "\\"
    return drive


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def is_admin() -> bool:
    if not is_windows():
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def get_drive_type(root: str) -> int:
    return int(ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(root)))


def get_drive_label(root: str) -> str:
    volume_name_buffer = ctypes.create_unicode_buffer(1024)
    file_system_buffer = ctypes.create_unicode_buffer(1024)
    serial_number = ctypes.c_ulong()
    max_component_length = ctypes.c_ulong()
    file_system_flags = ctypes.c_ulong()

    try:
        result = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(root),
            volume_name_buffer,
            ctypes.sizeof(volume_name_buffer),
            ctypes.byref(serial_number),
            ctypes.byref(max_component_length),
            ctypes.byref(file_system_flags),
            file_system_buffer,
            ctypes.sizeof(file_system_buffer),
        )
        if result:
            return volume_name_buffer.value or "No Label"
    except Exception:
        pass

    return "Unknown"


def get_logical_drives() -> List[Dict[str, object]]:
    if not is_windows():
        return []

    drives: List[Dict[str, object]] = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()

    for letter_ord in range(ord("A"), ord("Z") + 1):
        if bitmask & 1:
            root = f"{chr(letter_ord)}:\\"
            drive_type = get_drive_type(root)

            if drive_type in {DRIVE_REMOVABLE, DRIVE_FIXED}:
                try:
                    usage = shutil.disk_usage(root)
                    drives.append(
                        {
                            "root": root,
                            "letter": chr(letter_ord),
                            "type": drive_type,
                            "type_name": "Removable/External" if drive_type == DRIVE_REMOVABLE else "Fixed/Internal",
                            "label": get_drive_label(root),
                            "free": usage.free,
                            "total": usage.total,
                        }
                    )
                except Exception:
                    pass

        bitmask >>= 1

    return drives


def choose_destination_drive(provided_destination: Optional[str]) -> str:
    if provided_destination:
        destination = normalize_drive(provided_destination)
        if Path(destination).exists():
            return destination
        raise SystemExit(f"Destination drive was not found: {destination}")

    print_section("DESTINATION DRIVE SELECTION")

    drives = get_logical_drives()
    removable = [d for d in drives if d["type"] == DRIVE_REMOVABLE]
    fixed = [d for d in drives if d["type"] == DRIVE_FIXED]
    options = removable or fixed

    if removable:
        log("Detected removable/external drives:")
    else:
        log("No removable/external drives were detected.")
        log("Showing fixed/internal drives instead. Be careful not to select the source drive.")

    log()

    for index, drive in enumerate(options, start=1):
        log(
            f"[{index}] {drive['root']}  {drive['label']}  "
            f"Free: {format_bytes(float(drive['free']))}  "
            f"Total: {format_bytes(float(drive['total']))}  "
            f"Type: {drive['type_name']}"
        )

    log()
    log("Choose the destination drive number, or enter a drive letter such as E:")
    log("This should be your external hard drive, external SSD, or USB storage device.")
    log()

    while True:
        answer = input_logged("Destination drive: ").strip()

        if answer.isdigit():
            idx = int(answer)
            if 1 <= idx <= len(options):
                return str(options[idx - 1]["root"])

        candidate = normalize_drive(answer)
        if Path(candidate).exists():
            return candidate

        log("Invalid destination. Please choose a listed number or valid drive letter.")


def ask_yes_no(question: str, default: Optional[bool] = None) -> bool:
    suffix = " (Y/N): "
    if default is True:
        suffix = " (Y/n): "
    elif default is False:
        suffix = " (y/N): "

    while True:
        answer = input_logged(question + suffix).strip().lower()

        if not answer and default is not None:
            return default

        if answer in {"y", "yes"}:
            return True

        if answer in {"n", "no"}:
            return False

        log("Please enter Y or N.")


def explain_system_root_choice() -> None:
    print_section("OPTION: COPY ROOT OF C:\\")
    log("By default, this utility copies C:\\Users from the system drive.")
    log("That usually includes personal files, AppData, browser data, SSH keys, and user settings.")
    log()
    log("Copying the root of C:\\ means the utility will also attempt to copy folders outside C:\\Users, such as:")
    log("- C:\\Projects")
    log("- C:\\Repos")
    log("- C:\\Tools")
    log("- C:\\Scripts")
    log("- C:\\ProgramData")
    log()
    log("It may also scan protected Windows folders like C:\\Windows and C:\\Program Files.")
    log("Those folders can cause access errors and usually do not need to be copied for a personal backup.")
    log()
    log("Recommended for most users: N")


def explain_exclusions_choice() -> None:
    print_section("OPTION: DEFAULT EXCLUSIONS")
    log("Default exclusions skip folders that are usually large, temporary, or rebuildable.")
    log("This saves space and makes the backup faster.")
    log()
    log("Excluded by default:")
    for item in sorted(DEFAULT_EXCLUDED_FOLDER_NAMES):
        log(f"- {item}")
    log()
    log("Recommended for most users: Y")
    log("Choose N only if you want to copy these folders too and have enough storage.")


def show_disclaimer() -> None:
    log(
        r"""
============================================================
               WINDOWS SYSTEM BACKUP UTILITY
============================================================

WARNING

This utility is intended to create a backup of a Windows
computer before performing actions such as factory resets,
hardware replacement, operating system reinstallation,
device migration, storage replacement, or system maintenance.

COMMON USE CASES

✓ Factory reset preparation
✓ Operating system reinstall or migration
✓ Device replacement or upgrade
✓ Hardware maintenance or repair
✓ Storage device migration
✓ Disaster recovery preparation
✓ Development environment preservation
✓ Long-term archival

WHAT THIS TOOL ATTEMPTS TO BACK UP

✓ All user profiles under C:\Users
✓ Desktop, Documents, Downloads, Pictures, Videos, Music
✓ Hidden user files and folders
✓ AppData, including Roaming, Local, and LocalLow
✓ Browser profiles and locally stored browser data
✓ Git repositories, development projects, and source code
✓ User configuration files such as .ssh and .gitconfig
✓ Additional internal drives such as D:, E:, F:, etc.
✓ Local databases, virtual machines, and container folders if found
✓ Most personal files located on internal drives

WHAT MAY NOT BE FULLY BACKED UP

⚠ Cloud-only files that have not been downloaded locally
⚠ Locked encrypted drives
⚠ Files actively used or locked by running applications
⚠ Installed applications and software themselves
⚠ Windows operating system files and recovery partitions
⚠ Certain system-protected files
⚠ Running virtual machines, containers, databases, and services
⚠ Network shares unless mounted as normal local drives

DISCLAIMER

THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
KIND, EXPRESS OR IMPLIED. THE AUTHORS SHALL NOT BE LIABLE
FOR LOSS OF DATA, LOSS OF PROFITS, OR OTHER DAMAGES ARISING
FROM THE USE OF THIS SOFTWARE.

You are solely responsible for verifying the integrity and
completeness of your backups before deleting, resetting,
factory resetting, formatting, repairing, replacing, or
modifying your computer.

============================================================
"""
    )


def should_exclude(path: Path, excluded_names: set[str]) -> bool:
    parts = set(path.parts)
    return any(name in parts for name in excluded_names)


def get_backup_sources(destination_drive: str, include_system_root: bool) -> List[Dict[str, str]]:
    sources: List[Dict[str, str]] = []

    users_path = Path("C:/Users")
    if users_path.exists():
        sources.append(
            {
                "source": str(users_path),
                "name": "Users",
                "reason": "All Windows user profiles, personal files, AppData, browser profiles, SSH keys, Git config",
            }
        )

    destination_drive_upper = normalize_drive(destination_drive).upper()

    for drive in get_logical_drives():
        root = str(drive["root"])
        root_upper = normalize_drive(root).upper()

        if drive["type"] != DRIVE_FIXED:
            continue

        if root_upper == destination_drive_upper:
            continue

        if root_upper == "C:\\" and include_system_root:
            sources.append(
                {
                    "source": root,
                    "name": "Drive_C_Root",
                    "reason": "Entire C:\\ root requested by user",
                }
            )
        elif root_upper != "C:\\":
            sources.append(
                {
                    "source": root,
                    "name": f"Drive_{root[0].upper()}",
                    "reason": "Additional internal drive",
                }
            )

    return sources


def scan_source(source: Path, excluded_names: set[str]) -> Dict[str, object]:
    included_files = 0
    included_bytes = 0
    excluded_folders: Dict[str, int] = {}
    excluded_bytes = 0
    errors: List[str] = []

    for root, dirs, files in os.walk(source, topdown=True, onerror=lambda e: errors.append(str(e))):
        root_path = Path(root)

        kept_dirs = []
        for d in dirs:
            full_dir = root_path / d
            if d in excluded_names or should_exclude(full_dir, excluded_names):
                excluded_folders[d] = excluded_folders.get(d, 0) + 1
            else:
                kept_dirs.append(d)
        dirs[:] = kept_dirs

        for file_name in files:
            file_path = root_path / file_name

            if should_exclude(file_path, excluded_names):
                try:
                    excluded_bytes += file_path.stat().st_size
                except OSError as exc:
                    errors.append(f"{file_path}: {exc}")
                continue

            try:
                included_files += 1
                included_bytes += file_path.stat().st_size
            except OSError as exc:
                errors.append(f"{file_path}: {exc}")

    return {
        "path": str(source),
        "included_files": included_files,
        "included_bytes": included_bytes,
        "excluded_folders": excluded_folders,
        "excluded_bytes": excluded_bytes,
        "errors": errors,
    }


def merge_excluded_counts(scan_results: List[Dict[str, object]]) -> Dict[str, int]:
    merged: Dict[str, int] = {}
    for result in scan_results:
        folders = result["excluded_folders"]
        if isinstance(folders, dict):
            for name, count in folders.items():
                merged[name] = merged.get(name, 0) + int(count)
    return dict(sorted(merged.items(), key=lambda item: item[0].lower()))


def estimate_time_range(total_bytes: int) -> str:
    if total_bytes <= 0:
        return "Unknown"

    slow_seconds = total_bytes / (20 * 1024 * 1024)
    fast_seconds = total_bytes / (80 * 1024 * 1024)

    def fmt(seconds: float) -> str:
        minutes = int(seconds // 60)
        if minutes < 1:
            return "less than 1 minute"
        hours = minutes // 60
        mins = minutes % 60
        if hours:
            return f"{hours} hours {mins} minutes"
        return f"{mins} minutes"

    return f"{fmt(fast_seconds)} to {fmt(slow_seconds)}"


def log_error(error_log: Path, message: str) -> None:
    with error_log.open("a", encoding="utf-8") as file:
        file.write(message + "\n")


def copy_tree(source: Path, destination: Path, excluded_names: set[str], error_log: Path) -> Dict[str, int]:
    copied_files = 0
    copied_bytes = 0
    failed_files = 0

    for root, dirs, files in os.walk(source, topdown=True, onerror=lambda e: log_error(error_log, str(e))):
        root_path = Path(root)

        kept_dirs = []
        for d in dirs:
            full_dir = root_path / d
            if d in excluded_names or should_exclude(full_dir, excluded_names):
                continue
            kept_dirs.append(d)
        dirs[:] = kept_dirs

        try:
            relative_root = root_path.relative_to(source)
        except ValueError:
            relative_root = Path(".")

        target_root = destination / relative_root
        try:
            target_root.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            log_error(error_log, f"Could not create folder {target_root}: {exc}")
            continue

        for file_name in files:
            src_file = root_path / file_name
            dst_file = target_root / file_name

            if should_exclude(src_file, excluded_names):
                continue

            try:
                size = src_file.stat().st_size
                shutil.copy2(src_file, dst_file)
                copied_files += 1
                copied_bytes += size
            except Exception as exc:
                failed_files += 1
                log_error(error_log, f"{src_file} -> {dst_file}: {exc}")

    return {"copied_files": copied_files, "copied_bytes": copied_bytes, "failed_files": failed_files}


def calculate_folder_size(path: Path) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for file_name in files:
            try:
                total += (Path(root) / file_name).stat().st_size
            except OSError:
                pass
    return total


def count_error_lines(error_log: Path) -> int:
    if not error_log.exists():
        return 0
    return sum(1 for line in error_log.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())


def get_system_info() -> Dict[str, str]:
    return {
        "project_name": PROJECT_NAME,
        "version": VERSION,
        "generated_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "computer_name": socket.gethostname(),
        "username": os.environ.get("USERNAME") or os.environ.get("USER") or "Unknown",
        "user_domain": os.environ.get("USERDOMAIN", ""),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version_info": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "is_admin": str(is_admin()),
    }


def save_transcript(report_folder: Path) -> None:
    report_folder.mkdir(parents=True, exist_ok=True)
    (report_folder / "terminal-transcript.txt").write_text("\n".join(TRANSCRIPT_LINES), encoding="utf-8")


def save_execution_report(
    report_folder: Path,
    command: str,
    destination_root: Path,
    backup_sources: List[Dict[str, str]],
    excluded_names: set[str],
    scan_results: List[Dict[str, object]],
    free_bytes: int,
    user_choices: Dict[str, object],
    final_summary: Optional[Dict[str, object]] = None,
) -> None:
    report_folder.mkdir(parents=True, exist_ok=True)

    total_files = sum(int(r["included_files"]) for r in scan_results)
    total_bytes = sum(int(r["included_bytes"]) for r in scan_results)
    total_excluded_bytes = sum(int(r["excluded_bytes"]) for r in scan_results)
    total_errors = sum(len(r["errors"]) for r in scan_results if isinstance(r["errors"], list))

    report = {
        "system": get_system_info(),
        "command": command,
        "destination_root": str(destination_root),
        "user_choices": user_choices,
        "backup_sources": backup_sources,
        "excluded_folder_names": sorted(excluded_names),
        "summary": {
            "files_to_copy": total_files,
            "estimated_backup_bytes": total_bytes,
            "estimated_backup_size": format_bytes(total_bytes),
            "available_destination_bytes": free_bytes,
            "available_destination_size": format_bytes(free_bytes),
            "remaining_after_backup": format_bytes(free_bytes - total_bytes),
            "estimated_excluded_bytes": total_excluded_bytes,
            "estimated_excluded_size": format_bytes(total_excluded_bytes),
            "scan_error_count": total_errors,
            "rough_time_estimate": estimate_time_range(total_bytes),
        },
        "final_summary": final_summary or {},
        "scan_results": scan_results,
    }

    json_path = report_folder / "execution-report.json"
    txt_path = report_folder / "execution-report.txt"

    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        f"{PROJECT_NAME} {VERSION}",
        "",
        "EXECUTION REPORT",
        "",
        f"Generated At: {report['system']['generated_at']}",
        f"Computer Name: {report['system']['computer_name']}",
        f"Username: {report['system']['user_domain']}\\{report['system']['username']}",
        f"Platform: {report['system']['platform']}",
        f"Processor: {report['system']['processor']}",
        f"Python Version: {report['system']['python_version']}",
        f"Running As Admin: {report['system']['is_admin']}",
        "",
        f"Command Used: {command}",
        f"Destination Root: {destination_root}",
        "",
        "User Choices:",
        f"- Destination drive: {user_choices.get('destination_drive')}",
        f"- Include C root: {user_choices.get('include_system_root')}",
        f"- Use default exclusions: {user_choices.get('use_default_exclusions')}",
        "",
        "Backup Sources:",
    ]

    for source in backup_sources:
        lines.append(f"- {source['source']} => {source['name']} ({source['reason']})")

    lines.append("")
    lines.append("Excluded Folder Names:")
    if excluded_names:
        lines.extend([f"- {name}" for name in sorted(excluded_names)])
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "Scan Summary:",
            f"- Files to copy: {total_files:,}",
            f"- Estimated backup size: {format_bytes(total_bytes)}",
            f"- Available destination space: {format_bytes(free_bytes)}",
            f"- Remaining after backup: {format_bytes(free_bytes - total_bytes)}",
            f"- Estimated excluded size: {format_bytes(total_excluded_bytes)}",
            f"- Scan errors / inaccessible items: {total_errors}",
            f"- Rough time estimate: {estimate_time_range(total_bytes)}",
            "",
        ]
    )

    if final_summary:
        lines.extend(
            [
                "Final Copy Summary:",
                f"- Copied files: {final_summary.get('copied_files', 0):,}",
                f"- Copied size based on copy operations: {format_bytes(float(final_summary.get('copied_bytes', 0)))}",
                f"- Actual backup folder size: {format_bytes(float(final_summary.get('actual_backup_folder_bytes', 0)))}",
                f"- Failed files logged: {final_summary.get('failed_files', 0):,}",
                f"- Error log lines: {final_summary.get('copy_error_lines', 0):,}",
                "",
            ]
        )

    lines.extend(
        [
            "IMPORTANT:",
            "Verify this backup manually before wiping, formatting, factory resetting,",
            "repairing, replacing, or modifying the original device.",
            "",
        ]
    )

    txt_path.write_text("\n".join(lines), encoding="utf-8")


def save_backup_hierarchy(destination_root: Path, report_folder: Path) -> None:
    hierarchy_path = report_folder / "backup-hierarchy.txt"

    lines = [
        "BACKUP HIERARCHY",
        "",
        f"Destination: {destination_root}",
        "",
    ]

    max_depth = 3

    def walk_limited(path: Path, prefix: str = "", depth: int = 0) -> None:
        if depth > max_depth:
            return

        try:
            children = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            return

        visible_children = children[:100]
        for index, child in enumerate(visible_children):
            connector = "└── " if index == len(visible_children) - 1 else "├── "
            lines.append(f"{prefix}{connector}{child.name}")
            if child.is_dir():
                extension = "    " if index == len(visible_children) - 1 else "│   "
                walk_limited(child, prefix + extension, depth + 1)

        if len(children) > 100:
            lines.append(f"{prefix}└── ... {len(children) - 100} more items")

    walk_limited(destination_root)
    hierarchy_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{PROJECT_NAME} {VERSION}")
    parser.add_argument("--destination", help="Optional destination drive letter, for example E:")
    args = parser.parse_args()

    if not is_windows():
        print("This utility is intended to run on Windows.")
        return 1

    show_disclaimer()

    destination_drive = choose_destination_drive(args.destination)

    explain_system_root_choice()
    include_system_root = ask_yes_no("Would you like to attempt copying the root of C:\\", default=False)

    explain_exclusions_choice()
    use_default_exclusions = ask_yes_no("Should the default exclusions be used", default=True)

    excluded_names = set(DEFAULT_EXCLUDED_FOLDER_NAMES) if use_default_exclusions else set()

    destination_path = Path(destination_drive)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    device_name = socket.gethostname()
    destination_root = destination_path / f"WindowsSystemBackup_{device_name}_{timestamp}"
    backup_data_root = destination_root / "BackupData"
    report_folder = destination_root / "BackupReports"
    error_log = report_folder / "copy-errors.log"

    user_choices = {
        "destination_drive": destination_drive,
        "include_system_root": include_system_root,
        "use_default_exclusions": use_default_exclusions,
    }

    backup_sources = get_backup_sources(destination_drive, include_system_root)

    print_section("WHAT WILL BE COPIED")
    for source in backup_sources:
        log(f"Source: {source['source']}")
        log(f"Saved As: BackupData\\{source['name']}")
        log(f"Reason: {source['reason']}")
        log()

    print_section("SCANNING BACKUP SIZE")
    scan_results: List[Dict[str, object]] = []

    for source in backup_sources:
        source_path = Path(source["source"])
        log(f"Scanning {source_path} ...")
        scan_results.append(scan_source(source_path, excluded_names))

    total_files = sum(int(r["included_files"]) for r in scan_results)
    total_bytes = sum(int(r["included_bytes"]) for r in scan_results)
    total_excluded_bytes = sum(int(r["excluded_bytes"]) for r in scan_results)
    total_errors = sum(len(r["errors"]) for r in scan_results if isinstance(r["errors"], list))
    free_bytes = shutil.disk_usage(str(destination_path)).free
    excluded_counts = merge_excluded_counts(scan_results)
    rough_time = estimate_time_range(total_bytes)

    print_section("BACKUP SUMMARY")
    log(f"Files to be copied: {total_files:,}")
    log(f"Estimated backup size: {format_bytes(total_bytes)}")
    log(f"Available space on destination: {format_bytes(free_bytes)}")
    log(f"Remaining after backup: {format_bytes(free_bytes - total_bytes)}")
    log(f"Scan errors / inaccessible items: {total_errors}")
    log()
    log("Items excluded:")

    if excluded_counts:
        for name, count in excluded_counts.items():
            log(f"- {name} ({count} folders)")
    else:
        log("- None")

    log()
    log(f"Estimated excluded file size: {format_bytes(total_excluded_bytes)}")
    log()
    log(f"Rough time estimate: {rough_time}")
    log("The backup process may take several hours.")
    log()

    if free_bytes < total_bytes:
        log("Not enough free space on destination drive. Backup will not continue.")
        destination_root.mkdir(parents=True, exist_ok=True)
        report_folder.mkdir(parents=True, exist_ok=True)
        save_execution_report(
            report_folder,
            " ".join([sys.executable, *sys.argv]),
            destination_root,
            backup_sources,
            excluded_names,
            scan_results,
            free_bytes,
            user_choices,
        )
        save_transcript(report_folder)
        return 1

    answer = input_logged("Do you wish to continue? (Y/N): ").strip().lower()

    if answer != "y":
        log("Backup cancelled. No files were copied.")
        destination_root.mkdir(parents=True, exist_ok=True)
        report_folder.mkdir(parents=True, exist_ok=True)
        save_execution_report(
            report_folder,
            " ".join([sys.executable, *sys.argv]),
            destination_root,
            backup_sources,
            excluded_names,
            scan_results,
            free_bytes,
            user_choices,
        )
        save_transcript(report_folder)
        log(f"Reports saved to: {report_folder}")
        return 0

    backup_data_root.mkdir(parents=True, exist_ok=True)
    report_folder.mkdir(parents=True, exist_ok=True)
    error_log.write_text("", encoding="utf-8")

    command_used = " ".join([sys.executable, *sys.argv])

    save_execution_report(
        report_folder=report_folder,
        command=command_used,
        destination_root=destination_root,
        backup_sources=backup_sources,
        excluded_names=excluded_names,
        scan_results=scan_results,
        free_bytes=free_bytes,
        user_choices=user_choices,
    )

    print_section("COPYING FILES")
    start_time = time.time()

    total_copied_files = 0
    total_copied_bytes = 0
    total_failed_files = 0

    for source in backup_sources:
        source_path = Path(source["source"])
        target_path = backup_data_root / source["name"]
        log(f"Copying {source_path} -> {target_path}")
        target_path.mkdir(parents=True, exist_ok=True)

        result = copy_tree(source_path, target_path, excluded_names, error_log)
        total_copied_files += int(result["copied_files"])
        total_copied_bytes += int(result["copied_bytes"])
        total_failed_files += int(result["failed_files"])

        log(
            f"Completed {source_path}: "
            f"{int(result['copied_files']):,} files, "
            f"{format_bytes(float(result['copied_bytes']))}, "
            f"{int(result['failed_files']):,} failed"
        )

    elapsed_seconds = int(time.time() - start_time)
    actual_backup_folder_bytes = calculate_folder_size(backup_data_root)
    copy_error_lines = count_error_lines(error_log)

    final_summary = {
        "copied_files": total_copied_files,
        "copied_bytes": total_copied_bytes,
        "failed_files": total_failed_files,
        "copy_error_lines": copy_error_lines,
        "actual_backup_folder_bytes": actual_backup_folder_bytes,
        "elapsed_seconds": elapsed_seconds,
    }

    save_backup_hierarchy(destination_root, report_folder)

    save_execution_report(
        report_folder=report_folder,
        command=command_used,
        destination_root=destination_root,
        backup_sources=backup_sources,
        excluded_names=excluded_names,
        scan_results=scan_results,
        free_bytes=free_bytes,
        user_choices=user_choices,
        final_summary=final_summary,
    )

    print_section("BACKUP COMPLETE")
    log("Backup saved to:")
    log(str(destination_root))
    log()
    log("Reports saved to:")
    log(str(report_folder))
    log()
    log(f"Estimated data selected: {format_bytes(total_bytes)}")
    log(f"Actual copied data found in backup folder: {format_bytes(actual_backup_folder_bytes)}")
    log(f"Estimated excluded data: {format_bytes(total_excluded_bytes)}")
    log(f"Copied files: {total_copied_files:,}")
    log(f"Failed files logged: {total_failed_files:,}")
    log(f"Copy error log lines: {copy_error_lines:,}")
    log(f"Elapsed copy time: {elapsed_seconds // 3600}h {(elapsed_seconds % 3600) // 60}m {elapsed_seconds % 60}s")
    log()
    log("Generated reports:")
    log("- execution-report.txt")
    log("- execution-report.json")
    log("- backup-hierarchy.txt")
    log("- terminal-transcript.txt")
    log("- copy-errors.log")
    log()
    log("IMPORTANT: Open important files from the external drive before making changes to the original device.")

    save_transcript(report_folder)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
