# Remote

## Prerequesties
This section discover setup the application on cluster. Performance of the application was
tested on Digitial Ocean, because Docker Machine has driver for setup Docker on node and it just works.
You must have at least 3 nodes. For setup the cluster will be used Docker Swarm.

* First node will be data server. It will contain database.
* Second node will be manager of cluster. It will pass to nodes tasks, that we will assign to it.
* Third node will be worker. It will take task from cluster manager and process them.

Also you need Docker Machine on your local machine. It allows to you manage you cluster more convinient.

## Setup nodes.
Below we suppose that you have API key from Digital Ocean. And you have deployed your ssh keys
on your nodes.

### Data node.
For setup Docker on node just type
```
docker-machine create -d digitalocean --digitalocean-access-token=<your_token> \
    --digitalocean-image=ubuntu-16-04-x64 --digitalocean-size=512mb --digitalocean-region=fra1\
    datanode
```
Docker has been installed. Now you need setup data container on it. Before it you must connect to this Docker host.
Type this. `eval $(docker-machine env datanode)`. Now you can pull image and start it.
Type `docker run -d --name some-resonances-data -p 5432:5432 amarkov/resonances-data:v3`. Take a look, you forwarded port 5432.
It means, that database is available for connection from out. Setup password for postgres user for preventing sneakers.
And now create `.env` file on your local machine with next contents.
```
RESONANCES_DB_USER=postgres
RESONANCES_DB_NAME=resonances
POSTGRES_ENV_POSTGRES_PASSWORD=<youpassword>
POSTGRES_PORT_5432_TCP_ADDR=<ip_address_of_data_node>
```

### Cluster manager.
Before setup cluster you should choose swarm discovery. In documentation will be showed how to use swarm discovery Docker Hub.
But Docker's authors don't recommend it for production environment.

First for all we need to generate the token. You can generate on local machine. `docker run --rm swarm create` it will show you
swarm token. You will use it for creating any machine, which must be in cluster.

Now you can create cluster manager. Type command.
```
docker-machine create -d digitalocean --digitalocean-access-token=<your_token> \
    --digitalocean-image=ubuntu-14-04-x64 --digitalocean-size=512mb --digitalocean-region=fra1\
    --swarm --swarm-master --swarm-discovery token://<swarm_token> swarm-manager
```

### Node.
For setup node you can input
```
docker-machine create -d digitalocean --digitalocean-access-token=<your_token>\
    --digitalocean-image=ubuntu-14-04-x64 --digitalocean-size=512mb --digitalocean-region=fra1\
    --swarm --swarm-discovery token://<swarm_token> node1
```
That's all. Node has been created and has been included to cluster.

## Run commands.
Now you can run computing on the cluster. You need activate cluster environment.
Do it `eval $(docker-machine env --swarm swarm-manager)`. You are under cluster manager environment.
Any docker command, that you will execute, it will be executed by cluster manager. Any volume, that you will mount, will be mounted
on node, that will be assigned for resolving passed task. In this section will be showed only commands starting computing.
Details of them was discovered in [local.md](./local.md). But they are different from samples from [local.md](./local.md).

### Intergration
```
docker run --env-file=<path/to/.env> -v `pwd`/aei-files:/aei-files:rw \
    amarkov/resonances:v4 calc --from-day=2451000.5 --to-day=38976000.5 --start=1 --stop=101 -p /aei-files
```

### Load resonance table.
```
docker run --env-file=<path/to/.env> -v <path/to/file/with/integers>:/integers:ro \
    amarkov/resonances:v4 load-resonances --start=1 --stop=101 --file=/resonances --axis-swing=0.1 JUPITER SATURN
```

### Show resonance table.
```
docker run --link=some-resonances-data:postgres --env-file=<path/to/.env> amarkov/resonances:v4 resonances
```

### Search librations.
```
docker run --env-file=<path/to/.env> -v `pwd`/aei-files:/aei-files:ro \
    amarkov/resonances:v4 find --from-day=2451000.5 --to-day=38976000.5 --start=1 --stop=101 -p /aei-files JUPITER SATURN
```

### Show librations.
```
docker run --env-file=<path/to/.env> amarkov/resonances:v4 librations
```

## Multiple worker nodes.
Because cluster means, that you use several machines for getting your purpose faster. But if you use several workers,
it's very possible, that you want transver files between them. NFS was tested for solving this problem. You can install
package `nfs-kernel-server` on your data node and package `nfs-common` for worker.

### Setup NFS server.
* Login over ssh to your data node.
* Install `nfs-kernel-server`
* Make file `/etc/exports` if it doesn't exist.
* Put to file `/etc/exports` following content.
```
/srv/resonances-data     <node1_ip>(rw,fsid=root,no_subtree_check,no_root_squash)
/srv/resonances-data     <node2_ip>(rw,fsid=root,no_subtree_check,no_root_squash)
...
/srv/resonances-data     <nodeN_ip>(rw,fsid=root,no_subtree_check,no_root_squash)
```
* Execute command `exportfs -rav`
* Restart nfs-kernel-server. In Ubuntu it can be done by command `service nfs-kernel-server start`.

### Setup nfs client.
This steps must be done on every node.
* Login over ssh to your node.
* Install `nfs-common`
* Mount nfs directory to `/mnt/resonances-data/`

### Example with integration.
Now, when you mounted NFS directory, you can mount this folder to container. Take a look.
```
docker run --env-file=<path/to/.env> -v /mnt/resonances-data/aei/:/aei-files:rw \
    amarkov/resonances:v4 calc --from-day=2451000.5 --to-day=38976000.5 --start=1 --stop=101 -p /aei-files
```
And after this command all aei files will be in /mnt/resonances-data/aei/ and NFS will share them to server and another clients.
