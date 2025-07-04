"""
Knowledge Graph System for Agent Learning

This module implements a comprehensive knowledge graph that represents relationships
between concepts, solutions, experiences, and patterns. It provides semantic
understanding and relationship-based knowledge retrieval capabilities.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

import networkx as nx
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class NodeType(Enum):
    """Types of nodes in the knowledge graph"""
    CONCEPT = "concept"
    SOLUTION = "solution"
    EXPERIENCE = "experience"
    PATTERN = "pattern"
    AGENT = "agent"
    TASK = "task"
    TECHNOLOGY = "technology"
    DOMAIN = "domain"
    WORKFLOW = "workflow"
    ANTI_PATTERN = "anti_pattern"


class RelationType(Enum):
    """Types of relationships in the knowledge graph"""
    RELATES_TO = "relates_to"
    DEPENDS_ON = "depends_on"
    SIMILAR_TO = "similar_to"
    IMPLEMENTS = "implements"
    USES = "uses"
    SOLVES = "solves"
    CAUSED_BY = "caused_by"
    IMPROVES = "improves"
    CONTAINS = "contains"
    PART_OF = "part_of"
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    CONFLICTS_WITH = "conflicts_with"
    ENHANCES = "enhances"


@dataclass
class KnowledgeNode:
    """Represents a node in the knowledge graph"""
    id: str
    type: NodeType
    label: str
    properties: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    weight: float = 1.0
    relevance_score: float = 0.0
    usage_count: int = 0
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class KnowledgeEdge:
    """Represents an edge/relationship in the knowledge graph"""
    id: str
    source_id: str
    target_id: str
    relationship: RelationType
    weight: float
    properties: Dict[str, Any]
    created_at: datetime
    confidence: float = 1.0
    evidence_count: int = 1
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class GraphQuery:
    """Represents a query to the knowledge graph"""
    node_types: Optional[List[NodeType]] = None
    relationship_types: Optional[List[RelationType]] = None
    properties: Optional[Dict[str, Any]] = None
    text_query: Optional[str] = None
    max_depth: int = 3
    min_weight: float = 0.1
    limit: int = 100


class KnowledgeGraph:
    """
    Advanced knowledge graph system for semantic understanding and learning
    """
    
    def __init__(self, storage_path: str = "cache/knowledge_graph.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # NetworkX graph for in-memory operations
        self.graph = nx.MultiDiGraph()
        
        # Node and edge storage
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: Dict[str, KnowledgeEdge] = {}
        
        # Indexing for fast retrieval
        self.node_type_index: Dict[NodeType, Set[str]] = defaultdict(set)
        self.relationship_index: Dict[RelationType, Set[str]] = defaultdict(set)
        self.text_index: Dict[str, Set[str]] = defaultdict(set)
        
        # TF-IDF for semantic search
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.node_vectors = None
        self.node_texts = []
        self.node_ids = []
        
        # Load existing graph
        self._load_graph()
    
    async def initialize(self):
        """Initialize the knowledge graph"""
        await self._rebuild_indexes()
        self.logger.info("Knowledge graph initialized")
    
    async def add_node(self, node: KnowledgeNode) -> bool:
        """Add a node to the knowledge graph"""
        try:
            # Update timestamps
            if not node.created_at:
                node.created_at = datetime.now()
            node.updated_at = datetime.now()
            
            # Store node
            self.nodes[node.id] = node
            self.graph.add_node(node.id, **asdict(node))
            
            # Update indexes
            self.node_type_index[node.type].add(node.id)
            
            # Index text content
            text_content = f"{node.label} {json.dumps(node.properties)}"
            words = text_content.lower().split()
            for word in words:
                # Clean up punctuation from JSON formatting
                clean_word = word.strip('{}[],:"')
                if clean_word:
                    self.text_index[clean_word].add(node.id)
            
            # Trigger vector rebuild
            self._invalidate_vectors()
            
            self.logger.debug(f"Added node: {node.id} ({node.type})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding node: {e}")
            return False
    
    async def add_edge(self, edge: KnowledgeEdge) -> bool:
        """Add an edge to the knowledge graph"""
        try:
            # Validate nodes exist
            if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
                self.logger.warning(f"Cannot add edge: missing nodes {edge.source_id} -> {edge.target_id}")
                return False
            
            # Update timestamps
            if not edge.created_at:
                edge.created_at = datetime.now()
            
            # Store edge
            self.edges[edge.id] = edge
            self.graph.add_edge(
                edge.source_id, 
                edge.target_id, 
                key=edge.id,
                **asdict(edge)
            )
            
            # Update indexes
            self.relationship_index[edge.relationship].add(edge.id)
            
            self.logger.debug(f"Added edge: {edge.source_id} -> {edge.target_id} ({edge.relationship})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding edge: {e}")
            return False
    
    async def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    async def get_edge(self, edge_id: str) -> Optional[KnowledgeEdge]:
        """Get an edge by ID"""
        return self.edges.get(edge_id)
    
    async def query_nodes(self, query: GraphQuery) -> List[KnowledgeNode]:
        """Query nodes based on criteria"""
        try:
            candidate_ids = set(self.nodes.keys())
            
            # Filter by node types
            if query.node_types:
                type_ids = set()
                for node_type in query.node_types:
                    type_ids.update(self.node_type_index[node_type])
                candidate_ids &= type_ids
            
            # Filter by properties
            if query.properties:
                property_ids = set()
                for node_id in candidate_ids:
                    node = self.nodes[node_id]
                    if all(
                        key in node.properties and node.properties[key] == value
                        for key, value in query.properties.items()
                    ):
                        property_ids.add(node_id)
                candidate_ids &= property_ids
            
            # Text search
            if query.text_query:
                text_ids = await self._text_search(query.text_query)
                candidate_ids &= text_ids
            
            # Filter by weight
            if query.min_weight > 0:
                candidate_ids = {
                    node_id for node_id in candidate_ids
                    if self.nodes[node_id].weight >= query.min_weight
                }
            
            # Get nodes and sort by relevance
            results = [self.nodes[node_id] for node_id in candidate_ids]
            results.sort(key=lambda n: n.relevance_score, reverse=True)
            
            return results[:query.limit]
            
        except Exception as e:
            self.logger.error(f"Error querying nodes: {e}")
            return []
    
    async def find_path(
        self, 
        source_id: str, 
        target_id: str, 
        max_depth: int = 5,
        relationship_types: Optional[List[RelationType]] = None
    ) -> List[List[str]]:
        """Find paths between two nodes"""
        try:
            if source_id not in self.nodes or target_id not in self.nodes:
                return []
            
            # Create subgraph if relationship types specified
            graph = self.graph
            if relationship_types:
                edges_to_include = []
                for edge_id, edge in self.edges.items():
                    if edge.relationship in relationship_types:
                        edges_to_include.append((edge.source_id, edge.target_id, edge_id))
                
                graph = nx.MultiDiGraph()
                graph.add_nodes_from(self.graph.nodes())
                for source, target, key in edges_to_include:
                    graph.add_edge(source, target, key=key)
            
            # Find all simple paths
            try:
                paths = list(nx.all_simple_paths(
                    graph, 
                    source_id, 
                    target_id, 
                    cutoff=max_depth
                ))
                return paths[:10]  # Limit to top 10 paths
            except nx.NetworkXNoPath:
                return []
                
        except Exception as e:
            self.logger.error(f"Error finding path: {e}")
            return []
    
    async def get_neighbors(
        self, 
        node_id: str, 
        relationship_types: Optional[List[RelationType]] = None,
        direction: str = "both"  # "in", "out", "both"
    ) -> Dict[str, List[KnowledgeNode]]:
        """Get neighboring nodes"""
        try:
            if node_id not in self.nodes:
                return {"in": [], "out": []}
            
            neighbors = {"in": [], "out": []}
            
            # Outgoing edges
            if direction in ["out", "both"]:
                for target_id in self.graph.successors(node_id):
                    edges = self.graph[node_id][target_id]
                    for edge_key, edge_data in edges.items():
                        edge = self.edges[edge_key]
                        if not relationship_types or edge.relationship in relationship_types:
                            neighbors["out"].append(self.nodes[target_id])
                            break
            
            # Incoming edges
            if direction in ["in", "both"]:
                for source_id in self.graph.predecessors(node_id):
                    edges = self.graph[source_id][node_id]
                    for edge_key, edge_data in edges.items():
                        edge = self.edges[edge_key]
                        if not relationship_types or edge.relationship in relationship_types:
                            neighbors["in"].append(self.nodes[source_id])
                            break
            
            return neighbors
            
        except Exception as e:
            self.logger.error(f"Error getting neighbors: {e}")
            return {"in": [], "out": []}
    
    async def find_similar_nodes(
        self, 
        node_id: str, 
        similarity_threshold: float = 0.3,
        limit: int = 10
    ) -> List[Tuple[KnowledgeNode, float]]:
        """Find semantically similar nodes"""
        try:
            if node_id not in self.nodes:
                return []
            
            # Ensure vectors are built
            await self._build_vectors()
            
            if self.node_vectors is None or node_id not in self.node_ids:
                return []
            
            # Get node index
            node_index = self.node_ids.index(node_id)
            
            # Calculate similarities
            similarities = cosine_similarity(
                self.node_vectors[node_index:node_index+1],
                self.node_vectors
            ).flatten()
            
            # Get similar nodes
            similar_pairs = []
            for i, similarity in enumerate(similarities):
                if i != node_index and similarity >= similarity_threshold:
                    similar_node_id = self.node_ids[i]
                    similar_pairs.append((self.nodes[similar_node_id], similarity))
            
            # Sort by similarity
            similar_pairs.sort(key=lambda x: x[1], reverse=True)
            
            return similar_pairs[:limit]
            
        except Exception as e:
            self.logger.error(f"Error finding similar nodes: {e}")
            return []
    
    async def get_subgraph(
        self, 
        center_node_id: str, 
        depth: int = 2,
        node_types: Optional[List[NodeType]] = None,
        relationship_types: Optional[List[RelationType]] = None
    ) -> Dict[str, Any]:
        """Extract a subgraph around a central node"""
        try:
            if center_node_id not in self.nodes:
                return {"nodes": [], "edges": []}
            
            # BFS to collect nodes within depth
            visited = set()
            queue = [(center_node_id, 0)]
            subgraph_nodes = set()
            
            while queue:
                current_id, current_depth = queue.pop(0)
                
                if current_id in visited or current_depth > depth:
                    continue
                
                visited.add(current_id)
                
                # Check node type filter
                if node_types and self.nodes[current_id].type not in node_types:
                    continue
                
                subgraph_nodes.add(current_id)
                
                # Add neighbors for next level
                if current_depth < depth:
                    neighbors = await self.get_neighbors(
                        current_id, 
                        relationship_types=relationship_types
                    )
                    for neighbor in neighbors["in"] + neighbors["out"]:
                        queue.append((neighbor.id, current_depth + 1))
            
            # Collect edges within subgraph
            subgraph_edges = []
            for edge in self.edges.values():
                if (edge.source_id in subgraph_nodes and 
                    edge.target_id in subgraph_nodes):
                    if not relationship_types or edge.relationship in relationship_types:
                        subgraph_edges.append(edge)
            
            return {
                "nodes": [self.nodes[node_id] for node_id in subgraph_nodes],
                "edges": subgraph_edges,
                "center": self.nodes[center_node_id]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting subgraph: {e}")
            return {"nodes": [], "edges": []}
    
    async def analyze_centrality(self) -> Dict[str, Dict[str, float]]:
        """Analyze node centrality measures"""
        try:
            # Convert to simple graph for centrality calculations
            simple_graph = nx.Graph()
            simple_graph.add_nodes_from(self.graph.nodes())
            
            # Add edges with weights
            for edge in self.edges.values():
                if simple_graph.has_edge(edge.source_id, edge.target_id):
                    simple_graph[edge.source_id][edge.target_id]['weight'] += edge.weight
                else:
                    simple_graph.add_edge(edge.source_id, edge.target_id, weight=edge.weight)
            
            # Calculate centrality measures
            centrality_measures = {}
            
            if len(simple_graph.nodes()) > 0:
                # Degree centrality
                degree_centrality = nx.degree_centrality(simple_graph)
                
                # Betweenness centrality (sample for large graphs)
                if len(simple_graph.nodes()) > 100:
                    betweenness_centrality = nx.betweenness_centrality(simple_graph, k=100)
                else:
                    betweenness_centrality = nx.betweenness_centrality(simple_graph)
                
                # Closeness centrality
                closeness_centrality = nx.closeness_centrality(simple_graph)
                
                # PageRank
                pagerank = nx.pagerank(simple_graph, weight='weight')
                
                # Combine measures
                for node_id in simple_graph.nodes():
                    centrality_measures[node_id] = {
                        "degree": degree_centrality.get(node_id, 0),
                        "betweenness": betweenness_centrality.get(node_id, 0),
                        "closeness": closeness_centrality.get(node_id, 0),
                        "pagerank": pagerank.get(node_id, 0)
                    }
            
            return centrality_measures
            
        except Exception as e:
            self.logger.error(f"Error analyzing centrality: {e}")
            return {}
    
    async def detect_communities(self) -> Dict[str, List[str]]:
        """Detect communities in the knowledge graph"""
        try:
            # Convert to undirected graph
            undirected = self.graph.to_undirected()
            
            # Use Louvain algorithm for community detection
            import networkx.algorithms.community as nx_comm
            communities = nx_comm.louvain_communities(undirected)
            
            # Format results
            community_dict = {}
            for i, community in enumerate(communities):
                community_dict[f"community_{i}"] = list(community)
            
            return community_dict
            
        except Exception as e:
            self.logger.error(f"Error detecting communities: {e}")
            return {}
    
    async def save_graph(self):
        """Save the knowledge graph to storage"""
        try:
            data = {
                "nodes": {
                    node_id: {
                        **asdict(node),
                        "created_at": node.created_at.isoformat(),
                        "updated_at": node.updated_at.isoformat(),
                        "type": node.type.value
                    }
                    for node_id, node in self.nodes.items()
                },
                "edges": {
                    edge_id: {
                        **asdict(edge),
                        "created_at": edge.created_at.isoformat(),
                        "relationship": edge.relationship.value
                    }
                    for edge_id, edge in self.edges.items()
                },
                "metadata": {
                    "node_count": len(self.nodes),
                    "edge_count": len(self.edges),
                    "last_saved": datetime.now().isoformat()
                }
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved knowledge graph with {len(self.nodes)} nodes and {len(self.edges)} edges")
            
        except Exception as e:
            self.logger.error(f"Error saving graph: {e}")
    
    def _load_graph(self):
        """Load the knowledge graph from storage"""
        try:
            if not self.storage_path.exists():
                self.logger.info("No existing knowledge graph found, starting fresh")
                return
            
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Load nodes
            for node_id, node_data in data.get("nodes", {}).items():
                node_data["type"] = NodeType(node_data["type"])
                node_data["created_at"] = datetime.fromisoformat(node_data["created_at"])
                node_data["updated_at"] = datetime.fromisoformat(node_data["updated_at"])
                node = KnowledgeNode(**node_data)
                self.nodes[node_id] = node
                self.graph.add_node(node_id, **asdict(node))
            
            # Load edges
            for edge_id, edge_data in data.get("edges", {}).items():
                edge_data["relationship"] = RelationType(edge_data["relationship"])
                edge_data["created_at"] = datetime.fromisoformat(edge_data["created_at"])
                edge = KnowledgeEdge(**edge_data)
                self.edges[edge_id] = edge
                self.graph.add_edge(
                    edge.source_id,
                    edge.target_id,
                    key=edge_id,
                    **asdict(edge)
                )
            
            self.logger.info(f"Loaded knowledge graph with {len(self.nodes)} nodes and {len(self.edges)} edges")
            
        except Exception as e:
            self.logger.error(f"Error loading graph: {e}")
    
    async def _rebuild_indexes(self):
        """Rebuild all indexes"""
        # Clear indexes
        self.node_type_index.clear()
        self.relationship_index.clear()
        self.text_index.clear()
        
        # Rebuild node type index
        for node_id, node in self.nodes.items():
            self.node_type_index[node.type].add(node_id)
        
        # Rebuild relationship index
        for edge_id, edge in self.edges.items():
            self.relationship_index[edge.relationship].add(edge_id)
        
        # Rebuild text index
        for node_id, node in self.nodes.items():
            text_content = f"{node.label} {json.dumps(node.properties)}"
            words = text_content.lower().split()
            for word in words:
                # Clean up punctuation from JSON formatting
                clean_word = word.strip('{}[],:"')
                if clean_word:
                    self.text_index[clean_word].add(node_id)
        
        # Invalidate vectors for rebuild
        self._invalidate_vectors()
    
    async def _text_search(self, query: str) -> Set[str]:
        """Perform text search on nodes"""
        query_words = query.lower().split()
        matching_ids = set()
        
        for word in query_words:
            if word in self.text_index:
                if not matching_ids:
                    matching_ids = self.text_index[word].copy()
                else:
                    matching_ids &= self.text_index[word]
        
        return matching_ids if matching_ids else set()
    
    async def _build_vectors(self):
        """Build TF-IDF vectors for semantic search"""
        if self.node_vectors is not None:
            return
        
        try:
            # Collect node texts
            self.node_texts = []
            self.node_ids = []
            
            for node_id, node in self.nodes.items():
                text = f"{node.label} {json.dumps(node.properties)}"
                self.node_texts.append(text)
                self.node_ids.append(node_id)
            
            if len(self.node_texts) > 0:
                # Fit vectorizer and transform
                self.node_vectors = self.vectorizer.fit_transform(self.node_texts)
            
        except Exception as e:
            self.logger.error(f"Error building vectors: {e}")
    
    def _invalidate_vectors(self):
        """Invalidate vectors to force rebuild"""
        self.node_vectors = None
        self.node_texts = []
        self.node_ids = []


# Example usage and testing
async def main():
    """Example usage of the Knowledge Graph"""
    kg = KnowledgeGraph()
    await kg.initialize()
    
    # Create some sample nodes
    concept_node = KnowledgeNode(
        id="concept_001",
        type=NodeType.CONCEPT,
        label="REST API",
        properties={"domain": "web_development", "complexity": "medium"},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    solution_node = KnowledgeNode(
        id="solution_001",
        type=NodeType.SOLUTION,
        label="JWT Authentication Implementation",
        properties={"language": "python", "framework": "fastapi"},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Add nodes
    await kg.add_node(concept_node)
    await kg.add_node(solution_node)
    
    # Create relationship
    edge = KnowledgeEdge(
        id="edge_001",
        source_id=solution_node.id,
        target_id=concept_node.id,
        relationship=RelationType.IMPLEMENTS,
        weight=0.9,
        properties={"confidence": 0.9},
        created_at=datetime.now()
    )
    
    await kg.add_edge(edge)
    
    # Query the graph
    query = GraphQuery(
        node_types=[NodeType.CONCEPT],
        text_query="REST API"
    )
    
    results = await kg.query_nodes(query)
    print(f"Found {len(results)} concept nodes related to REST API")
    
    # Find neighbors
    neighbors = await kg.get_neighbors(concept_node.id)
    print(f"Found {len(neighbors['in'])} incoming and {len(neighbors['out'])} outgoing neighbors")
    
    # Save the graph
    await kg.save_graph()


if __name__ == "__main__":
    asyncio.run(main())
