import { useState, useEffect, useRef, useCallback } from 'react';

const useEnrichmentWebSocket = () => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected'); // 'connecting', 'connected', 'disconnected', 'error'
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelayRef = useRef(1000); // Start with 1 second

  const connect = useCallback((jobId) => {
    if (!jobId) {
      setError('Job ID is required to connect');
      return;
    }

    // Close existing connection if any
    disconnect();

    try {
      setConnectionStatus('connecting');
      setError(null);
      
      // Determine the WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = process.env.NODE_ENV === 'development' 
        ? 'localhost:8000' 
        : window.location.host;
      const wsUrl = `${protocol}//${host}/api/data-enrichment/ws/job/${jobId}`;
      
      console.log('Connecting to WebSocket:', wsUrl);
      
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected for job:', jobId);
        setConnectionStatus('connected');
        setError(null);
        reconnectAttemptsRef.current = 0;
        reconnectDelayRef.current = 1000; // Reset delay
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data);
          
          switch (data.type) {
            case 'update':
              setProgress(data.progress || 0);
              setStatus(data.status);
              setError(null);
              break;
              
            case 'final':
              setProgress(data.status === 'completed' ? 100 : progress);
              setStatus(data.status);
              if (data.error_message) {
                setError(data.error_message);
              }
              // Connection will be closed by server after final message
              break;
              
            case 'error':
              setError(data.message || 'WebSocket error occurred');
              setStatus('failed');
              break;
              
            default:
              console.warn('Unknown WebSocket message type:', data.type);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
          setError('Failed to parse server message');
        }
      };

      wsRef.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setConnectionStatus('error');
        setError('WebSocket connection error');
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setConnectionStatus('disconnected');
        
        // Only attempt reconnection if it wasn't a clean close and we haven't exceeded max attempts
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          console.log(`Attempting reconnection in ${reconnectDelayRef.current}ms (attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current += 1;
            reconnectDelayRef.current = Math.min(reconnectDelayRef.current * 2, 30000); // Exponential backoff, max 30s
            connect(jobId);
          }, reconnectDelayRef.current);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setError('Failed to maintain connection after multiple attempts');
        }
      };

    } catch (err) {
      console.error('Error creating WebSocket connection:', err);
      setConnectionStatus('error');
      setError('Failed to create WebSocket connection');
    }
  }, []);

  const disconnect = useCallback(() => {
    // Clear any pending reconnection attempts
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    // Close WebSocket connection
    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close(1000, 'Client disconnecting');
      }
      wsRef.current = null;
    }
    
    setConnectionStatus('disconnected');
    reconnectAttemptsRef.current = 0;
    reconnectDelayRef.current = 1000;
  }, []);

  const sendMessage = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message));
        return true;
      } catch (err) {
        console.error('Error sending WebSocket message:', err);
        setError('Failed to send message');
        return false;
      }
    } else {
      console.warn('WebSocket is not connected, cannot send message');
      return false;
    }
  }, []);

  const reset = useCallback(() => {
    setProgress(0);
    setStatus(null);
    setError(null);
    disconnect();
  }, [disconnect]);

  // Cleanup effect
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // Auto-reconnect logic for connection failures
  useEffect(() => {
    if (connectionStatus === 'error' && reconnectAttemptsRef.current < maxReconnectAttempts) {
      const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
      
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log('Auto-reconnecting after error...');
        reconnectAttemptsRef.current += 1;
        // Note: This would need the jobId, which we'd need to store in a ref
        // For now, we'll rely on manual reconnection
      }, delay);
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connectionStatus]);

  return {
    // State
    progress,
    status,
    error,
    connectionStatus,
    isConnected: connectionStatus === 'connected',
    isConnecting: connectionStatus === 'connecting',
    
    // Actions
    connect,
    disconnect,
    sendMessage,
    reset,
    
    // Metadata
    reconnectAttempts: reconnectAttemptsRef.current,
    maxReconnectAttempts
  };
};

export { useEnrichmentWebSocket };