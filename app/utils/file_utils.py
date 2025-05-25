import os
import time
from werkzeug.datastructures import FileStorage


def save_file_to_static(file: FileStorage, base_folder: str) -> str:
    _, ext = os.path.splitext(file.filename)
    timestamp_filename: str = f"{int(time.time_ns() / 1_000_000)}{ext}"
    file_path: str = os.path.join(base_folder, timestamp_filename)
    file.save(file_path)
    return os.path.join('../static/images', timestamp_filename)