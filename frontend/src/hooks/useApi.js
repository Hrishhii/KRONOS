import { useState, useCallback } from 'react';

const API_BASE = '/api/v1';

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const aggregate = useCallback(async (query, onProgress) => {
    setLoading(true);
    setError(null);
    
    try {
      // Use streaming endpoint for better UX
      const response = await fetch(`${API_BASE}/aggregate-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Handle streaming response (newline-delimited JSON)
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let completeData = null;

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Process complete lines
        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i].trim();
          if (line) {
            try {
              const event = JSON.parse(line);
              
              // Call progress callback if provided
              if (onProgress) {
                onProgress(event);
              }

              // Keep track of complete data
              if (event.status === 'complete') {
                completeData = event.data;
              }
              
              console.log('Stream event:', event);
            } catch (e) {
              console.warn('Failed to parse stream line:', line, e);
            }
          }
        }
        
        // Keep incomplete line in buffer
        buffer = lines[lines.length - 1];
      }

      // Process any remaining data in buffer
      if (buffer.trim()) {
        try {
          const event = JSON.parse(buffer);
          if (onProgress) {
            onProgress(event);
          }
          if (event.status === 'complete') {
            completeData = event.data;
          }
        } catch (e) {
          console.warn('Failed to parse final buffer:', buffer);
        }
      }

      if (!completeData) {
        throw new Error('No complete data received from server');
      }

      return completeData;
    } catch (err) {
      const errorMessage = err.message || 'Failed to fetch briefing';
      console.error('API Error:', errorMessage);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { aggregate, loading, error };
};
