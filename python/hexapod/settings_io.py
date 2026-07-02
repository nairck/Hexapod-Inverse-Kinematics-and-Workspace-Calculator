"""Read / validate / write the strict formdata.txt settings file.

Faithful port of load_data.m and save_data.m.  The on-disk format is kept
byte-for-byte compatible with the MATLAB tool:

    <tag> = <value with exactly 3 decimals>      (71 numeric lines)
    calculator_name = '<name>'                   (final line)

so files are interchangeable between the MATLAB original and this port.
"""
from __future__ import annotations
import os
import re
from . import config


def default_values_dict():
    return dict(zip(config.TAGS, config.DEFAULT_VALUES))


def fmt(value):
    """Format a number exactly like MATLAB '%.3f'."""
    return f"{float(value):.3f}"


def write_settings(path, values, name):
    """Write all numeric tags (3 decimals) then the calculator_name line.

    Mirrors save_data.m, including its fallback to formdata_new.txt when the
    primary file cannot be opened.
    """
    try:
        f = open(path, "w", newline="\n")
    except OSError:
        fallback = os.path.join(os.path.dirname(path) or ".", "formdata_new.txt")
        f = open(fallback, "w", newline="\n")
        path = fallback
    with f:
        for tag in config.TAGS:
            f.write(f"{tag} = {fmt(values[tag])}\n")
        f.write(f"calculator_name = '{name}'\n")
    return path


def write_defaults(path):
    write_settings(path, default_values_dict(), config.DEFAULT_NAME)


def _validate(raw_lines):
    """Validate raw text lines. Returns (values_dict, name, errors_list)."""
    tags = config.TAGS
    n = len(tags)
    total = n + 1
    values = {}
    errors = []
    name = config.DEFAULT_NAME

    if len(raw_lines) != total:
        errors.append(f"Expected {total} lines but found {len(raw_lines)}.")

    for i in range(min(n, len(raw_lines))):
        tag = tags[i]
        pat = rf"^{re.escape(tag)} = (-?\d+\.\d{{3}})$"
        m = re.match(pat, raw_lines[i])
        if not m:
            errors.append(f"Line {i + 1}: '{raw_lines[i]}'  - Expected: '{tag} = -123.456'")
        else:
            values[tag] = float(m.group(1))

    if len(raw_lines) >= n + 1:
        m = re.match(r"^calculator_name = '(.{1,100})'$", raw_lines[n])
        if not m:
            errors.append(f"Line {n + 1}: '{raw_lines[n]}'  - Expected: \"calculator_name = '...'\"")
        else:
            name = m.group(1)

    return values, name, errors


def read_settings(path):
    """Read and validate the settings file.

    Returns one of:
        ("missing",)                       file does not exist
        ("corrupt", errors, preview_text)  file present but invalid
        ("ok", values_dict, name)          file present and valid
    """
    if not os.path.isfile(path):
        return ("missing",)

    with open(path, "r") as f:
        raw_lines = [ln.rstrip("\n").strip() for ln in f.readlines()]

    values, name, errors = _validate(raw_lines)
    if errors:
        preview_count = min(4, len(errors))
        preview = "\n".join(errors[:preview_count])
        if len(errors) > preview_count:
            preview += f"\n...and {len(errors) - preview_count} more invalid lines"
        return ("corrupt", errors, preview)

    return ("ok", values, name)
