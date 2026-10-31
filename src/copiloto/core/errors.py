"""Hierarquia de erros do projeto."""


class CopilotoError(Exception):
    """Erro base do projeto. Toda exceção própria herda desta."""


class ConfigurationError(CopilotoError):
    """Configuração ausente ou inválida."""


class ExternalServiceError(CopilotoError):
    """Falha ao chamar um serviço externo (LLM, banco, embeddings)."""
