# Local

## Setup data container
* Pull docker images `amarkov/resonances:v4` and `amarkov/resonances-data:v3`.
* Run data container by command `docker run -d --name some-resonances-data amarkov/resonances-data:v3`
* For more convinient work you can create `.env` file with next contents ```RESONANCES_DB_USER=postgres RESONANCES_DB_NAME=resonances```

## Run computing.

### Integration.
That's all. Now you can run some computions via application.
For example you want get aei files.
```
docker run --link=some-resonances-data:postgres --env-file=<path/to/.env> -v `pwd`/aei-files:/aei-files:rw \
    amarkov/resonances:v4 calc --from-day=2451000.5 --to-day=38976000.5 --start=1 --stop=101 -p /aei-files
```
Take a look on your current directory. You should see new directory with name `aei-files`. There are you aei files for asteroids from 1 to 100.
Because filesystem of container is separated from your, you must mount volume to container, if you want to get result files of integration.
Our output directory is `/aei-files`, we pointed it here `-p /aei-files` and also it is mount point inside container for our folder `aei-files`
in current directory. For description of the command type `docker run --rm amarkov/resonances:v4 calc --help`

### Load resonance table.
Now you can run loading integers, satisfying D'Alambert rule for first 100 asteroids and planets Jupiter and Saturn.
For this operation you need file with this integers.
```
docker run --link=some-resonances-data:postgres --env-file=<path/to/.env> -v <path/to/file/with/integers>:/integers:ro \
    amarkov/resonances:v4 load-resonances --start=1 --stop=101 --file=/resonances --axis-swing=0.1 JUPITER SATURN
```
Here you mounted file to container and pointed it in application's options. Option `--axis-swing` says about possible swing for
comparation between axis from file and axis from AstDys catalog. By default image has catalog from
http://hamilton.dm.unipi.it/~astdys2/catalogs/allnum.cat. If you want to point your own catalog you must mount it too. Look.
```
docker run --link=some-resonances-data:postgres --env-file=<path/to/.env> -v <path/to/file/with/integers>:/integers:ro \
    -v <path/to/catalog_file>:/opt/resonances/catalog/allnum.cat:ro \
    amarkov/resonances:v4 load-resonances --start=1 --stop=101 --file=/resonances --axis-swing=0.1 JUPITER SATURN
```
For more details about this command type `docker run --rm amarkov/resonances:v4 load-resonances --help`

### Show resonance table.
When you loaded resonances to database. You want to see them probably. You can do this.
```
docker run --link=some-resonances-data:postgres --env-file=<path/to/.env> amarkov/resonances:v4 resonances
```
Maybe you want to see resonances only for first 10 asteroids. Look.
```
docker run --link=some-resonances-data:postgres --env-file=<path/to/.env> amarkov/resonances:v4 resonances --start=1 --stop=11
```
Or if you want to see resonances with that have first integer greated than 1 and any second and third integers. Look.
```
docker run --link=some-resonances-data:postgres --env-file=<path/to/.env> amarkov/resonances:v4 resonances -i '>1 * *'
```
Probably you don't see all resaonces, it happens because by default table contains only 100 entries.
You can point option `--limit=1000`, you will 1000 entries. For details type `docker run --rm amarkov/resonances:v4 resonances --help`

### Search librations.
Now, when you have aei files and resonance table, you can compute resonance phases and find libration in them.
Any libration, that will be found, will be saved in database.  For this operation you need to mount folder with aei files. Look.
```
docker run --link=some-resonances-data:postgres --env-file=<path/to/.env> -v `pwd`/aei-files:/aei-files:ro \
    amarkov/resonances:v4 find --start=1 --stop=101 -p /aei-files JUPITER SATURN
```
Or you can find librations for all asteroid, that represented by aei files. You just need to change interval options.
```
docker run --link=some-resonances-data:postgres --env-file=<path/to/.env> -v `pwd`/aei-files:/aei-files:ro \
    amarkov/resonances:v4 find --start=-1 --stop=-1 -p /aei-files JUPITER SATURN
```
For details type `docker run --rm amarkov/resonances:v4 find --help`

### Show librations.
Now you can see librations by this command.
```
docker run --link=some-resonances-data:postgres --env-file=<path/to/.env> amarkov/resonances:v4 librations
```
For filtering by planets add options `--first-planet=JUPITER --second-planet=SATURN`. For filtering by asteroid number
add options `--start=1 --stop=11`. This command is like a command for showing resonance table. By default it shows only
100 entries. And as that command, it has options `--limit` and `--offset`.
For details type `docker run --rm amarkov/resonances:v4 librations --help`
