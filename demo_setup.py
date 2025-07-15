# demo_setup.py - Быстрая настройка демо-версии
import json
from datetime import datetime, timedelta
from main import KnowledgeGraphDB, Node, Relationship
import random

def create_demo_graph():
    """Создает демо-граф для презентации"""
    db = KnowledgeGraphDB()
    
    print("Создание демо-графа знаний...")
    
    # Демо-данные для longevity research
    demo_data = {
        "genes": [
            {"id": "sirt1", "name": "SIRT1", "description": "Sirtuin 1 - ключевой регулятор долголетия", "connections": 15, "recent_mentions": 89},
            {"id": "foxo3", "name": "FOXO3", "description": "Forkhead Box O3 - транскрипционный фактор долголетия", "connections": 12, "recent_mentions": 67},
            {"id": "tp53", "name": "TP53", "description": "Tumor protein p53 - guardian of the genome", "connections": 18, "recent_mentions": 124},
            {"id": "tert", "name": "TERT", "description": "Telomerase reverse transcriptase", "connections": 9, "recent_mentions": 45},
            {"id": "klotho", "name": "KLOTHO", "description": "Anti-aging hormone regulator", "connections": 8, "recent_mentions": 38},
            {"id": "ampk", "name": "AMPK", "description": "AMP-activated protein kinase", "connections": 14, "recent_mentions": 72}
        ],
        
        "pathways": [
            {"id": "mtor_signaling", "name": "mTOR signaling", "description": "Mechanistic target of rapamycin pathway", "connections": 20, "recent_mentions": 156},
            {"id": "autophagy", "name": "Autophagy", "description": "Cellular self-digestion and renewal process", "connections": 16, "recent_mentions": 134},
            {"id": "dna_repair", "name": "DNA repair", "description": "Mechanisms for maintaining genomic integrity", "connections": 13, "recent_mentions": 98},
            {"id": "oxidative_stress", "name": "Oxidative stress response", "description": "Cellular defense against ROS", "connections": 17, "recent_mentions": 145},
            {"id": "senescence", "name": "Cellular senescence", "description": "Programmed cell cycle arrest", "connections": 11, "recent_mentions": 87},
            {"id": "mitochondrial_bio", "name": "Mitochondrial biogenesis", "description": "Creation of new mitochondria", "connections": 9, "recent_mentions": 63}
        ],
        
        "methods": [
            {"id": "crispr", "name": "CRISPR-Cas9", "description": "Gene editing technology", "connections": 8, "recent_mentions": 234},
            {"id": "rnaseq", "name": "RNA-seq", "description": "RNA sequencing technology", "connections": 12, "recent_mentions": 187},
            {"id": "scrnaseq", "name": "scRNA-seq", "description": "Single-cell RNA sequencing", "connections": 7, "recent_mentions": 156},
            {"id": "proteomics", "name": "Proteomics", "description": "Large-scale protein analysis", "connections": 10, "recent_mentions": 98},
            {"id": "metabolomics", "name": "Metabolomics", "description": "Metabolite profiling", "connections": 6, "recent_mentions": 76},
            {"id": "chipseq", "name": "ChIP-seq", "description": "Chromatin immunoprecipitation sequencing", "connections": 5, "recent_mentions": 54}
        ],
        
        "researchers": [
            {"id": "lopez_otin", "name": "Carlos López-Otín", "description": "Pioneer in aging research", "connections": 25, "affiliation": "Universidad de Oviedo"},
            {"id": "sinclair", "name": "David A. Sinclair", "description": "Harvard aging researcher", "connections": 22, "affiliation": "Harvard Medical School"},
            {"id": "kennedy", "name": "Brian K. Kennedy", "description": "Aging and longevity expert", "connections": 19, "affiliation": "Buck Institute"},
            {"id": "campisi", "name": "Judith Campisi", "description": "Senescence researcher", "connections": 21, "affiliation": "Buck Institute"},
            {"id": "austad", "name": "Steven N. Austad", "description": "Comparative aging researcher", "connections": 16, "affiliation": "University of Alabama"}
        ],
        
        "hypotheses": [
            {"id": "hyp_mtor_autophagy", "name": "mTOR-autophagy crosstalk hypothesis", "description": "mTOR inhibition promotes longevity through autophagy activation", "confidence": 0.85},
            {"id": "hyp_senescence_inflammation", "name": "Senescence-inflammation theory", "description": "Senescent cells drive aging through inflammatory signaling", "confidence": 0.78},
            {"id": "hyp_mitochondrial_theory", "name": "Mitochondrial theory of aging", "description": "Mitochondrial dysfunction is a primary driver of aging", "confidence": 0.72},
            {"id": "hyp_epigenetic_clock", "name": "Epigenetic aging clock", "description": "DNA methylation patterns predict biological age", "confidence": 0.88},
            {"id": "hyp_proteostasis", "name": "Proteostasis collapse theory", "description": "Protein homeostasis failure drives aging phenotypes", "confidence": 0.75}
        ]
    }
    
    # Создаем узлы
    all_entities = []
    
    for category, entities in demo_data.items():
        for entity in entities:
            node = Node(
                id=entity["id"],
                type=category[:-1],  # убираем 's' в конце
                name=entity["name"],
                properties={
                    "description": entity.get("description", ""),
                    "connections": entity.get("connections", 0),
                    "recent_mentions": entity.get("recent_mentions", 0),
                    "created_at": datetime.now().isoformat(),
                    "affiliation": entity.get("affiliation", ""),
                    "confidence": entity.get("confidence", 0.5)
                }
            )
            
            try:
                db.create_node(node)
                all_entities.append(entity)
                print(f"Создан узел: {entity['name']}")
            except Exception as e:
                print(f"Ошибка создания узла {entity['name']}: {e}")
    
    # Создаем связи на основе биологической логики
    relationships = [
        # Гены и пути
        ("sirt1", "mtor_signaling", "REGULATES", 0.9),
        ("sirt1", "autophagy", "ACTIVATES", 0.8),
        ("foxo3", "autophagy", "PROMOTES", 0.7),
        ("foxo3", "oxidative_stress", "REGULATES", 0.8),
        ("tp53", "dna_repair", "ACTIVATES", 0.9),
        ("tp53", "senescence", "TRIGGERS", 0.8),
        ("tert", "senescence", "PREVENTS", 0.7),
        ("klotho", "oxidative_stress", "REDUCES", 0.6),
        ("ampk", "mtor_signaling", "INHIBITS", 0.8),
        ("ampk", "mitochondrial_bio", "PROMOTES", 0.7),
        
        # Методы и гены/пути
        ("crispr", "sirt1", "USED_TO_STUDY", 0.7),
        ("crispr", "foxo3", "USED_TO_STUDY", 0.6),
        ("rnaseq", "mtor_signaling", "USED_TO_STUDY", 0.8),
        ("rnaseq", "autophagy", "USED_TO_STUDY", 0.7),
        ("scrnaseq", "senescence", "USED_TO_STUDY", 0.8),
        ("proteomics", "oxidative_stress", "USED_TO_STUDY", 0.6),
        ("metabolomics", "mitochondrial_bio", "USED_TO_STUDY", 0.5),
        ("chipseq", "tp53", "USED_TO_STUDY", 0.7),
        
        # Исследователи и гипотезы
        ("lopez_otin", "hyp_mtor_autophagy", "PROPOSED", 0.9),
        ("sinclair", "hyp_epigenetic_clock", "DEVELOPED", 0.8),
        ("campisi", "hyp_senescence_inflammation", "PROPOSED", 0.9),
        ("kennedy", "hyp_mitochondrial_theory", "SUPPORTS", 0.7),
        ("austad", "hyp_proteostasis", "INVESTIGATES", 0.6),
        
        # Исследователи и гены
        ("lopez_otin", "sirt1", "STUDIES", 0.8),
        ("sinclair", "sirt1", "STUDIES", 0.9),
        ("campisi", "tp53", "STUDIES", 0.8),
        ("kennedy", "ampk", "STUDIES", 0.7),
        
        # Межпутевые взаимодействия
        ("mtor_signaling", "autophagy", "INHIBITS", 0.9),
        ("autophagy", "senescence", "PREVENTS", 0.7),
        ("dna_repair", "senescence", "PREVENTS", 0.8),
        ("oxidative_stress", "senescence", "PROMOTES", 0.6),
        ("mitochondrial_bio", "oxidative_stress", "REDUCES", 0.5),
        
        # Гипотезы и пути
        ("hyp_mtor_autophagy", "mtor_signaling", "EXPLAINS", 0.9),
        ("hyp_mtor_autophagy", "autophagy", "EXPLAINS", 0.9),
        ("hyp_senescence_inflammation", "senescence", "EXPLAINS", 0.8),
        ("hyp_mitochondrial_theory", "mitochondrial_bio", "EXPLAINS", 0.8),
        ("hyp_epigenetic_clock", "dna_repair", "RELATES_TO", 0.6),
        ("hyp_proteostasis", "oxidative_stress", "RELATES_TO", 0.7)
    ]
    
    for source, target, rel_type, weight in relationships:
        relationship = Relationship(
            source=source,
            target=target,
            type=rel_type,
            weight=weight,
            properties={
                "created_at": datetime.now().isoformat(),
                "confidence": weight,
                "evidence_count": random.randint(1, 10)
            }
        )
        
        try:
            db.create_relationship(relationship)
            print(f"Создана связь: {source} -> {target} ({rel_type})")
        except Exception as e:
            print(f"Ошибка создания связи {source} -> {target}: {e}")
    
    print(f"\nДемо-граф создан успешно!")
    print(f"Узлов: {len(all_entities)}")
    print(f"Связей: {len(relationships)}")
    
    return len(all_entities), len(relationships)

def generate_demo_gaps():
    """Генерирует демо-пробелы в гипотезах для презентации"""
    return [
        {
            "potential_hypothesis": "SIRT1 может регулировать KLOTHO через epigenetic mechanisms",
            "confidence_score": 0.87,
            "supporting_evidence": [
                "Оба связаны с долголетием", 
                "Схожие эпигенетические мишени",
                "Отсутствие прямых исследований взаимодействия"
            ],
            "missing_connections": [{"source": "SIRT1", "target": "KLOTHO", "type": "REGULATES"}],
            "research_priority": "high",
            "suggested_methods": ["ChIP-seq", "Epigenome analysis", "Co-expression studies"]
        },
        {
            "potential_hypothesis": "Комбинация CRISPR + scRNA-seq может выявить новые senescence biomarkers",
            "confidence_score": 0.82,
            "supporting_evidence": [
                "Методы совместимы для single-cell analysis",
                "CRISPR может создавать senescence models",
                "scRNA-seq идеально для heterogeneity analysis"
            ],
            "missing_connections": [{"source": "CRISPR", "target": "scRNA-seq", "type": "COMBINES_WITH"}],
            "research_priority": "high",
            "suggested_methods": ["Pilot study", "Protocol optimization", "Validation experiments"]
        },
        {
            "potential_hypothesis": "AMPK-mTOR-Autophagy axis контролируется circadian rhythms",
            "confidence_score": 0.75,
            "supporting_evidence": [
                "Все компоненты имеют circadian regulation",
                "Metabolic processes связаны с circadian clock",
                "Aging связан с circadian dysfunction"
            ],
            "missing_connections": [{"pattern": "circadian + metabolic + aging", "instances": 6, "type": "TEMPORAL_REGULATION"}],
            "research_priority": "medium",
            "suggested_methods": ["Chronobiology experiments", "Time-course RNA-seq", "Metabolomics profiling"]
        },
        {
            "potential_hypothesis": "Proteostasis networks взаимодействуют с immune system aging",
            "confidence_score": 0.71,
            "supporting_evidence": [
                "Protein aggregation активирует immunity",
                "Immunosenescence связана с protein damage",
                "Общие stress response pathways"
            ],
            "missing_connections": [{"source": "proteostasis", "target": "immunosenescence", "type": "BIDIRECTIONAL_REGULATION"}],
            "research_priority": "medium",
            "suggested_methods": ["Systems immunology", "Proteomics", "Functional genomics"]
        },
        {
            "potential_hypothesis": "Telomere dynamics регулируют mitochondrial function through metabolic signaling",
            "confidence_score": 0.68,
            "supporting_evidence": [
                "TERT имеет mitochondrial localization",
                "Telomere dysfunction вызывает metabolic changes",
                "Mitochondria производят ROS, affecting telomeres"
            ],
            "missing_connections": [{"source": "TERT", "target": "mitochondrial_bio", "type": "BIDIRECTIONAL_REGULATION"}],
            "research_priority": "low",
            "suggested_methods": ["Mitochondrial functional assays", "Telomere length analysis", "Metabolic profiling"]
        }
    ]

def create_demo_trends():
    """Создает демо-данные для трендов"""
    return [
        {
            "area": "Senolytic drugs",
            "growth_rate": 0.34,
            "publications_last_month": 45,
            "key_researchers": ["Judith Campisi", "James Kirkland"],
            "emerging_targets": ["BCL-2", "p21", "p16"],
            "funding_trend": "increasing"
        },
        {
            "area": "Epigenetic reprogramming",
            "growth_rate": 0.28,
            "publications_last_month": 38,
            "key_researchers": ["David Sinclair", "Juan Carlos Izpisua Belmonte"],
            "emerging_targets": ["Yamanaka factors", "chromatin remodeling"],
            "funding_trend": "stable"
        },
        {
            "area": "NAD+ metabolism",
            "growth_rate": 0.22,
            "publications_last_month": 32,
            "key_researchers": ["David Sinclair", "Charles Brenner"],
            "emerging_targets": ["NMN", "NR", "NAMPT"],
            "funding_trend": "increasing"
        }
    ]

def setup_api_endpoints():
    """Настройка дополнительных API endpoints для демо"""
    from main import app
    
    @app.get("/api/v1/demo/gaps")
    async def get_demo_gaps():
        return {"gaps": generate_demo_gaps()}
    
    @app.get("/api/v1/demo/trends")
    async def get_demo_trends():
        return {"trends": create_demo_trends()}
    
    @app.get("/api/v1/demo/stats")
    async def get_demo_stats():
        return {
            "total_nodes": 25,
            "total_relationships": 35,
            "high_priority_gaps": 2,
            "medium_priority_gaps": 2,
            "low_priority_gaps": 1,
            "avg_confidence": 0.77,
            "last_updated": datetime.now().isoformat()
        }

def run_demo():
    """Запускает полную демо-версию"""
    print("🧬 Запуск Longevity Knowledge Graph Demo...")
    print("=" * 50)
    
    # Создаем демо-граф
    nodes_count, relationships_count = create_demo_graph()
    
    # Настраиваем API
    setup_api_endpoints()
    
    print(f"\n✅ Демо готово к запуску!")
    print(f"📊 Создано {nodes_count} узлов и {relationships_count} связей")
    print(f"🔬 Доступно {len(generate_demo_gaps())} потенциальных гипотез")
    print(f"📈 Отслеживается {len(create_demo_trends())} трендов")
    
    print(f"\n🚀 Для запуска выполните:")
    print(f"   python main.py")
    print(f"   Затем откройте frontend на Bolt.new")
    
    print(f"\n🎯 API endpoints:")
    print(f"   GET /api/v1/graph/analysis - полный анализ")
    print(f"   GET /api/v1/graph/hypothesis-gaps - пробелы в гипотезах")
    print(f"   GET /api/v1/demo/gaps - демо пробелы")
    print(f"   GET /api/v1/demo/trends - демо тренды")

if __name__ == "__main__":
    run_demo()
