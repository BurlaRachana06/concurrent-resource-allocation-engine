import time

from app.allocator import AllocationEngine
from app.models import Resource, ResourceType


def main():

    engine = AllocationEngine()

    # -------------------------------------------------
    # Add two ICU beds
    # -------------------------------------------------

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

    print("\n==============================================")
    print(" PRIORITY + RESOURCE AVAILABILITY DEMO")
    print("==============================================")

    # -------------------------------------------------
    # Step 1: Occupy both ICU beds
    # -------------------------------------------------

    print("\nSTEP 1: Both ICU beds are occupied")

    result = engine.allocate(
        "REQ-CURRENT-001",
        ["ICU-01"],
    )

    print("Patient A (Emergency):", result)

    result = engine.allocate(
        "REQ-CURRENT-002",
        ["ICU-02"],
    )

    print("Patient B (Emergency):", result)

    # -------------------------------------------------
    # Step 2: New Emergency patient arrives
    # -------------------------------------------------

    print("\nSTEP 2: New Emergency patient arrives")

    emergency_result = engine.allocate(
        "REQ-NEW-EMERGENCY",
        ["ICU-01"],
    )

    print("Emergency Patient C:", emergency_result)

    # -------------------------------------------------
    # Step 3: Normal patient arrives
    # -------------------------------------------------

    print("\nSTEP 3: Normal patient arrives")

    normal_result = engine.allocate(
        "REQ-NORMAL",
        ["ICU-02"],
    )

    print("Normal Patient D:", normal_result)

    # -------------------------------------------------
    # Step 4: Show current situation
    # -------------------------------------------------

    print("\nSTEP 4: All ICU beds are currently occupied")

    for resource in engine.get_resources():
        print(
            f"{resource.resource_id} | "
            f"Available: {resource.available}"
        )

    # -------------------------------------------------
    # Step 5: Release ICU-01
    # -------------------------------------------------

    print("\nSTEP 5: ICU-01 is released")

    release_result = engine.release(
        ["ICU-01"]
    )

    print(release_result)

    # -------------------------------------------------
    # Step 6: Emergency patient gets the released bed
    # -------------------------------------------------

    print("\nSTEP 6: Emergency patient gets the available ICU")

    result = engine.allocate(
        "REQ-NEW-EMERGENCY",
        ["ICU-01"],
    )

    print("Emergency Patient C:", result)

    # -------------------------------------------------
    # Final state
    # -------------------------------------------------

    print("\nFINAL ICU STATUS")

    for resource in engine.get_resources():
        print(
            f"{resource.resource_id} | "
            f"Available: {resource.available}"
        )

    print("\n==============================================")
    print(" DEMO COMPLETED")
    print("==============================================")


if __name__ == "__main__":
    main()