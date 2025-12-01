# Quick Reference Guide

## Getting Started

```python
from k4s import KubernetesCluster

cluster = KubernetesCluster()
cluster.start()
```

## Resource YAML Format

### Container

```yaml
kind: Container
metadata:
  name: my-worker
spec:
  module: workers # Python module name
  function: echo_worker # Function name in module
  parameters: # Kwargs passed to function
    prefix: "HELLO"
```

### ReplicaSet

```yaml
kind: ReplicaSet
metadata:
  name: my-replicaset
spec:
  container: my-worker # Template container name
  replicas: 3 # Number of replicas
```

### Service

```yaml
kind: Service
metadata:
  name: my-service
spec:
  selector: "my-replicaset-*" # Glob pattern for containers
```

## Common Operations

### Deploy Resources

```python
cluster.apply_yaml(yaml_content)
```

### Send Messages

#### Fire-and-Forget

```python
cluster.api.send_to_container("container-name", "message")
cluster.api.send_to_service("service-name", "message")
```

#### Request-Response

```python
future = cluster.api.send_to_container("container-name", "message", expect_response=True)
result = future.result(timeout=5)
```

### Resource Management

```python
# Get resource
resource = cluster.get_resource("Container", "my-worker")

# List resources
containers = cluster.list_resources("Container")
replicasets = cluster.list_resources("ReplicaSet")
services = cluster.list_resources("Service")

# Delete resource
cluster.delete_resource("Container", "my-worker")
```

### Scale ReplicaSet

```python
yaml = """
kind: ReplicaSet
metadata:
  name: my-replicaset
spec:
  container: my-worker
  replicas: 5
"""
cluster.apply_yaml(yaml)
```

## Writing Worker Functions

### Basic Template

```python
def my_worker(input_queue, api_client, **kwargs):
    """
    Args:
        input_queue: Queue to receive messages
        api_client: API for inter-container communication
        **kwargs: Custom parameters from resource spec
    """
    while True:
        item = input_queue.get()
        if item is None:  # Shutdown signal
            break

        # Process item
        process(item)
```

### With Request-Response Support

```python
def my_worker(input_queue, api_client, **kwargs):
    while True:
        item = input_queue.get()
        if item is None:
            break

        # Check if expecting response
        if isinstance(item, tuple) and len(item) == 2:
            value, future = item
            result = process(value)
            future.set_result(result)
        else:
            process(item)
```

### With Inter-Container Communication

```python
def my_worker(input_queue, api_client, forward_to=None, **kwargs):
    while True:
        item = input_queue.get()
        if item is None:
            break

        result = process(item)

        # Forward to another container
        if forward_to:
            api_client.send_to_container(forward_to, result)
```

## Example Workflows

### Simple Echo Service

```python
cluster = KubernetesCluster()
cluster.start()

cluster.apply_yaml("""
kind: Container
metadata:
  name: echo
spec:
  module: workers
  function: echo_worker
  parameters:
    prefix: "ECHO"
""")

cluster.api.send_to_container("echo", "Hello")
```

### Load-Balanced Calculator

```python
cluster.apply_yaml("""
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
""")

# Use the service
request = {"operation": "sum", "operands": [1, 2, 3]}
future = cluster.api.send_to_service("calculator", request, expect_response=True)
result = future.result(timeout=5)
```

### Processing Pipeline

```python
cluster.apply_yaml("""
kind: Container
metadata:
  name: stage2
spec:
  module: workers
  function: aggregator_worker
  parameters:
    window_size: 5
---
kind: Container
metadata:
  name: stage1
spec:
  module: workers
  function: processor_worker
  parameters:
    operation: uppercase
    forward_to: stage2
""")

# Send to stage1, which forwards to stage2
cluster.api.send_to_container("stage1", "data")
```

## Tips & Best Practices

1. **Always provide unique names** for containers
2. **Use services for load balancing** instead of directly targeting containers
3. **Use request-response** when you need confirmation or a result
4. **Let controllers handle lifecycle** - they automatically reconcile state
5. **Keep worker functions lightweight** - they run in threads
6. **Handle None gracefully** - it signals shutdown
7. **Use try-except** in worker functions to handle errors
8. **Check queue with timeout** if you need to do periodic work

## Common Patterns

### Worker with Periodic Tasks

```python
def worker(input_queue, api_client):
    while True:
        try:
            item = input_queue.get(timeout=1.0)
            if item is None:
                break
            process(item)
        except queue.Empty:
            # Do periodic work
            periodic_task()
```

### Worker with Error Handling

```python
def worker(input_queue, api_client):
    while True:
        item = input_queue.get()
        if item is None:
            break

        try:
            if isinstance(item, tuple) and len(item) == 2:
                value, future = item
                result = process(value)
                future.set_result(result)
            else:
                process(item)
        except Exception as e:
            print(f"Error: {e}")
            if future:
                future.set_exception(e)
```

## Troubleshooting

### Container Not Starting

- Check that module and function names are correct
- Verify the module is in Python path
- Look for import errors in console output

### Messages Not Being Processed

- Verify container is running: `cluster.list_resources("Container")`
- Check container name spelling
- Ensure controller is started: `cluster.start()`

### Service Not Found

- Verify service exists: `cluster.get_resource("Service", "name")`
- Check that selector pattern matches containers
- Wait a few seconds after deployment

### Request Timeout

- Increase timeout: `future.result(timeout=10)`
- Check that worker is processing messages
- Verify worker is setting result on future
