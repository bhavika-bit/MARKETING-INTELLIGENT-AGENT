import json
from pathlib import Path
import pandas as pd
from .utils import numeric, txt

# Required source columns for the three supplied files. "audience" deliberately
# reuses creator records only as a profile reference; it is NOT audience demographics.
SOURCE_REQUIRED = {
    "ads": {"Post_ID", "Platform", "Hashtag", "Content_Type", "Region", "Views", "Engagement_Level"},
    "creators": {"channel_info", "influence_score", "followers", "avg_likes", "60_day_eng_rate", "country"},
    "posts": {"post_id", "account_id", "account_type", "media_type", "reach", "impressions",
              "likes", "comments", "shares", "saves", "engagement_rate"},
    "audience": {"channel_info", "followers", "country"},
}

DEFAULT_DATA_PATHS = {
    "ads": "data/Cleaned_Viral_Social_Media_Trends.csv",
    "creators": "data/top_insta_influencers_data.csv",
    "posts": "data/Instagram_Analytics.csv",
    "audience": "data/top_insta_influencers_data.csv",
}


def load_config(path="config.json"):
    path = Path(path).resolve()
    config = json.loads(path.read_text(encoding="utf-8"))
    config["_project_root"] = str(path.parent)
    config.setdefault("data_paths", DEFAULT_DATA_PATHS.copy())
    return config


def _read_csv(path):
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False)
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"Could not decode CSV: {path}")


def _normalise_creators(df):
    if df.empty:
        return df
    x = df.copy()
    rename = {
        "channel_info": "handle", "60_day_eng_rate": "engagement_rate_pct",
        "new_post_avg_like": "new_post_avg_likes",
    }
    x = x.rename(columns={k: v for k, v in rename.items() if k in x.columns})
    if "handle" in x:
        x["handle"] = x["handle"].map(lambda v: txt(v).lstrip("@"))
    for c in ["followers", "avg_likes", "new_post_avg_likes", "total_likes", "posts"]:
        if c in x:
            x[c + "_numeric"] = numeric(x[c])
    if "engagement_rate_pct" in x:
        x["engagement_rate_pct"] = numeric(x["engagement_rate_pct"].astype(str).str.replace("%", "", regex=False))
    # Keep the source country as creator/account country, never label it audience location.
    if "country" in x:
        x["creator_country"] = x["country"]
    return x


def _normalise_ads(df):
    if df.empty:
        return df
    x = df.copy()
    rename = {"Post_ID": "trend_post_id", "Post_Date": "trend_date", "Platform": "platform",
              "Hashtag": "hashtag", "Content_Type": "content_type", "Region": "region",
              "Views": "views", "Likes": "likes", "Shares": "shares",
              "Comments": "comments", "Engagement_Level": "engagement_level"}
    return x.rename(columns={k: v for k, v in rename.items() if k in x.columns})


def _normalise_posts(df):
    if df.empty:
        return df
    x = df.copy()
    x.columns = [str(c).strip().lower() for c in x.columns]
    # No handle/account crosswalk exists in the supplied files.
    x["creator_handle"] = pd.NA
    return x


def load_datasets(config):
    root = Path(config.get("_project_root", Path.cwd()))
    paths = dict(DEFAULT_DATA_PATHS)
    paths.update(config.get("data_paths", {}))
    frames, missing = {}, []
    for name in ["ads", "creators", "posts", "audience"]:
        raw_path = paths.get(name)
        if not raw_path:
            frames[name] = pd.DataFrame()
            missing.append(f"{name}: no path configured")
            continue
        p = Path(raw_path)
        if not p.is_absolute():
            p = root / p
        if not p.exists():
            frames[name] = pd.DataFrame()
            missing.append(f"{name}: {p}")
            continue
        frames[name] = _read_csv(p)

    frames["ads"] = _normalise_ads(frames.get("ads", pd.DataFrame()))
    frames["creators"] = _normalise_creators(frames.get("creators", pd.DataFrame()))
    frames["posts"] = _normalise_posts(frames.get("posts", pd.DataFrame()))
    frames["audience"] = _normalise_creators(frames.get("audience", pd.DataFrame()))
    return frames, missing


def validate_datasets(frames):
    issues = []
    required_normalised = {
        "ads": {"trend_post_id", "platform", "hashtag", "content_type", "region", "views", "engagement_level"},
        "creators": {"handle", "influence_score", "followers", "avg_likes", "engagement_rate_pct", "creator_country"},
        "posts": {"post_id", "account_id", "account_type", "media_type", "reach", "impressions",
                  "likes", "comments", "shares", "saves", "engagement_rate"},
        "audience": {"handle", "followers", "creator_country"},
    }
    for name, required in required_normalised.items():
        df = frames.get(name, pd.DataFrame())
        if df.empty:
            issues.append(f"{name}: file is empty or could not be loaded")
            continue
        absent = sorted(required - set(df.columns))
        if absent:
            issues.append(f"{name}: missing expected columns after normalisation: {', '.join(absent)}")
    creators = frames.get("creators", pd.DataFrame())
    if not creators.empty and "handle" in creators and creators["handle"].duplicated().any():
        issues.append("creators: duplicate influencer handles detected")
    if not frames.get("posts", pd.DataFrame()).empty:
        issues.append("posts: account_id has no verified crosswalk to influencer handles; account-level analytics will not be joined to individual creators")
    if not frames.get("audience", pd.DataFrame()).empty:
        issues.append("audience: mapped to influencer profile file; follower demographics are not present and must remain unavailable")
    return issues


def data_health(frames):
    report = {}
    for name, df in frames.items():
        report[name] = {
            "rows": int(len(df)), "columns": int(len(df.columns)),
            "duplicate_rows": int(df.duplicated().sum()) if not df.empty else 0,
            "missing_cells": int(df.isna().sum().sum()) if not df.empty else 0,
        }
    return report
