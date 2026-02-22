MATCH (u:User {id: $user_id})-[:OWNS]->(i:Investigation {id: $investigation_id})
MATCH (i)-[r:INCLUDES]->(e {id: $entity_id})
DELETE r
RETURN 1 AS deleted
