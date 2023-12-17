# DTSOAR - Digital Twin Security Orchestration, Automation and Response

## Neo4j/NeoDash

Our SOAR solution uses Neo4j/NeoDash as our database/dashboard.

To run Neo4j, first build the Docker Image:

```
docker run --name dtsoar_neo4j --detach --publish=7474:7474 --publish=7687:7687 --volume=$HOME/neo4j/data:/data neo4j
```

Then run the Docker Container:

```
docker start -a dtsoar_neo4j
```

Go to http://localhost:7474/

Initialize neo4j with the default username and password, and change the password to the new passowrd:

```
Username: neo4j
Password: neo4j
New password: soar-neo4j
```


You can run NeoDash by visiting http://neodash.graphapp.io/

Make sure you are using the http procotol, and not the secure protocol.

## Configuring Mininet

pass