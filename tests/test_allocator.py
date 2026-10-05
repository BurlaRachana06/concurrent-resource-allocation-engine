from app.allocator import AllocationEngine
from app.models import Resource, ResourceType


def create_engine():
    engine = AllocationEngine()

    engine.add_resource(
        Resource(
            resource_id="ICU-01",
            resource_type=ResourceType.ICU_BED,
        )
    )

    engine.add_resource(
        Resource(
            resource_id="VENT-01",
            resource_type=ResourceType.EQUIPMENT,
        )
    )

    return engine


def test_single_resource_allocation():
    engine = create_engine()

    result = engine.allocate(
        "REQ-001",
        ["ICU-01"],
    )

    assert result["status"] == "ALLOCATED"
    assert "ICU-01" in result["allocated_resources"]


def test_cannot_double_book_resource():
    engine = create_engine()

    first = engine.allocate(
        "REQ-001",
        ["ICU-01"],
    )

    second = engine.allocate(
        "REQ-002",
        ["ICU-01"],
    )

    assert first["status"] == "ALLOCATED"
    assert second["status"] == "UNAVAILABLE"


def test_atomic_multi_resource_allocation():
    engine = create_engine()

    result = engine.allocate(
        "REQ-003",
        ["ICU-01", "VENT-01"],
    )

    assert result["status"] == "ALLOCATED"

    assert set(result["allocated_resources"]) == {
        "ICU-01",
        "VENT-01",
    }


def test_atomic_allocation_fails_if_one_resource_unavailable():
    engine = create_engine()

    engine.allocate(
        "REQ-001",
        ["VENT-01"],
    )

    result = engine.allocate(
        "REQ-002",
        ["ICU-01", "VENT-01"],
    )

    assert result["status"] == "UNAVAILABLE"

    resources = {
        resource.resource_id: resource
        for resource in engine.get_resources()
    }

    assert resources["ICU-01"].available is True


def test_release_resource():
    engine = create_engine()

    engine.allocate(
        "REQ-001",
        ["ICU-01"],
    )

    engine.release(["ICU-01"])

    result = engine.allocate(
        "REQ-002",
        ["ICU-01"],
    )

    assert result["status"] == "ALLOCATED"


def test_rejects_duplicate_resource_ids():
    engine = create_engine()

    result = engine.allocate(
        "REQ-DUPLICATE",
        ["ICU-01", "ICU-01"],
    )

    assert result["status"] == "FAILED"
    assert result["allocated_resources"] == []
    assert result["message"] == "Duplicate resource IDs are not allowed"

    resources = {
        resource.resource_id: resource
        for resource in engine.get_resources()
    }

    assert resources["ICU-01"].available is True


def test_same_request_id_does_not_allocate_twice():
    engine = create_engine()

    first = engine.allocate(
        "REQ-IDEMPOTENT",
        ["ICU-01"],
    )

    second = engine.allocate(
        "REQ-IDEMPOTENT",
        ["ICU-01"],
    )

    assert first["status"] == "ALLOCATED"
    assert first["allocated_resources"] == ["ICU-01"]

    assert second["status"] == "ALLOCATED"
    assert second["allocated_resources"] == ["ICU-01"]

    assert (
        second["message"]
        == "Request already processed. "
        "Returning previous allocation result."
    )
def test_get_resources_does_not_expose_internal_state():
    engine = create_engine()

    resources = engine.get_resources()

    resources_by_id = {
        resource.resource_id: resource
        for resource in resources
    }

    resources_by_id["ICU-01"].available = False

    actual_resources = {
        resource.resource_id: resource
        for resource in engine.get_resources()
    }

    assert actual_resources["ICU-01"].available is True