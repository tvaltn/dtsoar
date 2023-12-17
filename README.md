# DTSOAR - Digital Twin Security Orchestration, Automation and Response

## Neo4j/NeoDash

Our SOAR solution uses Neo4j/NeoDash as our database/dashboard.

### Neo4j

To run Neo4j, first build the Docker Image:

```
docker run --name dtsoar_neo4j --detach --publish=7474:7474 --publish=7687:7687 --volume=$HOME/neo4j/data:/data neo4j
```

Then run the Docker Container:

```
docker start -a dtsoar_neo4j
```

Go to http://localhost:7474/

Initialize neo4j with the default username and password, and change the password to the new password:

```
Username: neo4j
Password: neo4j
New password: soar-neo4j
```

To initialize the database:

1. Find the data.cypher file from the data folder in this repo.
2. Copy all the contents and paste them into the query box in Neo4j browser on http://localhost:7474/

### NeoDash

You can run NeoDash by going to http://neodash.graphapp.io/

Make sure you are using the http procotol, and not the secure protocol.

To initialize the dashboard:

1. Find the dashboard.json file from the data folder in this repo.
2. Inside NeoDash, after you have created a New Dashboard, click on the left panel on the page.
3. Click on the plus sign, and import dashboard.json.

## Configuring Mininet

pass