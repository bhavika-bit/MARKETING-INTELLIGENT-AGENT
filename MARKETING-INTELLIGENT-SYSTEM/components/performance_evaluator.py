import numpy as np
import pandas as pd
from .utils import numeric, score


def _percentile(values):
    s = pd.to_numeric(values, errors="coerce")
    return (s.rank(pct=True, method="average") * 100).fillna(50.0)


def evaluate_performance(creators, posts):
    """
    Score named influencers from their own influencer-table metrics.
    Instagram_Analytics has account_id but no handle crosswalk, so it is used
    only for a separately reported dataset-level benchmark, never per-creator joins.
    """
    if creators is None or creators.empty or "handle" not in creators:
        raise ValueError("creators dataset must contain a normalised handle column")
    c = creators.copy()
    for source, target in [
        ("followers_numeric", "followers_metric"),
        ("avg_likes_numeric", "avg_likes_metric"),
        ("new_post_avg_likes_numeric", "new_post_avg_likes_metric"),
        ("engagement_rate_pct", "engagement_rate_metric"),
        ("influence_score", "influence_metric"),
    ]:
        if source in c:
            c[target] = numeric(c[source])
        elif target not in c:
            c[target] = np.nan

    c["reach_score"] = _percentile(c["followers_metric"])
    c["engagement_score"] = _percentile(c["engagement_rate_metric"])
    c["likes_score"] = _percentile(c["avg_likes_metric"])
    c["influence_score_percentile"] = _percentile(c["influence_metric"])
    c["performance_score"] = (
        .30*c["reach_score"] + .30*c["engagement_score"] +
        .25*c["likes_score"] + .15*c["influence_score_percentile"]
    ).map(score).round(1)

    analytics = posts.copy() if posts is not None else pd.DataFrame()
    benchmark = {}
    if not analytics.empty:
        for field in ["reach", "impressions", "likes", "comments", "shares", "saves", "engagement_rate"]:
            if field in analytics:
                vals = numeric(analytics[field]).dropna()
                benchmark[f"dataset_median_{field}"] = float(vals.median()) if len(vals) else np.nan
        benchmark["analytics_rows"] = int(len(analytics))
        benchmark["analytics_account_count"] = int(analytics["account_id"].nunique()) if "account_id" in analytics else None
    else:
        benchmark["analytics_rows"] = 0

    rows = []
    for _, r in c.iterrows():
        followers = r.get("followers_metric", np.nan)
        likes = r.get("avg_likes_metric", np.nan)
        eng = r.get("engagement_rate_metric", np.nan)
        rows.append({
            "handle": r["handle"],
            "post_count_used": 0,
            "posts_with_play_data": 0,
            "median_plays": np.nan,
            "followers_metric": followers,
            "avg_likes_metric": likes,
            "engagement_rate_metric_pct": eng,
            "reach_score": round(float(r["reach_score"]), 1),
            "engagement_score": round(float(r["engagement_score"]), 1),
            "share_score": round(float(r["likes_score"]), 1),
            "consistency_score": round(float(r["influence_score_percentile"]), 1),
            "performance_score": float(r["performance_score"]),
            "performance_evidence": (
                f"Influencer table: followers {followers:,.0f}" if pd.notna(followers) else "Influencer table: followers unavailable"
            ) + (f"; average likes {likes:,.0f}" if pd.notna(likes) else "; average likes unavailable") +
            (f"; reported 60-day engagement {eng:.2f}%" if pd.notna(eng) else "; reported engagement unavailable") +
            ". Instagram account-level analytics are not attributed to this handle because no crosswalk is supplied."
        })
    result = pd.DataFrame(rows)
    for k, v in benchmark.items():
        result[k] = v
    return result
