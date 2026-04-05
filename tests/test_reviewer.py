"""Tests for reviewer - JSON parsing, review pipeline."""

import pytest
from src.agents.reviewer import (
    ReviewAgent, QAAgent, ReviewPipeline, ReviewResult,
    ReviewComment, ReviewSeverity, ReviewCategory, QAResult,
)


class TestReviewResultParsing:
    def _make_agent(self):
        return ReviewAgent(min_score=7.0)

    def test_parse_clean_json(self):
        agent = self._make_agent()
        json_str = '{"approved": true, "score": 8.5, "summary": "Good code", "comments": []}'
        result = agent._parse_review(json_str)
        assert result.approved is True
        assert result.score == 8.5
        assert result.summary == "Good code"

    def test_parse_json_in_markdown(self):
        agent = self._make_agent()
        text = '```json\n{"approved": true, "score": 9.0, "summary": "Clean", "comments": []}\n```'
        result = agent._parse_review(text)
        assert result.approved is True
        assert result.score == 9.0

    def test_parse_json_with_surrounding_text(self):
        agent = self._make_agent()
        text = 'Here is my review:\n\n{"approved": false, "score": 4.0, "summary": "Bad", "comments": [{"file": "app.py", "line": 10, "category": "bug", "severity": "error", "message": "NPE", "suggestion": "add null check"}]}\n\nEnd.'
        result = agent._parse_review(text)
        assert result.approved is False
        assert result.score == 4.0
        assert len(result.comments) == 1
        assert result.comments[0].category == ReviewCategory.BUG
        assert result.comments[0].severity == ReviewSeverity.ERROR

    def test_parse_malformed_json(self):
        agent = self._make_agent()
        result = agent._parse_review("This is not JSON at all")
        assert result.approved is False
        assert result.score == 0

    def test_parse_comments_with_invalid_enum(self):
        agent = self._make_agent()
        text = '{"approved": true, "score": 8.0, "summary": "ok", "comments": [{"file": "x.py", "line": 1, "category": "invalid_category", "severity": "info", "message": "test"}]}'
        result = agent._parse_review(text)
        # Invalid category should be skipped, not crash
        assert len(result.comments) == 0

    def test_score_below_threshold_rejects(self):
        agent = self._make_agent()
        text = '{"approved": true, "score": 5.0, "summary": "ok", "comments": []}'
        result = agent._parse_review(text)
        # LLM said approved but score < min_score
        assert result.approved is False

    def test_has_blockers(self):
        result = ReviewResult(
            approved=False, score=3.0,
            comments=[
                ReviewComment("f.py", 1, ReviewCategory.BUG, ReviewSeverity.CRITICAL, "NPE"),
                ReviewComment("f.py", 2, ReviewCategory.STYLE, ReviewSeverity.INFO, "naming"),
            ]
        )
        assert result.has_blockers is True

    def test_no_blockers(self):
        result = ReviewResult(
            approved=True, score=9.0,
            comments=[
                ReviewComment("f.py", 1, ReviewCategory.STYLE, ReviewSeverity.INFO, "naming"),
            ]
        )
        assert result.has_blockers is False

    def test_to_dict(self):
        result = ReviewResult(approved=True, score=8.0, summary="ok")
        d = result.to_dict()
        assert d["approved"] is True
        assert d["score"] == 8.0
        assert d["blockers"] == 0


class TestQAResultParsing:
    def _make_agent(self):
        return QAAgent()

    def test_parse_clean_json(self):
        agent = self._make_agent()
        text = '{"passed": true, "test_cases": [{"name": "test_basic"}], "coverage_estimate": "80%", "summary": "Good"}'
        result = agent._parse_qa(text)
        assert result.passed is True
        assert len(result.test_cases) == 1
        assert result.coverage_estimate == "80%"

    def test_parse_malformed(self):
        agent = self._make_agent()
        result = agent._parse_qa("Not JSON")
        assert result.passed is False

    def test_qa_result_to_dict(self):
        result = QAResult(passed=True, test_cases=[{"name": "t1"}], coverage_estimate="90%")
        d = result.to_dict()
        assert d["passed"] is True
        assert d["coverage_estimate"] == "90%"


class TestReviewPipeline:
    def test_pipeline_init(self):
        pipeline = ReviewPipeline()
        assert pipeline.reviewer is not None
        assert pipeline.qa is not None
