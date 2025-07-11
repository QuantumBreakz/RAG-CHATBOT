export async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch('/api/upload', {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function listFiles() {
  const res = await fetch('/api/upload/files');
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function deleteFile(fileHash: string) {
  const res = await fetch(`/api/upload/files/${fileHash}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
} 