MATCH (u:User {id: $user_id})-[:OWNS]->(i:Investigation {id: $investigation_id})
MATCH (i)-[r:INCLUDES]->(e)
WHERE e.cpf = $entity_id OR e.cnpj = $entity_id
   OR e.contract_id = $entity_id OR e.sanction_id = $entity_id
   OR e.amendment_id = $entity_id OR elementId(e) = $entity_id
DELETE r
RETURN 1 AS deleted
