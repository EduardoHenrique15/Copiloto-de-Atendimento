"""Cálculo de custo das chamadas ao LLM em reais."""

from dataclasses import dataclass
from datetime import date

from copiloto.core.config import Settings
from copiloto.core.errors import ConfigurationError

TOKENS_PER_MILLION = 1_000_000


@dataclass(frozen=True)
class LLMPrice:
    """Preço do provedor por milhão de tokens, com a data da cotação."""

    input_usd_per_mtok: float
    output_usd_per_mtok: float
    usd_brl: float
    quote_date: date | None = None

    def __post_init__(self) -> None:
        if self.input_usd_per_mtok < 0 or self.output_usd_per_mtok < 0:
            raise ConfigurationError("Preço por token não pode ser negativo.")
        if self.usd_brl <= 0:
            raise ConfigurationError("Cotação do dólar precisa ser positiva.")

    @classmethod
    def from_settings(cls, settings: Settings) -> "LLMPrice":
        """Monta o preço a partir da configuração. Exige `USD_BRL` preenchido."""
        if settings.usd_brl is None:
            raise ConfigurationError("Defina USD_BRL para calcular custos em reais.")
        return cls(
            input_usd_per_mtok=settings.llm_price_input_usd_per_mtok,
            output_usd_per_mtok=settings.llm_price_output_usd_per_mtok,
            usd_brl=settings.usd_brl,
            quote_date=settings.llm_price_quote_date,
        )


def llm_cost_usd(input_tokens: int, output_tokens: int, price: LLMPrice) -> float:
    """Custo em dólares de uma chamada."""
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("Contagem de tokens não pode ser negativa.")
    return (
        input_tokens * price.input_usd_per_mtok + output_tokens * price.output_usd_per_mtok
    ) / TOKENS_PER_MILLION


def llm_cost_brl(input_tokens: int, output_tokens: int, price: LLMPrice) -> float:
    """Custo em reais de uma chamada."""
    return llm_cost_usd(input_tokens, output_tokens, price) * price.usd_brl


def cost_per_thousand_brl(
    avg_input_tokens: float, avg_output_tokens: float, price: LLMPrice
) -> float:
    """Custo estimado em reais para 1.000 chamadas com o tamanho médio informado."""
    per_call = (
        avg_input_tokens * price.input_usd_per_mtok + avg_output_tokens * price.output_usd_per_mtok
    ) / TOKENS_PER_MILLION
    return per_call * price.usd_brl * 1000
