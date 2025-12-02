# GraphRAG React Components

Example React components for GraphRAG dashboard integration.

---

## 🎨 Component Library

### **1. GraphSearchInterface**

Real-time protocol search with hybrid retrieval.

```typescript
import React, { useState, useEffect } from 'react';
import { Search, Loader2, AlertCircle } from 'lucide-react';

interface SearchResult {
  protocol_id: string;
  protocol_name: string;
  score: number;
  vector_similarity: float;
  graph_importance: number;
  context: {
    tvl: number;
    category: string;
    dependent_count: number;
  };
  risk_info?: {
    risk_score: number;
    top_recommendation: string;
  };
}

export const GraphSearchInterface: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/graph/search/hybrid', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          query,
          limit: 10,
          include_risks: true,
          include_dependencies: true,
          similarity_threshold: 0.5,
        }),
      });

      if (!response.ok) throw new Error('Search failed');

      const data = await response.json();
      setResults(data.results);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-4">
      {/* Search Input */}
      <div className="relative mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search DeFi protocols... (e.g., 'decentralized lending')"
          className="w-full px-4 py-3 pl-12 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <Search className="absolute left-4 top-3.5 text-gray-400" size={20} />
        {loading && <Loader2 className="absolute right-4 top-3.5 animate-spin" size={20} />}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center text-red-700">
          <AlertCircle className="mr-2" size={20} />
          {error}
        </div>
      )}

      {/* Search Results */}
      <div className="space-y-4">
        {results.map((result) => (
          <div
            key={result.protocol_id}
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
          >
            {/* Protocol Header */}
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">
                  {result.protocol_name}
                </h3>
                <span className="text-sm text-gray-500">{result.context.category}</span>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-600">
                  {(result.score * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-gray-500">Match Score</div>
              </div>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <div className="text-sm text-gray-500">TVL</div>
                <div className="text-lg font-semibold">
                  ${(result.context.tvl / 1e9).toFixed(2)}B
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Dependencies</div>
                <div className="text-lg font-semibold">{result.context.dependent_count}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Vector Similarity</div>
                <div className="text-lg font-semibold">
                  {(result.vector_similarity * 100).toFixed(0)}%
                </div>
              </div>
            </div>

            {/* Risk Info */}
            {result.risk_info && (
              <div className={`p-3 rounded-lg ${
                result.risk_info.risk_score < 4 ? 'bg-green-50' :
                result.risk_info.risk_score < 7 ? 'bg-yellow-50' : 'bg-red-50'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">
                    Risk Score: {result.risk_info.risk_score}/10
                  </span>
                  <span className="text-xs">{result.risk_info.top_recommendation}</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

### **2. GraphVisualization**

Interactive graph visualization with D3.js.

```typescript
import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface Node {
  id: string;
  name: string;
  type: string;
  tvl?: number;
}

interface Link {
  source: string;
  target: string;
  type: string;
}

interface GraphVisualizationProps {
  protocolId: string;
}

export const GraphVisualization: React.FC<GraphVisualizationProps> = ({ protocolId }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    // Fetch graph data
    const fetchGraphData = async () => {
      const response = await fetch(
        `/api/v1/graph/protocols/${protocolId}/ecosystem`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      
      const data = await response.json();
      renderGraph(data);
    };

    const renderGraph = (data: { nodes: Node[]; links: Link[] }) => {
      const width = 800;
      const height = 600;

      // Clear existing
      d3.select(svgRef.current).selectAll('*').remove();

      const svg = d3.select(svgRef.current)
        .attr('width', width)
        .attr('height', height);

      // Create force simulation
      const simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.links).id((d: any) => d.id))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2));

      // Draw links
      const link = svg.append('g')
        .selectAll('line')
        .data(data.links)
        .enter().append('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', 2);

      // Draw nodes
      const node = svg.append('g')
        .selectAll('circle')
        .data(data.nodes)
        .enter().append('circle')
        .attr('r', (d) => Math.sqrt((d.tvl || 0) / 1e8) + 5)
        .attr('fill', (d) => {
          if (d.type === 'Protocol') return '#3b82f6';
          if (d.type === 'Token') return '#10b981';
          return '#6b7280';
        })
        .call(d3.drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended));

      // Add labels
      const label = svg.append('g')
        .selectAll('text')
        .data(data.nodes)
        .enter().append('text')
        .text((d) => d.name)
        .attr('font-size', 10)
        .attr('dx', 12)
        .attr('dy', 4);

      // Update positions
      simulation.on('tick', () => {
        link
          .attr('x1', (d: any) => d.source.x)
          .attr('y1', (d: any) => d.source.y)
          .attr('x2', (d: any) => d.target.x)
          .attr('y2', (d: any) => d.target.y);

        node
          .attr('cx', (d: any) => d.x)
          .attr('cy', (d: any) => d.y);

        label
          .attr('x', (d: any) => d.x)
          .attr('y', (d: any) => d.y);
      });

      // Drag functions
      function dragstarted(event: any) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      }

      function dragged(event: any) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      }

      function dragended(event: any) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      }
    };

    fetchGraphData();
  }, [protocolId]);

  return (
    <div className="w-full bg-white rounded-lg shadow-md p-4">
      <h3 className="text-lg font-semibold mb-4">Protocol Ecosystem</h3>
      <svg ref={svgRef} className="w-full h-auto border border-gray-200 rounded"></svg>
    </div>
  );
};
```

---

### **3. RealtimeUpdates**

WebSocket integration for live updates.

```typescript
import React, { useEffect, useState } from 'react';
import { Bell, TrendingUp, AlertTriangle } from 'lucide-react';

interface GraphEvent {
  type: string;
  protocol_id?: string;
  protocol_name?: string;
  message: string;
  timestamp: number;
}

export const RealtimeUpdates: React.FC = () => {
  const [events, setEvents] = useState<GraphEvent[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/graph?token=${token}`);

    ws.onopen = () => {
      setConnected(true);
      
      // Subscribe to all updates
      ws.send(JSON.stringify({
        action: 'subscribe',
        channel: 'all',
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      setEvents((prev) => [
        {
          type: data.type,
          protocol_id: data.protocol_id,
          protocol_name: data.protocol_name,
          message: data.message || JSON.stringify(data),
          timestamp: data.timestamp || Date.now(),
        },
        ...prev.slice(0, 49), // Keep last 50 events
      ]);
    };

    ws.onclose = () => {
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <div className="w-full max-w-md bg-white rounded-lg shadow-md p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center">
          <Bell className="mr-2" size={20} />
          Live Updates
        </h3>
        <div className={`px-2 py-1 rounded-full text-xs ${
          connected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
        }`}>
          {connected ? 'Connected' : 'Disconnected'}
        </div>
      </div>

      {/* Events Feed */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {events.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            Waiting for updates...
          </div>
        )}
        
        {events.map((event, idx) => (
          <div
            key={idx}
            className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                {event.protocol_name && (
                  <div className="font-medium text-sm mb-1">{event.protocol_name}</div>
                )}
                <div className="text-sm text-gray-600">{event.message}</div>
              </div>
              {event.type === 'risk:alert' && (
                <AlertTriangle className="text-red-500 ml-2" size={16} />
              )}
              {event.type === 'protocol:update' && (
                <TrendingUp className="text-blue-500 ml-2" size={16} />
              )}
            </div>
            <div className="text-xs text-gray-400 mt-1">
              {new Date(event.timestamp * 1000).toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

### **4. GraphDashboard**

Complete dashboard combining all components.

```typescript
import React from 'react';
import { GraphSearchInterface } from './GraphSearchInterface';
import { GraphVisualization } from './GraphVisualization';
import { RealtimeUpdates } from './RealtimeUpdates';

export const GraphDashboard: React.FC = () => {
  const [selectedProtocol, setSelectedProtocol] = React.useState<string | null>(null);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">GraphRAG Dashboard</h1>
          <p className="text-gray-600 mt-2">
            Intelligent DeFi protocol discovery powered by hybrid retrieval
          </p>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Search - Takes 2 columns */}
          <div className="lg:col-span-2">
            <GraphSearchInterface />
            
            {selectedProtocol && (
              <div className="mt-6">
                <GraphVisualization protocolId={selectedProtocol} />
              </div>
            )}
          </div>

          {/* Real-time Updates - Takes 1 column */}
          <div className="lg:col-span-1">
            <RealtimeUpdates />
          </div>
        </div>
      </div>
    </div>
  );
};
```

---

## 🚀 Usage

### **Installation**:
```bash
npm install d3 lucide-react
npm install --save-dev @types/d3
```

### **Integration**:
```typescript
import { GraphDashboard } from './components/GraphDashboard';

function App() {
  return <GraphDashboard />;
}
```

---

## 🎨 Styling

Using **TailwindCSS** for styling. Add to your `tailwind.config.js`:

```javascript
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

---

## 📡 API Integration

All components integrate with the GraphRAG REST API:
- `POST /api/v1/graph/search/hybrid` - Search
- `GET /api/v1/graph/protocols/{id}/ecosystem` - Graph data
- `WS /api/v1/ws/graph` - Real-time updates

---

## 🔐 Authentication

Store JWT token in localStorage:
```typescript
localStorage.setItem('token', 'your-jwt-token');
```

All API calls include:
```typescript
headers: {
  'Authorization': `Bearer ${localStorage.getItem('token')}`,
}
```

---

**Ready to build! 🚀**
