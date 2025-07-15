import React, { useState, useEffect, useRef } from 'react';
import { Search, MessageCircle, Brain, TrendingUp, Network, Lightbulb, Users, FlaskConical, Dna, Send, Filter, Download, Info } from 'lucide-react';

// Симуляция данных для демо (в реальной версии будут приходить с backend)
const mockGraphData = {
  nodes: [
    { id: 'mtor', type: 'pathway', name: 'mTOR signaling', x: 100, y: 100, connections: 15, priority: 'high' },
    { id: 'autophagy', type: 'pathway', name: 'Autophagy', x: 200, y: 150, connections: 12, priority: 'high' },
    { id: 'sirt1', type: 'gene', name: 'SIRT1', x: 150, y: 200, connections: 8, priority: 'medium' },
    { id: 'foxo3', type: 'gene', name: 'FOXO3', x: 250, y: 120, connections: 10, priority: 'high' },
    { id: 'crispr', type: 'method', name: 'CRISPR', x: 180, y: 80, connections: 6, priority: 'medium' },
    { id: 'rnaseq', type: 'method', name: 'RNA-seq', x: 120, y: 250, connections: 9, priority: 'medium' },
    { id: 'lopez_otin', type: 'researcher', name: 'Carlos López-Otín', x: 300, y: 180, connections: 14, priority: 'high' },
    { id: 'hyp1', type: 'hypothesis', name: 'mTOR-autophagy crosstalk in aging', x: 170, y: 180, connections: 5, priority: 'medium' }
  ],
  links: [
    { source: 'mtor', target: 'autophagy', type: 'REGULATES', strength: 0.9 },
    { source: 'sirt1', target: 'autophagy', type: 'ACTIVATES', strength: 0.8 },
    { source: 'foxo3', target: 'autophagy', type: 'PROMOTES', strength: 0.7 },
    { source: 'crispr', target: 'sirt1', type: 'USED_TO_STUDY', strength: 0.6 },
    { source: 'rnaseq', target: 'foxo3', type: 'USED_TO_STUDY', strength: 0.7 },
    { source: 'lopez_otin', target: 'hyp1', type: 'PROPOSED', strength: 0.8 }
  ]
};

const mockHypothesisGaps = [
  {
    potential_hypothesis: "SIRT1 может регулировать mTOR через неизвестный посредник",
    confidence_score: 0.85,
    supporting_evidence: ["Общие мишени: autophagy, FOXO3", "Высокая семантическая близость"],
    missing_connections: [{ source: "SIRT1", target: "mTOR", type: "REGULATES" }],
    research_priority: "high",
    suggested_methods: ["Co-immunoprecipitation", "Protein interaction screening", "Pathway analysis"]
  },
  {
    potential_hypothesis: "Комбинация CRISPR + single-cell RNA-seq может выявить новые aging biomarkers",
    confidence_score: 0.78,
    supporting_evidence: ["Методы совместимы", "Неиспользованная комбинация"],
    missing_connections: [{ source: "CRISPR", target: "scRNA-seq", type: "COMBINES_WITH" }],
    research_priority: "medium",
    suggested_methods: ["Pilot study", "Feasibility analysis"]
  },
  {
    potential_hypothesis: "Epigenetic clocks связаны с mTOR signaling через methylation patterns",
    confidence_score: 0.73,
    supporting_evidence: ["Паттерн повторяется 4 раза", "Общие регуляторные механизмы"],
    missing_connections: [{ pattern: "epigenetic + mTOR", instances: 4, type: "GENERAL_MECHANISM" }],
    research_priority: "medium",
    suggested_methods: ["Methylation analysis", "Epigenome-wide association study", "Longitudinal study"]
  }
];

const GraphVisualization = ({ data, selectedNode, onNodeSelect, filters }) => {
  const svgRef = useRef();
  const [hoveredNode, setHoveredNode] = useState(null);
  
  const getNodeColor = (node) => {
    const colors = {
      gene: '#3b82f6',
      pathway: '#10b981', 
      method: '#f59e0b',
      researcher: '#8b5cf6',
      hypothesis: '#ef4444'
    };
    return colors[node.type] || '#6b7280';
  };
  
  const getNodeSize = (node) => {
    const base = 6;
    const multiplier = Math.log(node.connections + 1) * 2;
    return base + multiplier;
  };
  
  const filteredNodes = data.nodes.filter(node => {
    if (filters.type && filters.type !== 'all' && node.type !== filters.type) return false;
    if (filters.priority && filters.priority !== 'all' && node.priority !== filters.priority) return false;
    if (filters.search && !node.name.toLowerCase().includes(filters.search.toLowerCase())) return false;
    return true;
  });
  
  const filteredLinks = data.links.filter(link => 
    filteredNodes.find(n => n.id === link.source) && 
    filteredNodes.find(n => n.id === link.target)
  );

  return (
    <div className="relative w-full h-full bg-gray-900 rounded-lg overflow-hidden">
      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        className="cursor-crosshair"
      >
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge> 
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        
        {/* Links */}
        {filteredLinks.map((link, i) => {
          const sourceNode = filteredNodes.find(n => n.id === link.source);
          const targetNode = filteredNodes.find(n => n.id === link.target);
          if (!sourceNode || !targetNode) return null;
          
          return (
            <line
              key={i}
              x1={sourceNode.x}
              y1={sourceNode.y}
              x2={targetNode.x}
              y2={targetNode.y}
              stroke="#4b5563"
              strokeWidth={link.strength * 3}
              opacity={0.6}
              className="transition-all duration-300"
            />
          );
        })}
        
        {/* Nodes */}
        {filteredNodes.map((node) => (
          <g key={node.id}>
            <circle
              cx={node.x}
              cy={node.y}
              r={getNodeSize(node)}
              fill={getNodeColor(node)}
              stroke={selectedNode?.id === node.id ? '#fff' : 'none'}
              strokeWidth="3"
              className={`cursor-pointer transition-all duration-300 ${
                hoveredNode === node.id ? 'filter-glow' : ''
              }`}
              filter={hoveredNode === node.id ? 'url(#glow)' : ''}
              onClick={() => onNodeSelect(node)}
              onMouseEnter={() => setHoveredNode(node.id)}
              onMouseLeave={() => setHoveredNode(null)}
            />
            {(hoveredNode === node.id || selectedNode?.id === node.id) && (
              <text
                x={node.x}
                y={node.y - getNodeSize(node) - 8}
                textAnchor="middle"
                fill="white"
                fontSize="12"
                className="pointer-events-none font-medium"
              >
                {node.name}
              </text>
            )}
          </g>
        ))}
      </svg>
      
      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-gray-800 rounded-lg p-3 text-sm">
        <div className="font-semibold text-white mb-2">Типы узлов:</div>
        {Object.entries({
          gene: { color: '#3b82f6', icon: Dna },
          pathway: { color: '#10b981', icon: Network },
          method: { color: '#f59e0b', icon: FlaskConical },
          researcher: { color: '#8b5cf6', icon: Users },
          hypothesis: { color: '#ef4444', icon: Lightbulb }
        }).map(([type, { color, icon: Icon }]) => (
          <div key={type} className="flex items-center gap-2 text-gray-300 mb-1">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: color }}
            />
            <Icon size={14} />
            <span className="capitalize">{type}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const HypothesisGapsPanel = ({ gaps, onGapSelect }) => {
  const getPriorityColor = (priority) => {
    return priority === 'high' ? 'text-red-400' : 
           priority === 'medium' ? 'text-yellow-400' : 'text-green-400';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-white font-semibold">
        <Brain size={20} />
        <span>Потенциальные гипотезы</span>
        <span className="bg-red-500 text-white px-2 py-1 rounded-full text-xs">
          {gaps.length}
        </span>
      </div>
      
      {gaps.map((gap, index) => (
        <div 
          key={index}
          className="bg-gray-800 rounded-lg p-4 cursor-pointer hover:bg-gray-700 transition-colors"
          onClick={() => onGapSelect(gap)}
        >
          <div className="flex items-start justify-between mb-2">
            <h3 className="text-white font-medium text-sm leading-tight">
              {gap.potential_hypothesis}
            </h3>
            <div className="flex flex-col items-end gap-1">
              <span className={`text-xs font-semibold ${getPriorityColor(gap.research_priority)}`}>
                {gap.research_priority.toUpperCase()}
              </span>
              <span className="text-xs text-gray-400">
                {Math.round(gap.confidence_score * 100)}%
              </span>
            </div>
          </div>
          
          <div className="text-xs text-gray-400 mb-2">
            <strong>Методы:</strong> {gap.suggested_methods.slice(0, 2).join(', ')}
            {gap.suggested_methods.length > 2 && '...'}
          </div>
          
          <div className="flex flex-wrap gap-1">
            {gap.supporting_evidence.slice(0, 2).map((evidence, i) => (
              <span key={i} className="bg-blue-900 text-blue-200 px-2 py-1 rounded text-xs">
                {evidence.length > 30 ? evidence.substring(0, 30) + '...' : evidence}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

const ChatInterface = ({ selectedNode, selectedGap }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    
    const userMessage = { 
      role: 'user', 
      content: inputValue,
      timestamp: new Date().toLocaleTimeString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    
    // Симуляция ответа AI (в реальной версии - запрос к backend)
    setTimeout(() => {
      let aiResponse = '';
      
      if (selectedNode) {
        aiResponse = `Анализирую ${selectedNode.name}... `;
        if (selectedNode.type === 'gene') {
          aiResponse += `Этот ген имеет ${selectedNode.connections} известных взаимодействий в области longevity. Ключевые функции включают регуляцию клеточного старения и метаболизма.`;
        } else if (selectedNode.type === 'pathway') {
          aiResponse += `Этот pathway центральный для процессов старения. Рекомендую изучить взаимодействие с mTOR signaling и autophagy.`;
        }
      } else if (selectedGap) {
        aiResponse = `Эта гипотеза имеет высокий потенциал (${Math.round(selectedGap.confidence_score * 100)}%). Рекомендуемые методы: ${selectedGap.suggested_methods.join(', ')}.`;
      } else {
        aiResponse = `Я могу помочь с анализом графа знаний в области longevity research. Выберите узел или гипотезу для детального анализа, или задайте вопрос о трендах в исследованиях старения.`;
      }
      
      const aiMessage = {
        role: 'assistant',
        content: aiResponse,
        timestamp: new Date().toLocaleTimeString()
      };
      
      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false);
    }, 1000);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 p-4 border-b border-gray-700">
        <MessageCircle size={20} className="text-blue-400" />
        <span className="text-white font-semibold">AI Research Assistant</span>
        {selectedNode && (
          <span className="bg-blue-600 text-white px-2 py-1 rounded text-xs">
            Анализ: {selectedNode.name}
          </span>
        )}
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-gray-400 text-center py-8">
            <Brain size={48} className="mx-auto mb-4 opacity-50" />
            <p className="mb-2">Добро пожаловать в Longevity Knowledge Graph!</p>
            <p className="text-sm">Задайте вопрос или выберите узел для анализа</p>
          </div>
        )}
        
        {messages.map((message, index) => (
          <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
              message.role === 'user' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-700 text-gray-100'
            }`}>
              <p className="text-sm">{message.content}</p>
              <p className="text-xs opacity-70 mt-1">{message.timestamp}</p>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 text-gray-100 px-4 py-2 rounded-lg">
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
                <span className="text-sm">Анализирую...</span>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div className="p-4 border-t border-gray-700">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Спросите о longevity research..."
            className="flex-1 bg-gray-800 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};

const FilterPanel = ({ filters, onFiltersChange }) => {
  return (
    <div className="bg-gray-800 rounded-lg p-4 space-y-4">
      <div className="flex items-center gap-2 text-white font-semibold">
        <Filter size={16} />
        <span>Фильтры</span>
      </div>
      
      <div className="space-y-3">
        <div>
          <label className="block text-gray-300 text-sm mb-1">Поиск</label>
          <input
            type="text"
            value={filters.search}
            onChange={(e) => onFiltersChange({...filters, search: e.target.value})}
            placeholder="Найти узел..."
            className="w-full bg-gray-700 text-white rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        
        <div>
          <label className="block text-gray-300 text-sm mb-1">Тип</label>
          <select
            value={filters.type}
            onChange={(e) => onFiltersChange({...filters, type: e.target.value})}
            className="w-full bg-gray-700 text-white rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">Все типы</option>
            <option value="gene">Гены</option>
            <option value="pathway">Пути</option>
            <option value="method">Методы</option>
            <option value="researcher">Исследователи</option>
            <option value="hypothesis">Гипотезы</option>
          </select>
        </div>
        
        <div>
          <label className="block text-gray-300 text-sm mb-1">Приоритет</label>
          <select
            value={filters.priority}
            onChange={(e) => onFiltersChange({...filters, priority: e.target.value})}
            className="w-full bg-gray-700 text-white rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">Все приоритеты</option>
            <option value="high">Высокий</option>
            <option value="medium">Средний</option>
            <option value="low">Низкий</option>
          </select>
        </div>
      </div>
    </div>
  );
};

const StatsPanel = ({ data, gaps }) => {
  const stats = {
    totalNodes: data.nodes.length,
    totalConnections: data.links.length,
    highPriorityGaps: gaps.filter(g => g.research_priority === 'high').length,
    avgConfidence: gaps.reduce((acc, g) => acc + g.confidence_score, 0) / gaps.length
  };

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg p-4 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-blue-100 text-sm">Узлов в графе</p>
            <p className="text-2xl font-bold">{stats.totalNodes}</p>
          </div>
          <Network size={32} className="text-blue-200" />
        </div>
      </div>
      
      <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-lg p-4 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-green-100 text-sm">Связей</p>
            <p className="text-2xl font-bold">{stats.totalConnections}</p>
          </div>
          <TrendingUp size={32} className="text-green-200" />
        </div>
      </div>
      
      <div className="bg-gradient-to-br from-red-600 to-red-700 rounded-lg p-4 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-red-100 text-sm">Приоритетных гипотез</p>
            <p className="text-2xl font-bold">{stats.highPriorityGaps}</p>
          </div>
          <Brain size={32} className="text-red-200" />
        </div>
      </div>
      
      <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-lg p-4 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-purple-100 text-sm">Средняя уверенность</p>
            <p className="text-2xl font-bold">{Math.round((stats.avgConfidence || 0) * 100)}%</p>
          </div>
          <Lightbulb size={32} className="text-purple-200" />
        </div>
      </div>
    </div>
  );
};

export default function LongevityKnowledgeGraph() {
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedGap, setSelectedGap] = useState(null);
  const [activeTab, setActiveTab] = useState('graph');
  const [filters, setFilters] = useState({
    search: '',
    type: 'all',
    priority: 'all'
  });

  const handleNodeSelect = (node) => {
    setSelectedNode(node);
    setSelectedGap(null);
    setActiveTab('chat');
  };

  const handleGapSelect = (gap) => {
    setSelectedGap(gap);
    setSelectedNode(null);
    setActiveTab('chat');
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-2">
              <Brain size={24} className="text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Longevity Knowledge Graph</h1>
              <p className="text-gray-400 text-sm">Научная навигация в задачах старения</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <button className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 px-3 py-2 rounded-lg transition-colors">
              <Download size={16} />
              <span className="text-sm">Экспорт</span>
            </button>
            <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded-lg transition-colors">
              <TrendingUp size={16} />
              <span className="text-sm">Обновить данные</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-80px)]">
        {/* Left Sidebar */}
        <div className="w-80 bg-gray-800 border-r border-gray-700 flex flex-col">
          <div className="p-4 border-b border-gray-700">
            <StatsPanel data={mockGraphData} gaps={mockHypothesisGaps} />
          </div>
          
          <div className="p-4 border-b border-gray-700">
            <FilterPanel filters={filters} onFiltersChange={setFilters} />
          </div>
          
          <div className="flex-1 p-4 overflow-y-auto">
            <HypothesisGapsPanel gaps={mockHypothesisGaps} onGapSelect={handleGapSelect} />
          </div>
        </div>

        {/* Main Area */}
        <div className="flex-1 flex flex-col">
          {/* Tab Navigation */}
          <div className="bg-gray-800 border-b border-gray-700 px-6 py-3">
            <div className="flex gap-4">
              <button
                onClick={() => setActiveTab('graph')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'graph' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                <Network size={16} />
                <span>Граф знаний</span>
              </button>
              <button
                onClick={() => setActiveTab('chat')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'chat' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                <MessageCircle size={16} />
                <span>AI Ассистент</span>
                {(selectedNode || selectedGap) && (
                  <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                )}
              </button>
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 p-6">
            {activeTab === 'graph' ? (
              <div className="h-full">
                <GraphVisualization 
                  data={mockGraphData} 
                  selectedNode={selectedNode}
                  onNodeSelect={handleNodeSelect}
                  filters={filters}
                />
              </div>
            ) : (
              <div className="h-full bg-gray-800 rounded-lg">
                <ChatInterface 
                  selectedNode={selectedNode}
                  selectedGap={selectedGap}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
