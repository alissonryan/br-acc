MATCH (e) WHERE elementId(e) = $element_id
RETURN e, labels(e) AS entity_labels
LIMIT 1
