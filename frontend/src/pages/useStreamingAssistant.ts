import { useState, useRef, useCallback } from 'react';

export type StreamingStatus = 'idle' | 'streaming' | 'error';

export function useStreamingAssistant() {
  const [streamingContent, setStreamingContent] = useState('');
  const [progress, setProgress] = useState<number | null>(null);
  const [status, setStatus] = useState<StreamingStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  const startStreaming = useCallback(async (question: string, history: any[]) => {
    setStatus('streaming');
    setStreamingContent('');
    setProgress(0);
    setError(null);
    controllerRef.current = new AbortController();
    try {
      const response = await fetch('/query/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          question,
          n_results: '3',
          expand: '2',
          filename: '',
          conversation_history: JSON.stringify(history || [])
        }),
        signal: controllerRef.current.signal
      });
      if (!response.body) throw new Error('No response body');
      const reader = response.body.getReader();
      let decoder = new TextDecoder();
      let done = false;
      let receivedLength = 0;
      let totalLength = 0;
      if (response.headers.has('content-length')) {
        totalLength = parseInt(response.headers.get('content-length') || '0', 10);
      }
      let streamed = '';
      let buffer = '';
      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          receivedLength += value.length;
          if (totalLength > 0) {
            setProgress(Math.round((receivedLength / totalLength) * 100));
          } else {
            setProgress(null);
          }
          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;
          let lines = buffer.split('\n');
          buffer = lines.pop() || '';
          for (const line of lines) {
            if (line.trim()) {
              try {
                const data = JSON.parse(line);
                if (data.answer !== undefined) {
                  streamed += data.answer;
                  setStreamingContent(streamed);
                }
              } catch (err) {
                setError('Stream parse error');
              }
            }
          }
        }
      }
      // Handle any remaining buffered line
      if (buffer.trim()) {
        try {
          const data = JSON.parse(buffer);
          if (data.answer !== undefined) {
            streamed += data.answer;
            setStreamingContent(streamed);
          }
        } catch (err) {
          setError('Stream parse error (final buffer)');
        }
      }
      setProgress(100);
      setTimeout(() => setProgress(null), 500);
      setStatus('idle');
      controllerRef.current = null;
      return streamed;
    } catch (err: any) {
      setError(err.message || 'Streaming error');
      setStatus('error');
      controllerRef.current = null;
      return '';
    }
  }, []);

  const resetStreaming = useCallback(() => {
    setStreamingContent('');
    setProgress(null);
    setStatus('idle');
    setError(null);
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
    }
  }, []);

  return {
    streamingContent,
    progress,
    status,
    error,
    startStreaming,
    resetStreaming,
  };
} 