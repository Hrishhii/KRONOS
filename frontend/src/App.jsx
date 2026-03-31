import React, { useEffect, useState } from 'react';
import { Dashboard } from './components/Dashboard';

// ── GLOBAL ERROR BOUNDARY ──────────────────────────────────────────
class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, stack: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    this.setState({ stack: errorInfo.componentStack });
    console.error("ROOT_OS_FAILURE:", error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          height: '100vh', width: '100vw', background: '#050000', color: '#ff4b4b',
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          fontFamily: 'Share Tech Mono', padding: '40px', textAlign: 'center', border: '20px solid #200000'
        }}>
          <h1 style={{ fontSize: '48px', margin: '0 0 20px 0', letterSpacing: '10px' }}>SYSTEM HALTED</h1>
          <div style={{ border: '1px solid #ff4b4b', padding: '20px', background: 'rgba(255,0,0,0.05)', maxWidth: '800px' }}>
            <p style={{ fontSize: '18px', color: '#fff' }}>KERNEL_PANIC: {this.state.error?.message || "UNKNOWN_EXCEPTION"}</p>
            <pre style={{ 
              textAlign: 'left', fontSize: '10px', opacity: 0.6, overflow: 'auto', 
              maxHeight: '300px', background: '#000', padding: '10px', marginTop: '20px' 
            }}>
              {this.state.stack}
            </pre>
          </div>
          <button 
            onClick={() => window.location.reload()}
            style={{
              marginTop: '30px', background: '#ff4b4b', color: '#000', border: 'none',
              padding: '10px 40px', fontSize: '14px', fontWeight: 'bold', cursor: 'pointer',
              letterSpacing: '2px'
            }}
          >
            REBOOT SYSTEM
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  const [briefingData, setBriefingData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [processingMessage, setProcessingMessage] = useState("");

  const handleQuery = async (query) => {
    setLoading(true);
    setBriefingData(null);
    setProcessingMessage("INITIATING SECURE UPLINK...");
    
    try {
      const response = await fetch('/api/v1/aggregate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`[QUERY_FAILURE] Status: ${response.status} | Body: ${errorText}`);
        throw new Error(`SYSTEM_ERROR: ${response.status} - ${errorText}`);
      }
      
      const data = await response.json();
      setBriefingData(data);
    } catch (err) {
      console.error("OS_AGGREGATION_CRASH:", err);
      setProcessingMessage(`ERROR: ${err.message}`);
    } finally {
      setLoading(false);
      setProcessingMessage("");
    }
  };

  return (
    <AppErrorBoundary>
      <div className="App">
        <Dashboard 
          onQueryClick={handleQuery} 
          briefingData={briefingData} 
          loading={loading}
          processingMessage={processingMessage}
        />
      </div>
    </AppErrorBoundary>
  );
}

export default App;
