# Usage

## Generating res files for plotting
The application allows you generate res file, that can be used in gnuplot for building some plot. It is possible for any
asteroid, any integers. But before this operation you *must load resonance table to database* [howto](./installation/local.md). 
For this operation you need aei files. For example you need generate this for asteroid *A490* with Jupiter and Saturn. Take a look.
```
docker run --link=some-resonances-data:postgres -v <path/to/aei/files>:/aei-files:ro -v `pwd`/res:/opt/resonances/res:rw\
    --env-file=<path/to/.env> 4xxi/resonances genres -p /aei-files -a 490 JUPITER SATURN
```
You must get `res` folder in you current working directory, because there is this option
```
-v `pwd`/res:/opt/resonances/res:rw
```
Maybe you have aei files inside tar.gz archive. You can point pass it to application. And let add filter by integers.
```
docker run --link=some-resonances-data:postgres -v <path/to/tar.gz>:/aei-401-501.tar.gz:ro -v `pwd`/res:/opt/resonances/res:rw\
    --env-file=<path/to/.env> 4xxi/resonances genres -p /aei-401-501.tar.gz -a 490 -i '5 -2 -2' JUPITER SATURN
```
This command will generate res file in res directory for asteroid A490 with Jupiter and Saturn.
*NOTE* If you run it on cluster remove option `--link=some-resonances-data:postgres`. Options for connection to database must be in `.env` file.

## Getting semi major axises of resonances.
Semi major axises will load by command `load-resonances` [howto](./installation/local.md). Application can show them.
Execute this.
```
docker run --link=some-resonances-data:postgres --env-file=<path/to/.env> 4xxi/resonances resonances
```
Last column contains semi major axises.
If you want to see semi major axises for resonance `5J -2S -2`. Execute this.
```
docker run --link=some-resonances-data:postgres --env-file=<path/to/.env> 4xxi/resonances resonances -i '5 -2 -2'
```
If want to see semi major axises and for planets Earth and Jupiter execute this.
```
docker run --link=some-resonances-data:postgres --env-file=<path/to/.env> 4xxi/resonances resonances \
    --first-planet=EARTHMOO --second-planet=JUPTER
```
*NOTE* If you run it on cluster remove option `--link=some-resonances-data:postgres`. Options for connection to database must be in `.env` file.

## Integration with custom catalog.
For processing integration the applications uses [catalog](http://hamilton.dm.unipi.it/~astdys2/catalogs/allnum.cat).
It is stores in container image and can be accessed by path `/opt/resonaces/catalog/allnum.cat`. If you want replace it by
your catalog, you can mount to this path your catalog and the application will use it. Take a look.

```
docker run --link=some-resonances-data:postgres --env-file=<path/to/.env> \
    -v <path/to/catalog_file>:/opt/resonances/catalog/allnum.cat:ro -v `pwd`/aei-files:/aei-files:rw \
    4xxi/resonances load-resonances --start=1 --stop=101 --file=/resonances --axis-swing=0.1 JUPITER SATURN
```
*NOTE* If you run it on cluster remove option `--link=some-resonances-data:postgres`. Options for connection to database must be in `.env` file.

## Compute librations remotely.
For any remote executing of commands you need activate environment of cluster manager by Docker Machine. If your cluster manager's name is
`swarm-manager`, then execute `eval $(docker-machine env --swarm swarm-manager)`. If have no cluster manager,
[see](./installation/remote.md). Now when you are in cluster manager, you can execute commands on cluster. For search librations
for any asteroid, Mars and Saturn you need aei files, if you have no aei files execute this command for first 100 asteroids.
```
docker run --env-file=<path/to/.env> -v /mnt/resonances-data/aei/:/aei-files:rw \
    4xxi/resonances calc --from-day=2451000.5 --to-day=38976000.5 --start=1 --stop=101 -p /aei-files
```
Currently we have 464622 asteroids. If you want integrate all asteroids, change `--stop=101` to `--stop=464622`
if you want start search libration on 3 nodes, for this you need execute same command three times with different options.
* `--start=1 --stop=150001`
* `--start=150001 --stop=300001`
* `--start=300001 --stop=464622`
The manager will assign tasks to nodes proportional itself.

Now you are ready for search librations.
```
docker run --env-file=<path/to/.env> -v /mnt/resonances-data/aei/:/aei-files:ro \
    4xxi/resonances find --start=-1 --stop=-1 -p /aei-files MARS SATURN
```
Options `--start=-1` and `--stop=-1` means that you want to get all asteroid, that has aei files inside directory
`/mnt/resonances-data/aei/`.
Unforunely for processing this operation parallel you must to know how many asteroids you have. Remember, that currently
we have 464622 asteroids. if you want start search libration on 3 nodes, for this you need execute same command three
times with different options
`--start` and `--stop`. In this case your options will be next
* `--start=1 --stop=150001`
* `--start=150001 --stop=300001`
* `--start=300001 --stop=464622`
The manager will assign tasks to nodes proportional itself.
