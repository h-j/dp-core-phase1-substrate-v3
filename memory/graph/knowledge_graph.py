import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from memory.graph.neo4j_client import driver as neo4j_driver
except Exception:
    neo4j_driver = None


class KnowledgeGraph:
    def __init__(self, run_dir: Optional[Path] = None):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self.run_dir = run_dir

    def add_node(
        self,
        node_id: str,
        node_type: str,
        label: str,
        properties: Optional[Dict[str, Any]] = None,
    ):
        self.nodes[node_id] = {
            "id": node_id,
            "type": node_type,
            "label": label,
            "properties": properties or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._sync_neo4j_node(node_id, node_type, label, properties)

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ):
        self.edges.append(
            {
                "source": source_id,
                "target": target_id,
                "type": edge_type,
                "properties": properties or {},
            }
        )
        self._sync_neo4j_edge(source_id, target_id, edge_type, properties)

    def _sync_neo4j_node(
        self,
        node_id: str,
        node_type: str,
        label: str,
        properties: Optional[Dict[str, Any]] = None,
    ):
        if not neo4j_driver:
            return
        try:
            with neo4j_driver.session() as session:
                query = (
                    f"MERGE (n:{node_type} {{id: $node_id}}) "
                    "SET n.label = $label, n.properties = $props"
                )
                session.run(
                    query,
                    node_id=node_id,
                    label=label,
                    props=json.dumps(properties or {}),
                )
        except Exception:
            pass  # Suppress connection errors if Neo4j is offline

    def _sync_neo4j_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ):
        if not neo4j_driver:
            return
        try:
            with neo4j_driver.session() as session:
                src_node = self.nodes.get(source_id)
                tgt_node = self.nodes.get(target_id)
                if src_node and tgt_node:
                    src_type = src_node["type"]
                    tgt_type = tgt_node["type"]
                    query = (
                        f"MATCH (s:{src_type} {{id: $source_id}}) "
                        f"MATCH (t:{tgt_type} {{id: $target_id}}) "
                        f"MERGE (s)-[r:{edge_type}]->(t) "
                        "SET r.properties = $props"
                    )
                    session.run(
                        query,
                        source_id=source_id,
                        target_id=target_id,
                        props=json.dumps(properties or {}),
                    )
        except Exception:
            pass

    def save(self, filepath: Optional[Path] = None):
        target = (
            filepath
            if filepath
            else (self.run_dir / "knowledge_graph.json" if self.run_dir else None)
        )
        if target:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w") as f:
                json.dump(
                    {"nodes": list(self.nodes.values()), "edges": self.edges},
                    f,
                    indent=2,
                )

    def why_prediction(self, prediction_id: str) -> Dict[str, Any]:
        """
        Traverses the graph backward from a prediction node to reconstruct the cognitive motivation.
        Provenance chain: Observation -> Theory -> Principle -> WorldModel -> Prediction -> Outcome -> Reflection
        """
        chain = []
        visited = set()

        def traverse_back(curr_id: str):
            if curr_id in visited:
                return
            visited.add(curr_id)
            node = self.nodes.get(curr_id)
            if node:
                chain.append(node)
            for edge in self.edges:
                if edge["target"] == curr_id:
                    traverse_back(edge["source"])

        traverse_back(prediction_id)
        return {"prediction_id": prediction_id, "provenance_chain": chain[::-1]}
