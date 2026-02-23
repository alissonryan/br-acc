MATCH (u:User {id: $user_id})-[:OWNS]->(i:Investigation {id: $investigation_id})
MATCH (e) WHERE e.cpf = $entity_id OR e.cnpj = $entity_id
            OR e.contract_id = $entity_id OR e.sanction_id = $entity_id
            OR e.amendment_id = $entity_id OR elementId(e) = $entity_id
MERGE (i)-[:INCLUDES]->(e)
RETURN i.id AS investigation_id,
       coalesce(e.cpf, e.cnpj, e.contract_id, e.sanction_id, e.amendment_id, elementId(e)) AS entity_id
