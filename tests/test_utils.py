"""Tests for utils - retry decorators, error classes."""

import pytest
import asyncio
from src.utils import (
    retry, async_retry,
    ThiemAICampError, AgentError, ExecutionError, PersistenceError,
)


class TestExceptions:
    def test_base_error(self):
        with pytest.raises(ThiemAICampError):
            raise ThiemAICampError("base error")

    def test_agent_error(self):
        original = ValueError("inner")
        err = AgentError("api_agent", "task failed", original)
        assert "api_agent" in str(err)
        assert "task failed" in str(err)
        assert err.agent_name == "api_agent"
        assert err.original is original

    def test_execution_error(self):
        err = ExecutionError("timeout", returncode=1, stderr="killed")
        assert err.returncode == 1
        assert err.stderr == "killed"

    def test_persistence_error(self):
        err = PersistenceError("db locked")
        assert isinstance(err, ThiemAICampError)

    def test_inheritance(self):
        assert issubclass(AgentError, ThiemAICampError)
        assert issubclass(ExecutionError, ThiemAICampError)
        assert issubclass(PersistenceError, ThiemAICampError)


class TestRetry:
    def test_success_no_retry(self):
        call_count = [0]

        @retry(max_attempts=3)
        def succeeds():
            call_count[0] += 1
            return "ok"

        assert succeeds() == "ok"
        assert call_count[0] == 1

    def test_retry_then_succeed(self):
        call_count = [0]

        @retry(max_attempts=3, delay=0.01)
        def fails_twice():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("not yet")
            return "ok"

        assert fails_twice() == "ok"
        assert call_count[0] == 3

    def test_retry_exhausted(self):
        @retry(max_attempts=2, delay=0.01)
        def always_fails():
            raise ValueError("always")

        with pytest.raises(ValueError, match="always"):
            always_fails()

    def test_retry_specific_exceptions(self):
        call_count = [0]

        @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
        def raises_type_error():
            call_count[0] += 1
            raise TypeError("wrong type")

        with pytest.raises(TypeError):
            raises_type_error()
        assert call_count[0] == 1  # No retry for TypeError

    def test_retry_with_backoff(self):
        call_count = [0]

        @retry(max_attempts=3, delay=0.01, backoff=2.0)
        def fails():
            call_count[0] += 1
            raise ValueError("fail")

        with pytest.raises(ValueError):
            fails()
        assert call_count[0] == 3


class TestAsyncRetry:
    def test_async_success(self):
        call_count = [0]

        @async_retry(max_attempts=3, delay=0.01)
        async def succeeds():
            call_count[0] += 1
            return "ok"

        result = asyncio.get_event_loop().run_until_complete(succeeds())
        assert result == "ok"
        assert call_count[0] == 1

    def test_async_retry_then_succeed(self):
        call_count = [0]

        @async_retry(max_attempts=3, delay=0.01)
        async def fails_once():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("not yet")
            return "ok"

        result = asyncio.get_event_loop().run_until_complete(fails_once())
        assert result == "ok"
        assert call_count[0] == 2

    def test_async_retry_exhausted(self):
        @async_retry(max_attempts=2, delay=0.01)
        async def always_fails():
            raise RuntimeError("always")

        with pytest.raises(RuntimeError, match="always"):
            asyncio.get_event_loop().run_until_complete(always_fails())
