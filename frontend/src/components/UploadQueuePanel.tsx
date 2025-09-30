import React, { useEffect, useState } from 'react';
import { UploadQueue, type UploadJob } from '../lib/uploadQueue';

const statusColor: Record<string, string> = {
  queued: 'text-gray-600',
  uploading: 'text-blue-600',
  paused: 'text-yellow-600',
  failed: 'text-red-600',
  completed: 'text-green-600',
  cancelled: 'text-gray-400'
};

export const UploadQueuePanel: React.FC = () => {
  const [jobs, setJobs] = useState<UploadJob[]>([]);
  const [paused, setPaused] = useState(false);
  const [online, setOnline] = useState<boolean>(navigator.onLine);
  const [domain, setDomain] = useState<string>(localStorage.getItem('xor-rag-domain') || '');
  const [version, setVersion] = useState<string>(localStorage.getItem('xor-rag-version') || '');

  const refresh = async () => {
    const list = await UploadQueue.list();
    setJobs(list.sort((a, b) => b.updatedAt - a.updatedAt));
  };

  useEffect(() => {
    refresh();
    const unsub = UploadQueue.subscribe(refresh);
    const handleOnline = () => { setOnline(true); };
    const handleOffline = () => { setOnline(false); };
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => unsub();
  }, []);

  return (
    <div className="p-3 border border-border rounded bg-surface-elevated shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-semibold">Pending Jobs</div>
        <div className="space-x-2">
          <label className="text-xs mr-1">Concurrency</label>
          <input
            type="range"
            min={1}
            max={4}
            defaultValue={UploadQueue.getConcurrency?.() || 1}
            onChange={(e) => UploadQueue.setConcurrency?.(Number(e.target.value))}
          />
          <span className="text-xs align-middle">{UploadQueue.getConcurrency?.() || 1}x</span>
          <button
            className="text-xs px-2 py-1 rounded border"
            onClick={() => { UploadQueue.pauseAll(); setPaused(true); }}
          >Pause All</button>
          <button
            className="text-xs px-2 py-1 rounded border"
            onClick={() => { UploadQueue.resumeAll(); setPaused(false); }}
          >Resume All</button>
        </div>
      </div>
      <div className="flex items-center gap-2 mb-2">
        <input
          className="border rounded px-2 py-1 text-xs flex-1"
          placeholder="Domain (optional)"
          value={domain}
          onChange={(e) => { setDomain(e.target.value); localStorage.setItem('xor-rag-domain', e.target.value); }}
        />
        <input
          className="border rounded px-2 py-1 text-xs flex-1"
          placeholder="Version (optional)"
          value={version}
          onChange={(e) => { setVersion(e.target.value); localStorage.setItem('xor-rag-version', e.target.value); }}
        />
      </div>
      {!online && (
        <div className="text-xs text-yellow-700 bg-yellow-50 border border-yellow-200 rounded p-2 mb-2">Offline: queued uploads will resume when connection is restored.</div>
      )}
      {jobs.length === 0 ? (
        <div className="text-xs text-muted-foreground">No pending jobs.</div>
      ) : (
        <div className="max-h-56 overflow-y-auto space-y-2">
          {jobs.map(j => (
            <div key={j.id} className="flex items-center justify-between text-xs p-2 bg-surface rounded border">
              <div className="min-w-0">
                <div className="truncate">{j.name}</div>
                <div className={`mt-0.5 ${statusColor[j.status] || ''}`}>{j.status}{j.error ? `: ${j.error}` : ''}</div>
              </div>
              <div className="flex items-center space-x-2">
                {(j.status === 'queued' || j.status === 'failed' || j.status === 'paused') && (
                  <button className="px-2 py-1 border rounded" onClick={() => UploadQueue.resume(j.id)}>Resume</button>
                )}
                {j.status === 'uploading' && (
                  <button className="px-2 py-1 border rounded" onClick={() => UploadQueue.pause(j.id)}>Pause</button>
                )}
                {j.status === 'failed' && (
                  <button className="px-2 py-1 border rounded" onClick={() => UploadQueue.retry(j.id)}>Retry</button>
                )}
                {j.status !== 'completed' && (
                  <button className="px-2 py-1 border rounded" onClick={() => UploadQueue.cancel(j.id)}>Cancel</button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default UploadQueuePanel;


