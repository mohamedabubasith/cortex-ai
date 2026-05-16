import logging
import json
from typing import List, Dict, Any

try:
    from neo4j import GraphDatabase
    _NEO4J_AVAILABLE = True
except ImportError:
    GraphDatabase = None
    _NEO4J_AVAILABLE = False
from app.core.config import settings
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

class Neo4jService:
    def __init__(self):
        self.driver = None
        if _NEO4J_AVAILABLE and settings.ENABLE_GRAPH:
            try:
                self.driver = GraphDatabase.driver(
                    settings.NEO4J_URI, 
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                )
                logger.info("Nodes: Neo4j Driver Initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Neo4j driver: {e}")

    def close(self):
        if self.driver:
            self.driver.close()

    async def verify_connectivity(self):
        if not self.driver:
            return False
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    async def process_graph(self, kb_id: str, tenant_id: str, text_chunks: List[str], llm_config: Any):
        """
        Extracts entities and relationships from chunks and stores them in Neo4j 
        with strict RLS (tenant_id).
        """
        if not self.driver:
            logger.warning("Graph processing skipped: Neo4j not enabled or connected.")
            return

        logger.info(f"Starting Graph Processing for KB {kb_id} (Tenant: {tenant_id})")
        
        # Batch process chunks to avoid overwhelming LLM or DB
        # For production, we might want to queue this better, but this works for "async background task".
        for i, chunk in enumerate(text_chunks):
            try:
                extraction = await self._extract_triples(chunk, llm_config)
                if extraction:
                    self._store_subgraph(kb_id, tenant_id, extraction)
            except Exception as e:
                logger.error(f"Error processing chunk {i} for Graph: {e}")

    async def delete_graph_for_kb(self, kb_id: str, tenant_id: str):
        """Delete all nodes/edges associated with a KB ID + Tenant ID"""
        if not self.driver:
             return

        query = """
        MATCH (n {kb_id: $kb_id, tenant_id: $tenant_id})
        DETACH DELETE n
        """
        try:
            with self.driver.session() as session:
                session.run(query, kb_id=kb_id, tenant_id=tenant_id)
            logger.info(f"Deleted graph data for KB {kb_id}")
        except Exception as e:
            logger.error(f"Failed to delete graph data for {kb_id}: {e}")

    async def _extract_triples(self, text: str, llm_config: Any) -> Dict[str, Any]:
        """
        Uses LLM to extract {nodes, edges}.
        """
        prompt = f"""
        You are a Knowledge Graph extraction expert.
        Extract relevant entities (nodes) and relationships (edges) from the following text.
        
        Rules:
        1. Nodes must have: "id" (unique name), "label" (e.g., Person, Organization, Concept).
        2. Edges must have: "source" (id of source node), "target" (id of target node), "type" (relationship verb, e.g., WORKS_AT, CONTAINS).
        3. Output MUST be valid JSON with keys "nodes" and "edges".
        4. Do not include duplicate or trivial information.
        
        Text:
        {text[:2000]} 
        
        JSON Output:
        """
        # Limit text to 2000 chars for context window safety if chunk is large
        
        try:
           response = await llm_service.generate_text(prompt, llm_config)
           # Cleanup markdown code blocks if present
           clean_response = response.replace("```json", "").replace("```", "").strip()
           data = json.loads(clean_response)
           return data
        except Exception as e:
            logger.warning(f"LLM Extraction failed: {e}")
            return None

    def _store_subgraph(self, kb_id: str, tenant_id: str, data: Dict[str, Any]):
        """
        Cypher query to merge nodes and relationships.
        Enforces tenant_id on ALL nodes.
        """
        # We add 'Document' label to all nodes to easily track them, 
        # plus their specific extracted label.
        
        # Note: Dynamic labels in Cypher are tricky with params, careful with injection if label comes from LLM.
        # Ideally we sanitize labels. For now, we use a generic query structure or APOC if available.
        # But standard Neo4j usually requires fixed labels or dynamic query building.
        # We will use "Entity" label + property "type" equal to extracted label for safety.
        
        query = """
        UNWIND $nodes AS node
        MERGE (n:Entity {id: node.id, tenant_id: $tenant_id})
        ON CREATE SET n.created = timestamp(), n.kb_id = $kb_id, n.type = node.label
        ON MATCH SET n.last_seen = timestamp()
        
        WITH n
        UNWIND $edges AS edge
        MATCH (source:Entity {id: edge.source, tenant_id: $tenant_id})
        MATCH (target:Entity {id: edge.target, tenant_id: $tenant_id})
        MERGE (source)-[r:RELATED {type: edge.type}]->(target)
        ON CREATE SET r.tenant_id = $tenant_id, r.kb_id = $kb_id
        """
        
        # Re-mapping data to fit query
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        
        if not nodes:
            return

        with self.driver.session() as session:
            session.run(query, 
                nodes=nodes, 
                edges=edges, 
                tenant_id=tenant_id, 
                kb_id=kb_id
            )

neo4j_service = Neo4jService()
