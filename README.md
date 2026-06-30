# Windows System Backup Utility

**Version:** v1.0.0

Windows System Backup Utility is a public-use Python backup tool for copying important files from a Windows laptop or desktop to an external hard drive before a factory reset, hardware replacement, operating system reinstall, device migration, or storage upgrade.

The tool is designed to be safe by default. It uses an interactive setup flow, scans first, estimates the backup size, checks available space on the destination drive, shows what will be copied and excluded, and only starts copying after the user confirms with `Y`.

---

## Features

- Interactive setup before scanning
- Lists available external/removable drives
- Lets the user choose the destination drive
- Asks whether to attempt copying the root of `C:\`
- Explains what copying the root of `C:\` means
- Asks whether to use the default exclusions
- Explains what the default exclusions are
- Scans before copying
- Estimates total backup size
- Counts files to be copied
- Checks available space on the destination drive
- Shows excluded folders before copying
- Gives a rough time estimate
- Requires explicit `Y` confirmation before copying
- Copies all user profiles under `C:\Users`
- Copies hidden files and folders
- Copies AppData
- Copies browser profiles stored locally
- Copies Git repositories and source code if stored inside copied folders
- Copies SSH keys and Git configuration files if stored inside copied folders
- Copies additional internal drives such as `D:`, `E:`, `F:`, etc.
- Saves an execution report
- Saves system/device information
- Saves a backup hierarchy report
- Saves an error log if some files cannot be copied
- Saves a full terminal transcript of the run
- Shows how much was copied and how much was not copied/skipped where possible

---

## Common Use Cases

Windows System Backup Utility can be used in situations where preserving user data and system-related files is important.

### Factory Reset Preparation

Create a backup before performing a Windows factory reset to ensure personal files, application data, and configuration files are preserved.

Examples:

- Resetting Windows due to performance issues
- Removing malware or unwanted software
- Starting with a clean installation

### Operating System Migration

Create a backup before replacing, reinstalling, or changing an operating system.

Examples:

- Reinstalling Windows
- Migrating from Windows 10 to Windows 11
- Migrating to another operating system
- Performing a clean operating system installation

### Device Replacement or Upgrade

Back up important files before moving to a new computer.

Examples:

- Purchasing a new laptop or desktop
- Replacing aging hardware
- Moving files to a newly built PC

### Hardware Maintenance and Repair

Protect important data before hardware servicing or repair.

Examples:

- Replacing storage drives
- Replacing motherboard components
- Sending a device for repair or warranty service

### Storage Device Migration

Move files from one storage device to another.

Examples:

- Migrating from HDD to SSD
- Upgrading to larger storage devices
- Consolidating multiple drives

### Disaster Recovery Preparation

Maintain a recent backup in case of unexpected events.

Examples:

- Drive failure
- Hardware failure
- Accidental file deletion
- Operating system corruption

### Development Environment Preservation

Preserve development projects and configuration files.

Examples:

- Backing up source code repositories
- Preserving SSH keys and Git configuration
- Backing up development workspaces
- Preserving virtual machine files and local databases

### Long-Term Archival

Create an archive of important files for long-term storage.

Examples:

- Preserving personal photos and videos
- Archiving documents and records
- Maintaining historical copies of projects

---

## What Gets Copied by Default

The utility attempts to copy:

- All user profiles under `C:\Users`
- Desktop
- Documents
- Downloads
- Pictures
- Videos
- Music
- AppData
- Browser profiles
- Git repositories
- SSH keys
- Git configuration files
- Local databases if stored inside copied folders
- Virtual machines if stored inside copied folders
- Additional internal drives, excluding the selected destination drive
- Most personal files stored on internal drives

---

## What Is Excluded by Default

These folders are excluded because they are usually large, temporary, or rebuildable:

```text
node_modules
.next
dist
build
target
bin
obj
.venv
__pycache__
Temp
tmp
$Recycle.Bin
System Volume Information
```

These can usually be recreated after restoring the project.

---

## Important Disclaimer

This software is provided **AS IS**, without warranty of any kind, express or implied.

The authors shall not be liable for data loss, lost profits, device damage, failed backups, or any other damages arising from the use of this software.

You are solely responsible for verifying the integrity and completeness of your backups before:

- Factory resetting a computer
- Formatting a drive
- Reinstalling an operating system
- Installing another operating system
- Deleting original files
- Repartitioning storage
- Sending a device for repair
- Replacing or upgrading hardware

Always manually open and verify important files from the external drive before wiping, modifying, repairing, or replacing the original computer.

---

## Requirements

- Windows 10 or Windows 11
- Python 3.9 or newer
- External hard drive or SSD
- Enough free space for the backup
- Administrator terminal recommended
- Git recommended if cloning from a repository

---

## How to Run from GitHub

Clone the repository:

```powershell
git clone https://github.com/YOUR-USERNAME/windows-system-backup-utility.git
```

Go into the project folder:

```powershell
cd windows-system-backup-utility
```

Check that Python is installed:

```powershell
python --version
```

If `python` does not work, try:

```powershell
py --version
```

Run the utility:

```powershell
python windows_system_backup_utility.py
```

Or:

```powershell
py windows_system_backup_utility.py
```

The script will guide the user through the setup.

---

## Interactive Setup Flow

When the script starts, it shows a disclaimer and then asks setup questions.

### 1. Choose the External Drive

The tool lists detected external/removable drives first.

Example:

```text
============================================================
DESTINATION DRIVE SELECTION
============================================================

Detected removable/external drives:

[1] E:\  My Passport  Free: 1.82 TB  Total: 2.00 TB
[2] F:\  Samsung SSD  Free: 931.44 GB  Total: 1.00 TB

Choose the destination drive number, or enter a drive letter such as E:
```

The selected drive is where the backup will be saved.

### 2. Include the Root of C:\

The tool then asks:

```text
Would you like to attempt copying the root of C:\ ? (Y/N)
```

By default, the utility copies `C:\Users`, which contains most personal files, AppData, browser profiles, SSH keys, and user settings.

Copying the root of `C:\` means the tool will also attempt to copy folders outside `C:\Users`, such as:

```text
C:\Projects
C:\Repos
C:\Tools
C:\Scripts
C:\ProgramData
```

This may be useful if the user stores work outside their user profile.

However, it may also try to scan protected Windows folders such as:

```text
C:\Windows
C:\Program Files
C:\Program Files (x86)
```

Those folders may create access errors, take longer, and are usually not needed for a personal backup.

Recommended answer for most users:

```text
N
```

### 3. Use Default Exclusions

The tool then asks:

```text
Should the default exclusions be used? (Y/N)
```

Default exclusions skip folders that are usually temporary, very large, or easy to rebuild later.

Examples:

```text
node_modules
.next
dist
build
target
bin
obj
.venv
__pycache__
Temp
tmp
$Recycle.Bin
System Volume Information
```

Recommended answer for most users:

```text
Y
```

Answering `N` copies more data but may require much more storage and time.

---

## Example Backup Summary

After setup, the utility scans the selected sources and shows a summary.

```text
============================================================
BACKUP SUMMARY
============================================================

Files to be copied: 1,284,512
Estimated backup size: 642.31 GB
Available space on destination: 1.82 TB
Remaining after backup: 1.19 TB
Scan errors / inaccessible items: 12

Items excluded:
- node_modules (27 folders)
- .next (4 folders)
- Temp (18 folders)

Estimated excluded file size: 13.21 GB

Rough time estimate: 2 hours 15 minutes to 5 hours 30 minutes
The backup process may take several hours.

Do you wish to continue? (Y/N)
```

The backup does not begin unless the user enters:

```text
Y
```

If the user enters `N`, no files are copied.

---

## What Happens During Copying

After confirmation, the utility:

1. Creates a timestamped backup folder on the external drive.
2. Creates a `BackupData` folder.
3. Creates a `BackupReports` folder.
4. Saves an initial execution report.
5. Copies the selected sources.
6. Logs files that cannot be copied.
7. Saves the backup hierarchy.
8. Saves a terminal transcript.
9. Shows the final backup summary.

---

## Backup Output Structure

The utility creates a timestamped backup folder on the selected external drive.

```text
E:\
└── WindowsSystemBackup_DEVICE_YYYYMMDD_HHMMSS\
    ├── BackupData\
    │   ├── Users\
    │   ├── Drive_D\
    │   └── Drive_F\
    │
    └── BackupReports\
        ├── execution-report.txt
        ├── execution-report.json
        ├── backup-hierarchy.txt
        ├── terminal-transcript.txt
        └── copy-errors.log
```

---

## Generated Reports

### execution-report.txt

Human-readable report containing:

- Date and time
- Computer name
- Username
- Command used
- Destination path
- Operating system
- System/device name
- Processor information
- Python version
- Sources selected for backup
- User choices
- Exclusions applied
- File count
- Estimated backup size
- Available destination space
- Scan errors
- Final copied size where possible
- Final skipped/error count where possible

### execution-report.json

Machine-readable execution report.

Useful for automation, troubleshooting, or later review.

### backup-hierarchy.txt

A simple hierarchy showing the copied top-level folders.

### terminal-transcript.txt

A saved copy of the terminal output from the run.

This includes:

- Disclaimer shown to the user
- Drive selection
- User choices
- Scan summary
- Backup summary
- Copy progress messages
- Final completion summary

### copy-errors.log

A log of files or folders that could not be copied.

Some errors are normal when files are locked, protected, or actively being used.

---

## Final Completion Output

When the backup finishes, the utility shows a final summary.

Example:

```text
============================================================
BACKUP COMPLETE
============================================================

Backup saved to:
E:\WindowsSystemBackup_MY-LAPTOP_20260628_184500

Reports saved to:
E:\WindowsSystemBackup_MY-LAPTOP_20260628_184500\BackupReports

Estimated data selected: 642.31 GB
Actual copied data found in backup folder: 638.92 GB
Estimated excluded data: 13.21 GB
Copy errors logged: 41

Generated reports:
- execution-report.txt
- execution-report.json
- backup-hierarchy.txt
- terminal-transcript.txt
- copy-errors.log

IMPORTANT:
Open important files from the external drive before making changes to the original device.
```

### How Much Was Copied vs Not Copied?

The utility can estimate:

- How much data was selected for backup
- How much data was excluded by folder rules
- How much data exists in the final backup folder
- How many copy errors were logged

This is not a perfect forensic backup audit, but it gives a practical overview of copied, excluded, and failed items.

---

## Recommended Post-Backup Actions

After the backup completes:

1. Open important files directly from the backup drive.
2. Verify Documents, Pictures, Downloads, and Desktop folders.
3. Verify application data if required.
4. Review `copy-errors.log` for files that could not be copied.
5. Confirm all generated reports were created successfully.
6. Keep the backup drive in a safe location until the original device changes have been completed.

---

## Recommended Verification Checklist

Before wiping, repairing, replacing, or modifying the original device:

- [ ] Open important files directly from the external drive.
- [ ] Verify Documents.
- [ ] Verify Downloads.
- [ ] Verify Desktop files.
- [ ] Verify Pictures and Videos.
- [ ] Verify AppData if needed.
- [ ] Verify Git repositories.
- [ ] Verify SSH keys.
- [ ] Verify browser data or browser sync.
- [ ] Verify local databases or virtual machines if needed.
- [ ] Confirm reports were generated.
- [ ] Check `copy-errors.log`.
- [ ] Keep the external drive disconnected and safe before making major changes.

---

## Version History

| Version | Date                       | Comments                                                                                                                                                     |
| ------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| v1.0.0  | June 30<sup>th</sup>, 2026 | Initial public release with interactive drive selection, scan, space check, confirmation prompt, copy process, exclusions, terminal transcript, and reports. |

---

## License

MIT License.
