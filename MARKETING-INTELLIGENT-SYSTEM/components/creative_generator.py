import json
from .utils import txt


def generate_concept(creator, campaign, llm):
    # Supplied creator dataset contains rank, handle, influence and aggregate metrics,
    # but no biography, voice, themes, catchphrases or recurring content formats.
    fields = ["handle", "rank", "influence_score", "followers", "followers_numeric",
              "avg_likes", "avg_likes_numeric", "engagement_rate_pct", "creator_country"]
    profile = {k: creator.get(k) for k in fields if k in creator and creator.get(k) is not None}
    payload = {
        "creator_profile_evidence": profile,
        "campaign": campaign,
        "approved_claims": campaign.get("approved_claims", []),
        "limitations": [
            "No creator bio, content themes, voice, audience demographics or post-level content is supplied.",
            "Instagram account analytics cannot be linked to this creator without an account_id-to-handle crosswalk."
        ]
    }
    system = (
        "Create a cautious creator campaign concept using only supplied evidence. Do not invent personal experiences, "
        "testimonials, routines, audience demographics or creator voice. Do not imply that aggregate account analytics "
        "belong to this creator. Use only approved_claims; if empty, make no efficacy or health claim. "
        "Clearly mark assumptions and human checks. Return valid JSON only with concept, hook, format, beats, CTA, "
        "claims_to_verify, evidence_used and limitations."
    )
    answer = llm.complete(system, json.dumps(payload, ensure_ascii=False)) if llm else None
    if answer:
        try:
            parsed = json.loads(answer)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "concept": "A transparent product introduction built around a format selected after reviewing the creator's current feed.",
        "hook": "Choose a hook only after verifying the creator's recent content style.",
        "format": "Creator format not available in supplied dataset; confirm directly with creator.",
        "beats": ["Review the creator's recent posts", "Agree on a format and disclosure", "Introduce the product factually",
                  "Use only approved claims", "Close with a clear invitation to learn more"],
        "CTA": "Discover more about the product.",
        "claims_to_verify": ["No approved product claims were supplied; obtain approved brand wording before publication."],
        "evidence_used": list(profile.keys()),
        "limitations": payload["limitations"]
    }
