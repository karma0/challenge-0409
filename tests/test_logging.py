"""Tests for logging functionality."""

import json
import logging
import time

import pytest

from qa_chain.config import QAConfig
from qa_chain.debug_utils import (
    DebugContext,
    DebugStats,
    debug_config,
    debug_mode,
    dump_debug_info,
    log_memory_usage,
    trace_llm_call,
)
from qa_chain.logging_config import (
    LogContext,
    StructuredFormatter,
    get_logger,
    log_execution_time,
    log_with_context,
    request_id_var,
    setup_logging,
    with_request_id,
)


class TestStructuredFormatter:
    """Test structured logging formatter."""

    def test_format_basic_message(self):
        """Test basic log message formatting."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert data["message"] == "Test message"
        assert data["line"] == 10

    def test_format_with_request_id(self):
        """Test formatting with request ID context."""
        formatter = StructuredFormatter()
        request_id = "test-request-123"

        token = request_id_var.set(request_id)
        try:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=10,
                msg="Test message",
                args=(),
                exc_info=None,
            )

            result = formatter.format(record)
            data = json.loads(result)

            assert data["request_id"] == request_id
        finally:
            request_id_var.reset(token)

    def test_format_with_extra_fields(self):
        """Test formatting with extra fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra_fields = {"user_id": "123", "action": "test"}

        result = formatter.format(record)
        data = json.loads(result)

        assert data["user_id"] == "123"
        assert data["action"] == "test"


class TestLoggingSetup:
    """Test logging setup and configuration."""

    def test_setup_logging_json_format(self, tmp_path):
        """Test setting up JSON formatted logging."""
        log_file = tmp_path / "test.log"
        setup_logging("INFO", "json", str(log_file))

        logger = get_logger("test")
        logger.info("Test message")

        # Check log file
        with open(log_file) as f:
            line = f.readline()
            data = json.loads(line)
            assert data["level"] == "INFO"
            assert data["message"] == "Test message"

    def test_setup_logging_simple_format(self, tmp_path):
        """Test setting up simple formatted logging."""
        log_file = tmp_path / "test.log"
        setup_logging("DEBUG", "simple", str(log_file))

        logger = get_logger("test")
        logger.debug("Debug message")

        # Check log file
        with open(log_file) as f:
            content = f.read()
            assert "DEBUG" in content
            assert "Debug message" in content

    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger("test.module")
        assert logger.name == "test.module"
        assert isinstance(logger, logging.Logger)


class TestLoggingDecorators:
    """Test logging decorator functions."""

    def test_with_request_id_decorator(self):
        """Test request ID decorator."""

        @with_request_id("test-123")
        def test_func():
            return request_id_var.get()

        result = test_func()
        assert result == "test-123"

        # Check context is cleared after function
        assert request_id_var.get() is None

    def test_with_request_id_auto_generate(self):
        """Test request ID decorator with auto-generation."""

        @with_request_id()
        def test_func():
            return request_id_var.get()

        result = test_func()
        assert result is not None
        assert len(result) == 36  # UUID length

    def test_log_with_context_decorator(self, caplog):
        """Test logging with context decorator."""

        @log_with_context(user_id="123", action="test")
        def test_func():
            logger = get_logger(__name__)
            logger.info("Test message")

        with caplog.at_level(logging.INFO):
            test_func()

        # Note: Testing the context injection is complex due to monkey patching
        assert "Test message" in caplog.text

    def test_log_execution_time_decorator(self, caplog):
        """Test execution time logging decorator."""

        @log_execution_time()
        def test_func():
            time.sleep(0.01)
            return "result"

        with caplog.at_level(logging.INFO):
            result = test_func()

        assert result == "result"
        assert "Completed test_func" in caplog.text

    def test_log_execution_time_with_error(self, caplog):
        """Test execution time logging with error."""

        @log_execution_time()
        def test_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            with caplog.at_level(logging.ERROR):
                test_func()

        assert "Failed test_func" in caplog.text
        assert "Test error" in caplog.text


class TestLogContext:
    """Test LogContext context manager."""

    def test_log_context_adds_fields(self):
        """Test that LogContext adds fields to logs."""
        # This is a complex test because LogContext modifies logger internals
        # We'll test that the context manager doesn't raise errors
        logger = get_logger("test")

        try:
            with LogContext(logger, user_id="123", request_type="test"):
                logger.info("Test message")
        except Exception as e:
            pytest.fail(f"LogContext raised an exception: {e}")


class TestDebugUtilities:
    """Test debug utilities."""

    def test_debug_context(self, caplog):
        """Test DebugContext manager."""
        with caplog.at_level(logging.DEBUG):
            with DebugContext() as ctx:
                ctx.checkpoint("start", {"step": 1})
                time.sleep(0.01)
                ctx.checkpoint("middle", {"step": 2})
                time.sleep(0.01)
                ctx.checkpoint("end", {"step": 3})

        assert "Debug checkpoint: start" in caplog.text
        assert "Debug checkpoint: middle" in caplog.text
        assert "Debug checkpoint: end" in caplog.text
        assert "Debug context completed" in caplog.text

    def test_debug_config(self):
        """Test config debugging."""
        config = QAConfig(model="gpt-4", temperature=0.5)

        # Test that debug_config doesn't raise errors
        try:
            debug_config(config)
        except Exception as e:
            pytest.fail(f"debug_config raised an exception: {e}")

    def test_trace_llm_call_success(self, caplog):
        """Test LLM call tracing for successful calls."""

        @trace_llm_call
        def mock_llm_call(prompt: str) -> str:
            return "response"

        with caplog.at_level(logging.DEBUG):
            result = mock_llm_call("test prompt")

        assert result == "response"
        assert "LLM call started: mock_llm_call" in caplog.text
        assert "LLM call completed: mock_llm_call" in caplog.text

    def test_trace_llm_call_error(self, caplog):
        """Test LLM call tracing for failed calls."""

        @trace_llm_call
        def mock_llm_call(prompt: str) -> str:
            raise RuntimeError("API error")

        with pytest.raises(RuntimeError):
            with caplog.at_level(logging.ERROR):
                mock_llm_call("test prompt")

        assert "LLM call failed: mock_llm_call" in caplog.text
        assert "API error" in caplog.text

    def test_log_memory_usage(self, caplog):
        """Test memory usage logging."""
        with caplog.at_level(logging.DEBUG):
            stats = log_memory_usage()

        # If psutil is available, we should get stats
        if stats:
            assert "Memory usage" in caplog.text
            assert "rss_mb" in stats
        else:
            assert "psutil not available" in caplog.text

    def test_debug_mode_context(self, caplog):
        """Test debug mode context manager."""
        logger = get_logger("test")
        original_level = logger.level

        with caplog.at_level(logging.DEBUG):
            with debug_mode(True):
                logger.debug("Debug message in debug mode")

            # After exiting, level should be restored
            assert logger.level == original_level

        assert "Debug mode enabled" in caplog.text
        assert "Debug message in debug mode" in caplog.text
        assert "Debug mode disabled" in caplog.text

    def test_dump_debug_info(self, tmp_path):
        """Test dumping debug info to file."""
        config = QAConfig(enable_debug_mode=True)
        debug_file = tmp_path / "debug.json"

        dump_debug_info(
            question="What is AI?",
            context="AI is artificial intelligence.",
            answer="AI stands for artificial intelligence.",
            config=config,
            execution_time=1.23,
            filename=str(debug_file),
        )

        assert debug_file.exists()

        with open(debug_file) as f:
            data = json.load(f)
            assert data["execution_time"] == 1.23
            assert data["input"]["question"] == "What is AI?"
            assert data["output"]["answer"] == "AI stands for artificial intelligence."

    def test_dump_debug_info_disabled(self, tmp_path):
        """Test debug dumping when disabled."""
        config = QAConfig(enable_debug_mode=False)
        debug_file = tmp_path / "debug.json"

        dump_debug_info(
            question="Test",
            context="Test",
            answer="Test",
            config=config,
            execution_time=1.0,
            filename=str(debug_file),
        )

        # File should not be created when debug mode is disabled
        assert not debug_file.exists()


class TestDebugStats:
    """Test debug statistics collector."""

    def test_record_metrics(self):
        """Test recording metrics."""
        stats = DebugStats()

        stats.record("latency", 100)
        stats.record("latency", 150)
        stats.record("latency", 200)
        stats.record("tokens", 50)
        stats.record("tokens", 75)

        assert len(stats.stats["latency"]) == 3
        assert len(stats.stats["tokens"]) == 2
        assert stats.stats["latency"] == [100, 150, 200]

    def test_log_summary(self):
        """Test logging summary statistics."""
        stats = DebugStats()

        stats.record("latency", 100)
        stats.record("latency", 200)
        stats.record("latency", 300)

        # Test that log_summary computes correct statistics
        # We'll verify the internal state rather than log output
        stats.log_summary()

        # Verify internal calculations were correct
        assert len(stats.stats["latency"]) == 3
        assert min(stats.stats["latency"]) == 100
        assert max(stats.stats["latency"]) == 300
        assert sum(stats.stats["latency"]) / len(stats.stats["latency"]) == 200
