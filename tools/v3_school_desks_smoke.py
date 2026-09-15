"""Compatibility entry for the recorded desk scenario; new batches use the shared probe."""
from v3_furniture_batch_smoke import exercise as batch_exercise


def exercise(debug, rom_path, record):
    return batch_exercise(debug,rom_path,record,section='school_desks')
