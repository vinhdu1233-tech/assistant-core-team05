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
    repo, engine = feedback_repo
    record(repo, "answer-01")
    for _ in range(105):
        assert repo.add_feedback("answer-01", 1, None) is not None

    # Set known, strictly increasing times; a LENGTH-only check could pass
    # even if LIMIT returned the oldest 100 instead of the newest 100.
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with Session(engine) as db:
        feedback = db.exec(select(Feedback)).all()
        for item in feedback:
            item.created_at = start + timedelta(seconds=item.id)
            db.add(item)
        db.commit()

    assert [item.id for item in repo.list_feedback()] == list(range(105, 5, -1))
    assert [item.id for item in repo.list_feedback(limit=1)] == [105]
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

def test_r1_missing_id_never_matches_another_interaction(feedback_repo):
    repo, engine = feedback_repo
    record(repo, "known-request-1")
    record(repo, "known-request-2")

    # Exact matching matters: even an SQL-looking request ID is only data.
    for unknown in ("known-request", "not-an-id", "' OR 1=1 --"):
        assert repo.add_feedback(unknown, 1, "should not be saved") is None

    assert repo.list_feedback() == []
    with Session(engine) as db:
        assert len(db.exec(select(Interaction)).all()) == 2
        assert db.exec(select(Feedback)).all() == []

    saved = repo.add_feedback("known-request-2", 1, "valid")
    assert saved is not None
    assert saved.id == 1  # rejected attempts did not consume an ID


def test_r1_does_not_change_existing_feedback_on_unknown_id(feedback_repo):
    repo, engine = feedback_repo
    record(repo, "existing-1")
    record(repo, "existing-2")
    original = repo.add_feedback("existing-1", 1, "keep this feedback")
    assert original is not None

    assert repo.add_feedback("invalid", -1, "discard this feedback") is None
    next_item = repo.add_feedback("existing-2", 0, None)
    assert next_item is not None
    assert next_item.id == original.id + 1

    with Session(engine) as db:
        items = db.exec(select(Feedback).order_by(Feedback.id)).all()
        assert [(item.request_id, item.rating, item.comment) for item in items] == [
            ("existing-1", 1, "keep this feedback"),
            ("existing-2", 0, None),
        ]


def test_r1_links_feedback_to_the_correct_interaction(feedback_repo):
    repo, engine = feedback_repo
    record(repo, "request-a", raw_session="session-a")
    record(repo, "request-b", raw_session="session-b")

    saved = repo.add_feedback("request-b", -1, "incorrect answer")
    assert saved is not None
    with Session(engine) as db:
        item = db.exec(select(Feedback)).one()
        assert item.request_id == "request-b"
        assert item.interaction is not None
        assert item.interaction.request_id == "request-b"
        assert item.interaction.session_id == hash_session("session-b", "only-for-tests")
        assert len(db.exec(select(Interaction)).all()) == 2


def test_r1_two_feedback_entries_for_same_answer_are_distinct(feedback_repo):
    repo, engine = feedback_repo
    record(repo, "answer-with-two-ratings")

    first = repo.add_feedback("answer-with-two-ratings", 1, None)
    second = repo.add_feedback("answer-with-two-ratings", -1, "needs revision")
    assert first is not None and second is not None
    assert first.id != second.id

    with Session(engine) as db:
        rows = db.exec(select(Feedback).order_by(Feedback.id)).all()
        assert len(rows) == 2
        assert [row.rating for row in rows] == [1, -1]
        assert {row.request_id for row in rows} == {"answer-with-two-ratings"}


def test_r1_persists_unicode_quotes_and_maximum_comment_length(feedback_repo):
    repo, engine = feedback_repo
    request_id = "r" * 32
    comment = "Ổn ✅ It's clear; ' OR 1=1 -- " + "x" * (500 - len("Ổn ✅ It's clear; ' OR 1=1 -- "))
    assert len(comment) == 500
    record(repo, request_id)

    saved = repo.add_feedback(request_id, 0, comment)
    assert saved is not None
    assert saved.comment == comment

    with Session(engine) as db:
        stored = db.exec(select(Feedback)).one()
        assert stored.request_id == request_id
        assert stored.comment == comment


def test_r1_feedback_timestamp_is_created_near_the_insert_time(feedback_repo):
    repo, engine = feedback_repo
    record(repo, "timestamp-check")

    before = datetime.now(timezone.utc) - timedelta(seconds=2)
    saved = repo.add_feedback("timestamp-check", 1, None)
    after = datetime.now(timezone.utc) + timedelta(seconds=2)
    assert saved is not None

    # SQLite may deserialize timezone-aware timestamps as naive datetimes.
    # The supplied utcnow() factory nevertheless creates UTC values.
    stored_time = saved.created_at
    if stored_time.tzinfo is None:
        stored_time = stored_time.replace(tzinfo=timezone.utc)
    assert before <= stored_time <= after

    with Session(engine) as db:
        persisted = db.exec(select(Feedback)).one()
        assert persisted.created_at == saved.created_at


def test_r2_empty_result_and_read_after_write(feedback_repo):
    repo, _ = feedback_repo
    assert repo.list_feedback() == []
    assert repo.list_feedback(limit=0) == []
    assert repo.list_feedback(limit=15) == []

    record(repo, "first-request")
    assert repo.add_feedback("first-request", 1, None) is not None
    assert len(repo.list_feedback()) == 1

    record(repo, "second-request")
    assert repo.add_feedback("second-request", -1, None) is not None
    results = repo.list_feedback(limit=10)
    assert len(results) == 2
    assert all(isinstance(item, Feedback) for item in results)

@pytest.mark.parametrize("invalid_limit", [-1, -10])
def test_r2_rejects_negative_limits_without_exposing_all_rows(feedback_repo, invalid_limit):
    repo, _ = feedback_repo
    record(repo, "bounded-result")
    assert repo.add_feedback("bounded-result", 1, None) is not None

    with pytest.raises(ValueError, match="limit must be non-negative"):
        repo.list_feedback(limit=invalid_limit)
    assert len(repo.list_feedback(limit=1)) == 1


def test_r1_failed_commit_does_not_leave_partial_feedback(feedback_repo, monkeypatch):
    repo, engine = feedback_repo
    record(repo, "commit-failure")
    with Session(engine) as db:
        assert len(db.exec(select(Interaction)).all()) == 1

    def fail_commit(_session):
        raise RuntimeError("simulated storage failure")

    with monkeypatch.context() as patch:
        patch.setattr(Session, "commit", fail_commit)
        with pytest.raises(RuntimeError, match="simulated storage failure"):
            repo.add_feedback("commit-failure", 1, "do not save")

    # The repository uses a session context, so an exception must not
    # accidentally commit a partially created feedback row.
    with Session(engine) as db:
        assert db.exec(select(Feedback)).all() == []
        assert len(db.exec(select(Interaction)).all()) == 1
