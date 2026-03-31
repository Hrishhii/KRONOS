import logging
from backend.graph_engine_connector import db
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test():
    print(f"Driver exists: {db.driver is not None}")
    if not db.driver:
        print("CRITICAL: Neo4j Driver is None!")
        return

    try:
        res = db.execute_read("MATCH (n) RETURN count(n) as count")
        print(f"Node count: {res[0]['count']}")
        
        # Test visual data query
        visual = db.get_graph_visual_data()
        print(f"Visual data: {len(visual['nodes'])} nodes, {len(visual['links'])} links")
        # print(json.dumps(visual, indent=2))
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test()
