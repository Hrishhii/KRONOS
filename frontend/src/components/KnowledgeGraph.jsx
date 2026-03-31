import React, { useEffect, useRef, useState, useCallback } from 'react';
import axios from 'axios';

// ── KRONOS Design Tokens ───────────────────────────────────────────
const NODE_COLORS = {
    'country':        '#00f5d4', // Neon Teal
    'location':       '#00f5d4',
    'asset':          '#f5a623', // Amber
    'commodity':      '#f5a623',
    'leader':         '#a855f7', // Purple
    'person':         '#a855f7',
    'organization':   '#3b82f6', // Blue
    'indicator':      '#22c55e', // Green
    'event':          '#ff4757', // Red
    'infrastructure': '#f97316', // Orange
    'technology':     '#00e5ff', // Cyan
    'company':        '#818cf8', // Indigo
    'policy':         '#e879f9', // Pink
    'topic':          '#ec4899', // Rose
};

const NODE_TYPE_DISPLAY = {
    'Country':        { label: 'Country',        color: '#00f5d4', desc: 'Sovereign nations' },
    'Asset':          { label: 'Commodity/Asset', color: '#f5a623', desc: 'Energy, resources, tradeable goods' },
    'Leader':         { label: 'Leader',          color: '#a855f7', desc: 'Political & military leaders' },
    'Organization':   { label: 'Organization',    color: '#3b82f6', desc: 'Alliances, militant groups, bodies' },
    'Indicator':      { label: 'Indicator',       color: '#22c55e', desc: 'Economic metrics & indices' },
    'Event':          { label: 'Event',           color: '#ff4757', desc: 'Specific incidents & events' },
    'Technology':     { label: 'Technology',       color: '#00e5ff', desc: 'Critical emerging tech' },
};

const KnowledgeGraph = () => {
    const canvasRef = useRef(null);
    const [data, setData] = useState({ nodes: [], links: [] });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [legendOpen, setLegendOpen] = useState(true);
    const [hoveredNode, setHoveredNode] = useState(null);
    const [hoveredLink, setHoveredLink] = useState(null);
    const [tooltipPos, setTooltipPos] = useState(null);
    
    // Camera State (Minimal Physics)
    const transformRef = useRef({ x: 0, y: 0, scale: 0.8 });
    const nodesRef = useRef([]);
    const linksRef = useRef([]);
    const [draggedNode, setDraggedNode] = useState(null);
    const dragOffsetRef = useRef({ x: 0, y: 0 });
    const layoutCalculatedRef = useRef(false);
    const [animating, setAnimating] = useState(false);

    const fetchData = useCallback(async () => {
        try {
            setLoading(true);
            const response = await axios.get('/api/v1/graph/data');
            
            const rawData = response.data;
            const nodes = rawData.nodes || [];
            const links = rawData.links || rawData.edges || [];
            
            // Better initial layout with proper radius based on graph size
            const canvas = canvasRef.current;
            if (!canvas) throw new Error('Canvas not ready');
            const rect = canvas.getBoundingClientRect();
            const radius = Math.min(rect.width, rect.height) * 0.25;
            
            nodesRef.current = nodes.map((n, idx) => {
                const angleStep = (2 * Math.PI) / nodes.length;
                const angle = idx * angleStep + (Math.random() - 0.5) * 0.5;
                return {
                    ...n,
                    x: Math.cos(angle) * radius + (Math.random()-0.5)*40,
                    y: Math.sin(angle) * radius + (Math.random()-0.5)*40,
                    vx: 0,
                    vy: 0,
                    fixed: false,
                    pulsePhase: Math.random() * Math.PI * 2
                };
            });
            
            linksRef.current = links;
            setData({ nodes, links });
            layoutCalculatedRef.current = true;
            setError(null);
        } catch (err) {
            console.error("Graph load error:", err);
            setError("LINK_FAILURE: DATA_STREAM_INTERRUPTED");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
        // Removed periodic sync - graph will stay stable
        return () => {};
    }, [fetchData]);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        let animationFrame;

        const render = () => {
            if (!ctx || !canvas) return;
            
            // DPI Management & Resize
            const dpr = window.devicePixelRatio || 1;
            const rect = canvas.getBoundingClientRect();
            if (canvas.width !== rect.width * dpr || canvas.height !== rect.height * dpr) {
                canvas.width = rect.width * dpr;
                canvas.height = rect.height * dpr;
                ctx.scale(dpr, dpr);
            }

            // Background
            ctx.fillStyle = '#030a0e';
            ctx.fillRect(0, 0, rect.width, rect.height);
            
            // Grid lines
            ctx.strokeStyle = 'rgba(0, 245, 212, 0.02)';
            ctx.lineWidth = 1;
            const gridSize = 50 * transformRef.current.scale;
            for (let x = transformRef.current.x % gridSize; x < rect.width; x += gridSize) {
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, rect.height); ctx.stroke();
            }
            for (let y = transformRef.current.y % gridSize; y < rect.height; y += gridSize) {
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(rect.width, y); ctx.stroke();
            }

            ctx.save();
            ctx.translate(rect.width / 2 + transformRef.current.x, rect.height / 2 + transformRef.current.y);
            ctx.scale(transformRef.current.scale, transformRef.current.scale);

            // ── Strong Physics to Spread Nodes ──
            const nodes = nodesRef.current;
            const links = linksRef.current;

            // Strong Repulsion between all node pairs
            for (let i = 0; i < nodes.length; i++) {
                const n1 = nodes[i];
                if (draggedNode && n1.id === draggedNode.id) continue;
                if (n1.fixed) continue;
                
                for (let j = i + 1; j < nodes.length; j++) {
                    const n2 = nodes[j];
                    if (draggedNode && n2.id === draggedNode.id) continue;
                    if (n2.fixed) continue;
                    
                    const dx = n2.x - n1.x;
                    const dy = n2.y - n1.y;
                    const dist = Math.max(Math.sqrt(dx*dx + dy*dy), 1);
                    const repulsion = 8000;  // Strong repulsion like reference
                    const force = repulsion / (dist * dist);
                    const fx = (dx / dist) * force;
                    const fy = (dy / dist) * force;
                    n1.vx -= fx; n1.vy -= fy;
                    n2.vx += fx; n2.vy += fy;
                }
            }

            // Link Attraction - Keep connected nodes together
            links.forEach(l => {
                const s = nodes.find(n => n.id === l.source);
                const t = nodes.find(n => n.id === l.target);
                if (s && t && !s.fixed && !t.fixed) {
                    const dx = t.x - s.x;
                    const dy = t.y - s.y;
                    const dist = Math.max(Math.sqrt(dx*dx + dy*dy), 1);
                    const minDist = 80;  // Better spacing like reference
                    const attraction = 0.03;  // Like reference code
                    const force = attraction * (dist - minDist);
                    const fx = (dx / dist) * force;
                    const fy = (dy / dist) * force;
                    s.vx += fx; s.vy += fy;
                    t.vx -= fx; t.vy -= fy;
                }
            });

            // Gentle center gravity to keep graph centered and pull solo nodes closer
            nodes.forEach(n => {
                if (draggedNode && n.id === draggedNode.id) return;
                if (n.fixed) return;
                n.vx += (0 - n.x) * 0.005;  // Increased from 0.001 to pull solo nodes closer
                n.vy += (0 - n.y) * 0.005;
            });

            // Update positions with moderate damping like reference
            nodes.forEach(n => {
                if (draggedNode && n.id === draggedNode.id) {
                    n.vx = 0; n.vy = 0;
                    return;
                }
                if (!n.fixed) {
                    n.x += n.vx;
                    n.y += n.vy;
                    n.vx *= 0.82;  // Moderate damping like reference (was 0.97)
                    n.vy *= 0.82;
                }
            });

            // Draw Links with Arrowheads and Labels
            links.forEach(l => {
                const s = nodes.find(n => n.id === l.source);
                const t = nodes.find(n => n.id === l.target);
                if (s && t) {
                    const isHoveredLink = hoveredLink?.source === l.source && hoveredLink?.target === l.target;
                    const dx = t.x - s.x;
                    const dy = t.y - s.y;
                    const dist = Math.sqrt(dx*dx + dy*dy);
                    const ux = dx / dist, uy = dy / dist;
                    
                    // Line with offset from node radius
                    ctx.beginPath();
                    ctx.strokeStyle = isHoveredLink ? 'rgba(0, 245, 212, 0.8)' : 'rgba(0, 245, 212, 0.35)';
                    ctx.lineWidth = isHoveredLink ? 1.5 : 0.9;
                    ctx.moveTo(s.x + ux * 8, s.y + uy * 8);
                    ctx.lineTo(t.x - ux * 16, t.y - uy * 16);
                    ctx.stroke();
                    
                    // Arrowhead
                    const angle = Math.atan2(dy, dx);
                    const ax = t.x - ux * 16;
                    const ay = t.y - uy * 16;
                    ctx.beginPath();
                    ctx.moveTo(ax, ay);
                    ctx.lineTo(ax - 8*Math.cos(angle-0.4), ay - 8*Math.sin(angle-0.4));
                    ctx.lineTo(ax - 8*Math.cos(angle+0.4), ay - 8*Math.sin(angle+0.4));
                    ctx.closePath();
                    ctx.fillStyle = isHoveredLink ? 'rgba(0, 245, 212, 0.8)' : 'rgba(0, 245, 212, 0.35)';
                    ctx.fill();
                    
                    // Relationship label on edge - HIDDEN
                    // Labels only shown in tooltip on hover
                }
            });

            // Draw Nodes with Enhanced Visuals
            nodes.forEach(n => {
                const color = NODE_COLORS[n.group?.toLowerCase()] || '#00f5d4';
                const isHovered = hoveredNode?.id === n.id;
                const nodeRadius = isHovered ? 9 : 7;
                const pulse = Math.sin((performance.now() * 0.002) + (n.pulsePhase || 0)) * 0.5 + 0.5;
                
                // Outer glow ring (pulsing)
                const glowR = nodeRadius + 5 + pulse * 3;
                const grd = ctx.createRadialGradient(n.x, n.y, nodeRadius, n.x, n.y, glowR + 4);
                grd.addColorStop(0, color + '40');
                grd.addColorStop(1, color + '05');
                ctx.beginPath();
                ctx.arc(n.x, n.y, glowR + 4, 0, Math.PI * 2);
                ctx.fillStyle = grd;
                ctx.fill();
                
                // Main circle
                ctx.beginPath();
                ctx.arc(n.x, n.y, nodeRadius, 0, Math.PI * 2);
                ctx.fillStyle = isHovered ? color : color + 'dd';
                ctx.fill();
                
                // Inner bright core
                ctx.beginPath();
                ctx.arc(n.x, n.y, nodeRadius * 0.45, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(255,255,255,0.65)';
                ctx.fill();

                // Label - always visible
                ctx.fillStyle = '#fff';
                ctx.font = `600 11px 'Rajdhani', sans-serif`;
                ctx.textAlign = 'left';
                ctx.textBaseline = 'top';
                ctx.fillText(n.name?.toUpperCase() || n.id, n.x + 16, n.y - 8);
                
                // Type badge - only show on hover
                if (isHovered) {
                    ctx.font = `400 8px 'Share Tech Mono', monospace`;
                    ctx.fillStyle = color + 'dd';
                    ctx.fillText((n.group || 'UNKNOWN').toUpperCase(), n.x + 16, n.y + 4);
                }
            });

            ctx.restore();
            animationFrame = requestAnimationFrame(render);
        };

        render();
        return () => cancelAnimationFrame(animationFrame);
    }, [data, hoveredNode, hoveredLink, draggedNode]);

    // ── MOUSE HOVER DETECTION ──
    const onMouseMove = (e) => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const canvasX = e.clientX - rect.left;
        const canvasY = e.clientY - rect.top;

        // Transform from screen to graph coordinates
        const transform = transformRef.current;
        const graphX = (canvasX - rect.width / 2 - transform.x) / transform.scale;
        const graphY = (canvasY - rect.height / 2 - transform.y) / transform.scale;

        // Check node hover
        let foundNode = null;
        for (const node of nodesRef.current) {
            const dx = node.x - graphX;
            const dy = node.y - graphY;
            if (dx*dx + dy*dy < 100) {
                foundNode = node;
                setTooltipPos({ x: e.clientX, y: e.clientY });
                break;
            }
        }
        setHoveredNode(foundNode);

        // Check link hover
        let foundLink = null;
        for (const link of linksRef.current) {
            const s = nodesRef.current.find(n => n.id === link.source);
            const t = nodesRef.current.find(n => n.id === link.target);
            if (!s || !t) continue;

            const dx = t.x - s.x;
            const dy = t.y - s.y;
            const len = Math.sqrt(dx*dx + dy*dy);
            if (len === 0) continue;

            const px = graphX - s.x;
            const py = graphY - s.y;
            const proj = (px * dx + py * dy) / (len * len);
            
            if (proj >= 0 && proj <= 1) {
                const nearX = s.x + proj * dx;
                const nearY = s.y + proj * dy;
                const dist = Math.sqrt((graphX - nearX)**2 + (graphY - nearY)**2);
                
                if (dist < 15) {
                    foundLink = link;
                    setTooltipPos({ x: e.clientX, y: e.clientY });
                    break;
                }
            }
        }
        setHoveredLink(foundLink);
    };

    // Handle Pan/Zoom and Node Dragging
    const onMouseDown = (e) => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const canvasX = e.clientX - rect.left;
        const canvasY = e.clientY - rect.top;

        // Transform from screen to graph coordinates
        const transform = transformRef.current;
        const graphX = (canvasX - rect.width / 2 - transform.x) / transform.scale;
        const graphY = (canvasY - rect.height / 2 - transform.y) / transform.scale;

        // Check if clicking on a node
        let clickedNode = null;
        for (const node of nodesRef.current) {
            const dx = node.x - graphX;
            const dy = node.y - graphY;
            if (dx*dx + dy*dy < 100) {
                clickedNode = node;
                break;
            }
        }

        if (clickedNode) {
            // Node drag mode
            setDraggedNode(clickedNode);
            dragOffsetRef.current = { x: clickedNode.x - graphX, y: clickedNode.y - graphY };

            const onMouseMoveDrag = (moveE) => {
                const movCanvasX = moveE.clientX - rect.left;
                const movCanvasY = moveE.clientY - rect.top;
                const movGraphX = (movCanvasX - rect.width / 2 - transform.x) / transform.scale;
                const movGraphY = (movCanvasY - rect.height / 2 - transform.y) / transform.scale;
                
                if (clickedNode) {
                    clickedNode.x = movGraphX + dragOffsetRef.current.x;
                    clickedNode.y = movGraphY + dragOffsetRef.current.y;
                }
            };

            const onMouseUpDrag = () => {
                setDraggedNode(null);
                window.removeEventListener('mousemove', onMouseMoveDrag);
                window.removeEventListener('mouseup', onMouseUpDrag);
            };

            window.addEventListener('mousemove', onMouseMoveDrag);
            window.addEventListener('mouseup', onMouseUpDrag);
        } else {
            // Pan mode
            const startX = e.clientX;
            const startY = e.clientY;
            const startTransform = { ...transformRef.current };

            const onMouseMovePan = (moveE) => {
                transformRef.current = {
                    ...transformRef.current,
                    x: startTransform.x + (moveE.clientX - startX),
                    y: startTransform.y + (moveE.clientY - startY)
                };
            };

            const onMouseUp = () => {
                window.removeEventListener('mousemove', onMouseMovePan);
                window.removeEventListener('mouseup', onMouseUp);
            };

            window.addEventListener('mousemove', onMouseMovePan);
            window.addEventListener('mouseup', onMouseUp);
        }
    };

    const onWheel = (e) => {
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        transformRef.current.scale = Math.min(Math.max(transformRef.current.scale * delta, 0.1), 5);
    };

    return (
        <div style={{ width: '100%', height: '100%', background: '#030a0e', position: 'relative', overflow: 'hidden' }}>
            <canvas 
                ref={canvasRef} 
                onMouseDown={onMouseDown}
                onWheel={onWheel}
                onMouseMove={onMouseMove}
                style={{ width: '100%', height: '100%', display: 'block', cursor: 'crosshair' }}
            />
            
            {/* ── Overlay Metadata ── */}
            <div style={{ position: 'absolute', top: '20px', left: '20px', pointerEvents: 'none' }}>
                <div style={{ color: '#00f5d4', fontFamily: 'Rajdhani', fontWeight: 700, fontSize: '18px', letterSpacing: '4px' }}>ONTOLOGY_MESH</div>
            </div>

            {/* Legend - COLLAPSIBLE */}
            <div style={{ position: 'absolute', bottom: '20px', left: '20px', background: 'rgba(3,10,14,0.95)', border: '1px solid rgba(0,245,212,0.2)', backdropFilter: 'blur(10px)' }}>
                <button 
                    onClick={() => setLegendOpen(!legendOpen)}
                    style={{
                        width: '100%', 
                        background: 'transparent',
                        border: 'none',
                        color: '#00f5d4',
                        fontFamily: 'Share Tech Mono',
                        fontSize: '11px',
                        fontWeight: 'bold',
                        textAlign: 'left',
                        padding: '10px 15px',
                        cursor: 'pointer',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        borderBottom: legendOpen ? '1px solid rgba(0,245,212,0.1)' : 'none'
                    }}
                >
                    <span>◆ NODE_TYPES</span>
                    <span>{legendOpen ? '▼' : '►'}</span>
                </button>
                {legendOpen && (
                    <div style={{ padding: '15px' }}>
                        {Object.keys(NODE_TYPE_DISPLAY).map(key => (
                            <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: NODE_TYPE_DISPLAY[key].color }} />
                                <span style={{ color: '#aaa', fontSize: '10px', fontFamily: 'Share Tech Mono' }}>{NODE_TYPE_DISPLAY[key].label.toUpperCase()}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Node Count - Bottom Left */}
            <div style={{ position: 'absolute', bottom: '20px', left: '300px', pointerEvents: 'none' }}>
                <div style={{ color: 'rgba(0,245,212,0.3)', fontFamily: 'Share Tech Mono', fontSize: '9px' }}>NODE_COUNT: {data.nodes.length}</div>
            </div>

            {/* Thread Count - Bottom Left */}
            <div style={{ position: 'absolute', bottom: '20px', left: '420px', pointerEvents: 'none' }}>
                <div style={{ color: 'rgba(0,245,212,0.3)', fontFamily: 'Share Tech Mono', fontSize: '9px' }}>THREAD_COUNT: {data.links.length}</div>
            </div>

            {/* Node Tooltip */}
            {hoveredNode && tooltipPos && (
                <div style={{
                    position: 'absolute',
                    left: tooltipPos.x + 10,
                    top: tooltipPos.y + 10,
                    background: 'rgba(3,10,14,0.95)',
                    border: `1px solid ${NODE_COLORS[hoveredNode.group?.toLowerCase()] || '#00f5d4'}`,
                    borderRadius: '4px',
                    padding: '8px 12px',
                    pointerEvents: 'none',
                    zIndex: 1000,
                    backdropFilter: 'blur(10px)',
                    fontSize: '11px',
                    fontFamily: 'Share Tech Mono',
                    color: '#fff',
                    maxWidth: '200px',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                }}>
                    <div style={{ color: NODE_COLORS[hoveredNode.group?.toLowerCase()] || '#00f5d4', fontWeight: 'bold' }}>
                        {hoveredNode.name?.toUpperCase()}
                    </div>
                    <div style={{ fontSize: '9px', opacity: 0.7 }}>
                        TYPE: {hoveredNode.group?.toUpperCase() || 'UNKNOWN'}
                    </div>
                    {hoveredNode.cluster && (
                        <div style={{ fontSize: '9px', opacity: 0.7 }}>
                            CLUSTER: {hoveredNode.cluster.toUpperCase()}
                        </div>
                    )}
                </div>
            )}

            {/* Link Tooltip */}
            {hoveredLink && tooltipPos && (() => {
                const sourceNode = nodesRef.current.find(n => n.id === hoveredLink.source);
                const targetNode = nodesRef.current.find(n => n.id === hoveredLink.target);
                const sourceName = sourceNode?.name?.toUpperCase() || '?';
                const targetName = targetNode?.name?.toUpperCase() || '?';
                const relType = hoveredLink.type?.toUpperCase() || 'LINKED';
                return (
                <div style={{
                    position: 'absolute',
                    left: tooltipPos.x + 10,
                    top: tooltipPos.y + 10,
                    background: 'rgba(3,10,14,0.98)',
                    border: '1.5px solid rgba(0,245,212,0.8)',
                    borderRadius: '6px',
                    padding: '12px 16px',
                    pointerEvents: 'none',
                    zIndex: 1000,
                    backdropFilter: 'blur(10px)',
                    fontFamily: 'Share Tech Mono',
                    color: '#00f5d4',
                    maxWidth: '280px'
                }}>
                    <div style={{ fontWeight: 'bold', marginBottom: '6px', fontSize: '12px', color: '#f5a623' }}>
                        {sourceName} → {relType} → {targetName}
                    </div>
                    {hoveredLink.description && (
                        <div style={{ fontSize: '11px', opacity: 0.85, color: 'rgba(200,216,212,0.9)', lineHeight: '1.4' }}>
                            {hoveredLink.description}
                        </div>
                    )}
                </div>
                );
            })()}

            {loading && (
                <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: '#00f5d4', fontFamily: 'Share Tech Mono', letterSpacing: '4px' }}>
                    SYNCING_NEURAL_MESH...
                </div>
            )}
            
            {error && (
                <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: '#ff4b4b', fontFamily: 'Share Tech Mono', textAlign: 'center' }}>
                    [ CRITICAL_ERROR ]<br/>{error}
                </div>
            )}
        </div>
    );
};

export default KnowledgeGraph;
