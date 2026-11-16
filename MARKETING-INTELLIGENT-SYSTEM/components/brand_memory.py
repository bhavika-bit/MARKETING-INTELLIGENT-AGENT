import hashlib
import json
import re
from pathlib import Path
from .utils import txt


class BrandMemory:
    """Persistent evidence store; never treats descriptive trends as campaign outcomes."""
    def __init__(self, path="outputs/brand_memory.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.items = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else []
        except (json.JSONDecodeError, OSError):
            self.items = []
        if not isinstance(self.items, list):
            self.items = []
        self._ids = {x.get("id") for x in self.items if isinstance(x, dict)}

    def add(self, category, text, source="provided data"):
        text = txt(text)
        if not text:
            return
        key = hashlib.sha256(f"{category}|{source}|{text}".encode("utf-8")).hexdigest()[:20]
        if key not in self._ids:
            self.items.append({"id": key, "category": category, "text": text, "source": source})
            self._ids.add(key)

    def seed(self, ads, creators):
        ad_fields = ["platform", "hashtag", "content_type", "region", "engagement_level"]
        creator_fields = ["handle", "influence_score", "followers_numeric", "avg_likes_numeric",
                          "engagement_rate_pct", "creator_country"]
        for _, row in ads.iterrows():
            self.add("trend_reference", " | ".join(txt(row.get(c)) for c in ad_fields), "Cleaned_Viral_Social_Media_Trends.csv")
        for _, row in creators.iterrows():
            self.add("creator_profile", " | ".join(txt(row.get(c)) for c in creator_fields), "top_insta_influencers_data.csv")
        # Instagram Analytics is aggregate/account-id data; it is not an outcome record for a named influencer.

    def retrieve(self, query, limit=8):
        q = set(re.findall(r"[a-z0-9]+", txt(query).lower()))
        ranked = []
        for item in self.items:
            words = set(re.findall(r"[a-z0-9]+", txt(item.get("text")).lower()))
            similarity = len(q & words) / max(1, len(q | words))
            ranked.append((similarity, item))
        return [item for similarity, item in sorted(ranked, key=lambda x: x[0], reverse=True)[:limit] if similarity > 0]

    def save(self):
        self.path.write_text(json.dumps(self.items, indent=2, ensure_ascii=False), encoding="utf-8")
