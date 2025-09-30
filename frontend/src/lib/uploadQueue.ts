/* IndexedDB-backed upload queue for offline-first ingestion */

type UploadStatus = 'queued' | 'uploading' | 'paused' | 'failed' | 'completed' | 'cancelled';

export type UploadJob = {
  id: string;
  name: string;
  status: UploadStatus;
  retries: number;
  maxRetries: number;
  error?: string | null;
  createdAt: number;
  updatedAt: number;
  size: number;
  type: string;
  metadata: { chunk_size: number; document_type: string; domain?: string | null; version?: string | null };
};

export type UploadJobWithBlob = UploadJob & { file: Blob };

class UploadQueueService extends EventTarget {
  private dbPromise: Promise<IDBDatabase> | null = null;
  private processing = false;
  private paused = false;
  private concurrency = 1;

  private getDB(): Promise<IDBDatabase> {
    if (this.dbPromise) return this.dbPromise;
    this.dbPromise = new Promise((resolve, reject) => {
      const req = indexedDB.open('xor-rag-upload', 1);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains('jobs')) {
          const store = db.createObjectStore('jobs', { keyPath: 'id' });
          store.createIndex('status', 'status', { unique: false });
          store.createIndex('updatedAt', 'updatedAt', { unique: false });
        }
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
    return this.dbPromise;
  }

  private async tx(storeMode: IDBTransactionMode = 'readonly') {
    const db = await this.getDB();
    const tx = db.transaction('jobs', storeMode);
    const store = tx.objectStore('jobs');
    return { tx, store };
  }

  async list(): Promise<UploadJob[]> {
    const { tx, store } = await this.tx('readonly');
    const req = store.getAll();
    const data = await new Promise<any[]>((resolve, reject) => {
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
    await new Promise(res => (tx.oncomplete = () => res(null)));
    return data.map(({ file, ...rest }) => rest as UploadJob);
  }

  async addFiles(files: File[], metadata: { chunk_size: number; document_type: string; domain?: string | null; version?: string | null }, maxRetries = 3) {
    const now = Date.now();
    const jobs: UploadJobWithBlob[] = files.map(f => ({
      id: crypto.randomUUID(),
      name: f.name,
      status: 'queued',
      retries: 0,
      maxRetries,
      error: null,
      createdAt: now,
      updatedAt: now,
      size: f.size,
      type: f.type,
      metadata,
      file: f,
    }));
    const { tx, store } = await this.tx('readwrite');
    await Promise.all(jobs.map(j => new Promise<void>((resolve, reject) => {
      const req = store.put(j);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    })));
    await new Promise(res => (tx.oncomplete = () => res(null)));
    this.emit();
    this.kick();
  }

  async update(partial: Partial<UploadJob> & { id: string }) {
    const { tx, store } = await this.tx('readwrite');
    const existing: any = await new Promise((resolve, reject) => {
      const req = store.get(partial.id);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
    if (!existing) return;
    const updated = { ...existing, ...partial, updatedAt: Date.now() };
    await new Promise<void>((resolve, reject) => {
      const req = store.put(updated);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
    await new Promise(res => (tx.oncomplete = () => res(null)));
    this.emit();
  }

  async remove(id: string) {
    const { tx, store } = await this.tx('readwrite');
    await new Promise<void>((resolve, reject) => {
      const req = store.delete(id);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
    await new Promise(res => (tx.oncomplete = () => res(null)));
    this.emit();
  }

  pauseAll() { this.paused = true; this.emit(); }
  resumeAll() { this.paused = false; this.kick(); this.emit(); }

  async pause(id: string) { await this.update({ id, status: 'paused' }); }
  async resume(id: string) { await this.update({ id, status: 'queued', error: null }); this.kick(); }
  async cancel(id: string) { await this.update({ id, status: 'cancelled' }); }
  async retry(id: string) { await this.update({ id, status: 'queued', error: null }); this.kick(); }

  private async nextJob(): Promise<UploadJobWithBlob | null> {
    const { tx, store } = await this.tx('readwrite');
    const all: any[] = await new Promise((resolve, reject) => {
      const req = store.getAll();
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
    const candidate = all
      .filter(j => (j.status === 'queued' || (j.status === 'failed' && j.retries < j.maxRetries)))
      .sort((a, b) => a.updatedAt - b.updatedAt)[0];
    await new Promise(res => (tx.oncomplete = () => res(null)));
    return candidate || null;
  }

  private async upload(job: UploadJobWithBlob) {
    await this.update({ id: job.id, status: 'uploading' });
    try {
      const form = new FormData();
      form.append('file', job.file, job.name);
      form.append('chunk_size', String(job.metadata.chunk_size));
      form.append('document_type', job.metadata.document_type);
      if (job.metadata.domain) form.append('domain', job.metadata.domain);
      if (job.metadata.version) form.append('version', job.metadata.version);

      const resp = await fetch('/api/upload', { method: 'POST', body: form });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(data?.error || resp.statusText || 'Upload failed');
      await this.update({ id: job.id, status: 'completed', error: null });
    } catch (e: any) {
      const errMsg = e?.message || String(e);
      const nextRetries = (job.retries ?? 0) + 1;
      // Exponential backoff with jitter (base 1000ms, cap 30s)
      const base = 1000;
      const max = 30000;
      const delay = Math.min(max, base * Math.pow(2, nextRetries));
      const jitter = Math.floor(Math.random() * (delay * 0.3));
      await this.update({ id: job.id, status: 'failed', error: errMsg, retries: nextRetries });
      await this.sleep(delay + jitter);
    }
  }

  private async processLoop() {
    if (this.processing) return;
    this.processing = true;
    try {
      while (!this.paused) {
        if (!navigator.onLine) { await this.sleep(2000); continue; }
        const slots = Math.max(1, this.concurrency);
        const tasks: Promise<any>[] = [];
        for (let i = 0; i < slots; i++) {
          const job = await this.nextJob();
          if (!job) break;
          const fresh = job as UploadJobWithBlob;
          if (fresh.status === 'paused' || fresh.status === 'cancelled') continue;
          tasks.push(this.upload(fresh));
        }
        if (tasks.length === 0) break;
        await Promise.allSettled(tasks);
        this.emit();
        await this.sleep(200);
      }
    } finally {
      this.processing = false;
    }
  }

  private sleep(ms: number) { return new Promise(res => setTimeout(res, ms)); }
  private kick() { this.processLoop(); }
  private emit() { this.dispatchEvent(new Event('change')); }

  subscribe(callback: () => void) {
    const handler = () => callback();
    this.addEventListener('change', handler);
    return () => this.removeEventListener('change', handler);
  }

  setConcurrency(n: number) {
    this.concurrency = Math.max(1, Math.min(4, Math.floor(n)));
    this.emit();
    this.kick();
  }

  getConcurrency() { return this.concurrency; }
}

export const UploadQueue = new UploadQueueService();

// Auto kick on connectivity
window.addEventListener('online', () => UploadQueue['kick'] && (UploadQueue as any).kick());


