MATCH (e) WHERE e.cpf = $id OR e.cnpj = $id
            OR e.contract_id = $id OR e.sanction_id = $id
            OR e.amendment_id = $id OR elementId(e) = $id
RETURN e, labels(e) AS entity_labels
LIMIT 1
