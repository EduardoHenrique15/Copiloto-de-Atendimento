"""Decisão do atendente sobre um rascunho."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from copiloto.db.models import Draft, Feedback
from copiloto.services.errors import ConflictError, NotFoundError

STATUS_BY_DECISION = {"approved": "aprovado", "edited": "editado", "rejected": "recusado"}


def record_feedback(
    session: Session, draft_id: str, decision: str, final_text: str | None, reviewer: str
) -> Feedback:
    draft = session.get(Draft, draft_id)
    if draft is None:
        raise NotFoundError(f"Rascunho {draft_id} não encontrado.")
    if session.scalar(select(Feedback).where(Feedback.draft_id == draft_id)) is not None:
        raise ConflictError("Este rascunho já recebeu uma decisão.")
    if decision == "edited" and not (final_text or "").strip():
        raise ConflictError("Decisão 'edited' exige o texto final.")
    text = (
        final_text if decision == "edited" else (draft.response if decision == "approved" else None)
    )
    feedback = Feedback(draft_id=draft_id, decision=decision, final_text=text, reviewer=reviewer)
    draft.status = STATUS_BY_DECISION[decision]
    session.add(feedback)
    session.commit()
    return feedback
