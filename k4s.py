"""
Kubernetes-like orchestration system for Python threads.

This demo implements:
- Resource types: Container, ReplicaSet, Service
- Controllers for each resource type
- In-memory resource tree
- Inter-container communication via queues
- External API for interacting with containers
"""

import threading
import queue
import yaml
import fnmatch
import random
import importlib
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import Future
from enum import Enum


class ResourceType(Enum):
    CONTAINER = "container"
    REPLICASET = "replicaset"
    SERVICE = "service"


@dataclass
class Resource:
    """Base resource class"""

    kind: str
    name: str
    spec: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContainerResource(Resource):
    """Container resource definition"""

    def __init__(
        self, name: str, spec: Dict[str, Any], metadata: Dict[str, Any] = None
    ):
        super().__init__(
            kind="Container", name=name, spec=spec, metadata=metadata or {}
        )

    @property
    def module_name(self) -> str:
        return self.spec.get("module")

    @property
    def function_name(self) -> str:
        return self.spec.get("function")

    @property
    def parameters(self) -> Dict[str, Any]:
        return self.spec.get("parameters", {})


@dataclass
class ReplicaSetResource(Resource):
    """ReplicaSet resource definition"""

    def __init__(
        self, name: str, spec: Dict[str, Any], metadata: Dict[str, Any] = None
    ):
        super().__init__(
            kind="ReplicaSet", name=name, spec=spec, metadata=metadata or {}
        )

    @property
    def container_name(self) -> str:
        return self.spec.get("container")

    @property
    def replicas(self) -> int:
        return self.spec.get("replicas", 1)


@dataclass
class ServiceResource(Resource):
    """Service resource definition"""

    def __init__(
        self, name: str, spec: Dict[str, Any], metadata: Dict[str, Any] = None
    ):
        super().__init__(kind="Service", name=name, spec=spec, metadata=metadata or {})

    @property
    def selector(self) -> str:
        return self.spec.get("selector")


class Container:
    """Running container (thread) instance"""

    def __init__(
        self,
        name: str,
        module_name: str,
        function_name: str,
        parameters: Dict[str, Any],
        api_client: "KubernetesAPI",
    ):
        self.name = name
        self.module_name = module_name
        self.function_name = function_name
        self.parameters = parameters
        self.api_client = api_client
        self.input_queue = queue.Queue()
        self.thread = None
        self.running = False

    def start(self):
        """Start the container thread"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the container thread"""
        self.running = False
        self.input_queue.put(None)  # Signal to stop
        if self.thread:
            self.thread.join(timeout=5)

    def _run(self):
        """Run the container function"""
        try:
            # Dynamically import the module and get the function
            module = importlib.import_module(self.module_name)
            func = getattr(module, self.function_name)

            # Run the function with parameters and input queue
            func(
                input_queue=self.input_queue,
                api_client=self.api_client,
                **self.parameters,
            )
        except Exception as e:
            print(f"Container {self.name} error: {e}")
        finally:
            self.running = False


class ResourceStore:
    """In-memory resource tree"""

    def __init__(self):
        self.resources: Dict[str, Dict[str, Resource]] = {
            "Container": {},
            "ReplicaSet": {},
            "Service": {},
        }
        self.lock = threading.RLock()

    def create(self, resource: Resource) -> Resource:
        """Create a resource"""
        with self.lock:
            if resource.name in self.resources[resource.kind]:
                raise ValueError(f"{resource.kind} {resource.name} already exists")
            self.resources[resource.kind][resource.name] = resource
            return resource

    def get(self, kind: str, name: str) -> Optional[Resource]:
        """Get a resource by kind and name"""
        with self.lock:
            return self.resources.get(kind, {}).get(name)

    def list(self, kind: str) -> List[Resource]:
        """List all resources of a kind"""
        with self.lock:
            return list(self.resources.get(kind, {}).values())

    def update(self, resource: Resource) -> Resource:
        """Update a resource"""
        with self.lock:
            if resource.name not in self.resources[resource.kind]:
                raise ValueError(f"{resource.kind} {resource.name} does not exist")
            self.resources[resource.kind][resource.name] = resource
            return resource

    def delete(self, kind: str, name: str) -> bool:
        """Delete a resource"""
        with self.lock:
            if name in self.resources.get(kind, {}):
                del self.resources[kind][name]
                return True
            return False


class Controller:
    """Base controller class"""

    def __init__(self, store: ResourceStore):
        self.store = store
        self.running = False
        self.thread = None

    def start(self):
        """Start the controller"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._reconcile_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the controller"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _reconcile_loop(self):
        """Main reconciliation loop"""
        while self.running:
            try:
                self.reconcile()
            except Exception as e:
                print(f"Controller {self.__class__.__name__} error: {e}")
            time.sleep(1)

    def reconcile(self):
        """Reconcile desired state with actual state"""
        raise NotImplementedError


class ContainerController(Controller):
    """Controller for Container resources"""

    def __init__(self, store: ResourceStore, api_client: "KubernetesAPI"):
        super().__init__(store)
        self.api_client = api_client
        self.containers: Dict[str, Container] = {}
        self.lock = threading.RLock()

    def reconcile(self):
        """Ensure containers match their resource definitions"""
        with self.lock:
            # Get desired containers
            desired_containers = {r.name: r for r in self.store.list("Container")}

            # Stop and remove containers that shouldn't exist
            for name in list(self.containers.keys()):
                if name not in desired_containers:
                    print(f"Stopping container: {name}")
                    self.containers[name].stop()
                    del self.containers[name]

            # Create or update containers
            for name, resource in desired_containers.items():
                if name not in self.containers:
                    print(f"Starting container: {name}")
                    container = Container(
                        name=name,
                        module_name=resource.module_name,
                        function_name=resource.function_name,
                        parameters=resource.parameters,
                        api_client=self.api_client,
                    )
                    container.start()
                    self.containers[name] = container

    def get_container(self, name: str) -> Optional[Container]:
        """Get a running container by name"""
        with self.lock:
            return self.containers.get(name)

    def list_containers(self) -> List[Container]:
        """List all running containers"""
        with self.lock:
            return list(self.containers.values())


class ReplicaSetController(Controller):
    """Controller for ReplicaSet resources"""

    def reconcile(self):
        """Ensure replica containers match ReplicaSet definitions"""
        for replicaset in self.store.list("ReplicaSet"):
            # Get the template container
            template = self.store.get("Container", replicaset.container_name)
            if not template:
                print(
                    f"ReplicaSet {replicaset.name}: template container {replicaset.container_name} not found"
                )
                continue

            # Find existing replicas
            prefix = f"{replicaset.name}-"
            existing_replicas = [
                r
                for r in self.store.list("Container")
                if r.name.startswith(prefix)
                and r.metadata.get("replicaset") == replicaset.name
            ]

            current_count = len(existing_replicas)
            desired_count = replicaset.replicas

            # Scale up
            if current_count < desired_count:
                for i in range(current_count, desired_count):
                    replica_name = f"{replicaset.name}-{i}"
                    print(f"Creating replica: {replica_name}")
                    replica = ContainerResource(
                        name=replica_name,
                        spec=template.spec.copy(),
                        metadata={"replicaset": replicaset.name},
                    )
                    self.store.create(replica)

            # Scale down
            elif current_count > desired_count:
                for i in range(desired_count, current_count):
                    replica_name = f"{replicaset.name}-{i}"
                    print(f"Deleting replica: {replica_name}")
                    self.store.delete("Container", replica_name)


class ServiceController(Controller):
    """Controller for Service resources - mainly for validation"""

    def reconcile(self):
        """Validate service selectors"""
        for service in self.store.list("Service"):
            # Just validate that the selector matches at least one container
            containers = self.store.list("Container")
            matches = [
                c for c in containers if fnmatch.fnmatch(c.name, service.selector)
            ]
            if not matches:
                print(
                    f"Warning: Service {service.name} selector '{service.selector}' matches no containers"
                )


class KubernetesAPI:
    """API for interacting with containers"""

    def __init__(self, container_controller: ContainerController, store: ResourceStore):
        self.container_controller = container_controller
        self.store = store

    def send_to_container(
        self, container_name: str, value: Any, expect_response: bool = False
    ) -> Optional[Future]:
        """Send a value to a container's queue"""
        container = self.container_controller.get_container(container_name)
        if not container:
            raise ValueError(f"Container {container_name} not found")

        if expect_response:
            future = Future()
            container.input_queue.put((value, future))
            return future
        else:
            container.input_queue.put(value)
            return None

    def send_to_service(
        self, service_name: str, value: Any, expect_response: bool = False
    ) -> Optional[Future]:
        """Send a value to a random container matched by the service"""
        service = self.store.get("Service", service_name)
        if not service:
            raise ValueError(f"Service {service_name} not found")

        # Find containers matching the service selector
        containers = self.container_controller.list_containers()
        matches = [c for c in containers if fnmatch.fnmatch(c.name, service.selector)]

        if not matches:
            raise ValueError(f"No containers match service {service_name}")

        # Random load balancing
        container = random.choice(matches)

        if expect_response:
            future = Future()
            container.input_queue.put((value, future))
            return future
        else:
            container.input_queue.put(value)
            return None


class KubernetesCluster:
    """Main cluster orchestrator"""

    def __init__(self):
        self.store = ResourceStore()
        self.container_controller = None
        self.replicaset_controller = None
        self.service_controller = None
        self.api = None

    def start(self):
        """Start the cluster"""
        # Initialize API
        self.container_controller = ContainerController(self.store, None)
        self.api = KubernetesAPI(self.container_controller, self.store)
        self.container_controller.api_client = self.api

        # Initialize controllers
        self.replicaset_controller = ReplicaSetController(self.store)
        self.service_controller = ServiceController(self.store)

        # Start controllers
        self.replicaset_controller.start()
        self.container_controller.start()
        self.service_controller.start()

        print("Cluster started")

    def stop(self):
        """Stop the cluster"""
        if self.container_controller:
            self.container_controller.stop()
        if self.replicaset_controller:
            self.replicaset_controller.stop()
        if self.service_controller:
            self.service_controller.stop()
        print("Cluster stopped")

    def apply_yaml(self, yaml_content: str):
        """Apply a YAML resource definition"""
        docs = yaml.safe_load_all(yaml_content)

        for doc in docs:
            if not doc:
                continue

            kind = doc.get("kind")
            name = doc.get("metadata", {}).get("name")
            spec = doc.get("spec", {})
            metadata = doc.get("metadata", {})

            if not kind or not name:
                print("Invalid resource: missing kind or name")
                continue

            # Create resource object
            if kind == "Container":
                resource = ContainerResource(name, spec, metadata)
            elif kind == "ReplicaSet":
                resource = ReplicaSetResource(name, spec, metadata)
            elif kind == "Service":
                resource = ServiceResource(name, spec, metadata)
            else:
                print(f"Unknown resource kind: {kind}")
                continue

            # Create or update
            try:
                if self.store.get(kind, name):
                    self.store.update(resource)
                    print(f"Updated {kind}: {name}")
                else:
                    self.store.create(resource)
                    print(f"Created {kind}: {name}")
            except Exception as e:
                print(f"Error applying resource: {e}")

    def delete_resource(self, kind: str, name: str):
        """Delete a resource"""
        if self.store.delete(kind, name):
            print(f"Deleted {kind}: {name}")
        else:
            print(f"{kind} {name} not found")

    def get_resource(self, kind: str, name: str) -> Optional[Resource]:
        """Get a resource"""
        return self.store.get(kind, name)

    def list_resources(self, kind: str) -> List[Resource]:
        """List resources"""
        return self.store.list(kind)
