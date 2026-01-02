DONE Container() should manage a podman container
DONE   podman container create --name=NAME --label com.example.key=value --detach --network=CLUSTER-NETWORK --entrypoint="..." --env a=1 b=2 image
  --expose=80
DONE on cluster init, create a network
DONE container should get a virtual IP
DONE DNS server that works with our API or is updated by ContainerController
N/A  on cluster init, create DNS server static container
Service() should manage TCP load balancer static Container that talks to our API to get selected Containers
TCP load balancer (TCP proxy)
REST API for our API
move name from metadata to spec
