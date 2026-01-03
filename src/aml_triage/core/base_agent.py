"""Base agent framework for all specialist agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from datetime import datetime
import asyncio
from enum import Enum

from anthropic import AsyncAnthropic
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from aml_triage.core.config import settings
from aml_triage.core.logging import get_logger, log_agent_action


T = TypeVar("T")


class AgentStatus(str, Enum):
    """Agent processing status."""

    IDLE = "IDLE"
    PROCESSING = "PROCESSING"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"
    COMPLETED = "COMPLETED"


class AgentState:
    """Track agent processing state."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.status = AgentStatus.IDLE
        self.current_alert_id: Optional[str] = None
        self.processing_start_time: Optional[datetime] = None
        self.last_heartbeat = datetime.now()
        self.performance_metrics: Dict[str, Any] = {}

    def start_processing(self, alert_id: str) -> None:
        """Mark agent as processing an alert."""
        self.status = AgentStatus.PROCESSING
        self.current_alert_id = alert_id
        self.processing_start_time = datetime.now()

    def complete_processing(self) -> None:
        """Mark agent as completed processing."""
        self.status = AgentStatus.COMPLETED
        if self.processing_start_time:
            duration = (datetime.now() - self.processing_start_time).total_seconds()
            self.performance_metrics["last_processing_duration_ms"] = duration * 1000
        self.processing_start_time = None

    def mark_error(self, error: str) -> None:
        """Mark agent as in error state."""
        self.status = AgentStatus.ERROR
        self.performance_metrics["last_error"] = error

    def heartbeat(self) -> None:
        """Update last heartbeat timestamp."""
        self.last_heartbeat = datetime.now()


class AgentException(Exception):
    """Base exception for agent errors."""

    pass


class RetryableAgentException(AgentException):
    """Exception that should trigger a retry."""

    pass


class CriticalAgentException(AgentException):
    """Critical exception that should not be retried."""

    pass


class BaseAgent(ABC, Generic[T]):
    """
    Base class for all specialist agents in the system.

    All agents must implement the process() method and can optionally
    override pre_process() and post_process() hooks.
    """

    def __init__(
        self,
        name: str,
        model: str,
        temperature: float,
        max_tokens: int = 4000,
        timeout: int = 30,
    ):
        """
        Initialize the base agent.

        Args:
            name: Agent name for identification
            model: LLM model to use
            temperature: Temperature setting for LLM
            max_tokens: Maximum tokens for LLM response
            timeout: Processing timeout in seconds
        """
        self.name = name
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        self.state = AgentState(name)
        self.logger = get_logger(name)

        # Initialize LLM client
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """
        Return the system prompt for this agent.

        Must be implemented by each specialist agent.
        """
        pass

    @abstractmethod
    async def process(self, *args: Any, **kwargs: Any) -> T:
        """
        Main processing logic for the agent.

        Must be implemented by each specialist agent.

        Returns:
            Processed result of type T
        """
        pass

    async def pre_process(self, *args: Any, **kwargs: Any) -> None:
        """
        Hook called before process(). Override to add preprocessing logic.
        """
        pass

    async def post_process(self, result: T) -> T:
        """
        Hook called after process(). Override to add postprocessing logic.

        Args:
            result: The result from process()

        Returns:
            Potentially modified result
        """
        return result

    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(RetryableAgentException),
        reraise=True,
    )
    async def execute(self, alert_id: str, *args: Any, **kwargs: Any) -> T:
        """
        Execute the agent workflow with retry logic and error handling.

        Args:
            alert_id: Alert ID being processed
            *args: Arguments to pass to process()
            **kwargs: Keyword arguments to pass to process()

        Returns:
            Processed result

        Raises:
            AgentException: If processing fails
        """
        self.state.start_processing(alert_id)

        start_time = datetime.now()

        try:
            # Pre-processing hook
            await self.pre_process(*args, **kwargs)

            # Main processing with timeout
            result = await asyncio.wait_for(
                self.process(*args, **kwargs), timeout=self.timeout
            )

            # Post-processing hook
            result = await self.post_process(result)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Log success
            log_agent_action(
                self.logger,
                agent_name=self.name,
                action="processing_completed",
                alert_id=alert_id,
                metadata={
                    "processing_time_ms": processing_time,
                    "status": "success",
                },
            )

            self.state.complete_processing()

            return result

        except asyncio.TimeoutError as e:
            error_msg = f"Agent {self.name} timed out after {self.timeout}s"
            self.logger.error("agent_timeout", alert_id=alert_id, error=error_msg)
            self.state.mark_error(error_msg)
            raise RetryableAgentException(error_msg) from e

        except Exception as e:
            error_msg = f"Agent {self.name} failed: {str(e)}"
            self.logger.error(
                "agent_error", alert_id=alert_id, error=error_msg, exc_info=True
            )
            self.state.mark_error(error_msg)
            raise CriticalAgentException(error_msg) from e

    async def call_llm(
        self,
        messages: list[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Call the LLM with the given messages.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            LLM response content
        """
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                system=self.system_prompt,
                messages=messages,
            )

            # Extract text content from response
            content = response.content[0].text if response.content else ""

            return content

        except Exception as e:
            self.logger.error("llm_call_failed", error=str(e), exc_info=True)
            raise RetryableAgentException(f"LLM call failed: {str(e)}") from e

    def get_state(self) -> Dict[str, Any]:
        """
        Get current agent state.

        Returns:
            Dictionary with agent state information
        """
        return {
            "agent_name": self.name,
            "status": self.state.status.value,
            "current_alert_id": self.state.current_alert_id,
            "processing_start_time": (
                self.state.processing_start_time.isoformat()
                if self.state.processing_start_time
                else None
            ),
            "last_heartbeat": self.state.last_heartbeat.isoformat(),
            "performance_metrics": self.state.performance_metrics,
        }
