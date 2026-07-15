export async function enrichEntry(entry, pageContent, existingEntries, settings) {
  const { aiProvider, claudeKey, openaiKey } = settings;
  if (aiProvider === 'none') return null;
  if (aiProvider === 'claude' && !claudeKey) return null;
  if (aiProvider === 'openai' && !openaiKey) return null;

  const existingTags = [...new Set(existingEntries.flatMap(e => e.tags || []))].slice(0, 60);
  const recentEntries = existingEntries.slice(-30).map(e => ({
    id: e.id,
    title: e.title,
    subtype: e.subtype,
    tags: e.tags,
  }));

  const prompt = `Você é um assistente curadoria para um blog pessoal de conhecimento chamado ContentBlog (pt-BR).

Dados da página capturada:
Título: ${entry.title}
URL: ${entry.url}
Autor: ${entry.author || 'desconhecido'}
Descrição: ${entry.description || ''}
Conteúdo (trecho): ${pageContent.slice(0, 1500)}

Tags existentes no blog: ${existingTags.join(', ') || 'nenhuma ainda'}
Últimas entradas: ${JSON.stringify(recentEntries)}

Responda APENAS com JSON válido, sem markdown:
{
  "subtype": "artigo|notícia|livro|curso|treinamento|vídeo",
  "tags": ["tag1", "tag2"],
  "notes_draft": "rascunho em pt-BR, tom objetivo e neutro (sem primeira pessoa), máx 200 chars, o que é relevante neste conteúdo e por que importa",
  "connections": ["id_entrada_relacionada"],
  "connection_reasons": {"id": "por que se relaciona"}
}

Regras:
- subtype: detecte a partir da URL, conteúdo e contexto
- tags: prefira tags existentes; sugira novas se necessário (máx 4, pt-BR, minúsculas)
- notes_draft: seja direto e pessoal, como uma nota rápida de leitura
- connections: máx 2 IDs de entradas existentes que se relacionam diretamente`;

  try {
    if (aiProvider === 'claude') return await callClaude(prompt, claudeKey);
    if (aiProvider === 'openai') return await callOpenAI(prompt, openaiKey);
  } catch (e) {
    throw new Error(`AI (${aiProvider}): ${e.message}`);
  }
  return null;
}

async function callClaude(prompt, apiKey) {
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 512,
      messages: [{ role: 'user', content: prompt }],
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || `HTTP ${res.status}`);
  }
  const data = await res.json();
  return JSON.parse(data.content[0].text);
}

async function callOpenAI(prompt, apiKey) {
  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      response_format: { type: 'json_object' },
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 512,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || `HTTP ${res.status}`);
  }
  const data = await res.json();
  return JSON.parse(data.choices[0].message.content);
}
