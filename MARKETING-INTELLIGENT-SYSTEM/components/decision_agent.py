import json
import pandas as pd
from .utils import handle


def build_decisions(creators, performance, semantic, brand, config, campaign):
    if creators is None or creators.empty or "handle" not in creators:
        raise ValueError("creators dataset must contain handle")
    base = creators.copy()
    base["_join_handle"] = base["handle"].map(handle)
    for evaluator in [performance, semantic, brand]:
        if evaluator is not None and not evaluator.empty:
            temp = evaluator.copy()
            if "handle" not in temp:
                continue
            temp["_join_handle"] = temp["handle"].map(handle)
            temp = temp.drop(columns=["handle"])
            base = base.merge(temp, on="_join_handle", how="left", validate="one_to_one")

    weights = config.get("weights", {})
    w = {k: max(0.0, float(weights.get(k, 0))) for k in ["performance", "semantic", "brand"]}
    total = sum(w.values())
    if total <= 0:
        raise ValueError("At least one positive evaluator weight is required in config.json")
    for c in ["performance_score", "semantic_score", "brand_score"]:
        if c not in base:
            base[c] = 50.0
        base[c] = pd.to_numeric(base[c], errors="coerce").fillna(50.0)
    base["overall_score"] = ((base.performance_score*w["performance"] +
                              base.semantic_score*w["semantic"] +
                              base.brand_score*w["brand"]) / total).round(1)
    score_cols = ["performance_score", "semantic_score", "brand_score"]
    base["evaluator_spread"] = base[score_cols].max(axis=1) - base[score_cols].min(axis=1)
    post_count = pd.to_numeric(base["post_count_used"], errors="coerce").fillna(0) if "post_count_used" in base else pd.Series(0, index=base.index)
    base["confidence"] = "Medium"
    base.loc[(post_count < 3) | (base.evaluator_spread > 35), "confidence"] = "Limited"
    base.loc[(post_count >= 8) & (base.evaluator_spread <= 15), "confidence"] = "Higher"
    base["confidence"] = "Limited"  # no named-creator post history or audience demographics in source data
    base["decision_reason"] = (
        "Weighted suitability heuristic using influencer-table metrics, campaign/trend text similarity and available profile fields. "
        "Confidence is limited because creator-level post history and follower demographics are unavailable. Not a paid ROAS prediction."
    )
    base = base.sort_values(["overall_score", "semantic_score", "performance_score"],
                            ascending=False).reset_index(drop=True)
    base["rank"] = base.index + 1

    selected = []
    def take(row, role):
        key = handle(row["handle"])
        if key not in {handle(x["handle"]) for x in selected}:
            item = row.to_dict()
            item["selection_role"] = role
            selected.append(item)

    if len(base):
        take(base.iloc[0], "Agent primary recommendation")
    for metric, role in [("performance_score", "Performance-led alternative"),
                         ("semantic_score", "Semantic-led alternative")]:
        ordered = base.sort_values(metric, ascending=False)
        already = {handle(x["handle"]) for x in selected}
        candidate = next((row for _, row in ordered.iterrows()
                          if handle(row["handle"]) not in already), None)
        if candidate is not None:
            take(candidate, role)
    for _, row in base.iterrows():
        if len(selected) >= min(5, len(base)):
            break
        take(row, "Next-best overall eligible creator")
    top = pd.DataFrame(selected)
    if not top.empty:
        top.insert(0, "recommendation_order", range(1, len(top)+1))
    return base.drop(columns=["_join_handle"]), top.drop(columns=["_join_handle"], errors="ignore")


def get_agent_explanations(top, campaign, memory, llm):
    fields = [c for c in ["handle", "selection_role", "overall_score", "performance_evidence",
                          "semantic_evidence", "brand_evidence", "confidence"] if c in top]
    payload = {"campaign": campaign, "retrieved_memory": memory,
               "candidates": top[fields].fillna("").to_dict("records")}
    system = ("You are an evidence-bound creator campaign analyst. Use only supplied facts. "
              "Never invent creator demographics, creator behaviour, product claims, campaign outcomes or ROAS. "
              "State that creator-level post mapping and audience demographics are unavailable. "
              "Return valid JSON: {recommendations:[{handle,rationale,campaign_angle,hook,human_checks}]}")
    answer = llm.complete(system, json.dumps(payload, ensure_ascii=False)) if llm else None
    if answer:
        try:
            parsed = json.loads(answer)
            if isinstance(parsed, dict) and isinstance(parsed.get("recommendations"), list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    return {"recommendations": [{
        "handle": r["handle"], "rationale": r.get("decision_reason", "Ranked by supplied influencer metrics and campaign fit."),
        "campaign_angle": "Build a concept only after reviewing the creator's current public content; the supplied influencer table has no content themes.",
        "hook": "Use a format verified from the creator's current feed.",
        "human_checks": ["Verify current content and audience fit", "Obtain follower-demographic data if targeting depends on it",
                         "Review all product claims", "Confirm disclosure and brand-safety requirements"]
    } for _, r in top.iterrows()]}
