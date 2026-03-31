import { useState, useEffect, useCallback, useRef } from 'react';
import { WorldMap } from './WorldMap';
import { BriefingDisplay } from './BriefingDisplay';
import KnowledgeGraph from './KnowledgeGraph';
import axios from 'axios';
import { Globe, Database, Send, User, AlertTriangle } from 'lucide-react';
import React from 'react';
import StandardErrorBoundary from './StandardErrorBoundary';

export const Dashboard = ({ onQueryClick, briefingData, status, loading: apiLoading, processingMessage }) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [alerts, setAlerts] = useState([]); 
  const [dashboardData, setDashboardData] = useState(null);

  // ── Neural Discovery Listener ──────────────────────────────────────────
  useEffect(() => {
    const handleDiscovery = (e) => {
        const { nodeName, label } = e.detail;
        const id = Date.now();
        const newAlert = { id, text: `NEW ENTITY DISCOVERED: ${nodeName}`, sub: `CLASS: ${label.toUpperCase()}`, type: 'discovery' };
        setAlerts(prev => [newAlert, ...prev].slice(0, 5));
        
        setTimeout(() => {
            setAlerts(prev => prev.filter(a => a.id !== id));
        }, 6000);
    };
    window.addEventListener('tactical-discovery', handleDiscovery);
    return () => window.removeEventListener('tactical-discovery', handleDiscovery);
  }, []);

  const [query, setQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [view, setView] = useState('dashboard'); 
  const [mapOverlays] = useState({
    conflicts: true,
    airTraffic: true,
    shipRoutes: true,
    weather: true,
  });
  const [loading, setLoading] = useState(true);
  const [queryLoading, setQueryLoading] = useState(false);

  // ── Resizable columns state ────────────────────────
  const [leftPct,     setLeftPct]     = useState(50);
  const [mapPct,      setMapPct]      = useState(52);
  const [resizing,    setResizing]    = useState(null);

  const workspaceRef = useRef(null);
  const leftColRef   = useRef(null);
  const rightColRef  = useRef(null);

  // ── Robust Window-Based Resizing ───────────────────────────────────
  useEffect(() => {
    if (!resizing) return;

    // Capture original values for style resets
    const originalSelect = document.body.style.userSelect;
    document.body.style.userSelect = 'none';

    const handleMove = (e) => {
      if (!workspaceRef.current) return;
      const rect = workspaceRef.current.getBoundingClientRect();

      if (resizing === 'v') {
        const x = e.clientX - rect.left;
        const pct = Math.min(Math.max((x / rect.width) * 100, 15), 85);
        setLeftPct(pct);
      } else if (resizing === 'h' && leftColRef.current) {
        const lRect = leftColRef.current.getBoundingClientRect();
        const y = e.clientY - lRect.top;
        const pct = Math.min(Math.max((y / lRect.height) * 100, 10), 90);
        setMapPct(pct);
      }
    };

    const handleUp = () => {
      setResizing(null);
      document.body.style.userSelect = originalSelect;
    };

    // Use capture phase to ensure we beat elements like Leaflet that stop propagation
    window.addEventListener('pointermove', handleMove, { capture: true });
    window.addEventListener('pointerup', handleUp, { capture: true });
    return () => {
      window.removeEventListener('pointermove', handleMove, { capture: true });
      window.removeEventListener('pointerup', handleUp, { capture: true });
      document.body.style.userSelect = originalSelect;
    };
  }, [resizing]);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/v1/dashboard');
        setDashboardData(response.data);
      } catch (err) {
        console.error('Dashboard error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 30 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const handleQuerySubmit = useCallback(async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    const captured = query.trim();
    setSubmittedQuery(captured);
    setQueryLoading(true);
    setQuery('');
    try {
      onQueryClick(captured);
    } finally {
      setQueryLoading(false);
    }
  }, [query, onQueryClick]);

  const renderOsintFeed = (newsItems, title) => {
    if (!newsItems || newsItems.length === 0) {
      return (
        <div className="pane-content empty">
          <div className="loader-scan"></div>
          <span>AWAITING {title} SIGNAL...</span>
        </div>
      );
    }
    return (
      <div className="pane-content osint-feed">
        <div className="news-list">
          {newsItems.map((item, idx) => (
            <div key={idx} className="news-item">
              <div className="news-meta">
                <span className="news-source neon-red">[SIGNAL {idx+1}]</span>
                <span className="news-time">{item?.publishedAt ? new Date(item.publishedAt).toLocaleTimeString() : 'RECENT'}</span>
              </div>
              <div className="news-title">{item?.title ? item.title.toUpperCase() : 'UNTITLED SIGNAL'}</div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderMarkets = (macros) => {
    if (!macros || macros.length === 0) {
      return (
        <div className="pane-content empty">
          <div className="loader-scan"></div>
          <span>AWAITING MARKET TICKERS...</span>
        </div>
      );
    }
    const TICKER_NAMES = {
      'GC=F': 'GOLD',
      'CL=F': 'OIL',
      'DX-Y.NYB': 'US DOLLAR',
      'BTC-USD': 'BITCOIN'
    };
    return (
      <div className="pane-content market-board" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <div className="market-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
          {macros.map((m, idx) => {
            const isPositive = m?.pct_change >= 0;
            const delta = m?.pct_change !== undefined ? Math.abs(m.pct_change).toFixed(2) : '0.00';
            return (
              <div key={idx} className="market-ticker" style={{ cursor: 'default', borderColor: 'var(--border-dim)', background: 'rgba(0,0,0,0.3)' }}>
                <div className="ticker-meta">
                  <span className="ticker-symbol" style={{ color: 'var(--neon-cyan)', fontSize: '11px' }}>
                    {TICKER_NAMES[m?.symbol] || m?.name?.split(' ')[0].toUpperCase() || 'N/A'}
                  </span>
                </div>
                <div className="ticker-price-wrapper" style={{ textAlign: 'right' }}>
                  <div className="ticker-price" style={{ fontSize: '12px' }}>${m?.price && typeof m.price === 'number' ? m.price.toFixed(2) : 'N/A'}</div>
                  <div className={`ticker-delta ${isPositive ? 'text-green' : 'text-red'}`} style={{ fontSize: '8px' }}>
                    {isPositive ? '+' : '-'}{delta}%
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="tactical-os-layout" style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* HEADER */}
      <div className="os-top-header" style={{ height: '54px', background: 'rgba(3,10,14,0.98)', borderBottom: '1px solid rgba(0,245,212,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px', zIndex: 1000, backdropFilter: 'blur(10px)' }}>
        <div className="global-branding" style={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
          <div style={{ fontFamily: 'Rajdhani', fontWeight: 700, fontSize: '22px', color: '#00f5d4', letterSpacing: '8px', textShadow: '0 0 12px rgba(0,245,212,0.4)', lineHeight: '1', display: 'flex', alignItems: 'center' }}>
            KRONOS
            <div style={{ width: '3px', height: '14px', background: '#00f5d4', marginLeft: '10px', opacity: 0.4, animation: 'blink 1.5s infinite' }}></div>
          </div>
          <div style={{ fontFamily: 'Share Tech Mono', fontSize: '8px', color: '#6bc0b4', letterSpacing: '1px', opacity: 0.7, paddingLeft: '2px' }}>COMMAND_ROOT // INTEL_OS_STABLE // V.4.2.0</div>
        </div>
        <div className="global-status-hud" style={{ textAlign: 'right' }}>
          <div style={{ fontFamily: 'Share Tech Mono', fontSize: '9px', color: '#00f5d4', letterSpacing: '1px', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px' }}>
            <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#00f5d4', boxShadow: '0 0 8px #00f5d4' }}></span>
            LIVE_DATA_STREAM: [CONNECTED]
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* SIDEBAR */}
        <div className="os-sidebar" style={{ width: '60px', background: 'rgba(3,10,14,0.95)', borderRight: '1px solid rgba(0,245,212,0.1)', display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: '20px', gap: '20px' }}>
          <div className={`nav-item ${view === 'dashboard' ? 'active' : ''}`} onClick={() => setView('dashboard')} style={{ cursor: 'pointer' }}><Globe size={20} /></div>
          <div className={`nav-item ${view === 'ontology' ? 'active' : ''}`} onClick={() => setView('ontology')} style={{ cursor: 'pointer' }}><Database size={20} /></div>
        </div>

        {/* WORKSPACE */}
        <div className="os-workspace" ref={workspaceRef} style={{ flex: 1, display: 'flex', position: 'relative', overflow: 'hidden' }}>
          
          {/* PERSISTENT DASHBOARD VIEW */}
          <div style={{ 
            display: view === 'dashboard' ? 'flex' : 'none', 
            width: '100%', 
            height: '100%',
            position: 'absolute',
            top: 0, left: 0
          }}>
            <div className="os-col-left" ref={leftColRef} style={{ width: `${leftPct}%`, display: 'flex', flexDirection: 'column', height: '100%', minWidth: '200px', pointerEvents: resizing ? 'none' : 'auto' }}>
              <div className="os-module map-module" style={{ height: `${mapPct}%`, position: 'relative', borderBottom: '1px solid rgba(0,245,212,0.1)', minHeight: '100px' }}>
                <WorldMap overlays={mapOverlays} dashboardData={dashboardData} />
              </div>
              
              {/* FINAL ROBUST HORIZONTAL DIVIDER */}
              <div 
                className="resizer-h" 
                onPointerDown={() => setResizing('h')}
                style={{ 
                  height: '24px', 
                  margin: '-12px 0',
                  cursor: 'row-resize', 
                  zIndex: 2000,
                  position: 'relative',
                  display: 'flex',
                  alignItems: 'center',
                  touchAction: 'none'
                }} 
              >
                <div style={{ width: '100%', height: '1px', background: resizing === 'h' ? 'rgba(0,245,212,0.6)' : 'rgba(0,245,212,0.15)', transition: 'background 0.2s' }}></div>
              </div>

              <div className="lower-domains-wrapper" style={{ flex: 1, display: 'flex', gap: '10px', padding: '10px', overflow: 'hidden', minHeight: '100px' }}>
                <div className="os-module" style={{ flex: 1, display: 'flex', flexDirection: 'column', border: '1px solid rgba(0,245,212,0.1)' }}>
                  <div className="pane-header" style={{ padding: '8px', background: 'rgba(0,245,212,0.05)', fontSize: '10px', color: '#00f5d4' }}>GEOPOLITICAL_LOG</div>
                  {renderOsintFeed(dashboardData?.geo_news, 'GEOPOLITICS')}
                </div>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div className="os-module" style={{ flex: 1, border: '1px solid rgba(0,245,212,0.1)' }}>
                     <div className="pane-header" style={{ padding: '8px', background: 'rgba(0,245,212,0.05)', fontSize: '10px', color: '#00f5d4' }}>MARKET_TICKERS</div>
                     {renderMarkets(dashboardData?.econ_news)}
                  </div>
                  <div className="os-module" style={{ flex: 1, border: '1px solid rgba(0,245,212,0.1)' }}>
                     <div className="pane-header" style={{ padding: '8px', background: 'rgba(0,245,212,0.05)', fontSize: '10px', color: '#00f5d4' }}>CYBER_SIGNALS</div>
                     {renderOsintFeed(dashboardData?.tech_news, 'CYBER')}
                  </div>
                </div>
              </div>
            </div>

            {/* FINAL ROBUST VERTICAL DIVIDER */}
            <div 
              className="resizer-v" 
              onPointerDown={() => setResizing('v')}
              style={{ 
                width: '24px', 
                margin: '0 -12px',
                cursor: 'col-resize', 
                zIndex: 2000,
                position: 'relative',
                display: 'flex',
                justifyContent: 'center',
                touchAction: 'none'
              }} 
            >
              <div style={{ width: '1px', height: '100%', background: resizing === 'v' ? 'rgba(0,245,212,0.6)' : 'rgba(0,245,212,0.15)', transition: 'background 0.2s' }}></div>
            </div>

            <div className="os-col-right" ref={rightColRef} style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', borderLeft: '1px solid rgba(0,245,212,0.1)', minWidth: '300px', pointerEvents: resizing ? 'none' : 'auto' }}>
               <div className="log-stream-container" style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
                  <BriefingDisplay data={briefingData} loading={apiLoading} processingMessage={processingMessage} currentQuery={submittedQuery} />
               </div>

               <div className="command-terminal-wrapper" style={{ padding: '20px', borderTop: '1px solid rgba(0,245,212,0.2)', background: 'rgba(0,10,15,0.8)' }}>
                  <form onSubmit={handleQuerySubmit} style={{ display: 'flex', gap: '12px', width: '100%' }}>
                    <input 
                      className="cmd-input-field" 
                      placeholder="INPUT STRATEGIC COMMAND SEQUENCE..." 
                      value={query} 
                      onChange={(e)=>setQuery(e.target.value)} 
                      style={{ 
                        flex: 1, 
                        background: 'rgba(0,20,30,0.6)', 
                        border: '1px solid rgba(0,245,212,0.4)', 
                        color: '#00f5d4', 
                        padding: '14px 18px',
                        fontFamily: "'Share Tech Mono', monospace",
                        fontSize: '14px',
                        letterSpacing: '1px',
                        outline: 'none',
                        boxShadow: 'inset 0 0 10px rgba(0,245,212,0.1)'
                      }} 
                    />
                    <button type="submit" style={{ background: 'rgba(0,245,212,0.15)', border: '1px solid #00f5d4', color: '#00f5d4', padding: '0 25px', cursor: 'pointer', transition: 'all 0.2s' }}>
                      <Send size={20}/>
                    </button>
                  </form>
               </div>
            </div>
          </div>

          {/* PERSISTENT ONTOLOGY VIEW */}
          <div style={{ 
            display: view === 'ontology' ? 'block' : 'none', 
            flex: 1, 
            height: '100%', 
            width: '100%',
            position: 'absolute',
            top: 0, left: 0
          }}>
            <StandardErrorBoundary key="ontology_boundary">
              <KnowledgeGraph />
            </StandardErrorBoundary>
          </div>
        </div>

      </div>
      <style>{`
        .nav-item { color: rgba(0,245,212,0.4); transition: 0.3s; }
        .nav-item.active { color: #00f5d4; }
        .os-sidebar .nav-item:hover { color: #fff; }
        @keyframes blink { 0%, 100% { opacity: 0.4; } 50% { opacity: 0.1; } }
        .os-module { background: rgba(3,10,14,0.4); position: relative; overflow: hidden; }
        .pane-content { flex: 1; overflow-y: auto; padding: 10px; font-family: 'Share Tech Mono'; font-size: 11px; }
        .news-item { margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px; }
        .news-meta { font-size: 9px; margin-bottom: 4px; display: flex; justify-content: space-between; }
        .news-source { color: #ff4b4b; }
        .news-title { color: #fff; line-height: 1.4; }
        .market-ticker { display: flex; justify-content: space-between; padding: 8px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 4px; }
        .text-green { color: #00f5d4; }
        .text-red { color: #ff4b4b; }
      `}</style>
    </div>
  );
};

export default Dashboard;
