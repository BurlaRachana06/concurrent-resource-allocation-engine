import threading

from app.allocator import AllocationEngine
from app.models import Resource, ResourceType


def test_no_double_booking_under_concurrency():
    engine = AllocationEngine()

    engine.add_resource(
        Resource(
            resource_id="ICU-01",
            resource_type=ResourceType.ICU_BED,
        )
    )

    results = []
    results_lock = threading.Lock()

    def allocate_resource(index):
        result = engine.allocate(
            f"REQ-{index}",
            ["ICU-01"],
        )

        with results_lock:
            results.append(result)

    threads = []

    # Create 100 competing requests
    for index in range(100):
        thread = threading.Thread(
            target=allocate_resource,
            args=(index,),
        )

        threads.append(thread)

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    successful_allocations = [
        result
        for result in results
        if result["status"] == "ALLOCATED"
    ]

    # Only ONE request can receive ICU-01.
    assert len(successful_allocations) == 1