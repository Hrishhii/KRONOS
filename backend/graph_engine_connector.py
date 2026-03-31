import os
import logging
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)

from backend.config import settings

logger = logging.getLogger(__name__)

# Use centralized settings only
NEO4J_URI = settings.NEO4J_URI
NEO4J_USER = settings.NEO4J_USER
NEO4J_PASSWORD = settings.NEO4J_PASSWORD

class Neo4jConnector:
    def __init__(self, uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        
        if not password:
            logger.error("NEO4J_PASSWORD not found in environment. Database connection aborted.")
            self.driver = None
            return

        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            logger.info(f"Successfully connected to Neo4j at {uri}")
            self._ensure_constraints()
        except Exception as e:
            logger.warning(f"Neo4j connection failed at {uri}. Fallback mode enabled. Error: {e}")
            self.driver = None

    def get_driver(self):
        """Lazy-init or return driver to handle transient connection failures upon startup."""
        if self.driver:
            return self.driver
        # Attempt to reconnect if driver was None and we have credentials
        if not self.password:
            return None
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.driver.verify_connectivity()
            return self.driver
        except Exception as e:
            logger.debug(f"Lazy-init Neo4j connection failed: {e}")
            return None
            
    def _ensure_constraints(self):
        """Creates unique constraints on the canonical 'id' for core node types to strictly prevent duplicates."""
        if not self.driver:
            return
            
        constraints = [
            "CREATE CONSTRAINT country_id IF NOT EXISTS FOR (n:Country) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT leader_id IF NOT EXISTS FOR (n:Leader) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT org_id IF NOT EXISTS FOR (n:Organization) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT asset_id IF NOT EXISTS FOR (n:Asset) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT tech_id IF NOT EXISTS FOR (n:Technology) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT company_id IF NOT EXISTS FOR (n:Company) REQUIRE n.id IS UNIQUE"
        ]
        
        with self.driver.session() as session:
            for query in constraints:
                try:
                    session.run(query)
                except Exception as e:
                    logger.error(f"Failed to create constraint: {e}")
                    
    def close(self):
        if self.driver is not None:
            self.driver.close()

    def execute_read(self, query: str, parameters=None):
        driver = self.get_driver()
        if not driver:
            return []
            
        with driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]
            
    def execute_write(self, query: str, parameters=None):
        driver = self.get_driver()
        if not driver:
            return None
            
        with driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]

    def get_graph_visual_data(self):
        """Returns all nodes and relationships formatted for a force-directed graph UI.
        Resilient: Includes all nodes and their relationships without double-counting.
        """
        driver = self.get_driver()
        if not driver:
            return {"nodes": [], "links": []}
            
        nodes = {}
        links = []
        
        # Phase 1: Fetch all valid nodes
        # The list of labels must be comprehensive for our visual graph
        node_query = """
            MATCH (n)
            WHERE n:Country OR n:Leader OR n:Organization OR n:Asset OR n:Technology OR n:Infrastructure OR n:Company OR n:Event OR n:Indicator OR n:Policy OR n:MilitaryBase OR n:Location
            RETURN 
                id(n) as internal_id,
                n.id AS id,
                n.name AS name,
                labels(n)[0] AS label,
                n.cluster AS cluster
        """
        node_results = self.execute_read(node_query)
        for row in node_results:
            nid = row.get('id')
            if nid:
                nodes[nid] = {
                    "id": nid,
                    "name": row.get('name') or nid,
                    "group": row.get('label') or 'Asset',
                    "cluster": row.get('cluster') or 'general'
                }
        
        # Phase 2: Fetch all unique directional relationships
        # Direct Match (s)-[r]->(t) ensures each uniquely directed relationship is counted once
        rel_query = """
            MATCH (s)-[r]->(t)
            WHERE (s:Country OR s:Leader OR s:Organization OR s:Asset OR s:Technology OR s:Infrastructure OR s:Company OR s:Event OR s:Indicator OR s:Policy OR s:MilitaryBase OR s:Location)
              AND (t:Country OR t:Leader OR t:Organization OR t:Asset OR t:Technology OR t:Infrastructure OR t:Company OR t:Event OR t:Indicator OR t:Policy OR t:MilitaryBase OR t:Location)
            RETURN 
                s.id AS source_id,
                t.id AS target_id,
                type(r) AS rel_type,
                r.description AS rel_description
        """
        rel_results = self.execute_read(rel_query)
        for row in rel_results:
            sid = row.get('source_id')
            tid = row.get('target_id')
            # Only add link if both source and target are in our canonical node set
            if sid in nodes and tid in nodes:
                links.append({
                    "source": sid,
                    "target": tid,
                    "type": row.get('rel_type') or 'LINKED',
                    "description": row.get('rel_description') or ''
                })
            
        return {"nodes": list(nodes.values()), "links": links}

    def get_contextual_graph_data(self, entities: list) -> str:
        """Fetches a strategic summary of the Knowledge Graph neighborhood for the given entities."""
        if not entities:
            return ""
            
        driver = self.get_driver()
        if not driver:
            return ""
            
        # Standardize entities to canonical IDs (best effort)
        from backend.graph_engine_schema import resolve_alias
        # We don't have the labels here so we check for common entity matches
        canon_ids = []
        for e in entities:
             # Try common labels
             for lbl in ["Country", "Leader", "Organization", "Asset", "Technology"]:
                 cid = resolve_alias(e, lbl)
                 # We'll just collect them and try to MATCH (s) WHERE s.id IN canon_ids
                 canon_ids.append(cid)
                 
        query = """
            MATCH (s)
            WHERE s.id IN $canon_ids OR s.name IN $entities
            OPTIONAL MATCH (s)-[r]-(t)
            RETURN 
                s.name AS source_name,
                labels(s)[0] AS source_label,
                type(r) AS rel_type,
                r.description AS description,
                t.name AS target_name,
                labels(t)[0] AS target_label
            LIMIT 50
        """
        
        results = self.execute_read(query, {"canon_ids": canon_ids, "entities": entities})
        if not results:
            return ""
            
        summary = "== KNOWLEDGE GRAPH STRATEGIC CONTEXT ==\n"
        relationships = set()
        
        for row in results:
            if not row.get('rel_type'):
                continue
            
            s_name = row.get('source_name')
            s_lbl = row.get('source_label', '')
            rel = row.get('rel_type')
            t_name = row.get('target_name')
            t_lbl = row.get('target_label', '')
            desc = row.get('description', '')
            
            # De-duplicate bidirectional results for cleaner prompt
            pair = tuple(sorted([s_name, t_name]) + [rel])
            if pair in relationships:
                 continue
            relationships.add(pair)
            
            line = f"- {s_name} ({s_lbl}) {rel} {t_name} ({t_lbl})"
            if desc:
                line += f": {desc}"
            summary += line + "\n"
            
        return summary

    def seed_if_empty(self):
        """Checks if the graph is empty and seeds it with initial tactical data if so."""
        driver = self.get_driver()
        if not driver:
            return
            
        try:
            # Check node count
            count_res = self.execute_read("MATCH (n) RETURN count(n) as count")
            if count_res and count_res[0].get('count', 0) == 0:
                logger.info("Knowledge Graph is empty. Initializing strategic seed...")
                
                queries = [
                    # Countries & Leaders
                    "MERGE (c:Country {id: 'country_india'}) SET c.name = 'India'",
                    "MERGE (c:Country {id: 'country_usa'}) SET c.name = 'USA'",
                    "MERGE (c:Country {id: 'country_russia'}) SET c.name = 'Russia'",
                    "MERGE (c:Country {id: 'country_china'}) SET c.name = 'China'",
                    "MERGE (c:Country {id: 'country_taiwan'}) SET c.name = 'Taiwan'",
                    
                    # Technology & Infrastructure
                    "MERGE (t:Technology {id: 'tech_semiconductors'}) SET t.name = 'Advanced Semiconductors'",
                    "MERGE (t:Technology {id: 'tech_quantum'}) SET t.name = 'Quantum Computing'",
                    "MERGE (i:Infrastructure {id: 'infra_tsmc'}) SET i.name = 'TSMC Fab 18'",
                    "MERGE (i:Infrastructure {id: 'infra_nordstream'}) SET i.name = 'Nord Stream Pipeline'",
                    
                    # Military & Energy
                    "MERGE (m:MilitaryBase {id: 'mil_diego_garcia'}) SET m.name = 'Diego Garcia (US)'",
                    "MERGE (m:MilitaryBase {id: 'mil_tartus'}) SET m.name = 'Tartus Naval Base (RU)'",
                    "MERGE (a:Asset {id: 'asset_oil'}) SET a.name = 'Urals Crude'",
                    "MERGE (a:Asset {id: 'asset_lng'}) SET a.name = 'Yamal LNG'",
                    
                    # Complex Relationships
                    "MATCH (c1 {id: 'country_india'}), (a {id: 'asset_oil'}) MERGE (c1)-[:IMPORTS]->(a)",
                    "MATCH (c2 {id: 'country_russia'}), (a {id: 'asset_oil'}) MERGE (c2)-[:EXPORTS]->(a)",
                    "MATCH (c2 {id: 'country_russia'}), (c1 {id: 'country_india'}) MERGE (c2)-[:STRATEGIC_PARTNER]-(c1)",
                    "MATCH (c3 {id: 'country_usa'}), (c4 {id: 'country_russia'}) MERGE (c3)-[:SANCTIONS]->(c4)",
                    "MATCH (c4 {id: 'country_china'}), (c5 {id: 'country_taiwan'}) MERGE (c4)-[:TERRITORIAL_CLAIM]->(c5)",
                    "MATCH (i {id: 'infra_tsmc'}), (c5 {id: 'country_taiwan'}) MERGE (i)-[:LOCATED_IN]->(c5)",
                    "MATCH (i {id: 'infra_tsmc'}), (t {id: 'tech_semiconductors'}) MERGE (i)-[:PRODUCES]->(t)",
                    "MATCH (c3 {id: 'country_usa'}), (t {id: 'tech_semiconductors'}) MERGE (c3)-[:DEPENDS_ON]->(t)",
                    "MATCH (m {id: 'mil_diego_garcia'}), (c3 {id: 'country_usa'}) MERGE (m)-[:OPERATED_BY]->(c3)",
                    "MATCH (m {id: 'mil_tartus'}), (c2 {id: 'country_russia'}) MERGE (m)-[:OPERATED_BY]->(c2)",
                    "MATCH (c1 {id: 'country_india'}), (c3 {id: 'country_usa'}) MERGE (c1)-[:QUAD_MEMBER]-(c3)"
                ]
                
                for q in queries:
                    self.execute_write(q)
                logger.info("Strategic seed complete.")
        except Exception as e:
            logger.error(f"Auto-seed failed: {e}")

# Global singleton instance
db = Neo4jConnector()
