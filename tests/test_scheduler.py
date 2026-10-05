import threading

from app.allocator import AllocationEngine
from app.models import AllocationRequest, Resource, ResourceType, Priority
from app.scheduler import PriorityScheduler


def create_scheduler():
    engine = AllocationEngine()

    engine.add_resource(
        Resource(
            resource_id="ICU-01",
            resource_type=ResourceType.ICU_BED,
        )
    )

    engine.add_resource(
        Resource(
            resource_id="ICU-02",
            resource_type=ResourceType.ICU_BED,
        )
    )

    return PriorityScheduler(engine)


def test_emergency_processed_before_normal():
    scheduler = create_scheduler()

    normal_request = AllocationRequest(
        request_id="REQ-NORMAL",
        patient_id="PATIENT-N",
        priority=Priority.NORMAL,
        resource_ids=["ICU-01"],
    )

    emergency_request = AllocationRequest(
        request_id="REQ-EMERGENCY",
        patient_id="PATIENT-E",
        priority=Priority.EMERGENCY,
        resource_ids=["ICU-02"],
    )

    scheduler.submit(normal_request)
    scheduler.submit(emergency_request)

    result = scheduler.process_next()

    assert result["request_id"] == "REQ-EMERGENCY"
    assert result["priority"] == "EMERGENCY"
    assert result["status"] == "ALLOCATED"


def test_urgent_processed_before_normal():
    scheduler = create_scheduler()

    normal_request = AllocationRequest(
        request_id="REQ-NORMAL",
        patient_id="PATIENT-N",
        priority=Priority.NORMAL,
        resource_ids=["ICU-01"],
    )

    urgent_request = AllocationRequest(
        request_id="REQ-URGENT",
        patient_id="PATIENT-U",
        priority=Priority.URGENT,
        resource_ids=["ICU-02"],
    )

    scheduler.submit(normal_request)
    scheduler.submit(urgent_request)

    result = scheduler.process_next()

    assert result["request_id"] == "REQ-URGENT"
    assert result["priority"] == "URGENT"
    assert result["status"] == "ALLOCATED"


def test_same_priority_is_fifo():
    scheduler = create_scheduler()

    first_request = AllocationRequest(
        request_id="REQ-FIRST",
        patient_id="PATIENT-1",
        priority=Priority.NORMAL,
        resource_ids=["ICU-01"],
    )

    second_request = AllocationRequest(
        request_id="REQ-SECOND",
        patient_id="PATIENT-2",
        priority=Priority.NORMAL,
        resource_ids=["ICU-02"],
    )

    scheduler.submit(first_request)
    scheduler.submit(second_request)

    first_result = scheduler.process_next()
    second_result = scheduler.process_next()

    assert first_result["request_id"] == "REQ-FIRST"
    assert second_result["request_id"] == "REQ-SECOND"


def test_unavailable_request_returns_to_queue():
    scheduler = create_scheduler()

    first_request = AllocationRequest(
        request_id="REQ-FIRST",
        patient_id="PATIENT-1",
        priority=Priority.NORMAL,
        resource_ids=["ICU-01"],
    )

    blocked_request = AllocationRequest(
        request_id="REQ-BLOCKED",
        patient_id="PATIENT-2",
        priority=Priority.EMERGENCY,
        resource_ids=["ICU-01"],
    )

    scheduler.submit(first_request)
    scheduler.process_next()

    scheduler.submit(blocked_request)

    result = scheduler.process_next()

    assert result["request_id"] == "REQ-BLOCKED"
    assert result["status"] == "WAITING"
    assert scheduler.queue_size() == 1


def test_queue_size():
    scheduler = create_scheduler()

    request = AllocationRequest(
        request_id="REQ-001",
        patient_id="PATIENT-1",
        priority=Priority.NORMAL,
        resource_ids=["ICU-01"],
    )

    scheduler.submit(request)

    assert scheduler.queue_size() == 1


def test_scheduler_no_double_booking_under_concurrency():
    scheduler = create_scheduler()

    results = []
    results_lock = threading.Lock()

    def submit_and_process(index):
        request = AllocationRequest(
            request_id=f"REQ-CONCURRENT-{index}",
            patient_id=f"PATIENT-{index}",
            priority=Priority.NORMAL,
            resource_ids=["ICU-01"],
        )

        scheduler.submit(request)

        result = scheduler.process_next()

        with results_lock:
            results.append(result)

    threads = []

    for index in range(20):
        thread = threading.Thread(
            target=submit_and_process,
            args=(index,),
        )

        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    successful_allocations = [
        result
        for result in results
        if result["status"] == "ALLOCATED"
    ]

    waiting_requests = [
        result
        for result in results
        if result["status"] == "WAITING"
    ]

    assert len(successful_allocations) == 1
    assert len(waiting_requests) == 19

    assert successful_allocations[0]["allocated_resources"] == [
        "ICU-01"
    ]

    assert scheduler.queue_size() == 19