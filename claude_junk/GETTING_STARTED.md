# Getting Started with Kubernetes-like Orchestration

## 🎯 What Is This?

A Python implementation of Kubernetes concepts that orchestrates worker **threads** instead of containers. Perfect for:

- Learning how Kubernetes works
- Building thread-based microservices
- Understanding orchestration patterns
- Rapid prototyping of distributed systems

## ⚡ 30-Second Quick Start

```bash
# Run the interactive example
python example.py
```

That's it! You'll see:

- Containers being deployed
- Messages being processed
- Services load balancing
- Dynamic scaling in action

## 🎓 5-Minute Tutorial

### Step 1: Create a Cluster

```python
from k4s import KubernetesCluster

cluster = KubernetesCluster()
cluster.start()
```

### Step 2: Deploy a Worker

```python
yaml = """
kind: Container
metadata:
  name: greeter
spec:
  module: workers
  function: echo_worker
  parameters:
    prefix: "Hello"
"""

cluster.apply_yaml(yaml)
```

### Step 3: Send a Message

```python
import time
time.sleep(2)  # Let it start

cluster.api.send_to_container("greeter", "World")
# Output: Hello: World
```

### Step 4: Clean Up

```python
cluster.stop()
```

## 📖 Core Concepts in 2 Minutes

### Resources (What You Define)

1. **Container** - A worker thread

   ```yaml
   kind: Container
   metadata:
     name: worker-1
   spec:
     module: workers
     function: my_function
   ```

2. **ReplicaSet** - Multiple copies

   ```yaml
   kind: ReplicaSet
   metadata:
     name: workers-rs
   spec:
     container: worker-1
     replicas: 3
   ```

3. **Service** - Load balancer
   ```yaml
   kind: Service
   metadata:
     name: workers-svc
   spec:
     selector: "workers-rs-*"
   ```

### How It Works

```
You create → Resources are stored → Controllers notice →
Workers start → You send messages → Workers process
```

### Communication Patterns

**Fire-and-forget:**

```python
cluster.api.send_to_container("worker", "data")
```

**Request-response:**

```python
future = cluster.api.send_to_container("worker", "data", expect_response=True)
result = future.result(timeout=5)
```

**Via service (load balanced):**

```python
cluster.api.send_to_service("my-service", "data")
```

## 🚀 Your First Real Example

Let's build a calculator service with 3 replicas:

```python
from k4s import KubernetesCluster
import time

# Start cluster
cluster = KubernetesCluster()
cluster.start()

# Deploy calculator with 3 replicas and a service
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
time.sleep(2)

# Use the calculator (automatically load balanced)
request = {"operation": "sum", "operands": [1, 2, 3, 4, 5]}
future = cluster.api.send_to_service("calculator", request, expect_response=True)
result = future.result(timeout=5)
print(f"Result: {result}")  # Output: 15

# Scale up
yaml = """
kind: ReplicaSet
metadata:
  name: calc-rs
spec:
  container: calc-template
  replicas: 5
"""
cluster.apply_yaml(yaml)
time.sleep(2)

# Still works, now with 5 replicas!
request = {"operation": "product", "operands": [2, 3, 4]}
future = cluster.api.send_to_service("calculator", request, expect_response=True)
result = future.result(timeout=5)
print(f"Result: {result}")  # Output: 24

# Clean up
cluster.stop()
```

## 🛠️ Writing Your Own Worker

Workers are just Python functions:

```python
def my_worker(input_queue, api_client, custom_param="default"):
    """
    A simple worker function.

    Args:
        input_queue: Queue to receive messages (required)
        api_client: API for sending to other containers (required)
        custom_param: Your custom parameter from YAML
    """
    print(f"Worker started with param: {custom_param}")

    while True:
        # Get next message
        item = input_queue.get()

        # None means shutdown
        if item is None:
            break

        # Process the message
        print(f"Processing: {item}")

        # Do something with it
        result = str(item).upper()

        # You can send to other containers
        # api_client.send_to_container("other-worker", result)

    print("Worker stopped")
```

Save this in a file called `my_workers.py`, then use it:

```python
yaml = """
kind: Container
metadata:
  name: my-container
spec:
  module: my_workers
  function: my_worker
  parameters:
    custom_param: "Hello!"
"""

cluster.apply_yaml(yaml)
```

## 📚 What to Read Next

**If you want to:**

- **See more examples** → Run `python demo.py`
- **Learn common operations** → Read [QUICKREF.md](./QUICKREF.md)
- **Understand architecture** → Read [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Deep dive** → Read [k4s.py](./k4s.py) source code

## 🎯 Common Use Cases

### 1. Processing Pipeline

```
Generator → Processor → Aggregator → Logger
```

### 2. Load-Balanced Service

```
Client → Service → [Worker1, Worker2, Worker3]
```

### 3. Request-Response Service

```
Client ← Future ← Worker (processes and responds)
```

### 4. Fan-Out Pattern

```
Source → Service → Multiple Workers (parallel processing)
```

## 🐛 Troubleshooting

**Container not starting?**

- Check module and function names
- Look for errors in console output
- Verify module is importable

**Messages not being processed?**

- Wait 2-3 seconds after deployment
- Check container is running: `cluster.list_resources("Container")`
- Verify you're using the correct name

**Service not found?**

- Ensure service selector matches container names
- Use glob patterns like "my-workers-\*"
- Check service exists: `cluster.get_resource("Service", "name")`

## 🎊 Success!

You now know enough to:

- ✅ Start a cluster
- ✅ Deploy workers
- ✅ Send messages
- ✅ Create services
- ✅ Scale replicas
- ✅ Write custom workers

**Ready for more?** Check out:

- `python demo.py` - 7 comprehensive demos
- [QUICKREF.md](./QUICKREF.md) - Command reference
- [README.md](./README.md) - Full documentation

## 💡 Pro Tips

1. Always `time.sleep(2)` after deployment before sending messages
2. Use services instead of targeting containers directly
3. Check `cluster.list_resources("Container")` to see what's running
4. Workers should handle `None` gracefully (shutdown signal)
5. Use request-response when you need confirmation
6. Start simple, then add complexity

## 🚦 Next Steps

1. Run the examples: `python example.py`
2. Modify a worker in `workers.py`
3. Create your own worker function
4. Build a multi-stage pipeline
5. Experiment with scaling
6. Try different communication patterns

Happy orchestrating! 🎉
