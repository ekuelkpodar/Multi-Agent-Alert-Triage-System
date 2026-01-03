"""Unit tests for BaseAgent."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from aml_triage.core.base_agent import (
    BaseAgent,
    AgentState,
    AgentStatus,
    RetryableAgentException,
    CriticalAgentException,
)


class TestAgent(BaseAgent[str]):
    """Test agent implementation."""

    @property
    def system_prompt(self) -> str:
        return "Test agent system prompt"

    async def process(self, test_input: str) -> str:
        """Simple test processing."""
        return f"Processed: {test_input}"


class TestAgentState:
    """Test AgentState functionality."""

    def test_initial_state(self):
        """Test initial agent state."""
        state = AgentState("test_agent")
        assert state.agent_name == "test_agent"
        assert state.status == AgentStatus.IDLE
        assert state.current_alert_id is None
        assert state.processing_start_time is None

    def test_start_processing(self):
        """Test starting processing updates state."""
        state = AgentState("test_agent")
        state.start_processing("alert-123")

        assert state.status == AgentStatus.PROCESSING
        assert state.current_alert_id == "alert-123"
        assert state.processing_start_time is not None

    def test_complete_processing(self):
        """Test completing processing updates metrics."""
        state = AgentState("test_agent")
        state.start_processing("alert-123")
        state.complete_processing()

        assert state.status == AgentStatus.COMPLETED
        assert "last_processing_duration_ms" in state.performance_metrics
        assert state.performance_metrics["last_processing_duration_ms"] > 0

    def test_mark_error(self):
        """Test error marking."""
        state = AgentState("test_agent")
        state.mark_error("Test error message")

        assert state.status == AgentStatus.ERROR
        assert state.performance_metrics["last_error"] == "Test error message"


class TestBaseAgent:
    """Test BaseAgent functionality."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful agent execution."""
        agent = TestAgent(
            name="test_agent",
            model="claude-3-5-sonnet-20241022",
            temperature=0.1,
        )

        result = await agent.execute("test-alert-123", "test input")

        assert result == "Processed: test input"
        assert agent.state.status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self):
        """Test agent execution timeout."""

        class SlowAgent(TestAgent):
            async def process(self, test_input: str) -> str:
                import asyncio

                await asyncio.sleep(2)
                return "done"

        agent = SlowAgent(
            name="slow_agent",
            model="claude-3-5-sonnet-20241022",
            temperature=0.1,
            timeout=0.1,  # 100ms timeout
        )

        with pytest.raises(RetryableAgentException):
            await agent.execute("test-alert-123", "test input")

    @pytest.mark.asyncio
    async def test_call_llm_mock(self):
        """Test LLM call with mocked response."""
        agent = TestAgent(
            name="test_agent",
            model="claude-3-5-sonnet-20241022",
            temperature=0.1,
        )

        # Mock the Anthropic client
        mock_response = Mock()
        mock_response.content = [Mock(text="Test LLM response")]

        agent.client.messages.create = AsyncMock(return_value=mock_response)

        result = await agent.call_llm(
            messages=[{"role": "user", "content": "Test prompt"}]
        )

        assert result == "Test LLM response"
        agent.client.messages.create.assert_called_once()

    def test_get_state(self):
        """Test getting agent state."""
        agent = TestAgent(
            name="test_agent",
            model="claude-3-5-sonnet-20241022",
            temperature=0.1,
        )

        state = agent.get_state()

        assert state["agent_name"] == "test_agent"
        assert state["status"] == AgentStatus.IDLE.value
        assert "performance_metrics" in state
