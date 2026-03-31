import logging
from backend.graph_engine_connector import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Perfection")

def perfect_graph():
    driver = db.get_driver()
    if not driver:
        print("Neo4j not connected.")
        return

    # 1. PURGE ISOLATED NODES
    logger.info("Purging isolated 'junk' nodes without relationships...")
    db.execute_write("MATCH (n) WHERE NOT (n)--() DELETE n")

    # 2. FIX USA LEADERS (BIDEN & TRUMP)
    logger.info("Enforcing Leader-Country relationships for Trump and Biden...")
    
    # Ensure USA exists
    db.execute_write("MERGE (n:Country {id: 'country_usa'}) ON CREATE SET n.name = 'USA'")
    
    # Biden
    db.execute_write("""
        MERGE (l:Leader {id: 'leader_biden'}) ON CREATE SET l.name = 'Joe Biden'
        WITH l
        MATCH (c:Country {id: 'country_usa'})
        MERGE (l)-[r:LEADS]->(c)
        SET r.description = 'Current leader of the United States'
    """)
    
    # Trump
    db.execute_write("""
        MERGE (l:Leader {id: 'leader_trump'}) ON CREATE SET l.name = 'Donald Trump'
        WITH l
        MATCH (c:Country {id: 'country_usa'})
        MERGE (l)-[r:LEADS]->(c)
        SET r.description = 'Political leader / former President of the United States'
    """)

    logger.info("Graph perfection complete.")

if __name__ == "__main__":
    perfect_graph()
