#!/usr/bin/env bash
## I hate setup bash scripts...but this one sets up a local postgres cluster for the postgres cluster backend...quite handy...
export PGDATABASE=postgres
export PGUSER=postgres
export PGPASSWORD=mysecret
export PGPORT=5432
export PGHOST=localhost

docker run --name some-postgres -e POSTGRES_PASSWORD=$PGPASSWORD -e POSTGRES_USER=$PGUSER -e POSTGRES_DB=$PGDATABASE -p $PGPORT:5432 -d postgres
