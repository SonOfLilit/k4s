Container() should manage a podman container
  podman container create --name=NAME --label com.example.key=value --detach --network=CLUSTER-NETWORK --dns=X.X.X.X --entrypoint="..." --env a=1 b=2 image
  --expose=80
on cluster init, create a network
container should get a virtual IP
DNS server that works with our API or is updated by ContainerController
on cluster init, create DNS server static container
Service() should manage TCP load balancer static Container that talks to our API to get selected Containers
TCP load balancer (TCP proxy)
REST API for our API
