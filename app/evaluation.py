
"""Deterministic quality metrics for research runs."""

from collections import Counter


def recall_at_k(retrieved_ids, relevant_ids, k=5):
    relevant = set(relevant_ids)
    if not relevant:
        return 1.0
    retrieved = list(retrieved_ids)[:max(0, k)]
    return len(set(retrieved) & relevant) / len(relevant)


def reciprocal_rank(retrieved_ids, relevant_ids):
    relevant = set(relevant_ids)
    for rank, item_id in enumerate(retrieved_ids, start=1):
        if item_id in relevant:
            return 1.0 / rank
    return 0.0


def source_coverage(source_count, min_sources=2):
    count = max(0, int(source_count))
    return {
        "source_count": count,
        "minimum_recommended": min_sources,
        "meets_minimum": count >= min_sources,
    }


def report_has_source_markers(report, sources):
    text = (report or "").lower()
    matches = []

    for source in sources or []:
        for field in ("url", "title"):
            value = str(source.get(field, "")).strip()
            if value and value.lower() in text:
                matches.append({"field": field, "value": value})

    return {
        "has_report": bool((report or "").strip()),
        "matched_source_markers": matches,
        "matched_marker_count": len(matches),
        "note": (
            "Heuristic only; matching text does not prove "
            "a claim is supported."
        ),
    }


def evaluate_research(result):
    """Produce transparent, deterministic checks for a research result."""
    sources = result.get("sources") or []
    report = result.get("report") or ""

    source_types = Counter(
        source.get("source_type", "unknown")
        for source in sources
    )

    marker_check = report_has_source_markers(report, sources)
    coverage = source_coverage(len(sources))

    return {
        "source_coverage": coverage,
        "source_type_counts": dict(source_types),
        "report_has_content": bool(report.strip()),
        "matched_source_marker_count": marker_check["matched_marker_count"],
        "source_marker_check": marker_check,
        "limitations": [
            "Source count does not measure source quality.",
            "Marker matching does not prove factual correctness.",
            "Retrieval recall requires labelled relevant documents.",
        ],
    }
