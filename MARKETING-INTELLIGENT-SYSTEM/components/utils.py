import re
import numpy as np
import pandas as pd


def txt(value):
    if value is None or value is pd.NA:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def handle(value):
    value = txt(value).strip().lower()
    value = re.sub(r"^https?://(www\.)?instagram\.com/", "", value)
    return value.strip("/@ ").split("/")[0]


def col(df, names):
    if df is None:
        return None
    lookup = {str(c).strip().lower(): c for c in df.columns}
    return next((lookup[str(n).strip().lower()] for n in names
                 if str(n).strip().lower() in lookup), None)


def numeric(series):
    """Convert ordinary numeric and abbreviated social counts (1.2m, 45k) to floats."""
    if not isinstance(series, pd.Series):
        series = pd.Series(series)
    def parse(v):
        if pd.isna(v):
            return np.nan
        if isinstance(v, (int, float, np.number)):
            return float(v)
        s = str(v).strip().lower().replace(",", "").replace("$", "")
        if not s or s in {"nan", "none", "n/a", "-", "—"}:
            return np.nan
        match = re.fullmatch(r"([-+]?\d*\.?\d+)\s*([kmb]?)", s)
        if match:
            scale = {"": 1, "k": 1_000, "m": 1_000_000, "b": 1_000_000_000}[match.group(2)]
            return float(match.group(1)) * scale
        cleaned = re.sub(r"[^0-9.eE+-]", "", s)
        try:
            return float(cleaned)
        except ValueError:
            return np.nan
    return series.map(parse)


def score(value):
    try:
        return float(np.clip(float(value), 0, 100))
    except (TypeError, ValueError):
        return 0.0


def split_list(value):
    if isinstance(value, (list, tuple, set)):
        return [txt(x) for x in value if txt(x)]
    s = txt(value)
    return [x.strip() for x in re.split(r"[;,]", s) if x.strip()]
