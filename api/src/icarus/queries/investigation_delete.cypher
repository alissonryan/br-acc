MATCH (u:User {id: $user_id})-[:OWNS]->(i:Investigation {id: $id})
DETACH DELETE i
RETURN 1 AS deleted
