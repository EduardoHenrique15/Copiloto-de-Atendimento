"""Taxonomia das reclamações (ADR 0007) e regra de urgência."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    key: str
    number: int
    name: str
    description: str


CATEGORIES: tuple[Category, ...] = (
    Category(
        "atraso_entrega",
        1,
        "Atraso na entrega",
        "O produto chegou, mas depois do prazo, ou o cliente reclama da demora ou do prazo longo.",
    ),
    Category(
        "nao_recebido",
        2,
        "Não recebido",
        "O cliente diz que ainda não recebeu o produto, mesmo que o status diga entregue.",
    ),
    Category(
        "produto_errado_ou_incompleto",
        3,
        "Produto errado ou incompleto",
        "Chegou outro item, outra cor ou tamanho que não o pedido, ou faltou item do pedido.",
    ),
    Category(
        "produto_defeituoso_ou_qualidade",
        4,
        "Defeito, avaria ou qualidade",
        "O produto pedido chegou quebrado, com defeito, avariado no transporte ou de má qualidade.",
    ),
    Category(
        "diferente_do_anuncio",
        5,
        "Diferente do anúncio",
        "Chegou o item pedido, mas ele não corresponde ao anúncio "
        "(medidas, material, foto, original).",
    ),
    Category(
        "atendimento_vendedor",
        6,
        "Atendimento",
        "A reclamação é só sobre o atendimento: falta de resposta, descaso, demora para resolver.",
    ),
    Category(
        "cancelamento_ou_cobranca",
        7,
        "Cancelamento ou cobrança",
        "Pedido cancelado, falta de estoque, estorno não feito, cobrança indevida ou pedido para "
        "cancelar.",
    ),
    Category(
        "outro",
        8,
        "Outro",
        "Reclamação que não se encaixa nas anteriores (frete caro, instalação, texto vago).",
    ),
    Category(
        "sem_problema",
        9,
        "Sem problema",
        "O comentário não relata problema (elogio ou comentário neutro).",
    ),
)

CATEGORY_KEYS: tuple[str, ...] = tuple(c.key for c in CATEGORIES)
BY_KEY = {c.key: c for c in CATEGORIES}
BY_NUMBER = {c.number: c for c in CATEGORIES}

ESCALATION_TERMS = ("procon", "reclame aqui", "juizado", "advogado", "processo", "justiça")


def urgency(category: str, text: str, delay_days: float | None, order_status: str | None) -> str:
    """Urgência por regra documentada (guia de rótulos, seção "Urgência").

    alta: ameaça de escalar (Procon, justiça), não recebido com status "entregue",
        não recebido com mais de 10 dias de atraso, ou cobrança/cancelamento.
    media: demais problemas de entrega ou de produto.
    baixa: atendimento isolado, outro e sem problema.
    """
    lowered = text.lower()
    if any(term in lowered for term in ESCALATION_TERMS):
        return "alta"
    if category == "nao_recebido":
        if order_status == "delivered" or (delay_days is not None and delay_days > 10):
            return "alta"
        return "media"
    if category == "cancelamento_ou_cobranca":
        return "alta"
    if category in {
        "atraso_entrega",
        "produto_errado_ou_incompleto",
        "produto_defeituoso_ou_qualidade",
        "diferente_do_anuncio",
    }:
        return "media"
    return "baixa"
