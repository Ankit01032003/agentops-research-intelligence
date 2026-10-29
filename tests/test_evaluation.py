from app.evaluation import recall_at_k, reciprocal_rank, source_coverage, report_has_source_markers

def test_recall_at_k():
    assert recall_at_k(["a", "b", "c"], ["b", "d"], k=2) == 0.5

def test_reciprocal_rank():
    assert reciprocal_rank(["x", "b", "c"], ["b"]) == 0.5
    assert reciprocal_rank(["x"], ["b"]) == 0.0

def test_source_coverage_and_markers():
    assert source_coverage(2)["meets_minimum"] is True
    result = report_has_source_markers("Read https://example.com", [{"url": "https://example.com"}])
    assert result["matched_marker_count"] == 1
