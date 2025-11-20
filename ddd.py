#!/usr/bin/env python3
"""
combine_images.py

Copy (or move) all images from immediate subfolders of a given source folder
into a single destination folder, renaming each file to include its
original subfolder name to avoid name collisions.

Usage:
    python combine_images.py /path/to/source /path/to/destination
    python combine_images.py /path/to/source /path/to/destination --move

Features:
- Detects image files using the standard library `imghdr` (no external deps).
- Handles images that live directly under the source folder (labels them with 'root').
- Sanitizes filenames by replacing whitespace with underscores.
- Avoids overwriting by appending a counter when needed (e.g. folder_file_1.jpg).
- Prints a short summary at the end.

Note: This script copies files by default. Use --move to move files instead of copying.
"""

from pathlib import Path
import argparse
import shutil
import imghdr
import sys


def is_image_file(path: Path) -> bool:
    """Return True if the file at `path` is an image (by imghdr)."""
    try:
        if not path.is_file():
            return False
        # imghdr.what returns None when it cannot identify the file as an image
        return imghdr.what(path) is not None
    except Exception:
        return False


def sanitize_name(s: str) -> str:
    """Sanitize a filename part: remove/replace problematic characters."""
    # keep it simple: replace spaces with underscores and strip slashes
    return s.replace(" ", "_").replace('/', '_').replace('\\', '_')


def unique_path(dst_dir: Path, name: str) -> Path:
    """Return a Path that does not yet exist by appending a counter if necessary."""
    candidate = dst_dir / name
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        candidate = dst_dir / new_name
        if not candidate.exists():
            return candidate
        counter += 1


def combine_images(src: Path, dst: Path, move_files: bool = False) -> dict:
    """Traverse immediate subfolders of src and copy/move image files to dst.

    Returns a summary dict with counts.
    """
    if not src.exists() or not src.is_dir():
        raise ValueError(f"Source folder does not exist or is not a folder: {src}")

    dst.mkdir(parents=True, exist_ok=True)

    counts = {
        'copied': 0,
        'moved': 0,
        'skipped_non_images': 0,
        'errors': 0,
        'total_processed': 0,
    }

    # We'll include files in immediate subfolders and files directly in src
    # For files directly in src, use subfolder name 'root'

    # Process top-level files first (label them root)
    try:
        entries = list(src.iterdir())
    except Exception as e:
        raise RuntimeError(f"Unable to read source directory: {e}")

    # Handle files directly under src
    for item in entries:
        if item.is_file():
            folder_label = 'root'
            if is_image_file(item):
                counts['total_processed'] += 1
                new_name = f"{sanitize_name(folder_label)}_{sanitize_name(item.name)}"
                target = unique_path(dst, new_name)
                try:
                    if move_files:
                        shutil.move(str(item), str(target))
                        counts['moved'] += 1
                    else:
                        shutil.copy2(str(item), str(target))
                        counts['copied'] += 1
                except Exception as e:
                    print(f"Error copying/moving {item} -> {target}: {e}")
                    counts['errors'] += 1
            else:
                counts['skipped_non_images'] += 1

    # Now handle immediate subfolders
    for folder in entries:
        if folder.is_dir():
            folder_label = folder.name
            try:
                for file in folder.iterdir():
                    if file.is_file():
                        if is_image_file(file):
                            counts['total_processed'] += 1
                            new_name = f"{sanitize_name(folder_label)}_{sanitize_name(file.name)}"
                            target = unique_path(dst, new_name)
                            try:
                                if move_files:
                                    shutil.move(str(file), str(target))
                                    counts['moved'] += 1
                                else:
                                    shutil.copy2(str(file), str(target))
                                    counts['copied'] += 1
                            except Exception as e:
                                print(f"Error copying/moving {file} -> {target}: {e}")
                                counts['errors'] += 1
                        else:
                            counts['skipped_non_images'] += 1
            except Exception as e:
                print(f"Warning: could not iterate folder {folder}: {e}")
                counts['errors'] += 1

    return counts


def main():
    src_input = input("Enter source folder path: ").strip()
    dst_input = input("Enter destination folder path: ").strip()
    move_choice = input("Move files instead of copying? (y/n): ").strip().lower() == 'y'

    src = Path(src_input).expanduser().resolve()
    dst = Path(dst_input).expanduser().resolve()

    try:
        summary = combine_images(src, dst, move_files=move_choice)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(2)

    print("Done. Summary:")
    print(f"  Total image files processed: {summary['total_processed']}")
    if move_choice:
        print(f"  Moved: {summary['moved']}")
    else:
        print(f"  Copied: {summary['copied']}")
    print(f"  Skipped (non-image files): {summary['skipped_non_images']}")
    print(f"  Errors: {summary['errors']}")

if __name__ == '__main__':
    main()
