"""
Solution Search System
Advanced search capabilities for the solutions archive
"""

import re
import json
import math
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
import logging
from datetime import datetime

from .solutions_archive import SolutionsArchive, SolutionEntry, SolutionType

logger = logging.getLogger(__name__)

class SolutionSearchEngine:
    """Advanced search engine for solutions with semantic matching"""
    
    def __init__(self, archive: SolutionsArchive):
        self.archive = archive
        self.stopwords = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'were', 'will', 'with', 'the', 'this', 'but', 'they',
            'have', 'had', 'what', 'said', 'each', 'which', 'their', 'time',
            'if', 'up', 'out', 'many', 'then', 'them', 'these', 'so', 'some',
            'her', 'would', 'make', 'like', 'into', 'him', 'two', 'more',
            'go', 'no', 'way', 'could', 'my', 'than', 'first', 'been', 'call',
            'who', 'oil', 'sit', 'now', 'find', 'long', 'down', 'day', 'did',
            'get', 'come', 'made', 'may', 'part'
        }
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into keywords"""
        # Convert to lowercase and remove special characters
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
        
        # Split into words
        words = text.split()
        
        # Remove stopwords and short words
        tokens = [word for word in words if word not in self.stopwords and len(word) > 2]
        
        return tokens
    
    def _calculate_tfidf(self, query_tokens: List[str], document_tokens: List[str], 
                        all_documents: List[List[str]]) -> float:
        """Calculate TF-IDF score for document relevance"""
        if not query_tokens or not document_tokens:
            return 0.0
        
        # Term frequency
        doc_counter = Counter(document_tokens)
        query_counter = Counter(query_tokens)
        
        score = 0.0
        total_docs = len(all_documents)
        
        for term in query_tokens:
            # Term frequency in document
            tf = doc_counter.get(term, 0) / len(document_tokens)
            
            # Document frequency
            df = sum(1 for doc in all_documents if term in doc)
            
            # Inverse document frequency
            idf = math.log(total_docs / (df + 1))
            
            # TF-IDF score
            score += tf * idf * query_counter[term]
        
        return score
    
    def _calculate_semantic_similarity(self, query_tokens: List[str], 
                                     document_tokens: List[str]) -> float:
        """Calculate semantic similarity between query and document"""
        if not query_tokens or not document_tokens:
            return 0.0
        
        # Jaccard similarity
        query_set = set(query_tokens)
        doc_set = set(document_tokens)
        
        intersection = len(query_set & doc_set)
        union = len(query_set | doc_set)
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        
        # Cosine similarity based on token frequencies
        query_counter = Counter(query_tokens)
        doc_counter = Counter(document_tokens)
        
        # Get all unique tokens
        all_tokens = set(query_tokens + document_tokens)
        
        # Create vectors
        query_vector = [query_counter.get(token, 0) for token in all_tokens]
        doc_vector = [doc_counter.get(token, 0) for token in all_tokens]
        
        # Calculate cosine similarity
        dot_product = sum(q * d for q, d in zip(query_vector, doc_vector))
        query_magnitude = math.sqrt(sum(q ** 2 for q in query_vector))
        doc_magnitude = math.sqrt(sum(d ** 2 for d in doc_vector))
        
        if query_magnitude == 0 or doc_magnitude == 0:
            cosine = 0.0
        else:
            cosine = dot_product / (query_magnitude * doc_magnitude)
        
        # Combine Jaccard and cosine similarity
        return (jaccard + cosine) / 2
    
    def _extract_solution_context(self, solution: SolutionEntry) -> str:
        """Extract searchable context from solution"""
        context_parts = [
            solution.title,
            solution.description,
            solution.problem_type,
            ' '.join(solution.tags),
            ' '.join(solution.solution_steps),
        ]
        
        # Add code artifacts context
        for artifact in solution.code_artifacts:
            context_parts.append(artifact.get('filename', ''))
            
        return ' '.join(context_parts)
    
    async def semantic_search(self, query: str, limit: int = 10, 
                            min_similarity: float = 0.01) -> List[Tuple[SolutionEntry, float]]:
        """Perform semantic search on solutions"""
        try:
            # Get all solutions
            all_solutions = await self.archive.search_solutions(limit=1000)
            
            if not all_solutions:
                return []
            
            # Tokenize query
            query_tokens = self._tokenize_text(query)
            
            if not query_tokens:
                return []
            
            # Prepare document tokens for TF-IDF
            solution_contexts = []
            solution_tokens = []
            
            for solution in all_solutions:
                context = self._extract_solution_context(solution)
                tokens = self._tokenize_text(context)
                solution_contexts.append(context)
                solution_tokens.append(tokens)
            
            # Calculate scores
            scored_solutions = []
            
            for i, solution in enumerate(all_solutions):
                # Calculate TF-IDF score
                tfidf_score = self._calculate_tfidf(query_tokens, solution_tokens[i], solution_tokens)
                
                # Calculate semantic similarity
                semantic_score = self._calculate_semantic_similarity(query_tokens, solution_tokens[i])
                
                # Combine scores with weights
                combined_score = (tfidf_score * 0.6) + (semantic_score * 0.4)
                
                # Boost score based on solution quality and usage
                quality_boost = solution.quality_score / 5.0
                usage_boost = min(1.0, solution.usage_count / 10.0)
                
                final_score = combined_score * (1 + quality_boost * 0.2 + usage_boost * 0.1)
                
                if final_score >= min_similarity:
                    scored_solutions.append((solution, final_score))
            
            # Sort by score and return top results
            scored_solutions.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"Semantic search found {len(scored_solutions)} relevant solutions")
            
            return scored_solutions[:limit]
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def search_by_problem_pattern(self, problem_description: str, 
                                      solution_type: SolutionType = None,
                                      limit: int = 10) -> List[Tuple[SolutionEntry, float]]:
        """Search for solutions by problem pattern matching"""
        try:
            # Extract key patterns from problem description
            patterns = self._extract_problem_patterns(problem_description)
            
            # Get candidate solutions
            candidates = await self.archive.search_solutions(
                solution_type=solution_type,
                limit=100
            )
            
            scored_solutions = []
            
            for solution in candidates:
                # Calculate pattern match score
                pattern_score = self._calculate_pattern_match(patterns, solution)
                
                if pattern_score > 0:
                    scored_solutions.append((solution, pattern_score))
            
            # Sort by score
            scored_solutions.sort(key=lambda x: x[1], reverse=True)
            
            return scored_solutions[:limit]
            
        except Exception as e:
            logger.error(f"Pattern search failed: {e}")
            return []
    
    def _extract_problem_patterns(self, problem_description: str) -> Dict[str, Any]:
        """Extract key patterns from problem description"""
        patterns = {
            'technologies': [],
            'actions': [],
            'entities': [],
            'constraints': []
        }
        
        text = problem_description.lower()
        
        # Technology patterns
        tech_patterns = [
            r'\b(python|java|javascript|react|angular|vue|node|django|flask|spring)\b',
            r'\b(mysql|postgresql|mongodb|redis|elasticsearch)\b',
            r'\b(docker|kubernetes|aws|azure|gcp)\b',
            r'\b(rest|graphql|grpc|api|microservice)\b',
            r'\b(jwt|oauth|auth|authentication)\b'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, text)
            patterns['technologies'].extend(matches)
        
        # Action patterns
        action_patterns = [
            r'\b(create|build|implement|develop|design|optimize|fix|debug|deploy|test)\b',
            r'\b(integrate|connect|migrate|refactor|scale|monitor|secure)\b'
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, text)
            patterns['actions'].extend(matches)
        
        # Entity patterns
        entity_patterns = [
            r'\b(user|customer|admin|database|server|application|service|component)\b',
            r'\b(authentication|authorization|payment|notification|email|file|image)\b'
        ]
        
        for pattern in entity_patterns:
            matches = re.findall(pattern, text)
            patterns['entities'].extend(matches)
        
        # Constraint patterns
        constraint_patterns = [
            r'\b(performance|security|scalability|reliability|availability)\b',
            r'\b(real-time|batch|concurrent|parallel|distributed)\b'
        ]
        
        for pattern in constraint_patterns:
            matches = re.findall(pattern, text)
            patterns['constraints'].extend(matches)
        
        return patterns
    
    def _calculate_pattern_match(self, patterns: Dict[str, Any], 
                               solution: SolutionEntry) -> float:
        """Calculate how well a solution matches the problem patterns"""
        solution_text = self._extract_solution_context(solution).lower()
        
        total_score = 0.0
        total_weight = 0.0
        
        # Technology match (weight: 0.3)
        if patterns['technologies']:
            tech_matches = sum(1 for tech in patterns['technologies'] if tech in solution_text)
            tech_score = tech_matches / len(patterns['technologies'])
            total_score += tech_score * 0.3
            total_weight += 0.3
        
        # Action match (weight: 0.25)
        if patterns['actions']:
            action_matches = sum(1 for action in patterns['actions'] if action in solution_text)
            action_score = action_matches / len(patterns['actions'])
            total_score += action_score * 0.25
            total_weight += 0.25
        
        # Entity match (weight: 0.25)
        if patterns['entities']:
            entity_matches = sum(1 for entity in patterns['entities'] if entity in solution_text)
            entity_score = entity_matches / len(patterns['entities'])
            total_score += entity_score * 0.25
            total_weight += 0.25
        
        # Constraint match (weight: 0.2)
        if patterns['constraints']:
            constraint_matches = sum(1 for constraint in patterns['constraints'] if constraint in solution_text)
            constraint_score = constraint_matches / len(patterns['constraints'])
            total_score += constraint_score * 0.2
            total_weight += 0.2
        
        if total_weight == 0:
            return 0.0
        
        return total_score / total_weight
    
    async def search_by_code_similarity(self, code_snippet: str, 
                                      limit: int = 10) -> List[Tuple[SolutionEntry, float]]:
        """Search for solutions with similar code patterns"""
        try:
            # Extract code patterns
            code_patterns = self._extract_code_patterns(code_snippet)
            
            # Get all solutions with code artifacts
            all_solutions = await self.archive.search_solutions(limit=1000)
            solutions_with_code = [s for s in all_solutions if s.code_artifacts]
            
            scored_solutions = []
            
            for solution in solutions_with_code:
                # Calculate code similarity score
                similarity_score = self._calculate_code_similarity(code_patterns, solution)
                
                if similarity_score > 0:
                    scored_solutions.append((solution, similarity_score))
            
            # Sort by similarity
            scored_solutions.sort(key=lambda x: x[1], reverse=True)
            
            return scored_solutions[:limit]
            
        except Exception as e:
            logger.error(f"Code similarity search failed: {e}")
            return []
    
    def _extract_code_patterns(self, code_snippet: str) -> Dict[str, Any]:
        """Extract patterns from code snippet"""
        patterns = {
            'functions': [],
            'classes': [],
            'imports': [],
            'keywords': [],
            'patterns': []
        }
        
        lines = code_snippet.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Python function definitions
            if re.match(r'def\s+\w+', line):
                func_name = re.search(r'def\s+(\w+)', line)
                if func_name:
                    patterns['functions'].append(func_name.group(1))
            
            # JavaScript function definitions
            js_func_patterns = [
                r'function\s+(\w+)',  # function name()
                r'(\w+)\s*:\s*function',  # name: function
                r'(\w+)\s*\(\s*\)\s*=>',  # name() =>
                r'(\w+)\s*=\s*\(\s*\)\s*=>',  # name = () =>
                r'async\s+(\w+)\s*\(',  # async name(
                r'(\w+)\s*\([^)]*\)\s*{'  # name() {
            ]
            
            for pattern in js_func_patterns:
                match = re.search(pattern, line)
                if match:
                    patterns['functions'].append(match.group(1))
            
            # Class definitions (Python and JS)
            if re.match(r'class\s+\w+', line):
                class_name = re.search(r'class\s+(\w+)', line)
                if class_name:
                    patterns['classes'].append(class_name.group(1))
            
            # Import statements
            if line.startswith('import ') or line.startswith('from '):
                patterns['imports'].append(line)
            
            # Common patterns
            if 'async' in line:
                patterns['patterns'].append('async')
            if 'await' in line:
                patterns['patterns'].append('await')
            if 'try:' in line or 'except' in line or 'try {' in line or 'catch' in line:
                patterns['patterns'].append('exception_handling')
            if 'return' in line:
                patterns['patterns'].append('return')
        
        return patterns
    
    def _calculate_code_similarity(self, code_patterns: Dict[str, Any], 
                                 solution: SolutionEntry) -> float:
        """Calculate code similarity between patterns and solution"""
        if not solution.code_artifacts:
            return 0.0
        
        solution_code = ' '.join([artifact.get('content', '') for artifact in solution.code_artifacts])
        solution_patterns = self._extract_code_patterns(solution_code)
        
        total_score = 0.0
        total_weight = 0.0
        
        # Function similarity
        if code_patterns['functions']:
            func_matches = len(set(code_patterns['functions']) & set(solution_patterns['functions']))
            func_score = func_matches / len(code_patterns['functions'])
            total_score += func_score * 0.3
            total_weight += 0.3
        
        # Class similarity
        if code_patterns['classes']:
            class_matches = len(set(code_patterns['classes']) & set(solution_patterns['classes']))
            class_score = class_matches / len(code_patterns['classes'])
            total_score += class_score * 0.25
            total_weight += 0.25
        
        # Import similarity
        if code_patterns['imports']:
            import_matches = len(set(code_patterns['imports']) & set(solution_patterns['imports']))
            import_score = import_matches / len(code_patterns['imports'])
            total_score += import_score * 0.2
            total_weight += 0.2
        
        # Pattern similarity
        if code_patterns['patterns']:
            pattern_matches = len(set(code_patterns['patterns']) & set(solution_patterns['patterns']))
            pattern_score = pattern_matches / len(code_patterns['patterns'])
            total_score += pattern_score * 0.25
            total_weight += 0.25
        
        if total_weight == 0:
            return 0.0
        
        return total_score / total_weight
    
    async def get_recommendations(self, agent_id: str, current_task: str, 
                                limit: int = 5) -> List[Tuple[SolutionEntry, str]]:
        """Get personalized solution recommendations for an agent"""
        try:
            # Get agent's previous solutions
            agent_solutions = await self.archive.search_solutions(limit=1000)
            agent_history = [s for s in agent_solutions if s.agent_id == agent_id]
            
            # Analyze agent's patterns
            agent_patterns = self._analyze_agent_patterns(agent_history)
            
            # Get relevant solutions
            relevant_solutions = await self.semantic_search(current_task, limit=20)
            
            # Score based on agent fit
            recommendations = []
            for solution, relevance_score in relevant_solutions:
                fit_score = self._calculate_agent_fit(agent_patterns, solution)
                combined_score = relevance_score * 0.7 + fit_score * 0.3
                
                # Generate recommendation reason
                reason = self._generate_recommendation_reason(solution, relevance_score, fit_score)
                
                recommendations.append((solution, reason))
            
            # Sort by combined score
            recommendations.sort(key=lambda x: x[1], reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return []
    
    def _analyze_agent_patterns(self, agent_solutions: List[SolutionEntry]) -> Dict[str, Any]:
        """Analyze patterns in agent's solution history"""
        if not agent_solutions:
            return {}
        
        patterns = {
            'preferred_types': Counter(),
            'common_tags': Counter(),
            'avg_quality': 0.0,
            'problem_types': Counter(),
            'technologies': Counter()
        }
        
        for solution in agent_solutions:
            patterns['preferred_types'][solution.solution_type.value] += 1
            patterns['common_tags'].update(solution.tags)
            patterns['problem_types'][solution.problem_type] += 1
            
            # Extract technologies from solution context
            context = self._extract_solution_context(solution)
            tech_matches = re.findall(r'\b(python|java|javascript|react|angular|vue|node|django|flask|spring|mysql|postgresql|mongodb|redis|elasticsearch|docker|kubernetes|aws|azure|gcp|rest|graphql|grpc|api|microservice)\b', context.lower())
            patterns['technologies'].update(tech_matches)
        
        patterns['avg_quality'] = sum(s.quality_score for s in agent_solutions) / len(agent_solutions)
        
        return patterns
    
    def _calculate_agent_fit(self, agent_patterns: Dict[str, Any], 
                           solution: SolutionEntry) -> float:
        """Calculate how well a solution fits an agent's patterns"""
        if not agent_patterns:
            return 0.5
        
        fit_score = 0.0
        
        # Solution type preference
        if solution.solution_type.value in agent_patterns['preferred_types']:
            fit_score += 0.3
        
        # Tag overlap
        tag_overlap = len(set(solution.tags) & set(agent_patterns['common_tags'].keys()))
        if solution.tags:
            fit_score += (tag_overlap / len(solution.tags)) * 0.2
        
        # Problem type preference
        if solution.problem_type in agent_patterns['problem_types']:
            fit_score += 0.25
        
        # Technology alignment
        solution_context = self._extract_solution_context(solution).lower()
        tech_matches = 0
        for tech in agent_patterns['technologies'].keys():
            if tech in solution_context:
                tech_matches += 1
        
        if agent_patterns['technologies']:
            fit_score += (tech_matches / len(agent_patterns['technologies'])) * 0.25
        
        return min(1.0, fit_score)
    
    def _generate_recommendation_reason(self, solution: SolutionEntry, 
                                      relevance_score: float, fit_score: float) -> str:
        """Generate a human-readable reason for the recommendation"""
        reasons = []
        
        if relevance_score > 0.7:
            reasons.append("highly relevant to your current task")
        elif relevance_score > 0.5:
            reasons.append("relevant to your current task")
        
        if fit_score > 0.7:
            reasons.append("matches your working style")
        elif fit_score > 0.5:
            reasons.append("aligns with your preferences")
        
        if solution.quality_score > 4.0:
            reasons.append("high quality solution")
        elif solution.quality_score > 3.5:
            reasons.append("good quality solution")
        
        if solution.usage_count > 10:
            reasons.append("frequently used by other agents")
        elif solution.usage_count > 5:
            reasons.append("used by other agents")
        
        if not reasons:
            reasons.append("potentially useful solution")
        
        return f"Recommended because it's {' and '.join(reasons)}"

# Global search engine instance
def get_search_engine() -> SolutionSearchEngine:
    """Get the global search engine instance"""
    from .solutions_archive import solutions_archive
    return SolutionSearchEngine(solutions_archive)

search_engine = get_search_engine()
