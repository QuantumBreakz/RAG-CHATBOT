export async function listConversations() {
  const res = await fetch('/api/conversation');
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function createConversation(title?: string) {
  const res = await fetch('/api/conversation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function getConversation(id: string) {
  const res = await fetch(`/api/conversation/${id}`);
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function renameConversation(id: string, title: string) {
  const res = await fetch(`/api/conversation/${id}/rename`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function deleteConversation(id: string) {
  const res = await fetch(`/api/conversation/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
} 