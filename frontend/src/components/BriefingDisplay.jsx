import { useEffect, useRef, useMemo } from 'react';
import html2pdf from 'html2pdf.js';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';

import remarkGfm from 'remark-gfm';

export const BriefingDisplay = ({ data, loading, processingMessage, currentQuery }) => {
  const contentRef = useRef(null);
  const briefingContainerRef = useRef(null);

  // Scroll to top when new briefing arrives
  useEffect(() => {
    if (contentRef.current && data) {
      setTimeout(() => {
        contentRef.current.scrollTop = 0;
      }, 100);
    }
  }, [data]);

  const briefing = data?.insight || data?.briefing || '';

  const renderSourceBadge = (sourceName) => {
    const sourceMap = {
      'FRED': '📊',
      'Yahoo Finance': '💰',
      'GitHub': '🔗',
      'HackerNews': '⚡',
      'Tavily': '🌐',
      'NewsAPI': '📰',
      'GDELT': '🗺',
      'Google News': '📱',
    };
    
    return sourceMap[sourceName] || '📌';
  };

  const exportToPDF = () => {
    if (!briefingContainerRef.current) return;

    const element = briefingContainerRef.current;
    const opt = {
      margin: 10,
      filename: `briefing-${new Date().toISOString().split('T')[0]}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { orientation: 'portrait', unit: 'mm', format: 'a4' },
    };

    html2pdf().set(opt).from(element).save();
  };

  const getSourceStatus = (source) => {
    if (typeof source === 'object') {
      return source.status === 'Success' ? 'success' : 'failed';
    }
    return 'success';
  };

  return (
    <div className="output-panel">
      <div className="output-header" style={{ display: 'none' }}>
        <span>BRIEFING OUTPUT</span>
        <div className="output-header-actions">
          <button
            onClick={exportToPDF}
            disabled={!data}
            className="export-pdf-btn"
            title="Export to PDF"
          >
            📄 PDF
          </button>
          <span style={{ fontSize: '10px', letterSpacing: '0.3px' }}>
            {loading ? '⟳ STREAMING...' : '✓ COMPLETE'}
          </span>
        </div>
      </div>

      <div className="output-content" ref={contentRef}>
        {!data && !loading && (
          <div className="empty-state" style={{ 
            background: 'transparent', 
            border: 'none', 
            padding: '10% 0', 
            textAlign: 'center', 
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <h2 style={{ 
              fontSize: '24px', 
              fontWeight: '500', 
              color: 'var(--neon-green)', 
              marginBottom: '10px', 
              opacity: 1.0,
              letterSpacing: '1.5px',
              fontFamily: 'var(--font-mono)',
              textTransform: 'uppercase',
              textShadow: '0 0 15px rgba(16, 185, 129, 0.3)'
            }}>
              How can I help you today?
            </h2>
            <p style={{ 
              fontSize: '11px', 
              opacity: 0.4, 
              letterSpacing: '2px', 
              fontFamily: 'var(--font-mono)',
              textTransform: 'uppercase',
              color: 'var(--text-main)'
            }}>
              Input a query to begin intelligence synthesis
            </p>
          </div>
        )}

        {loading && (
          <div className="conversation-thread">
            <div className="chat-block user-block">
              <div className="chat-msg-user">
                {currentQuery || 'COMMAND SEQUENCE INITIATED...'}
              </div>
            </div>
            
            <div className="chat-block ai-block">
              <div className="chat-meta">
                <span className="text-green" style={{ fontWeight: 'bold' }}>HEURISTIC_AI</span>
              </div>
              <div className="chat-msg-ai">
                <div style={{ padding: '10px 0' }}>
                  <div className="loading-label" style={{ fontSize: '11px', letterSpacing: '2px', marginBottom: '10px', color: 'var(--neon-cyan)' }}>
                    ANALYSING...
                  </div>
                  <div className="loader-scan" style={{ width: '60px', opacity: 0.6 }}></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {data && (
          <div className="conversation-thread" ref={briefingContainerRef}>
            
            <div className="chat-block user-block">
              <div className="chat-msg-user">
                {data.query || currentQuery || 'COMMAND SEQUENCE EXECUTED.'}
              </div>
            </div>

            <div className="chat-block ai-block">
              <div className="chat-meta">
                <span className="text-green" style={{ fontWeight: 'bold' }}>HEURISTIC_AI</span> {new Date(data.retrieved_at ? data.retrieved_at : Date.now()).toLocaleTimeString('en-GB')}
              </div>
              <div className="chat-msg-ai">
                {/* Domain Intelligence Tags */}
                {data.domains_triggered && data.domains_triggered.length > 0 && (() => {
                  const DOMAIN_META = {
                    'geopolitics':  { label: 'GEOPOLITICAL INTELLIGENCE', icon: '🌐' },
                    'climate':      { label: 'CLIMATE & HAZARDS INTEL',    icon: '🌡' },
                    'technology':   { label: 'CYBER / TECH SIGNALS',        icon: '⚡' },
                    'economics':    { label: 'ECONOMIC INTELLIGENCE',        icon: '📊' },
                    'weather':      { label: 'ATMOSPHERIC INTELLIGENCE',     icon: '🌩' },
                  };
                  return (
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '14px' }}>
                      {data.domains_triggered.map((domain, idx) => {
                        const meta = DOMAIN_META[domain] || { label: domain.toUpperCase() + ' INTELLIGENCE', icon: '📡' };
                        return (
                          <span key={idx} style={{
                            display: 'inline-flex', alignItems: 'center', gap: '5px',
                            fontSize: '9px', letterSpacing: '1.5px', fontFamily: 'var(--font-mono)',
                            padding: '3px 10px',
                            border: '1px solid rgba(0, 212, 255, 0.25)',
                            borderRadius: '2px',
                            color: 'rgba(0, 212, 255, 0.75)',
                            background: 'rgba(0, 212, 255, 0.05)',
                          }}>
                            {meta.icon} {meta.label}
                          </span>
                        );
                      })}
                    </div>
                  );
                })()}

                {/* Content Rendering via ReactMarkdown */}
            <div className="md-section">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw]}
                components={{
                  h1: ({node, ...props}) => <h1 className="markdown-body" style={{ color: 'var(--neon-green)', marginTop: '20px', marginBottom: '10px', fontSize: '18px', borderBottom: '1px solid var(--border-dim)', paddingBottom: '5px' }} {...props} />,
                  h2: ({node, ...props}) => <h2 className="markdown-body" style={{ color: 'var(--neon-green)', marginTop: '16px', marginBottom: '8px', fontSize: '14px', letterSpacing: '1px', textTransform: 'uppercase' }} {...props} />,
                  h3: ({node, ...props}) => <h3 style={{ marginTop: '14px', marginBottom: '8px', fontSize: '12px', color: 'var(--text-main)' }} {...props} />,
                  p: ({node, ...props}) => {
                    // Safe string parsing for custom intelligence boxes
                    if (node && node.children && node.children.length === 1 && node.children[0].type === 'text') {
                      const text = node.children[0].value;
                      if (text.includes('CRITICAL')) {
                         return <div className="intelligence-box critical"><div className="intelligence-label">🔴 CRITICAL INTELLIGENCE</div><div className="intelligence-content"><p {...props} /></div></div>;
                      }
                      if (text.includes('WARNING')) {
                         return <div className="intelligence-box warning"><div className="intelligence-label warning">⚠ WARNING ANALYSIS</div><div className="intelligence-content"><p {...props} /></div></div>;
                      }
                    }
                    return <p style={{ marginBottom: '10px', lineHeight: '1.6' }} {...props} />;
                  },
                  ul: ({node, ...props}) => <ul style={{ marginBottom: '12px', paddingLeft: '20px', lineHeight: '1.6' }} {...props} />,
                  ol: ({node, ...props}) => <ol style={{ marginBottom: '12px', paddingLeft: '20px', lineHeight: '1.6' }} {...props} />,
                  li: ({node, ...props}) => <li style={{ marginBottom: '4px' }} {...props} />,
                  table: ({node, ...props}) => (
                    <div className="markdown-table-wrapper" style={{ margin: '15px 0' }}>
                      <table className="markdown-table" {...props} />
                    </div>
                  ),
                  th: ({node, ...props}) => <th style={{ padding: '8px', borderBottom: '1px solid var(--neon-green)', background: 'rgba(0,0,0,0.5)', color: 'var(--neon-green)', textAlign: 'left' }} {...props} />,
                  td: ({node, ...props}) => <td style={{ padding: '8px', borderBottom: '1px solid var(--border-dim)' }} {...props} />,
                  a: ({node, ...props}) => <a style={{ color: 'var(--neon-cyan)', textDecoration: 'underline' }} target="_blank" rel="noopener noreferrer" {...props} />,
                  blockquote: ({node, ...props}) => <blockquote style={{ borderLeft: '3px solid var(--neon-amber)', margin: '10px 0', paddingLeft: '10px', color: 'var(--text-dim)' }} {...props} />
                }}
              >
                {briefing}
              </ReactMarkdown>
            </div>

            {/* Sources Section */}
            {data.sources_used && data.sources_used.length > 0 && (
              <div className="sources-section">
                <div className="sources-title">📌 DATA SOURCES</div>
                <ul className="sources-list">
                  {data.sources_used.map((source, idx) => {
                    const sourceName = typeof source === 'string' ? source : source.source_name;
                    const sourceStatus = typeof source === 'object' ? source.status : 'Success';
                    const statusClass =
                      sourceStatus === 'Success' || sourceStatus === 'NO_DATA'
                        ? 'success'
                        : 'failed';

                    return (
                      <li key={idx} className="source-item">
                        <span className={`source-status ${statusClass}`}></span>
                        <span>
                          {renderSourceBadge(sourceName)} {sourceName}
                        </span>
                        {sourceStatus && sourceStatus !== 'Success' && (
                          <span style={{ marginLeft: 'auto', fontSize: '10px', opacity: 0.7 }}>
                            [{sourceStatus}]
                          </span>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {/* Data Quality */}
            {data.data_quality_summary && (
              <div className="sources-section">
                <div className="sources-title">✓ DATA QUALITY</div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                  {data.data_quality_summary}
                </p>
              </div>
            )}
              </div>
            </div>
          </div>
        )}

        {data && (!briefing) && !loading && (
          <div className="empty-state">
            <div className="empty-state-icon">⚠</div>
            <div className="empty-state-text">
              No briefing content received. Check backend logs.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};


