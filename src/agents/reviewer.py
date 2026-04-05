"""
UPGRADE 4 - REVIEW AGENT (v2 - with error handling, structured QA)
Flow: Dev > Reviewer > QA
Reviewer kiểm tra: code smell, bugs, architecture violations.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from src.utils import async_retry, AgentError

logger = logging.getLogger(__name__)


class ReviewSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ReviewCategory(str, Enum):
    CODE_SMELL = "code_smell"
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    STYLE = "style"


@dataclass
class ReviewComment:
    file: str
    line: Optional[int]
    category: ReviewCategory
    severity: ReviewSeverity
    message: str
    suggestion: str = ""


@dataclass
class ReviewResult:
    approved: bool
    comments: list[ReviewComment] = field(default_factory=list)
    summary: str = ""
    score: float = 0.0

    @property
    def has_blockers(self) -> bool:
        return any(
            c.severity in (ReviewSeverity.ERROR, ReviewSeverity.CRITICAL)
            for c in self.comments
        )

    def to_dict(self) -> dict:
        return {
            "approved": self.approved,
            "score": self.score,
            "summary": self.summary,
            "blockers": sum(1 for c in self.comments if c.severity in (ReviewSeverity.ERROR, ReviewSeverity.CRITICAL)),
            "warnings": sum(1 for c in self.comments if c.severity == ReviewSeverity.WARNING),
            "comments": [
                {
                    "file": c.file,
                    "line": c.line,
                    "category": c.category.value,
                    "severity": c.severity.value,
                    "message": c.message,
                    "suggestion": c.suggestion,
                }
                for c in self.comments
            ],
        }


@dataclass
class QAResult:
    passed: bool
    test_cases: list[dict] = field(default_factory=list)
    coverage_estimate: str = "0%"
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "test_cases": self.test_cases,
            "coverage_estimate": self.coverage_estimate,
            "summary": self.summary,
        }


REVIEWER_SYSTEM_PROMPT = """Ban la Code Reviewer Agent chuyen nghiep. Nhiem vu:

1. **Code Smell Detection**: duplicate code, long methods, god classes, feature envy
2. **Bug Detection**: null pointer, race condition, resource leak, off-by-one, injection
3. **Architecture Review**: SOLID violations, coupling issues, layer violations
4. **Security**: SQL injection, XSS, hardcoded secrets, insecure crypto
5. **Performance**: N+1 queries, unnecessary loops, memory leaks

Tra ve review theo format JSON (KHONG co text ngoai JSON):
{
    "approved": true/false,
    "score": 0-10,
    "summary": "tom tat review",
    "comments": [
        {
            "file": "filename",
            "line": null,
            "category": "code_smell|bug|security|performance|architecture|style",
            "severity": "info|warning|error|critical",
            "message": "mo ta van de",
            "suggestion": "cach fix"
        }
    ]
}"""


class ReviewAgent:
    """Agent review code trước khi merge."""

    def __init__(self, model: str = "claude-sonnet-4-5-20250514", min_score: float = 7.0):
        self.model = model
        self.min_score = min_score

    def get_llm(self) -> ChatAnthropic:
        return ChatAnthropic(model=self.model, temperature=0)

    @async_retry(max_attempts=2, delay=1.0)
    async def review_code(self, code: str, filename: str = "unknown", context: str = "") -> ReviewResult:
        """Review một đoạn code."""
        llm = self.get_llm()
        prompt = f"Review code sau:\n\nFile: {filename}\n\n```\n{code}\n```"
        if context:
            prompt += f"\n\nContext: {context}"

        messages = [
            SystemMessage(content=REVIEWER_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = await llm.ainvoke(messages)
        return self._parse_review(response.content)

    @async_retry(max_attempts=2, delay=1.0)
    async def review_diff(self, diff: str, context: str = "") -> ReviewResult:
        """Review một git diff."""
        llm = self.get_llm()
        prompt = f"Review git diff sau:\n\n```diff\n{diff}\n```"
        if context:
            prompt += f"\n\nContext: {context}"

        messages = [
            SystemMessage(content=REVIEWER_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = await llm.ainvoke(messages)
        return self._parse_review(response.content)

    def _parse_review(self, response_text: str) -> ReviewResult:
        """Parse response từ LLM thành ReviewResult."""
        text = response_text.strip()

        # Extract JSON from various formats
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        # Try to find JSON object directly
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]

        try:
            data = json.loads(text.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse review JSON: {e}")
            return ReviewResult(
                approved=False, score=0,
                summary=f"Parse error - raw response: {response_text[:200]}",
            )

        comments = []
        for c in data.get("comments", []):
            try:
                comments.append(ReviewComment(
                    file=c.get("file", "unknown"),
                    line=c.get("line"),
                    category=ReviewCategory(c.get("category", "style")),
                    severity=ReviewSeverity(c.get("severity", "info")),
                    message=c.get("message", ""),
                    suggestion=c.get("suggestion", ""),
                ))
            except (ValueError, KeyError) as e:
                logger.debug(f"Skipped malformed comment: {e}")
                continue

        score = float(data.get("score", 0))
        return ReviewResult(
            approved=data.get("approved", False) and score >= self.min_score,
            comments=comments,
            summary=data.get("summary", ""),
            score=score,
        )


QA_SYSTEM_PROMPT = """Ban la QA Agent. Viet test cases va danh gia chat luong code.

Tra ve JSON (KHONG co text ngoai JSON):
{
    "passed": true/false,
    "test_cases": [
        {"name": "test name", "type": "unit|integration|e2e", "description": "what it tests", "expected": "expected result"}
    ],
    "coverage_estimate": "X%",
    "summary": "overall quality assessment"
}"""


class QAAgent:
    """Agent chạy QA checks sau review."""

    def __init__(self, model: str = "claude-sonnet-4-5-20250514"):
        self.model = model

    @async_retry(max_attempts=2, delay=1.0)
    async def run_qa(self, code: str, test_requirements: str = "") -> QAResult:
        """Chạy QA analysis trên code."""
        llm = ChatAnthropic(model=self.model, temperature=0)
        prompt = (
            f"Viet test cases va danh gia code:\n\n```\n{code}\n```\n\n"
            f"Yeu cau: {test_requirements or 'Tu xac dinh test cases phu hop'}"
        )
        messages = [
            SystemMessage(content=QA_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = await llm.ainvoke(messages)
        return self._parse_qa(response.content)

    def _parse_qa(self, response_text: str) -> QAResult:
        text = response_text.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]

        try:
            data = json.loads(text)
            return QAResult(
                passed=data.get("passed", False),
                test_cases=data.get("test_cases", []),
                coverage_estimate=data.get("coverage_estimate", "0%"),
                summary=data.get("summary", ""),
            )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse QA JSON: {e}")
            return QAResult(passed=False, summary=f"Parse error: {response_text[:200]}")


class ReviewPipeline:
    """Pipeline: Dev > Reviewer > QA."""

    def __init__(self, model: str = "claude-sonnet-4-5-20250514", min_score: float = 7.0):
        self.reviewer = ReviewAgent(model=model, min_score=min_score)
        self.qa = QAAgent(model=model)

    async def run(self, code: str, filename: str = "", context: str = "") -> dict:
        """Chạy full review pipeline."""
        # Step 1: Code Review
        review = await self.reviewer.review_code(code, filename, context)
        result = {
            "step": "review",
            "review": review.to_dict(),
            "passed": review.approved,
        }

        # Step 2: QA if review passed
        if review.approved:
            qa_result = await self.qa.run_qa(code)
            result["step"] = "qa"
            result["qa"] = qa_result.to_dict()
            result["passed"] = qa_result.passed

        logger.info(f"Review pipeline for {filename}: passed={result['passed']}")
        return result
