"""
Test suite for the Knowledge Graph system
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from tools.knowledge_graph import (
    KnowledgeGraph, KnowledgeNode, KnowledgeEdge,
    NodeType, RelationType, GraphQuery
)


class TestKnowledgeGraph:
    """Test cases for the Knowledge Graph system"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def knowledge_graph(self, temp_dir):
        """Create a knowledge graph instance for testing"""
        storage_path = Path(temp_dir) / "test_kg.json"
        return KnowledgeGraph(storage_path=str(storage_path))
    
    @pytest.fixture
    def sample_nodes(self):
        """Create sample nodes for testing"""
        return [
            KnowledgeNode(
                id="concept_001",
                type=NodeType.CONCEPT,
                label="REST API",
                properties={"domain": "web_development", "complexity": "medium"},
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            KnowledgeNode(
                id="solution_001",
                type=NodeType.SOLUTION,
                label="JWT Authentication Implementation",
                properties={"language": "python", "framework": "fastapi"},
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            KnowledgeNode(
                id="pattern_001",
                type=NodeType.PATTERN,
                label="Authentication Pattern",
                properties={"category": "security", "usage": "high"},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
    
    @pytest.fixture
    def sample_edges(self):
        """Create sample edges for testing"""
        return [
            KnowledgeEdge(
                id="edge_001",
                source_id="solution_001",
                target_id="concept_001",
                relationship=RelationType.IMPLEMENTS,
                weight=0.9,
                properties={"confidence": 0.9},
                created_at=datetime.now()
            ),
            KnowledgeEdge(
                id="edge_002",
                source_id="solution_001",
                target_id="pattern_001",
                relationship=RelationType.USES,
                weight=0.8,
                properties={"confidence": 0.8},
                created_at=datetime.now()
            )
        ]
    
    @pytest.mark.asyncio
    async def test_graph_initialization(self, knowledge_graph):
        """Test knowledge graph initialization"""
        await knowledge_graph.initialize()
        
        assert knowledge_graph.nodes == {}
        assert knowledge_graph.edges == {}
        assert len(knowledge_graph.node_type_index) == 0
        assert len(knowledge_graph.relationship_index) == 0
    
    @pytest.mark.asyncio
    async def test_add_node(self, knowledge_graph, sample_nodes):
        """Test adding nodes to the graph"""
        await knowledge_graph.initialize()
        
        # Add first node
        result = await knowledge_graph.add_node(sample_nodes[0])
        assert result is True
        assert sample_nodes[0].id in knowledge_graph.nodes
        assert sample_nodes[0].id in knowledge_graph.node_type_index[NodeType.CONCEPT]
        
        # Add second node
        result = await knowledge_graph.add_node(sample_nodes[1])
        assert result is True
        assert sample_nodes[1].id in knowledge_graph.nodes
        assert sample_nodes[1].id in knowledge_graph.node_type_index[NodeType.SOLUTION]
    
    @pytest.mark.asyncio
    async def test_add_edge(self, knowledge_graph, sample_nodes, sample_edges):
        """Test adding edges to the graph"""
        await knowledge_graph.initialize()
        
        # Add nodes first
        for node in sample_nodes:
            await knowledge_graph.add_node(node)
        
        # Add edge
        result = await knowledge_graph.add_edge(sample_edges[0])
        assert result is True
        assert sample_edges[0].id in knowledge_graph.edges
        assert sample_edges[0].id in knowledge_graph.relationship_index[RelationType.IMPLEMENTS]
        
        # Test edge with missing nodes
        invalid_edge = KnowledgeEdge(
            id="invalid_edge",
            source_id="nonexistent_001",
            target_id="nonexistent_002",
            relationship=RelationType.RELATES_TO,
            weight=0.5,
            properties={},
            created_at=datetime.now()
        )
        
        result = await knowledge_graph.add_edge(invalid_edge)
        assert result is False
        assert invalid_edge.id not in knowledge_graph.edges
    
    @pytest.mark.asyncio
    async def test_get_node_and_edge(self, knowledge_graph, sample_nodes, sample_edges):
        """Test retrieving nodes and edges"""
        await knowledge_graph.initialize()
        
        # Add nodes and edges
        for node in sample_nodes:
            await knowledge_graph.add_node(node)
        
        for edge in sample_edges:
            await knowledge_graph.add_edge(edge)
        
        # Test getting node
        retrieved_node = await knowledge_graph.get_node(sample_nodes[0].id)
        assert retrieved_node is not None
        assert retrieved_node.id == sample_nodes[0].id
        assert retrieved_node.label == sample_nodes[0].label
        
        # Test getting edge
        retrieved_edge = await knowledge_graph.get_edge(sample_edges[0].id)
        assert retrieved_edge is not None
        assert retrieved_edge.id == sample_edges[0].id
        assert retrieved_edge.relationship == sample_edges[0].relationship
        
        # Test getting nonexistent items
        assert await knowledge_graph.get_node("nonexistent") is None
        assert await knowledge_graph.get_edge("nonexistent") is None
    
    @pytest.mark.asyncio
    async def test_query_nodes(self, knowledge_graph, sample_nodes):
        """Test querying nodes with different criteria"""
        await knowledge_graph.initialize()
        
        # Add nodes
        for node in sample_nodes:
            await knowledge_graph.add_node(node)
        
        # Query by node type
        query = GraphQuery(node_types=[NodeType.CONCEPT])
        results = await knowledge_graph.query_nodes(query)
        assert len(results) == 1
        assert results[0].type == NodeType.CONCEPT
        
        # Query by properties
        query = GraphQuery(properties={"domain": "web_development"})
        results = await knowledge_graph.query_nodes(query)
        assert len(results) == 1
        assert results[0].properties["domain"] == "web_development"
        
        # Query by text
        query = GraphQuery(text_query="REST API")
        results = await knowledge_graph.query_nodes(query)
        assert len(results) == 1
        assert "REST API" in results[0].label
        
        # Combined query
        query = GraphQuery(
            node_types=[NodeType.SOLUTION],
            properties={"language": "python"}
        )
        results = await knowledge_graph.query_nodes(query)
        assert len(results) == 1
        assert results[0].type == NodeType.SOLUTION
        assert results[0].properties["language"] == "python"
    
    @pytest.mark.asyncio
    async def test_find_path(self, knowledge_graph, sample_nodes, sample_edges):
        """Test finding paths between nodes"""
        await knowledge_graph.initialize()
        
        # Add nodes and edges
        for node in sample_nodes:
            await knowledge_graph.add_node(node)
        
        for edge in sample_edges:
            await knowledge_graph.add_edge(edge)
        
        # Find path from solution to concept
        paths = await knowledge_graph.find_path(
            sample_nodes[1].id,  # solution
            sample_nodes[0].id   # concept
        )
        assert len(paths) >= 1
        assert paths[0][0] == sample_nodes[1].id
        assert paths[0][-1] == sample_nodes[0].id
        
        # Find path with relationship filter
        paths = await knowledge_graph.find_path(
            sample_nodes[1].id,
            sample_nodes[0].id,
            relationship_types=[RelationType.IMPLEMENTS]
        )
        assert len(paths) >= 1
        
        # Find path between unconnected nodes
        paths = await knowledge_graph.find_path(
            sample_nodes[0].id,
            sample_nodes[1].id
        )
        assert len(paths) == 0
    
    @pytest.mark.asyncio
    async def test_get_neighbors(self, knowledge_graph, sample_nodes, sample_edges):
        """Test getting neighboring nodes"""
        await knowledge_graph.initialize()
        
        # Add nodes and edges
        for node in sample_nodes:
            await knowledge_graph.add_node(node)
        
        for edge in sample_edges:
            await knowledge_graph.add_edge(edge)
        
        # Get neighbors of concept node (should have incoming edges)
        neighbors = await knowledge_graph.get_neighbors(sample_nodes[0].id)
        assert len(neighbors["in"]) == 1
        assert len(neighbors["out"]) == 0
        assert neighbors["in"][0].id == sample_nodes[1].id
        
        # Get neighbors of solution node (should have outgoing edges)
        neighbors = await knowledge_graph.get_neighbors(sample_nodes[1].id)
        assert len(neighbors["in"]) == 0
        assert len(neighbors["out"]) == 2
        
        # Get neighbors with relationship filter
        neighbors = await knowledge_graph.get_neighbors(
            sample_nodes[1].id,
            relationship_types=[RelationType.IMPLEMENTS]
        )
        assert len(neighbors["out"]) == 1
        assert neighbors["out"][0].id == sample_nodes[0].id
    
    @pytest.mark.asyncio
    async def test_find_similar_nodes(self, knowledge_graph, sample_nodes):
        """Test finding semantically similar nodes"""
        await knowledge_graph.initialize()
        
        # Add nodes
        for node in sample_nodes:
            await knowledge_graph.add_node(node)
        
        # Add a similar node
        similar_node = KnowledgeNode(
            id="concept_002",
            type=NodeType.CONCEPT,
            label="RESTful API Design",
            properties={"domain": "web_development", "complexity": "medium"},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        await knowledge_graph.add_node(similar_node)
        
        # Find similar nodes
        similar = await knowledge_graph.find_similar_nodes(
            sample_nodes[0].id,
            similarity_threshold=0.1
        )
        
        # Should find at least one similar node
        assert len(similar) >= 1
        
        # Check similarity scores
        for node, score in similar:
            assert 0 <= score <= 1
            assert node.id != sample_nodes[0].id
    
    @pytest.mark.asyncio
    async def test_get_subgraph(self, knowledge_graph, sample_nodes, sample_edges):
        """Test extracting subgraphs"""
        await knowledge_graph.initialize()
        
        # Add nodes and edges
        for node in sample_nodes:
            await knowledge_graph.add_node(node)
        
        for edge in sample_edges:
            await knowledge_graph.add_edge(edge)
        
        # Get subgraph around solution node
        subgraph = await knowledge_graph.get_subgraph(
            sample_nodes[1].id,
            depth=1
        )
        
        assert len(subgraph["nodes"]) == 3  # solution + 2 connected nodes
        assert len(subgraph["edges"]) == 2  # 2 edges from solution
        assert subgraph["center"].id == sample_nodes[1].id
        
        # Get subgraph with filters
        subgraph = await knowledge_graph.get_subgraph(
            sample_nodes[1].id,
            depth=1,
            node_types=[NodeType.CONCEPT, NodeType.SOLUTION]
        )
        
        # Should include solution (center) and concept nodes
        concept_nodes = [n for n in subgraph["nodes"] if n.type == NodeType.CONCEPT]
        assert len(concept_nodes) >= 1
    
    @pytest.mark.asyncio
    async def test_analyze_centrality(self, knowledge_graph, sample_nodes, sample_edges):
        """Test centrality analysis"""
        await knowledge_graph.initialize()
        
        # Add nodes and edges
        for node in sample_nodes:
            await knowledge_graph.add_node(node)
        
        for edge in sample_edges:
            await knowledge_graph.add_edge(edge)
        
        # Analyze centrality
        centrality = await knowledge_graph.analyze_centrality()
        
        # Should have centrality measures for all nodes
        assert len(centrality) == len(sample_nodes)
        
        # Check centrality measures
        for node_id, measures in centrality.items():
            assert "degree" in measures
            assert "betweenness" in measures
            assert "closeness" in measures
            assert "pagerank" in measures
            
            # All measures should be between 0 and 1
            for measure, value in measures.items():
                assert 0 <= value <= 1
    
    @pytest.mark.asyncio
    async def test_detect_communities(self, knowledge_graph, sample_nodes, sample_edges):
        """Test community detection"""
        await knowledge_graph.initialize()
        
        # Add nodes and edges
        for node in sample_nodes:
            await knowledge_graph.add_node(node)
        
        for edge in sample_edges:
            await knowledge_graph.add_edge(edge)
        
        # Detect communities
        communities = await knowledge_graph.detect_communities()
        
        # Should detect at least one community
        assert len(communities) >= 1
        
        # All nodes should be in some community
        all_community_nodes = set()
        for community_nodes in communities.values():
            all_community_nodes.update(community_nodes)
        
        assert len(all_community_nodes) == len(sample_nodes)
    
    @pytest.mark.asyncio
    async def test_save_and_load_graph(self, knowledge_graph, sample_nodes, sample_edges):
        """Test saving and loading the graph"""
        await knowledge_graph.initialize()
        
        # Add nodes and edges
        for node in sample_nodes:
            await knowledge_graph.add_node(node)
        
        for edge in sample_edges:
            await knowledge_graph.add_edge(edge)
        
        # Save the graph
        await knowledge_graph.save_graph()
        
        # Create new graph instance and load
        new_graph = KnowledgeGraph(storage_path=str(knowledge_graph.storage_path))
        await new_graph.initialize()
        
        # Verify data was loaded correctly
        assert len(new_graph.nodes) == len(sample_nodes)
        assert len(new_graph.edges) == len(sample_edges)
        
        # Check specific nodes and edges
        for node in sample_nodes:
            loaded_node = await new_graph.get_node(node.id)
            assert loaded_node is not None
            assert loaded_node.label == node.label
            assert loaded_node.type == node.type
        
        for edge in sample_edges:
            loaded_edge = await new_graph.get_edge(edge.id)
            assert loaded_edge is not None
            assert loaded_edge.relationship == edge.relationship
            assert loaded_edge.weight == edge.weight
    
    @pytest.mark.asyncio
    async def test_text_search(self, knowledge_graph, sample_nodes):
        """Test text search functionality"""
        await knowledge_graph.initialize()
        
        # Add nodes
        for node in sample_nodes:
            await knowledge_graph.add_node(node)
        
        # Test text search
        matching_ids = await knowledge_graph._text_search("REST API")
        assert len(matching_ids) == 1
        assert sample_nodes[0].id in matching_ids
        
        # Test multi-word search
        matching_ids = await knowledge_graph._text_search("JWT Authentication")
        assert len(matching_ids) == 1
        assert sample_nodes[1].id in matching_ids
        
        # Test property search
        matching_ids = await knowledge_graph._text_search("python")
        assert len(matching_ids) >= 1
        assert sample_nodes[1].id in matching_ids
    
    @pytest.mark.asyncio
    async def test_vector_building(self, knowledge_graph, sample_nodes):
        """Test TF-IDF vector building"""
        await knowledge_graph.initialize()
        
        # Add nodes
        for node in sample_nodes:
            await knowledge_graph.add_node(node)
        
        # Build vectors
        await knowledge_graph._build_vectors()
        
        # Check vectors were built
        assert knowledge_graph.node_vectors is not None
        assert len(knowledge_graph.node_texts) == len(sample_nodes)
        assert len(knowledge_graph.node_ids) == len(sample_nodes)
        
        # Check vector dimensions
        assert knowledge_graph.node_vectors.shape[0] == len(sample_nodes)
    
    @pytest.mark.asyncio
    async def test_index_rebuilding(self, knowledge_graph, sample_nodes):
        """Test index rebuilding"""
        await knowledge_graph.initialize()
        
        # Add nodes
        for node in sample_nodes:
            await knowledge_graph.add_node(node)
        
        # Check initial indexes
        assert len(knowledge_graph.node_type_index) > 0
        assert len(knowledge_graph.text_index) > 0
        
        # Rebuild indexes
        await knowledge_graph._rebuild_indexes()
        
        # Check indexes were rebuilt correctly
        assert len(knowledge_graph.node_type_index[NodeType.CONCEPT]) == 1
        assert len(knowledge_graph.node_type_index[NodeType.SOLUTION]) == 1
        assert len(knowledge_graph.node_type_index[NodeType.PATTERN]) == 1
        
        # Check text index
        assert len(knowledge_graph.text_index) > 0
        assert sample_nodes[0].id in knowledge_graph.text_index["rest"]
        assert sample_nodes[1].id in knowledge_graph.text_index["jwt"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
