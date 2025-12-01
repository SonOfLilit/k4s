# Kubernetes-like Orchestration System for Python Threads

A simplified Kubernetes implementation that orchestrates Python worker threads instead of containers. This demo provides resource management, controllers, and inter-container communication APIs similar to Kubernetes.

## Features

- **Resource Types**: Container, ReplicaSet, Service
- **Controllers**: Automatic reconciliation of desired vs actual state
- **In-Memory Resource Tree**: CRUD operations on resources
- **Inter-Container Communication**: Queue-based messaging with request-response support
- **Load Balancing**: Service-based routing to multiple containers
- **Dynamic Scaling**: ReplicaSets automatically manage replicas

## Architecture

### Components

1. **Resource Store**: In-memory storage for resource definitions
2. **Controllers**: Background threads that reconcile state
   - `ContainerController`: Manages container lifecycle
   - `ReplicaSetController`: Manages replica counts
   - `ServiceController`: Validates service selectors
3. **KubernetesAPI**: Interface for inter-container communication
4. **KubernetesCluster**: Main orchestrator

### Resource Types

#### Container

Defines a worker thread that runs a Python function.

```yaml
kind: Container
metadata:
  name: my-worker
spec:
  module: workers # Python module name
  function: echo_worker # Function to run
  parameters: # Parameters passed to function
    prefix: "HELLO"
```

#### ReplicaSet

Ensures a specified number of container replicas are running.

```yaml
kind: ReplicaSet
metadata:
  name: my-replicaset
spec:
  container: my-worker # Template container name
  replicas: 3 # Desired replica count
```

#### Service

Provides load-balanced access to containers via glob pattern.

```yaml
kind: Service
metadata:
  name: my-service
spec:
  selector: "my-replicaset-*" # Glob pattern for container names
```

## Usage

### Starting a Cluster

```python
from k4s import KubernetesCluster

cluster = KubernetesCluster()
cluster.start()
```

### Deploying Resources

```python
yaml_content = """
kind: Container
metadata:
  name: echo-1
spec:
  module: workers
  function: echo_worker
  parameters:
    prefix: "HELLO"
"""

cluster.apply_yaml(yaml_content)
```

### Sending Messages to Containers

```python
# Fire-and-forget
cluster.api.send_to_container("echo-1", "Hello World")

# Request-response
future = cluster.api.send_to_container("echo-1", "Hello", expect_response=True)
response = future.result(timeout=5)
print(response)
```

### Sending Messages to Services

```python
# Send to random container matched by service
cluster.api.send_to_service("my-service", "Hello")

# Request-response with service
future = cluster.api.send_to_service("my-service", {"operation": "sum", "operands": [1,2,3]},
                                      expect_response=True)
result = future.result(timeout=5)
```

### Resource CRUD Operations

```python
# Create/Update
cluster.apply_yaml(yaml_content)

# Read
resource = cluster.get_resource("Container", "my-worker")

# List
containers = cluster.list_resources("Container")

# Delete
cluster.delete_resource("Container", "my-worker")
```

## Writing Worker Functions

Worker functions must accept `input_queue` and `api_client` parameters:

```python
def my_worker(input_queue, api_client, custom_param="default"):
    """
    Custom worker function.

    Args:
        input_queue: Queue to receive messages
        api_client: API for inter-container communication
        custom_param: Custom parameter from resource spec
    """
    while True:
        item = input_queue.get()

        # None signals shutdown
        if item is None:
            break

        # Handle request-response pattern
        if isinstance(item, tuple) and len(item) == 2:
            value, future = item
            result = process(value, custom_param)
            future.set_result(result)
        else:
            # Fire-and-forget
            process(item, custom_param)
```

### Inter-Container Communication

Workers can communicate with other containers:

```python
def processor_worker(input_queue, api_client, forward_to=None):
    while True:
        item = input_queue.get()
        if item is None:
            break

        result = process(item)

        # Forward to another container
        if forward_to:
            api_client.send_to_container(forward_to, result)
```

## Examples

### Example 1: Simple Echo Service

```python
cluster = KubernetesCluster()
cluster.start()

yaml = """
kind: Container
metadata:
  name: echo-1
spec:
  module: workers
  function: echo_worker
  parameters:
    prefix: "ECHO"
"""

cluster.apply_yaml(yaml)
time.sleep(2)

# Send message
cluster.api.send_to_container("echo-1", "Hello World")
```

### Example 2: Scalable Processing Service

```python
yaml = """
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
  replicas: 5
---
kind: Service
metadata:
  name: processors
spec:
  selector: "processor-rs-*"
"""

cluster.apply_yaml(yaml)
time.sleep(2)

# Send to service (load balanced across 5 replicas)
for i in range(10):
    cluster.api.send_to_service("processors", f"message-{i}")
```

### Example 3: Request-Response Calculator

```python
yaml = """
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
  name: calc-rs
spec:
  container: calc-template
  replicas: 3
---
kind: Service
metadata:
  name: calculator
spec:
  selector: "calc-rs-*"
"""

cluster.apply_yaml(yaml)

# Make calculation request
request = {"operation": "sum", "operands": [1, 2, 3, 4, 5]}
future = cluster.api.send_to_service("calculator", request, expect_response=True)
result = future.result(timeout=5)
print(f"Sum result: {result}")  # Output: 15
```

### Example 4: Pipeline Architecture

```python
yaml = """
kind: Container
metadata:
  name: aggregator
spec:
  module: workers
  function: aggregator_worker
  parameters:
    window_size: 5
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
---
kind: Container
metadata:
  name: generator
spec:
  module: workers
  function: generator_worker
  parameters:
    target: processor
    interval: 1
    count: 10
"""

cluster.apply_yaml(yaml)

# Generator -> Processor -> Aggregator pipeline runs automatically
```

## Running the Demo

```bash
python demo.py
```

This will run through 7 comprehensive demos showcasing all features:

1. Basic container deployment
2. ReplicaSets with load balancing
3. Dynamic scaling
4. Inter-container communication
5. Generator -> Service pipeline
6. Request-response calculator service
7. Resource CRUD operations

## Files

- `k4s.py`: Core orchestration system
- `workers.py`: Example worker implementations
- `demo.py`: Comprehensive demonstration script
- `README.md`: This file

## Key Concepts

### Controllers

Controllers run in background threads and continuously reconcile desired state (resource definitions) with actual state (running containers). This is the core Kubernetes pattern.

### Reconciliation Loop

Each controller:

1. Reads desired state from resource store
2. Compares with actual state
3. Takes actions to converge actual to desired
4. Sleeps and repeats

### Load Balancing

Services use glob patterns to match container names and randomly select one for each message, providing basic load balancing.

### Request-Response Pattern

For synchronous communication, send a tuple of `(value, Future)`:

- Container receives the tuple
- Processes the value
- Sets the result on the Future
- Caller gets result via `future.result()`

## Limitations

This is a simplified demo and lacks many Kubernetes features:

- No persistent storage
- No network isolation
- No resource limits (CPU/memory)
- No health checks/restart policies
- No namespaces
- No ConfigMaps/Secrets
- Simplified scheduling (no node selection)

## License

This is a demonstration project for educational purposes.
