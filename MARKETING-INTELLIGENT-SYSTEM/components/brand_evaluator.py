import re
import pandas as pd
from .utils import txt, score

RISK_TERMS = ["cure", "treats", "prevents disease", "guaranteed", "clinically proven", "doctor approved"]


def evaluate_brand(creators, audience, campaign):
    if creators is None or creators.empty or "handle" not in creators:
        raise ValueError("creators dataset must contain handle")
    rows = []
    target = txt(campaign.get("target_audience", "")).lower()
    keywords = campaign.get("keywords", [])
    if not isinstance(keywords, (list, tuple, set)):
        keywords = [keywords]
    campaign_terms = set(re.findall(r"[a-z0-9]+", " ".join(
        [target, txt(campaign.get("product", ""))] + [txt(x) for x in keywords]).lower()))
    stop = {"the", "and", "for", "with", "of", "in", "to", "a", "an", "on", "india", "indian", "brand", "campaign", "young"}
    campaign_terms -= stop

    for _, creator in creators.iterrows():
        handle = txt(creator.get("handle"))
        country = txt(creator.get("creator_country", creator.get("country", "")))
        profile_text = " ".join(txt(creator.get(c)) for c in
                                ["handle", "creator_country", "country"]).lower()
        risk_text = " ".join(txt(creator.get(c)) for c in
                             ["bio", "persona", "feed_story", "voice", "themes"]).lower()
        flags = [term for term in RISK_TERMS if term in risk_text]
        profile_terms = set(re.findall(r"[a-z0-9]+", profile_text)) - stop
        overlap = len(campaign_terms & profile_terms) / max(1, len(campaign_terms))
        # The source contains influencer country, not follower/audience demographics.
        score_value = 45 + 25 * overlap - (15 if flags else 0)
        rows.append({
            "handle": handle, "brand_score": round(score(score_value), 1),
            "audience_data_available": False,
            "audience_platform": "Unavailable",
            "audience_age_split": "Unavailable",
            "audience_top_cities": "Unavailable",
            "audience_top_countries": "Unavailable",
            "creator_country": country or "Unavailable",
            "previous_brand_partnerships": "Unavailable",
            "risk_flags": "; ".join(flags) if flags else "No configured keyword flag detected; human review still required",
            "brand_evidence": "Creator country is available where provided, but follower demographics, age split, audience cities/countries and brand partnerships are not present in the supplied dataset. No audience match has been inferred."
        })
    return pd.DataFrame(rows)
