from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditLog

def log_audit_event(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    actor_reference: Optional[str] = None,
    request_reference: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Persists an append-only audit trail record to registry.audit_log.
    """
    audit_entry = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_reference=actor_reference or "system",
        request_reference=request_reference,
        details=details or {}
    )
    db.add(audit_entry)
    db.commit()
    return audit_entry
