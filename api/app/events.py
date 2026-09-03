"""Event emission: business actions write product_events.

This is the *instrumentation* layer. Business actions (signup, create project,
complete task, ...) call these functions, which write the corresponding
product_events rows. Events are never created disconnected from a business
action - this module is the only place product_events are inserted.
"""
from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from .models import ProductEvent


def emit(
    session: Session,
    *,
    event_name: str,
    account_id: str,
    user_id: str,
    event_at: datetime | None = None,
    properties: dict | None = None,
    event_id: str | None = None,
) -> ProductEvent:
    """Insert a single product event (business action -> event).

    `event_id` is the stable dedup key; it defaults to a generated id unless
    the caller supplies one (the simulation supplies deterministic ids).
    """
    event = ProductEvent(
        event_id=event_id or f"evt_{uuid.uuid4().hex}",
        event_name=event_name,
        distinct_id=user_id,
        account_id=account_id,
        event_at=event_at or datetime.utcnow(),
        properties=properties or {},
    )
    session.add(event)
    return event


def signup(session: Session, *, user_id: str, account_id: str, email: str, country: str, channel: str, event_at: datetime | None = None, event_id: str | None = None) -> ProductEvent:
    return emit(
        session,
        event_name="user_signup",
        account_id=account_id,
        user_id=user_id,
        event_at=event_at,
        properties={"email": email, "country": country, "channel": channel},
        event_id=event_id,
    )


def account_created(session: Session, *, user_id: str, account_id: str, name: str, country: str, channel: str, plan: str, event_at: datetime | None = None, event_id: str | None = None) -> ProductEvent:
    return emit(
        session,
        event_name="account_created",
        account_id=account_id,
        user_id=user_id,
        event_at=event_at,
        properties={"account_name": name, "country": country, "channel": channel, "initial_plan": plan},
        event_id=event_id,
    )


def workspace_created(session: Session, *, user_id: str, account_id: str, workspace_id: str, name: str, event_at: datetime | None = None, event_id: str | None = None) -> ProductEvent:
    return emit(
        session,
        event_name="workspace_created",
        account_id=account_id,
        user_id=user_id,
        event_at=event_at,
        properties={"workspace_id": workspace_id, "workspace_name": name},
        event_id=event_id,
    )


def project_created(session: Session, *, user_id: str, account_id: str, workspace_id: str, project_id: str, name: str, event_at: datetime | None = None, event_id: str | None = None) -> ProductEvent:
    return emit(
        session,
        event_name="project_created",
        account_id=account_id,
        user_id=user_id,
        event_at=event_at,
        properties={"workspace_id": workspace_id, "project_id": project_id, "project_name": name},
        event_id=event_id,
    )


def membership_invited(session: Session, *, user_id: str, account_id: str, invitee_email: str, role: str, event_at: datetime | None = None, event_id: str | None = None) -> ProductEvent:
    return emit(
        session,
        event_name="membership_invited",
        account_id=account_id,
        user_id=user_id,
        event_at=event_at,
        properties={"invitee_email": invitee_email, "role": role},
        event_id=event_id,
    )


def task_created(session: Session, *, user_id: str, account_id: str, workspace_id: str, project_id: str, task_id: str, event_at: datetime | None = None, event_id: str | None = None) -> ProductEvent:
    return emit(
        session,
        event_name="task_created",
        account_id=account_id,
        user_id=user_id,
        event_at=event_at,
        properties={"workspace_id": workspace_id, "project_id": project_id, "task_id": task_id},
        event_id=event_id,
    )


def task_assigned(session: Session, *, user_id: str, account_id: str, task_id: str, assignee_id: str, event_at: datetime | None = None, event_id: str | None = None) -> ProductEvent:
    return emit(
        session,
        event_name="task_assigned",
        account_id=account_id,
        user_id=user_id,
        event_at=event_at,
        properties={"task_id": task_id, "assignee_id": assignee_id},
        event_id=event_id,
    )


def task_commented(session: Session, *, user_id: str, account_id: str, task_id: str, comment_length: int, event_at: datetime | None = None, event_id: str | None = None) -> ProductEvent:
    return emit(
        session,
        event_name="task_commented",
        account_id=account_id,
        user_id=user_id,
        event_at=event_at,
        properties={"task_id": task_id, "comment_length": comment_length},
        event_id=event_id,
    )


def task_completed(session: Session, *, user_id: str, account_id: str, task_id: str, project_id: str, hours_to_complete: int, event_at: datetime | None = None, event_id: str | None = None) -> ProductEvent:
    return emit(
        session,
        event_name="task_completed",
        account_id=account_id,
        user_id=user_id,
        event_at=event_at,
        properties={"task_id": task_id, "project_id": project_id, "hours_to_complete": hours_to_complete},
        event_id=event_id,
    )


def integration_connected(session: Session, *, user_id: str, account_id: str, integration_type: str, event_at: datetime | None = None, event_id: str | None = None) -> ProductEvent:
    return emit(
        session,
        event_name="integration_connected",
        account_id=account_id,
        user_id=user_id,
        event_at=event_at,
        properties={"integration_type": integration_type},
        event_id=event_id,
    )


def plan_changed(session: Session, *, user_id: str, account_id: str, from_plan: str, to_plan: str, event_at: datetime | None = None, event_id: str | None = None) -> ProductEvent:
    return emit(
        session,
        event_name="plan_changed",
        account_id=account_id,
        user_id=user_id,
        event_at=event_at,
        properties={"from_plan": from_plan, "to_plan": to_plan},
        event_id=event_id,
    )
