"""
Demo script showing how to use the Kubernetes-like orchestration system.
"""

import subprocess
import time
from k4s import KissCluster


def demo_basic_container():
    """Demo 1: Basic container deployment"""
    print("\n" + "=" * 60)
    print("DEMO 1: Basic Container Deployment")
    print("=" * 60)

    cluster = KissCluster()
    cluster.start()

    # Deploy a simple echo container
    yaml_content = """
kind: Container
metadata:
  name: echo-1
spec:
  image: hello-world
"""

    cluster.apply_yaml(yaml_content)
    time.sleep(2)

    # Send messages to the container
    print("\nSending messages to echo-1...")
    # cluster.api.send_to_container("echo-1", "World")
    # cluster.api.send_to_container("echo-1", "Kubernetes")

    # time.sleep(2)

    # # Test request-response
    # print("\nTesting request-response pattern...")
    # future = cluster.api.send_to_container(
    #     "echo-1", "test message", expect_response=True
    # )
    # response = future.result(timeout=5)
    # print(f"Received response: {response}")

    time.sleep(1)
    cluster.stop()


def demo_network():
    print("\n" + "=" * 60)
    print("DEMO: Two containers that talk to each other")
    print("=" * 60)

    cluster = KissCluster()
    cluster.start()

    # Deploy a simple echo container
    yaml_content = """
kind: Container
metadata:
  name: health
spec:
  image: health
---
kind: Container
metadata:
  name: ping
spec:
  image: ping
  env:
    HEALTH_SERVICE: health:5000
"""

    try:
        cluster.apply_yaml(yaml_content)
        time.sleep(5)
        print(subprocess.check_output(["docker", "ps"]))
        print(subprocess.check_output(["docker", "logs", "ping"]))
        input("Press [Enter] to continue")
    finally:
        cluster.stop()


def demo_replicaset():
    """Demo 2: ReplicaSet with multiple replicas"""
    print("\n" + "=" * 60)
    print("DEMO 2: ReplicaSet with Load Balancing")
    print("=" * 60)

    cluster = KissCluster()
    cluster.start()

    # Deploy container template and replicaset
    yaml_content = """
kind: Container
metadata:
  name: processor-template
spec:
  module: workers
  function: processor_worker
  parameters:
    operation: uppercase
---
kind: ReplicaSet
metadata:
  name: processor-rs
spec:
  container: processor-template
  replicas: 3
---
kind: Service
metadata:
  name: processor-service
spec:
  selector: "processor-rs-*"
"""

    cluster.apply_yaml(yaml_content)
    time.sleep(3)

    # List resources
    print("\nDeployed containers:")
    for container in cluster.list_resources("Container"):
        print(f"  - {container.name}")

    # Send messages to the service (load balanced)
    print("\nSending messages to processor-service (load balanced)...")
    for i in range(6):
        message = f"message-{i}"
        cluster.api.send_to_service("processor-service", message)
        time.sleep(0.5)

    time.sleep(2)
    cluster.stop()


def demo_scaling():
    """Demo 3: Dynamic scaling"""
    print("\n" + "=" * 60)
    print("DEMO 3: Dynamic Scaling")
    print("=" * 60)

    cluster = KissCluster()
    cluster.start()

    # Deploy with 2 replicas
    yaml_content = """
kind: Container
metadata:
  name: echo-template
spec:
  module: workers
  function: echo_worker
  parameters:
    prefix: "REPLICA"
---
kind: ReplicaSet
metadata:
  name: echo-rs
spec:
  container: echo-template
  replicas: 2
"""

    cluster.apply_yaml(yaml_content)
    time.sleep(3)

    print(
        f"\nInitial replicas: {len([c for c in cluster.list_resources('Container') if c.name.startswith('echo-rs-')])}"
    )

    # Scale up to 5
    print("\nScaling up to 5 replicas...")
    yaml_content = """
kind: ReplicaSet
metadata:
  name: echo-rs
spec:
  container: echo-template
  replicas: 5
"""
    cluster.apply_yaml(yaml_content)
    time.sleep(3)

    print(
        f"After scale up: {len([c for c in cluster.list_resources('Container') if c.name.startswith('echo-rs-')])}"
    )

    # Scale down to 2
    print("\nScaling down to 2 replicas...")
    yaml_content = """
kind: ReplicaSet
metadata:
  name: echo-rs
spec:
  container: echo-template
  replicas: 2
"""
    cluster.apply_yaml(yaml_content)
    time.sleep(3)

    print(
        f"After scale down: {len([c for c in cluster.list_resources('Container') if c.name.startswith('echo-rs-')])}"
    )

    time.sleep(1)
    cluster.stop()


def demo_inter_container_communication():
    """Demo 4: Containers communicating with each other"""
    print("\n" + "=" * 60)
    print("DEMO 4: Inter-Container Communication")
    print("=" * 60)

    cluster = KissCluster()
    cluster.start()

    # Deploy processor that forwards to aggregator
    yaml_content = """
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

    cluster.apply_yaml(yaml_content)
    time.sleep(2)

    # Send messages to processor, which will forward to aggregator
    print("\nSending messages to processor (which forwards to aggregator)...")
    for i in range(5):
        cluster.api.send_to_container("processor", f"test-{i}")
        time.sleep(0.5)

    time.sleep(2)
    cluster.stop()


def demo_generator_pipeline():
    """Demo 5: Generator -> Processor pipeline"""
    print("\n" + "=" * 60)
    print("DEMO 5: Generator -> Service Pipeline")
    print("=" * 60)

    cluster = KissCluster()
    cluster.start()

    # Deploy processor replicaset and service
    yaml_content = """
kind: Container
metadata:
  name: proc-template
spec:
  module: workers
  function: processor_worker
  parameters:
    operation: reverse
---
kind: ReplicaSet
metadata:
  name: processor-rs
spec:
  container: proc-template
  replicas: 2
---
kind: Service
metadata:
  name: processors
spec:
  selector: "processor-rs-*"
---
kind: Container
metadata:
  name: generator
spec:
  module: workers
  function: generator_worker
  parameters:
    target: processors
    interval: 1
    count: 5
"""

    cluster.apply_yaml(yaml_content)

    print("\nGenerator will send messages to processor service...")
    time.sleep(8)

    cluster.stop()


def demo_calculator_service():
    """Demo 6: Request-response calculator service"""
    print("\n" + "=" * 60)
    print("DEMO 6: Calculator Request-Response Service")
    print("=" * 60)

    cluster = KissCluster()
    cluster.start()

    yaml_content = """
kind: Container
metadata:
  name: calc-template
spec:
  module: workers
  function: calculator_worker
  parameters: {}
---
kind: ReplicaSet
metadata:
  name: calculator-rs
spec:
  container: calc-template
  replicas: 3
---
kind: Service
metadata:
  name: calculator
spec:
  selector: "calculator-rs-*"
"""

    cluster.apply_yaml(yaml_content)
    time.sleep(2)

    # Make calculation requests
    print("\nMaking calculation requests to calculator service...")

    requests = [
        {"operation": "sum", "operands": [1, 2, 3, 4, 5]},
        {"operation": "product", "operands": [2, 3, 4]},
        {"operation": "average", "operands": [10, 20, 30, 40]},
    ]

    for req in requests:
        future = cluster.api.send_to_service("calculator", req, expect_response=True)
        result = future.result(timeout=5)
        print(f"Request: {req} -> Result: {result}")
        time.sleep(0.5)

    time.sleep(1)
    cluster.stop()


def demo_resource_crud():
    """Demo 7: CRUD operations on resources"""
    print("\n" + "=" * 60)
    print("DEMO 7: Resource CRUD Operations")
    print("=" * 60)

    cluster = KissCluster()
    cluster.start()

    # Create
    print("\n1. Creating resources...")
    yaml_content = """
kind: Container
metadata:
  name: test-container
spec:
  module: workers
  function: echo_worker
  parameters:
    prefix: "TEST"
"""
    cluster.apply_yaml(yaml_content)
    time.sleep(1)

    # Read
    print("\n2. Reading resource...")
    resource = cluster.get_resource("Container", "test-container")
    print(f"   Found: {resource.name} - {resource.spec}")

    # Update
    print("\n3. Updating resource...")
    yaml_content = """
kind: Container
metadata:
  name: test-container
spec:
  module: workers
  function: echo_worker
  parameters:
    prefix: "UPDATED"
"""
    cluster.apply_yaml(yaml_content)
    time.sleep(2)

    # Send message to verify update
    cluster.api.send_to_container("test-container", "hello")
    time.sleep(1)

    # Delete
    print("\n4. Deleting resource...")
    cluster.delete_resource("Container", "test-container")
    time.sleep(2)

    # Verify deletion
    print("\n5. Verifying deletion...")
    resource = cluster.get_resource("Container", "test-container")
    print(f"   Resource exists: {resource is not None}")

    cluster.stop()


def run_all_demos():
    """Run all demos"""
    demos = [
        # demo_basic_container,
        demo_network,
        # demo_replicaset,
        # demo_scaling,
        # demo_inter_container_communication,
        # demo_generator_pipeline,
        # demo_calculator_service,
        # demo_resource_crud,
    ]

    for demo in demos:
        try:
            demo()
            time.sleep(2)
        except KeyboardInterrupt:
            print("\nDemo interrupted by user")
            break
        except Exception as e:
            print(f"\nDemo error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    run_all_demos()
