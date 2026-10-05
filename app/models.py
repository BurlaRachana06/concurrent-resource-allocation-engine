from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional


class ResourceType(str, Enum):
    ICU_BED = "ICU_BED"
    OR_SLOT = "OR_SLOT"
    EQUIPMENT = "EQUIPMENT"


class Priority(str, Enum):
    EMERGENCY = "EMERGENCY"
    URGENT = "URGENT"
    NORMAL = "NORMAL"


class Resource(BaseModel):
    resource_id: str
    resource_type: ResourceType
    available: bool = True


class AllocationRequest(BaseModel):
    request_id: str
    patient_id: str
    priority: Priority
    resource_ids: List[str] = Field(min_length=1)


class AllocationResponse(BaseModel):
    request_id: str
    status: str
    allocated_resources: List[str] = []
    message: Optional[str] = None