import fnmatch
import os

from typing import Any, List, Optional


def chunks(values: List[Any], batch_size: Optional[int]):
    if batch_size is None:
        yield values
    else:
        for i in range(0, len(values), batch_size):
            yield values[i:i + batch_size]


def get_files(paths: List[str], suffix: str):
    for path in paths:
        for root, _, files in os.walk(path):
            for filename in fnmatch.filter(files, f'*.{suffix}'):
                yield os.path.join(root, filename)


def get_last_modified_timestamp(paths: List[str], suffix: str) -> float:
    return max(
        map(
            os.path.getmtime,
            get_files(paths, suffix)
        ),
        default=0
    )
