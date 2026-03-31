import os
import sys
# Add current directory to path so we can import our connector
sys.path.append(os.getcwd())

from backend.graph_engine_connector import db
import logging

logging.basicConfig(level=logging.INFO)

def seed_test_data():
    print("--- STARTING NEO4J SEED ---")
    
    # 1. Create Constraints (handled in connector __init__, but let's be sure)
    
    # 2. Create foundational nodes and relationships
    cypher_queries = [
        # Countries
        "MERGE (c:Country {id: 'country_india'}) SET c.name = 'India'",
        "MERGE (c:Country {id: 'country_usa'}) SET c.name = 'USA'",
        "MERGE (c:Country {id: 'country_russia'}) SET c.name = 'Russia'",
        "MERGE (c:Country {id: 'country_china'}) SET c.name = 'China'",
        
        # Assets
        "MERGE (a:Asset {id: 'asset_oil'}) SET a.name = 'Crude Oil'",
        "MERGE (a:Asset {id: 'asset_lng'}) SET a.name = 'LNG'",
        
        # Technologies
        "MERGE (t:Technology {id: 'tech_semiconductors'}) SET t.name = 'Semiconductors'",
        
        # Alliances & Dependencies
        "MATCH (c1 {id: 'country_india'}), (a {id: 'asset_oil'}) MERGE (c1)-[:IMPORTS]->(a)",
        "MATCH (c2 {id: 'country_russia'}), (a {id: 'asset_oil'}) MERGE (c2)-[:EXPORTS]->(a)",
        "MATCH (c2 {id: 'country_russia'}), (c1 {id: 'country_india'}) MERGE (c2)-[:ALLY_WITH]-(c1)",
        "MATCH (c3 {id: 'country_usa'}), (c4 {id: 'country_russia'}) MERGE (c3)-[:SANCTIONS]->(c4)"
    ]
    
    for q in cypher_queries:
        try:
            db.execute_write(q)
            print(f"Executed: {q[:40]}...")
        except Exception as e:
            print(f"Failed query: {e}")
            
    print("--- SEED COMPLETE ---")

if __name__ == "__main__":
    seed_test_data()
