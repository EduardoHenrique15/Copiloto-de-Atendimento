import json

from copiloto.core.logging import (
    bind_correlation_id,
    clear_correlation_id,
    configure_logging,
    get_logger,
)


def _last_json_line(capsys) -> dict:
    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    return json.loads(lines[-1])


def test_logs_are_json_with_level_and_timestamp(capsys):
    configure_logging("INFO")
    get_logger("teste").info("evento_teste", quantidade=3)
    event = _last_json_line(capsys)
    assert event["event"] == "evento_teste"
    assert event["level"] == "info"
    assert event["quantidade"] == 3
    assert event["logger"] == "teste"
    assert "timestamp" in event


def test_correlation_id_is_attached_and_cleared(capsys):
    configure_logging("INFO")
    cid = bind_correlation_id("abc123")
    get_logger().info("com_id")
    assert _last_json_line(capsys)["correlation_id"] == cid == "abc123"
    clear_correlation_id()
    get_logger().info("sem_id")
    assert "correlation_id" not in _last_json_line(capsys)


def test_generated_correlation_id_is_unique():
    first = bind_correlation_id()
    second = bind_correlation_id()
    clear_correlation_id()
    assert first != second


def test_level_filter_drops_debug(capsys):
    configure_logging("WARNING")
    get_logger().info("nao_aparece")
    assert capsys.readouterr().out == ""


def test_accented_text_is_kept(capsys):
    configure_logging("INFO")
    get_logger().info("avaliação", texto="não chegou")
    assert _last_json_line(capsys)["texto"] == "não chegou"
