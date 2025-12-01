"""
Interactive example - Quick start guide for the Kubernetes demo.

This script provides a simple way to experiment with the system.
"""

import time
from k4s import KubernetesCluster


def main():
    print("Starting Kubernetes-like Orchestration Demo")
    print("=" * 50)

    # Create and start cluster
    cluster = KubernetesCluster()
    cluster.start()
    print("✓ Cluster started\n")

    # Example 1: Deploy a simple service
    print("Example 1: Deploying a simple echo service")
    print("-" * 50)

    yaml_config = """
kind: Container
metadata:
  name: echo-worker
spec:
  module: workers
  function: echo_worker
  parameters:
    prefix: "DEMO"
"""

    cluster.apply_yaml(yaml_config)
    print("✓ Deployed echo-worker container")
    time.sleep(2)

    # Test fire-and-forget messaging
    print("\nSending fire-and-forget messages:")
    cluster.api.send_to_container("echo-worker", "Hello")
    cluster.api.send_to_container("echo-worker", "World")
    time.sleep(1)

    # Test request-response
    print("\nSending request-response message:")
    future = cluster.api.send_to_container(
        "echo-worker", "Sync message", expect_response=True
    )
    response = future.result(timeout=5)
    print(f"  Received: {response}")

    # Example 2: Deploy a replicated service
    print("\n\nExample 2: Deploying a replicated calculator service")
    print("-" * 50)

    yaml_config = """
kind: Container
metadata:
  name: calculator-template
spec:
  module: workers
  function: calculator_worker
  parameters: {}
---
kind: ReplicaSet
metadata:
  name: calculator-rs
spec:
  container: calculator-template
  replicas: 3
---
kind: Service
metadata:
  name: calculator-service
spec:
  selector: "calculator-rs-*"
"""

    cluster.apply_yaml(yaml_config)
    print("✓ Deployed 3 calculator replicas with load-balanced service")
    time.sleep(3)

    # Make some calculations
    print("\nMaking calculations (load balanced across replicas):")

    calculations = [
        {"operation": "sum", "operands": [1, 2, 3, 4, 5]},
        {"operation": "product", "operands": [5, 6, 7]},
        {"operation": "average", "operands": [10, 20, 30, 40, 50]},
    ]

    for calc in calculations:
        future = cluster.api.send_to_service(
            "calculator-service", calc, expect_response=True
        )
        result = future.result(timeout=5)
        print(f"  {calc['operation']}({calc['operands']}) = {result}")

    # Example 3: Demonstrate scaling
    print("\n\nExample 3: Dynamic scaling")
    print("-" * 50)

    print("Current replicas: 3")
    print("Scaling up to 5 replicas...")

    yaml_config = """
kind: ReplicaSet
metadata:
  name: calculator-rs
spec:
  container: calculator-template
  replicas: 5
"""

    cluster.apply_yaml(yaml_config)
    time.sleep(3)

    containers = [
        c
        for c in cluster.list_resources("Container")
        if c.name.startswith("calculator-rs-")
    ]
    print(f"✓ Scaled to {len(containers)} replicas")

    # Make more calculations with more replicas
    print("\nMaking more calculations with 5 replicas:")
    for i in range(3):
        calc = {"operation": "sum", "operands": [i, i + 1, i + 2]}
        future = cluster.api.send_to_service(
            "calculator-service", calc, expect_response=True
        )
        result = future.result(timeout=5)
        print(f"  sum([{i}, {i + 1}, {i + 2}]) = {result}")

    # Example 4: Pipeline
    print("\n\nExample 4: Processing pipeline")
    print("-" * 50)

    yaml_config = """
kind: Container
metadata:
  name: aggregator
spec:
  module: workers
  function: aggregator_worker
  parameters:
    window_size: 3
---
kind: Container
metadata:
  name: processor
spec:
  module: workers
  function: processor_worker
  parameters:
    operation: uppercase
    forward_to: aggregator
"""

    cluster.apply_yaml(yaml_config)
    print("✓ Deployed processor -> aggregator pipeline")
    time.sleep(2)

    print("\nSending data through pipeline:")
    for i in range(5):
        message = f"data-{i}"
        cluster.api.send_to_container("processor", message)
        print(f"  Sent: {message}")
        time.sleep(0.3)

    time.sleep(2)

    # Summary
    print("\n\n" + "=" * 50)
    print("Demo Summary")
    print("=" * 50)
    print("\nDeployed Resources:")
    print(f"  Containers: {len(cluster.list_resources('Container'))}")
    print(f"  ReplicaSets: {len(cluster.list_resources('ReplicaSet'))}")
    print(f"  Services: {len(cluster.list_resources('Service'))}")

    print("\nRunning Containers:")
    for container in cluster.list_resources("Container"):
        print(f"  - {container.name}")

    print("\nFeatures Demonstrated:")
    print("  ✓ Container deployment from YAML")
    print("  ✓ Fire-and-forget messaging")
    print("  ✓ Request-response pattern")
    print("  ✓ ReplicaSets with automatic scaling")
    print("  ✓ Services with load balancing")
    print("  ✓ Inter-container communication")
    print("  ✓ Processing pipelines")

    print("\n" + "=" * 50)
    print("Cleaning up...")
    cluster.stop()
    print("✓ Cluster stopped")
    print("\nDemo completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback

        traceback.print_exc()
