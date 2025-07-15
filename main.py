# main.py - FastAPI application
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import networkx as nx
from neo4j import GraphDatabase
import openai
from datetime import datetime, timedelta
import numpy as np
from sentence_transformers import SentenceTransformer
import json

app = FastAPI(title="Longevity Knowledge Graph API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Node(BaseModel):
    id: str
    type: str  # 'gene', 'pathway', 'hypothesis', 'method', 'result', 'researcher'
    name: str
    properties: Dict[str, Any]
    embedding: Optional[List[float]] = None

class Relationship(BaseModel):
    source: str
    target: str
    type: str  # 'RELATES_TO', 'VALIDATES', 'CONTRADICTS', 'TARGETS', 'USES_METHOD'
    weight: float
    properties: Dict[str, Any]

class HypothesisGap(BaseModel):
    potential_hypothesis: str
    confidence_score: float
    supporting_evidence: List[str]
    missing_connections: List[Dict[str, str]]
    research_priority: str  # 'high', 'medium', 'low'
    suggested_methods: List[str]

class GraphAnalysis(BaseModel):
    total_nodes: int
    total_relationships: int
    hypothesis_gaps: List[HypothesisGap]
    trending_areas: List[Dict[str, Any]]
    knowledge_clusters: List[Dict[str, Any]]

# Database connection
class KnowledgeGraphDB:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def create_node(self, node: Node):
        with self.driver.session() as session:
            query = f"""
            CREATE (n:{node.type} {{
                id: $id,
                name: $name,
                created_at: datetime(),
                properties: $properties
            }})
            RETURN n
            """
            session.run(query, 
                       id=node.id, 
                       name=node.name, 
                       properties=node.properties)
    
    def create_relationship(self, rel: Relationship):
        with self.driver.session() as session:
            query = f"""
            MATCH (a {{id: $source}}), (b {{id: $target}})
            CREATE (a)-[r:{rel.type} {{
                weight: $weight,
                created_at: datetime(),
                properties: $properties
            }}]->(b)
            RETURN r
            """
            session.run(query,
                       source=rel.source,
                       target=rel.target,
                       weight=rel.weight,
                       properties=rel.properties)
    
    def get_graph_data(self):
        with self.driver.session() as session:
            query = """
            MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT 1000
            """
            result = session.run(query)
            return [record for record in result]

# Network Analysis Engine
class NetworkAnalyzer:
    def __init__(self, db: KnowledgeGraphDB):
        self.db = db
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def build_networkx_graph(self) -> nx.Graph:
        """Конвертирует Neo4j граф в NetworkX для анализа"""
        G = nx.Graph()
        
        graph_data = self.db.get_graph_data()
        for record in graph_data:
            node1 = record['n']
            node2 = record['m']
            relationship = record['r']
            
            G.add_node(node1['id'], **node1)
            G.add_node(node2['id'], **node2)
            G.add_edge(node1['id'], node2['id'], 
                      type=relationship.type,
                      weight=relationship.get('weight', 1.0))
        
        return G
    
    def find_hypothesis_gaps(self, G: nx.Graph) -> List[HypothesisGap]:
        """Находит потенциальные гипотезы через анализ пробелов в сети"""
        gaps = []
        
        # 1. Анализ недостающих связей между биологическими процессами
        gaps.extend(self._find_missing_pathway_connections(G))
        
        # 2. Поиск неисследованных комбинаций методов
        gaps.extend(self._find_untested_method_combinations(G))
        
        # 3. Анализ изолированных узлов с высоким потенциалом
        gaps.extend(self._find_isolated_high_potential_nodes(G))
        
        # 4. Поиск паттернов, которые повторяются, но не обобщены
        gaps.extend(self._find_pattern_gaps(G))
        
        return sorted(gaps, key=lambda x: x.confidence_score, reverse=True)
    
    def _find_missing_pathway_connections(self, G: nx.Graph) -> List[HypothesisGap]:
        """Ищет связи между pathway, которые логически должны существовать"""
        gaps = []
        
        pathway_nodes = [n for n, d in G.nodes(data=True) 
                        if d.get('type') == 'pathway']
        
        for i, pathway1 in enumerate(pathway_nodes):
            for pathway2 in pathway_nodes[i+1:]:
                if not G.has_edge(pathway1, pathway2):
                    # Проверяем семантическую близость
                    embedding1 = self._get_node_embedding(G, pathway1)
                    embedding2 = self._get_node_embedding(G, pathway2)
                    
                    if embedding1 is not None and embedding2 is not None:
                        similarity = np.dot(embedding1, embedding2) / (
                            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
                        )
                        
                        if similarity > 0.7:  # Высокая семантическая близость
                            # Проверяем, есть ли общие соседи
                            common_neighbors = set(G.neighbors(pathway1)) & set(G.neighbors(pathway2))
                            
                            if len(common_neighbors) >= 2:
                                gap = HypothesisGap(
                                    potential_hypothesis=f"Pathway {G.nodes[pathway1]['name']} может регулировать {G.nodes[pathway2]['name']} через {len(common_neighbors)} общих мишеней",
                                    confidence_score=similarity * (len(common_neighbors) / 10),
                                    supporting_evidence=[f"Общие мишени: {[G.nodes[n]['name'] for n in list(common_neighbors)[:3]]}"],
                                    missing_connections=[{"source": pathway1, "target": pathway2, "type": "REGULATES"}],
                                    research_priority="high" if similarity > 0.8 else "medium",
                                    suggested_methods=["Pathway enrichment analysis", "Co-expression analysis", "Proteomics"]
                                )
                                gaps.append(gap)
        
        return gaps
    
    def _find_untested_method_combinations(self, G: nx.Graph) -> List[HypothesisGap]:
        """Ищет комбинации методов, которые не применялись вместе"""
        gaps = []
        
        method_nodes = [n for n, d in G.nodes(data=True) 
                       if d.get('type') == 'method']
        
        # Анализируем успешные комбинации методов
        successful_combinations = self._get_successful_method_combinations(G)
        
        for i, method1 in enumerate(method_nodes):
            for method2 in method_nodes[i+1:]:
                combo_key = tuple(sorted([method1, method2]))
                
                if combo_key not in successful_combinations:
                    # Проверяем совместимость методов
                    compatibility = self._assess_method_compatibility(G, method1, method2)
                    
                    if compatibility > 0.6:
                        target_areas = self._find_potential_application_areas(G, method1, method2)
                        
                        if target_areas:
                            gap = HypothesisGap(
                                potential_hypothesis=f"Комбинация {G.nodes[method1]['name']} + {G.nodes[method2]['name']} может дать новые инсайты в {target_areas[0]}",
                                confidence_score=compatibility,
                                supporting_evidence=[f"Методы совместимы (score: {compatibility:.2f})", f"Потенциальное применение: {target_areas}"],
                                missing_connections=[{"source": method1, "target": method2, "type": "COMBINES_WITH"}],
                                research_priority="medium",
                                suggested_methods=["Pilot study", "Feasibility analysis"]
                            )
                            gaps.append(gap)
        
        return gaps
    
    def _find_isolated_high_potential_nodes(self, G: nx.Graph) -> List[HypothesisGap]:
        """Находит изолированные узлы с высоким потенциалом для исследований"""
        gaps = []
        
        for node_id, node_data in G.nodes(data=True):
            degree = G.degree(node_id)
            
            # Ищем узлы с малым количеством связей, но высокой важностью
            if degree <= 2 and node_data.get('type') in ['gene', 'pathway', 'method']:
                # Оцениваем потенциал на основе метаданных
                potential_score = self._calculate_research_potential(node_data)
                
                if potential_score > 0.7:
                    # Ищем похожие узлы с большим количеством связей
                    similar_connected_nodes = self._find_similar_well_connected_nodes(G, node_id)
                    
                    if similar_connected_nodes:
                        gap = HypothesisGap(
                            potential_hypothesis=f"{node_data['name']} может играть важную роль в longevity, аналогично {similar_connected_nodes[0]['name']}",
                            confidence_score=potential_score,
                            supporting_evidence=[f"Высокий потенциал (score: {potential_score:.2f})", f"Похожие хорошо изученные узлы: {[n['name'] for n in similar_connected_nodes[:2]]}"],
                            missing_connections=[{"source": node_id, "target": similar_connected_nodes[0]['id'], "type": "SIMILAR_FUNCTION"}],
                            research_priority="high",
                            suggested_methods=["Literature review", "Functional analysis", "Comparative study"]
                        )
                        gaps.append(gap)
        
        return gaps
    
    def _find_pattern_gaps(self, G: nx.Graph) -> List[HypothesisGap]:
        """Ищет повторяющиеся паттерны, которые не обобщены в гипотезы"""
        gaps = []
        
        # Ищем мотивы в графе (треугольники, звезды и т.д.)
        triangles = [list(triangle) for triangle in nx.enumerate_all_cliques(G) if len(triangle) == 3]
        
        # Группируем треугольники по типам узлов
        pattern_groups = {}
        for triangle in triangles:
            types = tuple(sorted([G.nodes[node]['type'] for node in triangle]))
            if types not in pattern_groups:
                pattern_groups[types] = []
            pattern_groups[types].append(triangle)
        
        # Ищем паттерны, которые повторяются часто, но не имеют общих гипотез
        for pattern_type, instances in pattern_groups.items():
            if len(instances) >= 3:  # Паттерн повторяется минимум 3 раза
                # Проверяем, есть ли гипотеза, объясняющая этот паттерн
                if not self._has_explaining_hypothesis(G, pattern_type, instances):
                    gap = HypothesisGap(
                        potential_hypothesis=f"Существует общий механизм для паттерна {' + '.join(pattern_type)} в longevity research",
                        confidence_score=min(0.9, len(instances) / 10),
                        supporting_evidence=[f"Паттерн повторяется {len(instances)} раз", f"Примеры: {[G.nodes[inst[0]]['name'] for inst in instances[:3]]}"],
                        missing_connections=[{"pattern": str(pattern_type), "instances": len(instances), "type": "GENERAL_MECHANISM"}],
                        research_priority="medium",
                        suggested_methods=["Meta-analysis", "Systems biology approach", "Pathway analysis"]
                    )
                    gaps.append(gap)
        
        return gaps
    
    def _get_node_embedding(self, G: nx.Graph, node_id: str):
        """Получает embedding для узла"""
        node = G.nodes[node_id]
        text = f"{node.get('name', '')} {node.get('description', '')}"
        if text.strip():
            return self.model.encode(text)
        return None
    
    def _get_successful_method_combinations(self, G: nx.Graph):
        """Анализирует успешные комбинации методов"""
        combinations = set()
        
        # Ищем research результаты, которые использовали несколько методов
        for node_id, node_data in G.nodes(data=True):
            if node_data.get('type') == 'result':
                methods = [neighbor for neighbor in G.neighbors(node_id) 
                          if G.nodes[neighbor].get('type') == 'method']
                if len(methods) >= 2:
                    for i in range(len(methods)):
                        for j in range(i+1, len(methods)):
                            combinations.add(tuple(sorted([methods[i], methods[j]])))
        
        return combinations
    
    def _assess_method_compatibility(self, G: nx.Graph, method1: str, method2: str):
        """Оценивает совместимость двух методов"""
        # Простая эвристика на основе типов данных и областей применения
        method1_data = G.nodes[method1]
        method2_data = G.nodes[method2]
        
        # Проверяем семантическую близость
        embedding1 = self._get_node_embedding(G, method1)
        embedding2 = self._get_node_embedding(G, method2)
        
        if embedding1 is not None and embedding2 is not None:
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            return max(0, similarity)
        
        return 0.5  # Базовая совместимость
    
    def _find_potential_application_areas(self, G: nx.Graph, method1: str, method2: str):
        """Находит области применения для комбинации методов"""
        areas = []
        
        # Ищем общие области применения методов
        method1_targets = set(G.neighbors(method1))
        method2_targets = set(G.neighbors(method2))
        
        common_areas = method1_targets & method2_targets
        for area in common_areas:
            if G.nodes[area].get('type') in ['pathway', 'gene', 'hypothesis']:
                areas.append(G.nodes[area]['name'])
        
        return areas[:3]  # Возвращаем топ-3
    
    def _calculate_research_potential(self, node_data):
        """Оценивает исследовательский потенциал узла"""
        score = 0.5  # Базовый score
        
        # Добавляем score на основе метаданных
        if 'recent_mentions' in node_data.get('properties', {}):
            score += min(0.3, node_data['properties']['recent_mentions'] / 100)
        
        if 'clinical_relevance' in node_data.get('properties', {}):
            score += node_data['properties']['clinical_relevance'] * 0.2
        
        return min(1.0, score)
    
    def _find_similar_well_connected_nodes(self, G: nx.Graph, node_id: str):
        """Находит похожие узлы с большим количеством связей"""
        target_node = G.nodes[node_id]
        similar_nodes = []
        
        for other_id, other_data in G.nodes(data=True):
            if (other_id != node_id and 
                other_data.get('type') == target_node.get('type') and
                G.degree(other_id) > 5):
                
                # Проверяем семантическую близость
                embedding1 = self._get_node_embedding(G, node_id)
                embedding2 = self._get_node_embedding(G, other_id)
                
                if embedding1 is not None and embedding2 is not None:
                    similarity = np.dot(embedding1, embedding2) / (
                        np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
                    )
                    
                    if similarity > 0.6:
                        similar_nodes.append({
                            'id': other_id,
                            'name': other_data['name'],
                            'similarity': similarity,
                            'degree': G.degree(other_id)
                        })
        
        return sorted(similar_nodes, key=lambda x: x['similarity'], reverse=True)[:3]
    
    def _has_explaining_hypothesis(self, G: nx.Graph, pattern_type, instances):
        """Проверяет, есть ли гипотеза, объясняющая паттерн"""
        # Ищем hypothesis узлы, которые связаны с элементами паттерна
        hypothesis_nodes = [n for n, d in G.nodes(data=True) 
                          if d.get('type') == 'hypothesis']
        
        for hyp_node in hypothesis_nodes:
            connected_to_pattern = 0
            for instance in instances:
                for node in instance:
                    if G.has_edge(hyp_node, node):
                        connected_to_pattern += 1
                        break
            
            # Если гипотеза связана с большинством экземпляров паттерна
            if connected_to_pattern >= len(instances) * 0.7:
                return True
        
        return False

# Global instances
db = KnowledgeGraphDB()
analyzer = NetworkAnalyzer(db)

# API Endpoints
@app.get("/api/v1/graph/analysis", response_model=GraphAnalysis)
async def get_graph_analysis():
    """Получает полный анализ графа знаний с выявлением пробелов"""
    try:
        G = analyzer.build_networkx_graph()
        hypothesis_gaps = analyzer.find_hypothesis_gaps(G)
        
        # Анализ трендов (упрощенная версия для MVP)
        trending_areas = []
        knowledge_clusters = []
        
        return GraphAnalysis(
            total_nodes=G.number_of_nodes(),
            total_relationships=G.number_of_edges(),
            hypothesis_gaps=hypothesis_gaps,
            trending_areas=trending_areas,
            knowledge_clusters=knowledge_clusters
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/graph/hypothesis-gaps")
async def get_hypothesis_gaps():
    """Получает только пробелы в гипотезах"""
    try:
        G = analyzer.build_networkx_graph()
        gaps = analyzer.find_hypothesis_gaps(G)
        return {"hypothesis_gaps": gaps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/graph/nodes")
async def create_node(node: Node):
    """Создает новый узел в графе"""
    try:
        db.create_node(node)
        return {"status": "success", "node_id": node.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/graph/relationships")
async def create_relationship(relationship: Relationship):
    """Создает новую связь в графе"""
    try:
        db.create_relationship(relationship)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/graph/search")
async def search_graph(query: str, node_type: Optional[str] = None):
    """Поиск по графу знаний"""
    try:
        # Реализация поиска (упрощенная версия для MVP)
        return {"results": [], "query": query}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
