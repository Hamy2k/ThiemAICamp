"""
UPGRADE 4 - REVIEW AGENT
Flow: Dev > Reviewer > QA
Reviewer kiểm tra: code smell, bugs, architecture violations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage


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
    score: float = 0.0  # 0-10

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


REVIEWER_SYSTEM_PROMPT = """Bạn là Code Reviewer Agent chuyên nghiệp. Nhiệm vụ:

1. **Code Smell Detection**: tìm duplicate code, long methods, god classes, feature envy
2. **Bug Detection**: null pointer, race condition, resource leak, off-by-one, injection
3. **Architecture Review**: SOLID violations, coupling issues, layer violations
4. **Security**: SQL injection, XSS, hardcoded secrets, insecure crypto
5. **Performance**: N+1 queries, unnecessary loops, memory leaks

Trả về review theo format JSON:
{
    "approved": true/false,
    "score": 0-10,
    "summary": "tóm tắt review",
    "comments": [
        {
            "file": "filename",
            "line": number or null,
            "category": "code_smell|bug|security|performance|architecture|style",
            "severity": "info|warning|error|critical",
            "message": "mô tả vấn đề",
            "suggestion": "cách fix"
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
        import json

        # Tìm JSON block trong response
        text = response_text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        try:
            data = json.loads(text.strip())
        except json.JSONDecodeError:
            return ReviewResult(
                approved=False,
                score=0,
                summary="Không thể parse review response",
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
            except (ValueError, KeyError):
                continue

        score = float(data.get("score", 0))
        return ReviewResult(
            approved=data.get("approved", False) and score >= self.min_score,
            comments=comments,
            summary=data.get("summary", ""),
            score=score,
        )


class QAAgent:
    """Agent chạy QA checks sau review."""

    def __init__(self, model: str = "claude-sonnet-4-5-20250514"):
        self.model = model

    async def run_qa(self, code: str, test_requirements: str = "") -> dict:
        """Chạy QA analysis trên code."""
        llm = ChatAnthropic(model=self.model, temperature=0)
        prompt = (
            f"Hãy viết test cases cho code sau và đánh giá chất lượng:\n\n"
            f"```\n{code}\n```\n\n"
            f"Yêu cầu test: {test_requirements or 'Tự xác định test cases phù hợp'}\n\n"
            f"Trả về JSON: {{\"test_cases\": [...], \"coverage_estimate\": \"X%\", \"qa_passed\": true/false}}"
        )
        messages = [
            SystemMessage(content="Bạn là QA Agent. Viết test cases và đánh giá chất lượng code."),
            HumanMessage(content=prompt),
        ]
        response = await llm.ainvoke(messages)
        return {"qa_response": response.content}


class ReviewPipeline:
    """Pipeline: Dev > Reviewer > QA."""

    def __init__(self):
        self.reviewer = ReviewAgent()
        self.qa = QAAgent()

    async def run(self, code: str, filename: str = "", context: str = "") -> dict:
        """Chạy full review pipeline."""
        # Step 1: Code Review
        review = await self.reviewer.review_code(code, filename, context)

        result = {
            "step": "review",
            "review": review.to_dict(),
        }

        # Step 2: Nếu review pass, chạy QA
        if review.approved:
            qa_result = await self.qa.run_qa(code)
            result["step"] = "qa"
            result["qa"] = qa_result

        return result
