from datetime import date

import pytest

from copiloto.core.config import Settings
from copiloto.core.costs import LLMPrice, cost_per_thousand_brl, llm_cost_brl, llm_cost_usd
from copiloto.core.errors import ConfigurationError

PRICE = LLMPrice(input_usd_per_mtok=0.10, output_usd_per_mtok=0.40, usd_brl=5.0)


def test_cost_usd_uses_price_per_million_tokens():
    assert llm_cost_usd(1_000_000, 0, PRICE) == pytest.approx(0.10)
    assert llm_cost_usd(0, 1_000_000, PRICE) == pytest.approx(0.40)


def test_cost_brl_converts_with_exchange_rate():
    assert llm_cost_brl(1000, 500, PRICE) == pytest.approx((1000 * 0.10 + 500 * 0.40) / 1e6 * 5)


def test_zero_tokens_cost_nothing():
    assert llm_cost_brl(0, 0, PRICE) == 0


def test_free_tier_price_costs_nothing():
    free = LLMPrice(input_usd_per_mtok=0, output_usd_per_mtok=0, usd_brl=5.0)
    assert llm_cost_brl(10_000, 10_000, free) == 0


def test_cost_per_thousand_matches_single_call_times_thousand():
    assert cost_per_thousand_brl(300, 50, PRICE) == pytest.approx(
        llm_cost_brl(300, 50, PRICE) * 1000
    )


def test_negative_tokens_rejected():
    with pytest.raises(ValueError):
        llm_cost_usd(-1, 0, PRICE)


@pytest.mark.parametrize(
    ("inp", "out", "fx"),
    [(-0.1, 0.1, 5.0), (0.1, -0.1, 5.0), (0.1, 0.1, 0.0)],
)
def test_invalid_price_rejected(inp, out, fx):
    with pytest.raises(ConfigurationError):
        LLMPrice(input_usd_per_mtok=inp, output_usd_per_mtok=out, usd_brl=fx)


def test_from_settings_requires_usd_brl(monkeypatch):
    monkeypatch.delenv("USD_BRL", raising=False)
    with pytest.raises(ConfigurationError):
        LLMPrice.from_settings(Settings(_env_file=None))


def test_from_settings_reads_prices_and_quote_date(monkeypatch):
    monkeypatch.setenv("USD_BRL", "5.5")
    monkeypatch.setenv("LLM_PRICE_INPUT_USD_PER_MTOK", "0.1")
    monkeypatch.setenv("LLM_PRICE_OUTPUT_USD_PER_MTOK", "0.4")
    monkeypatch.setenv("LLM_PRICE_QUOTE_DATE", "2026-10-31")
    price = LLMPrice.from_settings(Settings(_env_file=None))
    assert price.usd_brl == 5.5
    assert price.quote_date == date(2026, 10, 31)
