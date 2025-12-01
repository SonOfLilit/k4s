# 🎯 Kubernetes-like Orchestration System

Welcome! This project implements Kubernetes orchestration patterns using Python threads.

## 🚀 Quick Start (30 seconds)

```bash
python example.py
```

## 📚 Documentation

Start with one of these based on your goal:

### 🎓 Learning Path

1. **[GETTING_STARTED.md](./GETTING_STARTED.md)** ← Start here!

   - What is this project?
   - 5-minute tutorial
   - Your first example

2. **[README.md](./README.md)**

   - Complete documentation
   - Architecture overview
   - API reference

3. **[QUICKREF.md](./QUICKREF.md)**
   - Quick reference
   - Common operations
   - Code snippets

### 🏗️ Architecture & Design

4. **[ARCHITECTURE.md](./ARCHITECTURE.md)**

   - System diagrams
   - Component overview
   - Communication patterns

5. **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)**

   - High-level overview
   - Design decisions
   - Feature matrix

6. **[INDEX.md](./INDEX.md)**
   - Complete file listing
   - Project statistics
   - Navigation guide

## 💻 Code Files

### Run These

- **example.py** - Interactive demo (run this first!)
- **demo.py** - Comprehensive demo suite (7 examples)

### Core Implementation

- **k4s.py** - Main orchestration system
- **workers.py** - Example worker functions

## 🎯 What Should I Read?

**"I just want to see it work"**
→ Run `python example.py`

**"I want to understand the basics"**
→ Read [GETTING_STARTED.md](./GETTING_STARTED.md)

**"I want complete documentation"**
→ Read [README.md](./README.md)

**"I want to see code examples"**
→ Check [demo.py](./demo.py) and [QUICKREF.md](./QUICKREF.md)

**"I want to understand the architecture"**
→ Read [ARCHITECTURE.md](./ARCHITECTURE.md)

**"I want to see everything"**
→ Check [INDEX.md](./INDEX.md)

## 🎓 Core Concepts

This system has **3 resource types**:

1. **Container** - A worker thread that runs a function
2. **ReplicaSet** - Manages multiple container replicas
3. **Service** - Load balances across containers

And **3 controllers** that automatically:

- Start/stop containers
- Scale replicas
- Validate services

## 🎮 Try It Now

```python
from k4s import KubernetesCluster
import time

# Start cluster
cluster = KubernetesCluster()
cluster.start()

# Deploy a worker
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
time.sleep(2)

# Send a message
cluster.api.send_to_container("greeter", "World")

# Clean up
cluster.stop()
```

## 📊 Features

✅ Container deployment  
✅ ReplicaSets with auto-scaling  
✅ Services with load balancing  
✅ Fire-and-forget messaging  
✅ Request-response pattern  
✅ Inter-container communication  
✅ Dynamic scaling  
✅ YAML resource definitions  
✅ Controller reconciliation loops  
✅ Processing pipelines

## 🛠️ Requirements

- Python 3.7+
- No external dependencies (standard library only!)

## 📁 Project Structure

```
├── START_HERE.md           ← You are here
├── GETTING_STARTED.md      ← Begin here
├── README.md               ← Main documentation
├── QUICKREF.md             ← Quick reference
├── ARCHITECTURE.md         ← System design
├── PROJECT_SUMMARY.md      ← Overview
├── INDEX.md                ← File listing
├── k4s.py            ← Core system
├── workers.py             ← Example workers
├── example.py             ← Quick demo
└── demo.py                ← Full demo suite
```

## 🎯 Next Steps

1. Run `python example.py`
2. Read [GETTING_STARTED.md](./GETTING_STARTED.md)
3. Try modifying [workers.py](./workers.py)
4. Create your own worker function
5. Experiment with [demo.py](./demo.py)

## 🎊 Have Fun!

This is a learning project. Feel free to:

- Modify the code
- Add new features
- Break things and fix them
- Share what you build

Questions? Read the docs above or explore the code!

**Happy orchestrating!** 🚀
