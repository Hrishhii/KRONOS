import logging
from backend.graph_engine_connector import db
from backend.graph_engine_schema import resolve_alias

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Cleanup")

def merge_nodes():
    driver = db.get_driver()
    if not driver:
        print("Neo4j not connected.")
        return

    # 1. Fetch all nodes
    query = """
    MATCH (n)
    WHERE n:Country OR n:Leader OR n:Organization OR n:Asset OR n:Technology OR n:Infrastructure OR n:Company OR n:Event OR n:Indicator OR n:Policy OR n:MilitaryBase OR n:Location
    RETURN id(n) as internal_id, n.id as id, n.name as name, labels(n)[0] as label
    """
    results = db.execute_read(query)
    
    id_map = {}
    for row in results:
        canon_id = resolve_alias(row['name'], row['label'])
        if canon_id not in id_map: id_map[canon_id] = []
        id_map[canon_id].append(row)

    TYPES = ["ALLIED_WITH", "IN_CONFLICT_WITH", "SANCTIONS", "EXPORTS", "IMPORTS", "DEPENDS_ON", "LEADS", "INVESTS_IN", "THREATENS", "HOSTS", "TRANSITS_THROUGH", "MEMBER_OF", "PART_OF", "TARGETS", "SIGNED"]

    for canon_id, occurrences in id_map.items():
        if len(occurrences) > 1 or (occurrences[0]['id'] != canon_id):
            logger.info(f"Merging {len(occurrences)} nodes to {canon_id}")
            master = sorted(occurrences, key=lambda x: (x['id'] != canon_id, len(x['name'])))[0]
            
            db.execute_write("MATCH (n) WHERE id(n) = $int_id SET n.id = $canon_id", {"int_id": master['internal_id'], "canon_id": canon_id})
            
            for other in occurrences:
                if other['internal_id'] == master['internal_id']: continue
                
                for r_type in TYPES:
                    # Outbound
                    db.execute_write(f"""
                    MATCH (o) WHERE id(o) = $other_id
                    MATCH (m) WHERE id(m) = $master_id
                    MATCH (o)-[r:{r_type}]->(target)
                    MERGE (m)-[new_r:{r_type}]->(target)
                    SET new_r += properties(r)
                    """, {"other_id": other['internal_id'], "master_id": master['internal_id']})
                    
                    # Inbound
                    db.execute_write(f"""
                    MATCH (o) WHERE id(o) = $other_id
                    MATCH (m) WHERE id(m) = $master_id
                    MATCH (source)-[r:{r_type}]->(o)
                    MERGE (source)-[new_r:{r_type}]->(m)
                    SET new_r += properties(r)
                    """, {"other_id": other['internal_id'], "master_id": master['internal_id']})

                db.execute_write("MATCH (n) WHERE id(n) = $other_id DETACH DELETE n", {"other_id": other['internal_id']})

    print("Cleanup complete.")

if __name__ == "__main__":
    merge_nodes()
