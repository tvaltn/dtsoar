# DTSOAR - Digital Twin Security Orchestration, Automation and Response

## Neo4j/NeoDash

Our SOAR solution uses Neo4j/NeoDash as our database/dashboard.
To run Neo4j, simply run this docker image:

```
docker run --name dtsoar_neodash --publish=7474:7474 --publish=7687:7687 --volume=$HOME/neo4j/data:/data neo4j
```

You can run NeoDash by visiting http://neodash.graphapp.io/
Make sure you are using the http procotol, and not the secure protocol.

## Configuring Mininet

pass