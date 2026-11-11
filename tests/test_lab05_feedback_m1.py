"""Lab 5 M1: SQLModel feedback repository regression tests (Issue #31).

The tests use isolated SQLite databases; they do not require the HTTP API or network.
FastAPI wiring belongs to M3, and is verified after team integration.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import inspect
from sqlmodel import Session, select

from assistant_api.db import ChatSession, Feedback, Interaction, Repository, hash_session, init_db, make_engine


@pytest.fixture
def feedback_repo():
    engine = make_engine("sqlite://")
    init_db(engine)
    return Repository(engine, "only-for-tests"), engine


def record(repo, request_id, raw_session="test-session"):
    repo.record_interaction(
        raw_session=raw_session,
        request_id=request_id,
        intent="fee",
        topic=None,
        resolved=True,
        degraded=False,
        latency_ms=12.5,
    )


def test_r1_unknown_request_id_returns_none_and_does_not_save(feedback_repo):
    repo, engine = feedback_repo
    assert repo.add_feedback("no-matching-interaction", 1, "unknown answer") is None
    assert repo.list_feedback() == []

    with Session(engine) as db:
        assert db.exec(select(Feedback)).all() == []
        assert db.exec(select(Interaction)).all() == []


@pytest.mark.parametrize("rating", [-1, 0, 1])
def test_r1_saves_all_valid_ratings_with_database_id_and_fields(feedback_repo, rating):
    repo, engine = feedback_repo
    record(repo, "response-001")
    saved = repo.add_feedback("response-001", rating, "helpful feedback")

    assert saved is not None
    assert isinstance(saved.id, int) and saved.id > 0
    assert saved.request_id == "response-001"
    assert saved.rating == rating
    assert saved.comment == "helpful feedback"
    assert isinstance(saved.created_at, datetime)

    with Session(engine) as db:
        stored = db.get(Feedback, saved.id)
        assert stored is not None
        assert (stored.request_id, stored.rating, stored.comment) == (
            "response-001",
            rating,
            "helpful feedback",
        )


def test_r1_optional_comment_and_sequential_ids(feedback_repo):
    repo, _ = feedback_repo
    record(repo, "answer-a")
    record(repo, "answer-b")

    first = repo.add_feedback("answer-a", 1, None)
    second = repo.add_feedback("answer-b", -1, "needs correction")

    assert first is not None and second is not None
    assert first.id == 1
    assert second.id == 2
    assert first.comment is None
    assert len(repo.list_feedback()) == 2


def test_r2_orders_by_created_at_desc_and_respects_limit(feedback_repo):
    repo, engine = feedback_repo
    for request_id in ("old", "new", "middle"):
        record(repo, request_id)
        assert repo.add_feedback(request_id, 0, None) is not None

    # Fix timestamps explicitly: the test must not depend on wall-clock timing.
    now = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)
    created = {
        "old": now - timedelta(days=2),
        "middle": now - timedelta(days=1),
        "new": now,
    }
    with Session(engine) as db:
        for fb in db.exec(select(Feedback)).all():
            fb.created_at = created[fb.request_id]
            db.add(fb)
        db.commit()

    assert [item.request_id for item in repo.list_feedback()] == ["new", "middle", "old"]
    assert [item.request_id for item in repo.list_feedback(limit=2)] == ["new", "middle"]
    assert repo.list_feedback(limit=0) == []
    assert len(repo.list_feedback(limit=100)) == 3


def test_r2_default_limit_is_100(feedback_repo):
    repo, _ = feedback_repo
    record(repo, "answer-01")
    for _ in range(105):
        assert repo.add_feedback("answer-01", 1, None) is not None

    assert len(repo.list_feedback()) == 100
    assert len(repo.list_feedback(limit=200)) == 105


def test_r1_feedback_survives_reopening_file_backed_sqlite(tmp_path):
    db_path = tmp_path / "m1_feedback.db"
    url = f"sqlite:///{db_path}"

    original_engine = make_engine(url)
    init_db(original_engine)
    first = Repository(original_engine, "test-private-salt")
    record(first, "persisted-request", raw_session="private-session-name")
    saved = first.add_feedback("persisted-request", -1, "needs more detail")

    assert saved is not None
    assert db_path.exists()
    original_engine.dispose()  # Close the first engine, like restarting the process.

    reopened_engine = make_engine(url)
    second = Repository(reopened_engine, "test-private-salt")
    results = second.list_feedback()
    assert len(results) == 1
    assert (results[0].id, results[0].request_id, results[0].rating, results[0].comment) == (
        saved.id,
        "persisted-request",
        -1,
        "needs more detail",
    )
    reopened_engine.dispose()


def test_r1_does_not_store_raw_session_or_message(feedback_repo):
    repo, engine = feedback_repo
    raw_session = "student-private-session-value"
    record(repo, "request-privacy", raw_session=raw_session)
    assert repo.add_feedback("request-privacy", 1, None) is not None

    with Session(engine) as db:
        session = db.exec(select(ChatSession)).one()
        interaction = db.exec(select(Interaction)).one()
        assert session.id == hash_session(raw_session, "only-for-tests")
        assert session.id != raw_session
        assert interaction.session_id == session.id
        # The starter schema is metadata-only and must not gain raw text fields.
        interaction_columns = {column["name"] for column in inspect(engine).get_columns("interaction")}
        assert "message" not in interaction_columns
        assert "question" not in interaction_columns
        assert "raw_session" not in interaction_columns
