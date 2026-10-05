import threading
from typing import Dict, List

from app.models import Resource


class AllocationEngine:

    def __init__(self):
        self.resources: Dict[str, Resource] = {}

        # One lock protects the complete allocation state.
        self.lock = threading.RLock()

        # Fixed resource ordering provides deterministic processing.
        self.resource_order = {
            "ICU_BED": 1,
            "OR_SLOT": 2,
            "EQUIPMENT": 3,
        }

    def add_resource(self, resource: Resource):
        with self.lock:
            self.resources[resource.resource_id] = resource

    def get_resources(self):
        with self.lock:
            return list(self.resources.values())

    def allocate(
        self,
        request_id: str,
        resource_ids: List[str],
    ):
        with self.lock:

            # -------------------------------------------------
            # 1. Validate that every requested resource exists
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
            # 2. Sort only after validation
            # -------------------------------------------------
            sorted_ids = sorted(
                resource_ids,
                key=lambda resource_id: self.resource_order[
                    self.resources[resource_id].resource_type.value
                ],
            )

            # -------------------------------------------------
            # 3. Check ALL resources before allocating ANY
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
            # 4. Atomic allocation
            # -------------------------------------------------
            for resource_id in sorted_ids:
                self.resources[resource_id].available = False

            return {
                "status": "ALLOCATED",
                "allocated_resources": sorted_ids,
                "message": "Resources allocated successfully",
            }

    def release(self, resource_ids: List[str]):

        with self.lock:

            released_resources = []

            for resource_id in resource_ids:
                if resource_id in self.resources:
                    self.resources[resource_id].available = True
                    released_resources.append(resource_id)

            return {
                "status": "RELEASED",
                "released_resources": released_resources,
                "message": "Resources released successfully",
            }