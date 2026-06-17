from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AgentContext:
    company_id: UUID
    user_id: UUID | None = None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    agent: str
    status: str = "success"
    score: Decimal | None = None
    insights: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class BaseAgent(ABC):
    name: str = "base"
    description: str = ""

    def __init__(self, session: AsyncSession):
        self.session = session

    @abstractmethod
    async def analyze(self, context: AgentContext) -> AgentResult:
        pass

    async def _llm_analyze(self, system_prompt: str, user_prompt: str) -> str:
        if not settings.OPENAI_API_KEY:
            return "AI analysis unavailable — configure OPENAI_API_KEY for enhanced insights."
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage, SystemMessage

            llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                temperature=0.2,
            )
            response = await llm.ainvoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            )
            return response.content
        except Exception as exc:
            logger.warning("llm_analysis_failed", agent=self.name, error=str(exc))
            return f"Rule-based analysis applied (LLM unavailable: {exc})"
