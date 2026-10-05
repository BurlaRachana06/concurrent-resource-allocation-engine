import heapq
import threading

from app.allocator import AllocationEngine
from app.models import AllocationRequest


class PriorityScheduler:

    PRIORITY_ORDER = {
        "EMERGENCY": 1,
        "URGENT": 2,
        "NORMAL": 3,
    }

    def __init__(self, engine: AllocationEngine):
        self.engine = engine
        self.lock = threading.Lock()
        self.queue = []
        self.sequence = 0

    # -----------------------------------------------------
    # Add request to priority queue
    # -----------------------------------------------------

    def submit(self, request: AllocationRequest):

        with self.lock:

            self.sequence += 1

            priority = self.PRIORITY_ORDER[
                request.priority.value
            ]

            heapq.heappush(
                self.queue,
                (
                    priority,
                    self.sequence,
                    request,
                ),
            )

            return {
                "status": "QUEUED",
                "request_id": request.request_id,
                "priority": request.priority.value,
                "queue_position": len(self.queue),
            }

    # -----------------------------------------------------
    # Process highest-priority request
    # -----------------------------------------------------

    def process_next(self):

        with self.lock:

            if not self.queue:
                return {
                    "status": "EMPTY",
                    "message": "No requests in scheduler queue",
                }

            priority, sequence, request = heapq.heappop(
                self.queue
            )

        # Try to allocate the requested resources
        result = self.engine.allocate(
            request.request_id,
            request.resource_ids,
        )

        # -------------------------------------------------
        # If resources are unavailable, put the request
        # back into the priority queue.
        # -------------------------------------------------

        if result["status"] == "UNAVAILABLE":

            with self.lock:

                heapq.heappush(
                    self.queue,
                    (
                        priority,
                        sequence,
                        request,
                    ),
                )

            return {
                "request_id": request.request_id,
                "patient_id": request.patient_id,
                "priority": request.priority.value,
                "status": "WAITING",
                "allocated_resources": [],
                "message": (
                    "Requested resources are unavailable. "
                    "Request remains in the priority queue."
                ),
            }

        # -------------------------------------------------
        # Successful allocation or other result
        # -------------------------------------------------

        return {
            "request_id": request.request_id,
            "patient_id": request.patient_id,
            "priority": request.priority.value,
            **result,
        }

    # -----------------------------------------------------
    # Get current queue size
    # -----------------------------------------------------

    def queue_size(self):

        with self.lock:
            return len(self.queue)

    # -----------------------------------------------------
    # Clear all queued requests
    # -----------------------------------------------------

    def clear(self):

        with self.lock:
            self.queue.clear()