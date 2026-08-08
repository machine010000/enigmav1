from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeType(str, Enum):
    PRODUCT = "PRODUCT"
    AUDIENCE = "AUDIENCE"
    PERSONA = "PERSONA"
    KEYWORD = "KEYWORD"
    TREND = "TREND"
    FEATURE = "FEATURE"
    BENEFIT = "BENEFIT"
    PROBLEM = "PROBLEM"
    PLATFORM = "PLATFORM"
    COUNTRY = "COUNTRY"
    CATEGORY = "CATEGORY"
    EVIDENCE = "EVIDENCE"


class RelationType(str, Enum):
    SOLVES = "SOLVES"
    HAS = "HAS"
    USES = "USES"
    TARGETS = "TARGETS"
    SELLS = "SELLS"
    AFFECTS = "AFFECTS"
    HAS_CATEGORY = "HAS_CATEGORY"
    HAS_FEATURE = "HAS_FEATURE"
    HAS_KEYWORD = "HAS_KEYWORD"
    HAS_EVIDENCE = "HAS_EVIDENCE"
    RELATED_TO = "RELATED_TO"


@dataclass(slots=True)
class Node:
    id: str
    type: NodeType
    name: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.id,
            "node_type": self.type.value,
            "name": self.name,
            "properties": deepcopy(self.properties),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(slots=True)
class Edge:
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: Optional[float] = None
    source: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation_type.value,
            "weight": self.weight,
            "source": self.source,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class KnowledgeGraphService:
    """A lightweight in-memory knowledge graph for accumulating structured domain knowledge."""

    def __init__(self) -> None:
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: List[Dict[str, Any]] = []

    def create_node(self, node_type: str, node_id: Optional[str] = None, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        resolved_id = node_id or self._make_node_id(node_type)
        node = {
            "node_id": resolved_id,
            "node_type": node_type,
            "properties": deepcopy(properties or {}),
        }
        self._nodes[resolved_id] = node
        return deepcopy(node)

    def create_edge(self, source_id: str, target_id: str, relation: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        edge = {
            "source_id": source_id,
            "target_id": target_id,
            "relation": relation,
            "properties": deepcopy(properties or {}),
        }
        self._edges.append(edge)
        return deepcopy(edge)

    def get_neighbors(self, node_id: str) -> List[Dict[str, Any]]:
        neighbors: List[Dict[str, Any]] = []
        for edge in self._edges:
            if edge["source_id"] == node_id:
                neighbors.append(self._node_snapshot(edge["target_id"], edge))
            elif edge["target_id"] == node_id:
                neighbors.append(self._node_snapshot(edge["source_id"], edge))
        return neighbors

    def get_edges(self, node_id: str) -> List[Dict[str, Any]]:
        edges = []
        for edge in self._edges:
            if edge["source_id"] == node_id or edge["target_id"] == node_id:
                edges.append(deepcopy(edge))
        return edges

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        return deepcopy(self._nodes.get(node_id))

    def list_nodes(self, node_type: Optional[str] = None) -> List[Dict[str, Any]]:
        nodes = list(self._nodes.values())
        if node_type is not None:
            nodes = [node for node in nodes if node["node_type"] == node_type]
        return [deepcopy(node) for node in nodes]

    def _make_node_id(self, node_type: str) -> str:
        return f"{node_type.lower()}:{len(self._nodes) + 1}"

    def _node_snapshot(self, node_id: str, edge: Dict[str, Any]) -> Dict[str, Any]:
        node = self.get_node(node_id)
        if node is None:
            return {"node_id": node_id, "node_type": "Unknown", "properties": {}, "relation": edge["relation"]}
        node_copy = deepcopy(node)
        node_copy["relation"] = edge["relation"]
        return node_copy


class KnowledgeService:
    def __init__(self, graph: Optional[KnowledgeGraphService] = None) -> None:
        self.graph = graph or KnowledgeGraphService()
        self._nodes: Dict[str, Node] = {}
        self._edges: List[Edge] = []

    def add_node(self, node_id: str, node_type: NodeType, name: Optional[str] = None, properties: Optional[Dict[str, Any]] = None) -> Node:
        node = Node(id=node_id, type=node_type, name=name, properties=properties or {})
        self._nodes[node.id] = node
        self.graph.create_node(node_type.value, node_id=node.id, properties={"name": name, **(properties or {})})
        return node

    def add_product(self, node_id: str, name: Optional[str] = None, properties: Optional[Dict[str, Any]] = None) -> Node:
        return self.add_node(node_id=node_id, node_type=NodeType.PRODUCT, name=name, properties=properties)

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        weight: Optional[float] = None,
        source: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> Edge:
        edge = Edge(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            source=source,
            confidence=confidence,
        )
        self._edges.append(edge)
        self.graph.create_edge(
            source_id,
            target_id,
            relation_type.value,
            properties={
                "weight": weight,
                "source": source,
                "confidence": confidence,
            },
        )
        return edge

    def get_neighbors(self, node_id: str) -> List[Dict[str, Any]]:
        return self.graph.get_neighbors(node_id)

    def get_edges(self, node_id: str) -> List[Edge]:
        return [edge for edge in self._edges if edge.source_id == node_id or edge.target_id == node_id]

    def get_node(self, node_id: str) -> Optional[Node]:
        return self._nodes.get(node_id)

    def list_nodes(self) -> List[Node]:
        return list(self._nodes.values())

    def get_product_graph(self, product_id: str) -> Dict[str, Any]:
        product = self.get_node(product_id)
        if product is None:
            return {"product_id": product_id, "product_name": None, "sections": {}}

        sections: Dict[str, List[Dict[str, Any]]] = {
            "Category": [],
            "Features": [],
            "Problems Solved": [],
            "Audience": [],
            "Keywords": [],
            "Evidence": [],
            "Related Products": [],
        }

        for edge in self._edges:
            if edge.source_id != product_id:
                continue

            target = self.get_node(edge.target_id)
            if target is None:
                continue

            if edge.relation_type == RelationType.HAS_CATEGORY:
                sections["Category"].append({"node_id": target.id, "node_type": target.type.value, "name": target.name})
            elif edge.relation_type == RelationType.HAS_FEATURE:
                sections["Features"].append({"node_id": target.id, "node_type": target.type.value, "name": target.name})
            elif edge.relation_type == RelationType.SOLVES:
                sections["Problems Solved"].append({"node_id": target.id, "node_type": target.type.value, "name": target.name})
            elif edge.relation_type == RelationType.TARGETS:
                sections["Audience"].append({"node_id": target.id, "node_type": target.type.value, "name": target.name})
            elif edge.relation_type == RelationType.HAS_KEYWORD:
                sections["Keywords"].append({"node_id": target.id, "node_type": target.type.value, "name": target.name})
            elif edge.relation_type == RelationType.HAS_EVIDENCE:
                sections["Evidence"].append({"node_id": target.id, "node_type": target.type.value, "name": target.name})
            elif edge.relation_type == RelationType.RELATED_TO:
                sections["Related Products"].append({"node_id": target.id, "node_type": target.type.value, "name": target.name})

        return {
            "product_id": product.id,
            "product_name": product.name,
            "sections": sections,
        }
