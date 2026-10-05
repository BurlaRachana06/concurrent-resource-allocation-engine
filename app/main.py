from fastapi import FastAPI

from app.models import (
    AllocationRequest,
    Resource,
    ResourceType,
)

from app.allocator import AllocationEngine
from app.scheduler import PriorityScheduler


app = FastAPI(
    title="Concurrent Bed/Resource Allocation Engine",
    description=(
        "Thread-safe scheduler for allocating ICU beds, "
        "OR slots, and equipment across competing requests. "
        "Supports priority scheduling, atomic allocation, "
        "deadlock avoidance, and no double-booking."
    ),
    version="1.0.0",
)


engine = AllocationEngine()
scheduler = PriorityScheduler(engine)


# ---------------------------------------------------------
# Initial Resources
# ---------------------------------------------------------

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

engine.add_resource(
    Resource(
        resource_id="OR-01",
        resource_type=ResourceType.OR_SLOT,
    )
)

engine.add_resource(
    Resource(
        resource_id="VENT-01",
        resource_type=ResourceType.EQUIPMENT,
    )
)

engine.add_resource(
    Resource(
        resource_id="MONITOR-01",
        resource_type=ResourceType.EQUIPMENT,
    )
)


# ---------------------------------------------------------
# Basic APIs
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "service": "Concurrent Bed/Resource Allocation Engine",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/resources")
def resources():
    return engine.get_resources()


# ---------------------------------------------------------
# Direct Allocation APIs
# ---------------------------------------------------------

@app.post("/allocate")
def allocate(request: AllocationRequest):
    return engine.allocate(
        request.request_id,
        request.resource_ids,
    )


@app.post("/release")
def release(request: AllocationRequest):
    return engine.release(
        request.resource_ids
    )


# ---------------------------------------------------------
# Priority Scheduler APIs
# ---------------------------------------------------------

@app.post("/schedule")
def schedule(request: AllocationRequest):
    return scheduler.submit(request)


@app.post("/schedule/process")
def process_schedule():
    return scheduler.process_next()


@app.get("/schedule/queue")
def queue_status():
    return {
        "queued_requests": scheduler.queue_size()
    }


@app.delete("/schedule/queue")
def clear_queue():
    scheduler.clear()

    return {
        "status": "CLEARED",
        "message": "Scheduler queue cleared",
    }