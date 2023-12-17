// This file includes simple tests using the Cypher language.

// SOAR DPS Response
CREATE (soar:SOAR)-[:RESPONSE]->(response:RESPONSE{ip:"10.0.0.6", reason:"No Value", response:"Disable Communication"})

// Remove SOAR Responses
MATCH (s:SOAR)-[r:RESPONSE]->(resp:RESPONSE)
DELETE s, r, resp

// Put DPS in Quarantine
MATCH (host:Component{ip:"10.0.0.6"}), (quarantine:Quarantine{name:"Quarantine"})
CREATE (host)-[:QUARANTINE]->(quarantine)

// Remove DPS from Quarantine
MATCH (host:Component{ip:"10.0.0.6"})-[r:QUARANTINE]->()
DELETE r

// Remove all from Quarantine
MATCH ()-[r:QUARANTINE]->()
DELETE r

// Receive data of DPS from Digital Twin
MATCH (host:Component{ip:"10.0.0.6"})
CREATE (host)-[:DATA]->(digital_twin:Digital_Twin{data:"2844"})

// Remove all Digital Twin information
MATCH ()-[r:DATA]->(n:Digital_Twin)
DELETE r, n

// Drop database
MATCH (n)
DETACH DELETE n