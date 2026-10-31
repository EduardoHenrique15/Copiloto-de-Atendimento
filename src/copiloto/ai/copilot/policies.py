"""Leitura das políticas fictícias e divisão em trechos indexáveis."""

import re
from dataclasses import dataclass
from pathlib import Path

ACTIONS = ("nenhuma", "cupom", "troca", "reembolso", "escalar")
META_RE = re.compile(r"<!--\s*id:\s*([\w-]+)\s*\|\s*acoes:\s*([^>]*?)\s*-->")
FICTION_NOTICE = "Política fictícia criada para este projeto"


@dataclass(frozen=True)
class PolicyChunk:
    id: str  # "<política>#<seção>"
    policy_id: str
    policy_title: str
    section: str
    text: str
    actions: tuple[str, ...]


def _slug(text: str) -> str:
    text = text.lower()
    for a, b in zip("áàâãéêíóôõúüç", "aaaaeeiooouuc", strict=True):
        text = text.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def parse_policy(markdown: str) -> list[PolicyChunk]:
    """Um trecho por seção `##`. Falha se faltar o aviso de ficção ou os metadados."""
    if FICTION_NOTICE not in markdown:
        raise ValueError("Toda política precisa do aviso de que é fictícia.")
    meta = META_RE.search(markdown)
    if not meta:
        raise ValueError("Política sem o comentário de metadados (id e ações).")
    policy_id = meta.group(1)
    actions = tuple(a.strip() for a in meta.group(2).split(",") if a.strip())
    unknown = set(actions) - set(ACTIONS)
    if unknown:
        raise ValueError(f"Ações desconhecidas em {policy_id}: {sorted(unknown)}")
    title = re.search(r"^# (.+)$", markdown, re.MULTILINE).group(1).strip()
    chunks = []
    for block in re.split(r"^## ", markdown, flags=re.MULTILINE)[1:]:
        section, _, body = block.partition("\n")
        chunks.append(
            PolicyChunk(
                id=f"{policy_id}#{_slug(section)}",
                policy_id=policy_id,
                policy_title=title,
                section=section.strip(),
                text=" ".join(body.split()),
                actions=actions,
            )
        )
    return chunks


def load_policies(directory: Path) -> list[PolicyChunk]:
    """Todos os trechos de `policies/*.md` (o README é ignorado)."""
    chunks = []
    for path in sorted(directory.glob("*.md")):
        if path.name.lower() != "readme.md":
            chunks += parse_policy(path.read_text(encoding="utf-8"))
    ids = [c.id for c in chunks]
    if len(ids) != len(set(ids)):
        raise ValueError("Ids de trechos repetidos nas políticas.")
    return chunks
