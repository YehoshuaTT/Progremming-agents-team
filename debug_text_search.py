import asyncio
import sys
sys.path.append('.')
from tools.knowledge_graph import KnowledgeGraph, KnowledgeNode, NodeType
from datetime import datetime
import json

async def test_text_search():
    kg = KnowledgeGraph()
    await kg.initialize()
    
    node = KnowledgeNode(
        id='solution_001',
        type=NodeType.SOLUTION,
        label='JWT Authentication Implementation',
        properties={'language': 'python', 'framework': 'fastapi'},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    await kg.add_node(node)
    
    # Debug: Check what text is indexed
    text_content = f'{node.label} {json.dumps(node.properties)}'
    words = text_content.lower().split()
    print(f'Text content: {text_content}')
    print(f'Words: {words}')
    
    # Test search
    matching_ids = await kg._text_search('python')
    print(f'Matching IDs for python: {matching_ids}')
    
    # Check text index
    print(f'Text index keys: {list(kg.text_index.keys())}')
    
    # Check if quoted python is in index
    if '"python"' in kg.text_index:
        print(f'Quoted python in text index: {kg.text_index['"python"']}')

if __name__ == "__main__":
    asyncio.run(test_text_search())
