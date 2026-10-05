import threading
from typing import Dict, List

from app.models import Resource


class AllocationEngine:

    def __init__(self):
        self.resources: Dict[str, Resource] = {}

        # Stores successfully processed allocation requests.
        # request_id -> allocation result
        self.processed_requests = {}

        # One shared lock protects the complete allocation state.
        self.lock = threading.RLock()

        # Fixed resource ordering provides deterministic processing
        # and helps avoid circular locking patterns.
        self.resource_order = {
            "ICU_BED": 1,
            "OR_SLOT": 2,
            "EQUIPMENT": 3,
        }

    # -----------------------------------------------------
    # Add Resource
    # -----------------------------------------------------

    def add_resource(self, resource: Resource):

        with self.lock:
            self.resources[resource.resource_id] = resource

    # -----------------------------------------------------
    # Get Resources
    # -----------------------------------------------------

    def get_resources(self):

        with self.lock:
            # Return deep copies so external callers cannot
            # directly modify the allocator's internal state.
            return [
                resource.model_copy(deep=True)
                for resource in self.resources.values()
            ]

    # -----------------------------------------------------
    # Allocate Resources
    # -----------------------------------------------------

    def allocate(
        self,
        request_id: str,
        resource_ids: List[str],
    ):

        with self.lock:

            # -------------------------------------------------
            # 1. Idempotency Check
            # -------------------------------------------------
            if request_id in self.processed_requests:

                previous_result = self.processed_requests[
                    request_id
                ].copy()

                previous_result["message"] = (
                    "Request already processed. "
                    "Returning previous allocation result."
                )

                return previous_result

            # -------------------------------------------------
            # 2. Reject Duplicate Resource IDs
            # -------------------------------------------------
            if len(resource_ids) != len(set(resource_ids)):

                return {
                    "status": "FAILED",
                    "allocated_resources": [],
                    "message": (
                        "Duplicate resource IDs are not allowed"
                    ),
                }

            # -------------------------------------------------
            # 3. Validate Resource IDs
            # -------------------------------------------------
            for resource_id in resource_ids:

                if resource_id not in self.resources:

                    return {
                        "status": "FAILED",
                        "allocated_resources": [],
                        "message": (
                            f"Resource {resource_id} does not exist"
                        ),
                    }

            # -------------------------------------------------
            # 4. Sort Resources
            # -------------------------------------------------
            sorted_ids = sorted(
                resource_ids,
                key=lambda resource_id: self.resource_order[
                    self.resources[resource_id]
                    .resource_type
                    .value
                ],
            )

            # -------------------------------------------------
            # 5. Check ALL Resources Before Allocation
            # -------------------------------------------------
            for resource_id in sorted_ids:

                resource = self.resources[resource_id]

                if not resource.available:

                    return {
                        "status": "UNAVAILABLE",
                        "allocated_resources": [],
                        "message": (
                            f"Resource {resource_id} is unavailable"
                        ),
                    }

            # -------------------------------------------------
            # 6. Atomic Allocation
            # -------------------------------------------------
            # All requested resources have been verified.
            # Now allocate them together while holding the lock.

            for resource_id in sorted_ids:

                self.resources[resource_id].available = False

            result = {
                "status": "ALLOCATED",
                "allocated_resources": sorted_ids,
                "message": (
                    "Resources allocated successfully"
                ),
            }

            # -------------------------------------------------
            # 7. Store Successful Request
            # -------------------------------------------------
            self.processed_requests[request_id] = result.copy()

            return result

    # -----------------------------------------------------
    # Release Resources
    # -----------------------------------------------------

    def release(
        self,
        resource_ids: List[str],
    ):

        with self.lock:

            released_resources = []

            for resource_id in resource_ids:

                if resource_id in self.resources:

                    self.resources[
                        resource_id
                    ].available = True

                    released_resources.append(resource_id)

            return {
                "status": "RELEASED",
                "released_resources": released_resources,
                "message": (
                    "Resources released successfully"
                ),
            }