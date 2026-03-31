import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// ── EONET sub-type config ─────────────────────────────────────────────────────
const EONET_SUBS = {
  wildfire: { label: '🔥 Wildfire',  color: '#ff4500', bg: 'rgba(255,69,0,0.2)' },
  flood:    { label: '🌊 Flood',     color: '#1e90ff', bg: 'rgba(30,144,255,0.2)' },
  storm:    { label: '🌀 Storm',     color: '#9b59b6', bg: 'rgba(155,89,182,0.2)' },
  volcano:  { label: '🌋 Volcano',   color: '#e67e22', bg: 'rgba(230,126,34,0.2)' },
};

function quakeStyle(mag) {
  const radius = Math.max(3, mag * mag * 0.4);
  let color = '#ffd700'; // < 4
  if (mag >= 6) color = '#ff0000'; // Severe
  else if (mag >= 5) color = '#ff3b3b'; // Strong
  else if (mag >= 4) color = '#ff8c00'; // Moderate
  return { color, radius };
}

// ── Toggle button component ───────────────────────────────────────────────────
function Btn({ active, onClick, label, color, bg }) {
  return (
    <button onClick={onClick} style={{
      background: active ? bg : 'transparent',
      color: active ? color : '#555',
      border: `1px solid ${active ? color : '#2a3444'}`,
      padding: '4px 10px', borderRadius: '4px',
      fontSize: '10px', cursor: 'pointer',
      fontWeight: 'bold', transition: 'all 0.18s',
      textAlign: 'left', width: '100%', display: 'flex',
      alignItems: 'center', justifyContent: 'space-between', gap: '6px',
    }}>
      <span>{label}</span>
      <span style={{ opacity: 0.6, fontSize: '9px' }}>{active ? 'ON' : 'OFF'}</span>
    </button>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export const WorldMap = ({ overlays, dashboardData }) => {
  // ALL OFF by default — user opts in
  const [showAir,      setShowAir]      = useState(false);
  const [climateOpen,  setClimateOpen]  = useState(false); // accordion expand
  const [showQuake,    setShowQuake]    = useState(false);
  const [eonetSubs, setEonetSubs] = useState({
    wildfire: false, flood: false, storm: false, volcano: false,
  });

  const mapRef         = useRef(null);
  const mapInstanceRef = useRef(null);
  const layersRef      = useRef({});

  const toggleEonet = (key) =>
    setEonetSubs((p) => ({ ...p, [key]: !p[key] }));

  // Whether any climate layer is active (for rendering)
  const anyClimateActive = showQuake || Object.values(eonetSubs).some(Boolean);

  // ── Draw / redraw layers ──────────────────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current) return;

    if (!mapInstanceRef.current) {
      const canvasRenderer = L.canvas({ padding: 1.5 });
      mapInstanceRef.current = L.map(mapRef.current, {
        center: [20, 0], zoom: 2, minZoom: 2, maxZoom: 19,
        zoomControl: true, attributionControl: false,
        renderer: canvasRenderer, 
        maxBounds: [[-90, -180], [90, 180]],
        maxBoundsViscosity: 1.0,
      });
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        subdomains: 'abcd', maxZoom: 19, minZoom: 2, noWrap: true, bounds: [[-90, -180], [90, 180]],
      }).addTo(mapInstanceRef.current);
      mapInstanceRef.current.getContainer().style.background = '#0a0e17';
    }

    // ── Resizer ──
    const ro = new ResizeObserver(() => {
      mapInstanceRef.current?.invalidateSize();
    });
    ro.observe(mapRef.current);

    // Clear all
    Object.values(layersRef.current).forEach((lg) => {
      if (lg instanceof L.LayerGroup) mapInstanceRef.current.removeLayer(lg);
    });
    layersRef.current = {};

    const popupOpts = {
      closeButton: true,
      className: 'tactical-popup',
      autoPan: true,
      minWidth: 200,
      maxWidth: 280,
      autoPanPaddingTopLeft:     L.point(60, 60),
      autoPanPaddingBottomRight: L.point(60, 60),
    };

    // ── AIR TRAFFIC ──
    if (showAir && overlays?.airTraffic && dashboardData?.map_data?.air_traffic) {
      const layer = L.layerGroup();
      dashboardData.map_data.air_traffic.forEach((f) => {
        if (!f || f.lat == null || f.lng == null) return;
        L.circleMarker([f.lat, f.lng], {
          radius: 3, weight: 1, opacity: 0.8,
          fillColor: '#00d4ff', fillOpacity: 0.6, color: '#00d4ff', fill: true,
        }).bindPopup(
          `<div style="font-family:monospace;font-size:10px;color:#e2e8f0;background:#0a0e17;border:1px solid #00d4ff;padding:8px;border-radius:4px;min-width:160px;line-height:1.7">
            <strong style="color:#00d4ff">[AIR ASSET]</strong><br/>
            Callsign: ${f.callsign || 'UNKNOWN'}<br/>
            Altitude: ${f.altitude} ft<br/>
            Velocity: ${f.speed ? Number(f.speed).toFixed(4) : '0.0000'} kn
          </div>`, popupOpts,
        ).addTo(layer);
      });
      layer.addTo(mapInstanceRef.current);
      layersRef.current.airTraffic = layer;
    }

    // ── EARTHQUAKES ──
    if (showQuake && dashboardData?.map_data?.earthquakes) {
      const layer = L.layerGroup();
      dashboardData.map_data.earthquakes.forEach((q) => {
        if (!q || q.lat == null || q.lng == null) return;
        const { color, radius } = quakeStyle(q.magnitude);
        L.circleMarker([q.lat, q.lng], {
          radius, weight: 1.5, opacity: 0.9,
          fillColor: color, fillOpacity: 0.7, color, fill: true,
        }).bindPopup(
          `<div style="font-family:monospace;font-size:10px;color:#e2e8f0;background:#0a0e17;border:1px solid ${color};padding:8px;border-radius:4px;min-width:200px;line-height:1.7">
            <strong style="color:${color}">[SEISMIC — M${q.magnitude}]</strong><br/>
            ${q.place}<br/>
            <span style="color:#718096;font-size:9px">${q.time ? new Date(q.time).toUTCString() : 'Unknown'}</span>
          </div>`, popupOpts,
        ).addTo(layer);
      });
      layer.addTo(mapInstanceRef.current);
      layersRef.current.earthquakes = layer;
    }

    // ── EONET climate events ──
    const activeEonetTypes = Object.entries(eonetSubs).filter(([, v]) => v).map(([k]) => k);
    if (activeEonetTypes.length > 0 && dashboardData?.map_data?.eonet_events) {
      const layer = L.layerGroup();
      dashboardData.map_data.eonet_events.forEach((ev) => {
        if (!ev || ev.lat == null || ev.lng == null) return;
        if (!eonetSubs[ev.type]) return;
        const cfg = EONET_SUBS[ev.type];
        if (!cfg) return;
        L.circleMarker([ev.lat, ev.lng], {
          radius: 7, weight: 2, opacity: 0.9,
          fillColor: cfg.color, fillOpacity: 0.55, color: cfg.color, fill: true,
        }).bindPopup(
          `<div style="font-family:monospace;font-size:10px;color:#e2e8f0;background:#0a0e17;border:1px solid ${cfg.color};padding:8px;border-radius:4px;min-width:180px;line-height:1.7">
            <strong style="color:${cfg.color}">${cfg.label.toUpperCase()}</strong><br/>
            ${ev.title}
          </div>`, popupOpts,
        ).addTo(layer);
      });
      layer.addTo(mapInstanceRef.current);
      layersRef.current.eonet = layer;
    }

    return () => {
      Object.values(layersRef.current).forEach((lg) => {
        if (lg) mapInstanceRef.current?.removeLayer(lg);
      });
    };
  }, [overlays, dashboardData, showAir, showQuake, eonetSubs]);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={mapRef} className="world-map-container" style={{ width: '100%', height: '100%' }} />

      {/* ── Controls overlay ── */}
      <div style={{
        position: 'absolute', top: '8px', right: '8px', zIndex: 1000,
        background: 'rgba(8,11,18,0.93)', border: '1px solid #1e2a3a',
        borderRadius: '6px', padding: '8px', backdropFilter: 'blur(8px)',
        display: 'flex', flexDirection: 'column', gap: '5px', minWidth: '175px',
      }}>
        {/* AIR TRAFFIC */}
        <Btn active={showAir} onClick={() => setShowAir(!showAir)}
          label="✈ Air Traffic" color="#00d4ff" bg="rgba(0,212,255,0.15)" />

        {/* CLIMATE accordion header — clicking just expands/collapses */}
        <button
          onClick={() => setClimateOpen(!climateOpen)}
          style={{
            background: anyClimateActive ? 'rgba(107,207,127,0.15)' : 'transparent',
            color: anyClimateActive ? '#6bcf7f' : '#555',
            border: `1px solid ${anyClimateActive ? '#6bcf7f' : '#2a3444'}`,
            padding: '4px 10px', borderRadius: '4px',
            fontSize: '10px', cursor: 'pointer',
            fontWeight: 'bold', transition: 'all 0.18s',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          }}
        >
          <span>🌍 Climate / Hazards</span>
          <span style={{ opacity: 0.6, fontSize: '9px' }}>{climateOpen ? '▲' : '▼'}</span>
        </button>

        {/* Sub-panel — vertical list, independent controls */}
        {climateOpen && (
          <div style={{
            display: 'flex', flexDirection: 'column', gap: '4px',
            paddingLeft: '8px', borderLeft: '2px solid #1e2a3a', marginTop: '2px',
          }}>
            <Btn active={showQuake} onClick={() => setShowQuake(!showQuake)}
              label="⚡ Earthquakes" color="#ff3b3b" bg="rgba(255,59,59,0.15)" />
            {Object.entries(EONET_SUBS).map(([key, cfg]) => (
              <Btn key={key}
                active={eonetSubs[key]}
                onClick={() => toggleEonet(key)}
                label={cfg.label} color={cfg.color} bg={cfg.bg}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
