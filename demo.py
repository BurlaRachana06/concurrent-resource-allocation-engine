from app.allocator import AllocationEngine
from app.models import Resource, ResourceType


def main():

    engine = AllocationEngine()

    # Add ICU beds
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

    print("\n========================================")
    print(" CONCURRENT RESOURCE ALLOCATION ENGINE")
    print("========================================")

    print("\nInitial ICU Beds:")

    for resource in engine.get_resources():
        print(
            f"{resource.resource_id} | "
            f"Available: {resource.available}"
        )

    # Emergency Patient 1
    print("\n--- Emergency Patient 1 ---")

    result = engine.allocate(
        "REQ-EMERGENCY-001",
        ["ICU-01"],
    )

    print(result)

    # Emergency Patient 2 requests same ICU
    print("\n--- Emergency Patient 2 ---")

    result = engine.allocate(
        "REQ-EMERGENCY-002",
        ["ICU-01"],
    )

    print(result)

    # Normal Patient requests second ICU
    print("\n--- Normal Patient ---")

    result = engine.allocate(
        "REQ-NORMAL-001",
        ["ICU-02"],
    )

    print(result)

    # Final state
    print("\nFinal ICU Beds:")

    for resource in engine.get_resources():
        print(
            f"{resource.resource_id} | "
            f"Available: {resource.available}"
        )

    print("\n========================================")
    print(" DEMO COMPLETED")
    print("========================================")


if __name__ == "__main__":
    main()