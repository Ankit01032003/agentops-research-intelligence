"""Deterministic evaluation helpers. Scores need labelled test data to be meaningful."""
def recall_at_k(retrieved_ids, relevant_ids, k=5):
    relevant = set(relevant_ids)
    if not relevant:
        return 1.0
    return len(set(list(retrieved_ids)[:max(0, k)]) & relevant) / len(relevant)

def reciprocal_rank(retrieved_ids, relevant_ids):
    relevant = set(relevant_ids)
    for rank, item_id in enumerate(retrieved_ids, start=1):
        if item_id in relevant:
            return 1.0 / rank
    return 0.0

def source_coverage(source_count, min_sources=2):
    count = max(0, int(source_count))
    return {"source_count": count, "minimum_recommended": min_sources,
            "meets_minimum": count >= min_sources}

def report_has_source_markers(report, sources):
    text = (report or "").lower()
    matches = []
    for source in sources or []:
        for field in ("url", "title"):
            value = str(source.get(field, "")).strip()
            if value and value.lower() in text:
                matches.append({"field": field, "value": value})
    return {"has_report": bool((report or "").strip()),
            "matched_source_markers": matches,
            "matched_marker_count": len(matches),
            "note": "Heuristic only; matching text does not prove a claim is supported."}
