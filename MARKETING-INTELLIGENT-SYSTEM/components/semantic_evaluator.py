import re
import pandas as pd
from .utils import txt, score


def _tokens(value):
    return set(re.findall(r"[a-zA-Z0-9']+", txt(value).lower()))


def _similarities(docs, query, config):
    if not docs:
        return []
    if not txt(query):
        return [0.0 for _ in docs]
    if config.get("semantic", {}).get("use_embeddings", True):
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            model = SentenceTransformer(config.get("semantic", {}).get(
                "embedding_model", "sentence-transformers/all-MiniLM-L6-v2"))
            vectors = model.encode([query] + docs, normalize_embeddings=True, show_progress_bar=False)
            return [float((x + 1) / 2) for x in cosine_similarity([vectors[0]], vectors[1:])[0]]
        except Exception:
            pass
    q = _tokens(query)
    return [len(q & _tokens(d)) / max(1, len(q | _tokens(d))) for d in docs]


def evaluate_semantic(creators, posts, ads, campaign, config):
    if creators is None or creators.empty or "handle" not in creators:
        raise ValueError("creators dataset must contain handle")
    profile_fields = ["handle", "creator_country", "country", "influence_score", "followers",
                      "followers_numeric", "avg_likes_numeric", "engagement_rate_pct"]
    trend_fields = ["platform", "hashtag", "content_type", "region", "engagement_level"]
    analytics_fields = ["media_type", "content_category", "traffic_source", "performance_bucket_label"]
    campaign_parts = [txt(campaign.get(k, "")) for k in
                      ["product", "objective", "target_audience", "preferred_language", "creative_direction"]]
    campaign_parts += [txt(x) for x in campaign.get("keywords", [])] if isinstance(campaign.get("keywords", []), (list, tuple)) else [txt(campaign.get("keywords", ""))]
    trend_docs = []
    if ads is not None and not ads.empty:
        for _, row in ads.head(300).iterrows():
            s = " ".join(txt(row.get(f)) for f in trend_fields)
            if s.strip():
                trend_docs.append(s)
    trend_context = " ".join(trend_docs[:100])
    # Analytics contributes only broad content-format/category context, never creator-specific post text.
    analytics_context = ""
    if posts is not None and not posts.empty:
        parts = []
        for f in analytics_fields:
            if f in posts:
                parts.extend(posts[f].dropna().astype(str).value_counts().head(12).index.tolist())
        analytics_context = " ".join(parts)

    query = " ".join(x for x in campaign_parts + [trend_context, analytics_context] if x)
    docs, handles = [], []
    for _, creator in creators.iterrows():
        parts = [txt(creator.get(f)) for f in profile_fields if f in creators.columns]
        docs.append(" ".join(x for x in parts if x))
        handles.append(creator["handle"])
    similarities = _similarities(docs, query, config or {})
    pct = pd.Series(similarities, dtype=float).rank(pct=True, method="average") * 100 if similarities else pd.Series(dtype=float)
    rows = []
    for i, (h, sim) in enumerate(zip(handles, similarities)):
        rows.append({
            "handle": h, "semantic_score": round(score(pct.iloc[i]), 1),
            "semantic_match_strength": round(float(sim), 4),
            "semantic_posts_used": 0,
            "semantic_evidence": "Influencer-table fields compared with campaign brief and aggregate trend references. No post-level text or creator-to-account mapping is supplied; trend labels are contextual signals, not creator attributes."
        })
    return pd.DataFrame(rows)
