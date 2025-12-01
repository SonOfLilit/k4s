# Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                            │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                   Resource Store (In-Memory)                │    │
│  │                                                              │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │    │
│  │  │  Containers  │  │ ReplicaSets  │  │   Services   │    │    │
│  │  │              │  │              │  │              │    │    │
│  │  │ echo-1       │  │ proc-rs      │  │ calculator   │    │    │
│  │  │ calc-0       │  │ replicas: 3  │  │ selector:*   │    │    │
│  │  │ calc-1       │  │              │  │              │    │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      Controllers                              │  │
│  │                                                                │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │  │
│  │  │  Container   │  │  ReplicaSet  │  │   Service    │      │  │
│  │  │  Controller  │  │  Controller  │  │  Controller  │      │  │
│  │  │              │  │              │  │              │      │  │
│  │  │ • Start/Stop │  │ • Create     │  │ • Validate   │      │  │
│  │  │   Containers │  │   Replicas   │  │   Selectors  │      │  │
│  │  │ • Monitor    │  │ • Scale Up   │  │              │      │  │
│  │  │   Health     │  │ • Scale Down │  │              │      │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │  │
│  │         ↕                 ↕                 ↕                 │  │
│  └─────────┼─────────────────┼─────────────────┼────────────────┘  │
│            ↓                 ↓                 ↓                    │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              Running Containers (Threads)                   │   │
│  │                                                              │   │
│  │  ┏━━━━━━━━━━━━┓  ┏━━━━━━━━━━━━┓  ┏━━━━━━━━━━━━┓         │   │
│  │  ┃ Container  ┃  ┃ Container  ┃  ┃ Container  ┃         │   │
│  │  ┃  echo-1    ┃  ┃  calc-0    ┃  ┃  calc-1    ┃         │   │
│  │  ┃            ┃  ┃            ┃  ┃            ┃         │   │
│  │  ┃ ┌────────┐ ┃  ┃ ┌────────┐ ┃  ┃ ┌────────┐ ┃         │   │
│  │  ┃ │ Queue  │ ┃  ┃ │ Queue  │ ┃  ┃ │ Queue  │ ┃         │   │
│  │  ┃ └────────┘ ┃  ┃ └────────┘ ┃  ┃ └────────┘ ┃         │   │
│  │  ┃     ↓      ┃  ┃     ↓      ┃  ┃     ↓      ┃         │   │
│  │  ┃ ┌────────┐ ┃  ┃ ┌────────┐ ┃  ┃ ┌────────┐ ┃         │   │
│  │  ┃ │Function│ ┃  ┃ │Function│ ┃  ┃ │Function│ ┃         │   │
│  │  ┃ │ Worker │ ┃  ┃ │ Worker │ ┃  ┃ │ Worker │ ┃         │   │
│  │  ┃ └────────┘ ┃  ┃ └────────┘ ┃  ┃ └────────┘ ┃         │   │
│  │  ┗━━━━━━━━━━━━┛  ┗━━━━━━━━━━━━┛  ┗━━━━━━━━━━━━┛         │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │                   Kubernetes API                           │    │
│  │                                                             │    │
│  │  • send_to_container(name, value, expect_response)        │    │
│  │  • send_to_service(name, value, expect_response)          │    │
│  │                                                             │    │
│  └───────────────────────────────────────────────────────────┘    │
│                              ↑                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                    ┌──────────┴─────────┐
                    │   External API     │
                    │   (Client Code)    │
                    └────────────────────┘


Communication Patterns
══════════════════════

1. Fire-and-Forget:
   Client → API → Container Queue → Worker Function

2. Request-Response:
   Client → API → Container Queue → Worker Function
                                      ↓
   Client ← Future.result() ←────── Future.set_result()

3. Inter-Container:
   Worker A → API → Worker B Queue → Worker B Function

4. Service Load Balancing:
   Client → Service → Random Container (from selector match)


Controller Reconciliation Loop
═══════════════════════════════

┌──────────────────────────────────────┐
│ 1. Read Desired State                │
│    (from Resource Store)              │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ 2. Read Actual State                 │
│    (running containers, etc.)        │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ 3. Calculate Diff                    │
│    (what needs to change?)           │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ 4. Take Actions                      │
│    • Start new containers            │
│    • Stop excess containers          │
│    • Create missing replicas         │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ 5. Sleep (1 second)                  │
└──────────────┬───────────────────────┘
               ↓
               └────────────┐
                            │ (loop)
                            └──> Back to step 1


Resource Lifecycle
══════════════════

YAML Applied
     ↓
Resource Created in Store
     ↓
Controller Detects New Resource
     ↓
Controller Takes Action:
  • Container → Start Thread
  • ReplicaSet → Create Container Resources
  • Service → No action (used for routing)
     ↓
Running State
     ↓
Resource Deleted from Store
     ↓
Controller Detects Missing Resource
     ↓
Controller Takes Action:
  • Container → Stop Thread
  • ReplicaSet → Delete Container Resources
     ↓
Terminated
```
