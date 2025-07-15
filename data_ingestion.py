# data_ingestion.py - Система загрузки и обработки данных
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Set
import time
import re
from datetime import datetime, timedelta
import spacy
from sentence_transformers import SentenceTransformer
import json
from main import KnowledgeGraphDB, Node, Relationship
import hashlib

# Загружаем модель для NER
nlp = spacy.load("en_core_web_sm")

class PubMedParser:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.email = "your_email@example.com"  # Обязательно для PubMed API
        
        # Ключевые термины для longevity research
        self.longevity_terms = [
            "aging", "longevity", "lifespan", "senescence", "cellular aging",
            "mitochondrial dysfunction", "telomere", "autophagy", "mTOR",
            "sirtuins", "caloric restriction", "oxidative stress", "inflammation",
            "epigenetic aging", "DNA repair", "proteostasis", "senolytic",
            "geroscience", "healthspan", "age-related diseases"
        ]
        
        # Словари для распознавания сущностей
        self.gene_patterns = self._load_gene_patterns()
        self.pathway_patterns = self._load_pathway_patterns()
        self.method_patterns = self._load_method_patterns()
        
    def _load_gene_patterns(self) -> Set[str]:
        """Загружает паттерны для распознавания генов"""
        # Основные гены, связанные с долголетием
        return {
            "TP53", "FOXO1", "FOXO3", "SIRT1", "SIRT2", "SIRT3", "SIRT6",
            "mTOR", "AMPK", "ATG5", "ATG7", "BECN1", "TERT", "TERC",
            "CDKN2A", "CDKN1A", "IGF1", "IGF1R", "APOE", "KLOTHO",
            "NRF2", "NFE2L2", "SOD1", "SOD2", "CAT", "GPX1"
        }
    
    def _load_pathway_patterns(self) -> Set[str]:
        """Загружает паттерны для распознавания pathway"""
        return {
            "mTOR signaling", "autophagy", "DNA repair", "oxidative stress response",
            "insulin signaling", "IGF-1 signaling", "caloric restriction",
            "mitochondrial biogenesis", "telomere maintenance", "senescence",
            "inflammation", "immune response", "circadian rhythm", "proteostasis",
            "unfolded protein response", "apoptosis", "cell cycle regulation"
        }
    
    def _load_method_patterns(self) -> Set[str]:
        """Загружает паттерны для распознавания методов"""
        return {
            "RNA-seq", "scRNA-seq", "proteomics", "metabolomics", "lipidomics",
            "GWAS", "ChIP-seq", "ATAC-seq", "bisulfite sequencing", "methylation analysis",
            "flow cytometry", "immunofluorescence", "western blot", "qPCR",
            "CRISPR", "siRNA", "overexpression", "knockdown", "knockout",
            "mass spectrometry", "NMR", "microscopy", "cell culture"
        }
    
    def search_pubmed(self, query: str, max_results: int = 100) -> List[str]:
        """Поиск статей в PubMed и возвращение PMIDs"""
        search_url = f"{self.base_url}esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "datetype": "pdat",
            "reldate": 365,  # За последний год
            "retmode": "json",
            "email": self.email
        }
        
        try:
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            pmids = data.get("esearchresult", {}).get("idlist", [])
            print(f"Найдено {len(pmids)} статей для запроса: {query}")
            return pmids
            
        except Exception as e:
            print(f"Ошибка поиска в PubMed: {e}")
            return []
    
    def fetch_article_details(self, pmids: List[str]) -> List[Dict]:
        """Получает детали статей по PMIDs"""
        if not pmids:
            return []
            
        fetch_url = f"{self.base_url}efetch.fcgi"
        pmid_string = ",".join(pmids)
        
        params = {
            "db": "pubmed",
            "id": pmid_string,
            "retmode": "xml",
            "email": self.email
        }
        
        try:
            response = requests.get(fetch_url, params=params)
            response.raise_for_status()
            
            return self._parse_pubmed_xml(response.text)
            
        except Exception as e:
            print(f"Ошибка получения деталей статей: {e}")
            return []
    
    def _parse_pubmed_xml(self, xml_content: str) -> List[Dict]:
        """Парсит XML ответ от PubMed"""
        articles = []
        
        try:
            root = ET.fromstring(xml_content)
            
            for article in root.findall(".//PubmedArticle"):
                article_data = self._extract_article_data(article)
                if article_data:
                    articles.append(article_data)
                    
        except ET.ParseError as e:
            print(f"Ошибка парсинга XML: {e}")
            
        return articles
    
    def _extract_article_data(self, article_elem) -> Dict:
        """Извлекает данные из элемента статьи"""
        try:
            # Базовые данные
            pmid_elem = article_elem.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else ""
            
            title_elem = article_elem.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else ""
            
            abstract_elem = article_elem.find(".//AbstractText")
            abstract = abstract_elem.text if abstract_elem is not None else ""
            
            # Дата публикации
            pub_date = self._extract_publication_date(article_elem)
            
            # Авторы
            authors = self._extract_authors(article_elem)
            
            # Журнал
            journal_elem = article_elem.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None else ""
            
            # Keywords/MeSH terms
            keywords = self._extract_keywords(article_elem)
            
            return {
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "publication_date": pub_date,
                "authors": authors,
                "journal": journal,
                "keywords": keywords,
                "full_text": f"{title} {abstract}"
            }
            
        except Exception as e:
            print(f"Ошибка извлечения данных статьи: {e}")
            return {}
    
    def _extract_publication_date(self, article_elem) -> str:
        """Извлекает дату публикации"""
        try:
            pub_date_elem = article_elem.find(".//PubDate")
            if pub_date_elem is not None:
                year = pub_date_elem.find("Year")
                month = pub_date_elem.find("Month")
                day = pub_date_elem.find("Day")
                
                year_text = year.text if year is not None else "2024"
                month_text = month.text if month is not None else "01"
                day_text = day.text if day is not None else "01"
                
                return f"{year_text}-{month_text.zfill(2)}-{day_text.zfill(2)}"
        except:
            pass
        return "2024-01-01"
    
    def _extract_authors(self, article_elem) -> List[str]:
        """Извлекает список авторов"""
        authors = []
        author_list = article_elem.find(".//AuthorList")
        
        if author_list is not None:
            for author in author_list.findall("Author"):
                last_name = author.find("LastName")
                first_name = author.find("ForeName")
                
                if last_name is not None and first_name is not None:
                    authors.append(f"{first_name.text} {last_name.text}")
                elif last_name is not None:
                    authors.append(last_name.text)
        
        return authors
    
    def _extract_keywords(self, article_elem) -> List[str]:
        """Извлекает ключевые слова и MeSH terms"""
        keywords = []
        
        # MeSH terms
        mesh_list = article_elem.find(".//MeshHeadingList")
        if mesh_list is not None:
            for mesh in mesh_list.findall("MeshHeading"):
                descriptor = mesh.find("DescriptorName")
                if descriptor is not None:
                    keywords.append(descriptor.text)
        
        # Keywords
        keyword_list = article_elem.find(".//KeywordList")
        if keyword_list is not None:
            for keyword in keyword_list.findall("Keyword"):
                if keyword.text:
                    keywords.append(keyword.text)
        
        return keywords

class EntityExtractor:
    def __init__(self, parser: PubMedParser):
        self.parser = parser
        self.nlp = nlp
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def extract_entities_from_article(self, article: Dict) -> Dict[str, List[Dict]]:
        """Извлекает сущности из статьи"""
        text = article.get("full_text", "")
        
        entities = {
            "genes": self._extract_genes(text),
            "pathways": self._extract_pathways(text),
            "methods": self._extract_methods(text),
            "researchers": self._extract_researchers(article),
            "hypotheses": self._extract_hypotheses(text)
        }
        
        return entities
    
    def _extract_genes(self, text: str) -> List[Dict]:
        """Извлекает гены из текста"""
        genes = []
        text_upper = text.upper()
        
        for gene in self.parser.gene_patterns:
            if gene in text_upper:
                gene_id = self._generate_id("gene", gene)
                genes.append({
                    "id": gene_id,
                    "name": gene,
                    "type": "gene",
                    "context": self._extract_context(text, gene),
                    "mentions": text_upper.count(gene)
                })
        
        return genes
    
    def _extract_pathways(self, text: str) -> List[Dict]:
        """Извлекает биологические пути"""
        pathways = []
        text_lower = text.lower()
        
        for pathway in self.parser.pathway_patterns:
            if pathway.lower() in text_lower:
                pathway_id = self._generate_id("pathway", pathway)
                pathways.append({
                    "id": pathway_id,
                    "name": pathway,
                    "type": "pathway",
                    "context": self._extract_context(text, pathway),
                    "mentions": text_lower.count(pathway.lower())
                })
        
        return pathways
    
    def _extract_methods(self, text: str) -> List[Dict]:
        """Извлекает методы исследования"""
        methods = []
        text_lower = text.lower()
        
        for method in self.parser.method_patterns:
            if method.lower() in text_lower:
                method_id = self._generate_id("method", method)
                methods.append({
                    "id": method_id,
                    "name": method,
                    "type": "method",
                    "context": self._extract_context(text, method),
                    "mentions": text_lower.count(method.lower())
                })
        
        return methods
    
    def _extract_researchers(self, article: Dict) -> List[Dict]:
        """Извлекает исследователей"""
        researchers = []
        authors = article.get("authors", [])
        
        for author in authors:
            researcher_id = self._generate_id("researcher", author)
            researchers.append({
                "id": researcher_id,
                "name": author,
                "type": "researcher",
                "affiliation": "",  # Можно расширить парсинг для получения аффилиации
                "articles": [article.get("pmid", "")]
            })
        
        return researchers
    
    def _extract_hypotheses(self, text: str) -> List[Dict]:
        """Извлекает гипотезы из текста"""
        hypotheses = []
        
        # Простые паттерны для поиска гипотез
        hypothesis_patterns = [
            r"we hypothesize that ([^.]+)",
            r"we propose that ([^.]+)",
            r"we suggest that ([^.]+)",
            r"may play a role in ([^.]+)",
            r"could be involved in ([^.]+)"
        ]
        
        text_lower = text.lower()
        
        for i, pattern in enumerate(hypothesis_patterns):
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                hypothesis_id = self._generate_id("hypothesis", f"hyp_{i}_{match[:20]}")
                hypotheses.append({
                    "id": hypothesis_id,
                    "name": match.strip(),
                    "type": "hypothesis",
                    "confidence": 0.5,  # Базовая уверенность
                    "evidence": self._extract_context(text, match[:10])
                })
        
        return hypotheses
    
    def _extract_context(self, text: str, entity: str, window: int = 100) -> str:
        """Извлекает контекст вокруг упоминания сущности"""
        entity_pos = text.lower().find(entity.lower())
        if entity_pos == -1:
            return ""
        
        start = max(0, entity_pos - window)
        end = min(len(text), entity_pos + len(entity) + window)
        
        return text[start:end].strip()
    
    def _generate_id(self, entity_type: str, name: str) -> str:
        """Генерирует уникальный ID для сущности"""
        combined = f"{entity_type}_{name}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]

class GraphBuilder:
    def __init__(self, db: KnowledgeGraphDB):
        self.db = db
        self.entity_extractor = EntityExtractor(PubMedParser())
        
    def build_graph_from_articles(self, articles: List[Dict]):
        """Строит граф знаний из списка статей"""
        print(f"Обработка {len(articles)} статей...")
        
        all_entities = {}
        article_entities = []
        
        # Извлекаем сущности из всех статей
        for i, article in enumerate(articles):
            print(f"Обработка статьи {i+1}/{len(articles)}: {article.get('title', '')[:50]}...")
            
            entities = self.entity_extractor.extract_entities_from_article(article)
            article_entities.append({
                "article": article,
                "entities": entities
            })
            
            # Собираем все уникальные сущности
            for entity_type, entity_list in entities.items():
                if entity_type not in all_entities:
                    all_entities[entity_type] = {}
                
                for entity in entity_list:
                    entity_id = entity["id"]
                    if entity_id not in all_entities[entity_type]:
                        all_entities[entity_type][entity_id] = entity
                    else:
                        # Обновляем информацию о сущности
                        all_entities[entity_type][entity_id]["mentions"] += entity.get("mentions", 1)
        
        # Создаем узлы в графе
        self._create_nodes(all_entities)
        
        # Создаем связи
        self._create_relationships(article_entities)
        
        print("Граф знаний успешно построен!")
        
    def _create_nodes(self, all_entities: Dict):
        """Создает узлы в графе"""
        for entity_type, entities in all_entities.items():
            print(f"Создание узлов типа {entity_type}: {len(entities)} штук")
            
            for entity_id, entity_data in entities.items():
                node = Node(
                    id=entity_id,
                    type=entity_data["type"],
                    name=entity_data["name"],
                    properties={
                        "mentions": entity_data.get("mentions", 1),
                        "context": entity_data.get("context", ""),
                        "created_at": datetime.now().isoformat()
                    }
                )
                
                try:
                    self.db.create_node(node)
                except Exception as e:
                    print(f"Ошибка создания узла {entity_id}: {e}")
    
    def _create_relationships(self, article_entities: List[Dict]):
        """Создает связи между сущностями"""
        print("Создание связей между сущностями...")
        
        for article_data in article_entities:
            entities = article_data["entities"]
            
            # Связываем исследователей со всеми сущностями в их статьях
            researchers = entities.get("researchers", [])
            for researcher in researchers:
                self._link_researcher_to_entities(researcher, entities)
            
            # Связываем гены с pathway
            self._link_genes_to_pathways(entities.get("genes", []), entities.get("pathways", []))
            
            # Связываем методы с результатами
            self._link_methods_to_results(entities.get("methods", []), entities.get("genes", []) + entities.get("pathways", []))
            
            # Связываем гипотезы с сущностями
            self._link_hypotheses_to_entities(entities.get("hypotheses", []), entities)
    
    def _link_researcher_to_entities(self, researcher: Dict, entities: Dict):
        """Связывает исследователя с сущностями"""
        researcher_id = researcher["id"]
        
        for entity_type, entity_list in entities.items():
            if entity_type != "researchers":
                for entity in entity_list:
                    relationship = Relationship(
                        source=researcher_id,
                        target=entity["id"],
                        type="STUDIES",
                        weight=1.0,
                        properties={"created_at": datetime.now().isoformat()}
                    )
                    
                    try:
                        self.db.create_relationship(relationship)
                    except Exception as e:
                        print(f"Ошибка создания связи researcher-entity: {e}")
    
    def _link_genes_to_pathways(self, genes: List[Dict], pathways: List[Dict]):
        """Связывает гены с биологическими путями"""
        for gene in genes:
            for pathway in pathways:
                # Простая эвристика связывания на основе совместного упоминания
                relationship = Relationship(
                    source=gene["id"],
                    target=pathway["id"],
                    type="PARTICIPATES_IN",
                    weight=0.8,
                    properties={"created_at": datetime.now().isoformat()}
                )
                
                try:
                    self.db.create_relationship(relationship)
                except Exception as e:
                    print(f"Ошибка создания связи gene-pathway: {e}")
    
    def _link_methods_to_results(self, methods: List[Dict], results: List[Dict]):
        """Связывает методы с результатами"""
        for method in methods:
            for result in results:
                relationship = Relationship(
                    source=method["id"],
                    target=result["id"],
                    type="USED_TO_STUDY",
                    weight=0.7,
                    properties={"created_at": datetime.now().isoformat()}
                )
                
                try:
                    self.db.create_relationship(relationship)
                except Exception as e:
                    print(f"Ошибка создания связи method-result: {e}")
    
    def _link_hypotheses_to_entities(self, hypotheses: List[Dict], entities: Dict):
        """Связывает гипотезы с сущностями"""
        for hypothesis in hypotheses:
            for entity_type, entity_list in entities.items():
                if entity_type != "hypotheses":
                    for entity in entity_list:
                        # Проверяем семантическую близость
                        if self._entities_are_related(hypothesis, entity):
                            relationship = Relationship(
                                source=hypothesis["id"],
                                target=entity["id"],
                                type="RELATES_TO",
                                weight=0.6,
                                properties={"created_at": datetime.now().isoformat()}
                            )
                            
                            try:
                                self.db.create_relationship(relationship)
                            except Exception as e:
                                print(f"Ошибка создания связи hypothesis-entity: {e}")
    
    def _entities_are_related(self, entity1: Dict, entity2: Dict) -> bool:
        """Проверяет, связаны ли две сущности"""
        # Простая проверка на основе общих слов
        words1 = set(entity1["name"].lower().split())
        words2 = set(entity2["name"].lower().split())
        
        common_words = words1 & words2
        return len(common_words) > 0

# Функция инициализации графа
def initialize_knowledge_graph():
    """Инициализирует граф знаний данными из PubMed"""
    parser = PubMedParser()
    db = KnowledgeGraphDB()
    builder = GraphBuilder(db)
    
    print("Инициализация графа знаний Longevity...")
    
    # Поиск статей по ключевым терминам
    all_articles = []
    
    for term in parser.longevity_terms[:5]:  # Ограничиваем для MVP
        print(f"Поиск статей по термину: {term}")
        pmids = parser.search_pubmed(f"({term}) AND aging", max_results=20)
        
        if pmids:
            articles = parser.fetch_article_details(pmids)
            all_articles.extend(articles)
            time.sleep(1)  # Уважаем лимиты API
    
    print(f"Собрано {len(all_articles)} статей")
    
    # Строим граф
    builder.build_graph_from_articles(all_articles)
    
    print("Инициализация завершена!")
    return len(all_articles)

if __name__ == "__main__":
    # Пример использования
    articles_count = initialize_knowledge_graph()
    print(f"Граф создан на основе {articles_count} статей")
