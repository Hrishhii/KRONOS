import React from 'react';
import { AlertTriangle } from 'lucide-react';

class StandardErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    console.error("Neural Mesh Render Error:", error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#030a0e', color: '#ff4b4b', textAlign: 'center', padding: '40px' }}>
          <AlertTriangle size={48} style={{ marginBottom: '20px' }} />
          <div style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '16px' }}>NEURAL MESH FAILURE</div>
          <div style={{ fontFamily: 'Share Tech Mono', fontSize: '14px', maxWidth: '500px', lineHeight: '1.6' }}>
            CRITICAL RENDER EXCEPTION DETECTED:
            <br/><br/>
            <span style={{ color: '#aaa' }}>{this.state.error?.message || "Unknown error"}</span>
          </div>
          <button 
            onClick={() => window.location.reload()}
            style={{ marginTop: '20px', background: 'none', border: '1px solid #ff4b4b', color: '#ff4b4b', padding: '8px 16px', cursor: 'pointer' }}
          >
            RELOAD SYSTEM
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default StandardErrorBoundary;
