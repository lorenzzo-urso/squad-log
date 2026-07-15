export function createEntry(overrides = {}) {
  const today = new Date().toISOString().split('T')[0];
  return {
    id: crypto.randomUUID(),
    type: 'conteudo',
    subtype: 'artigo',
    title: '',
    url: '',
    author: '',
    source: '',
    image: '',
    tags: [],
    status: 'consumido',
    rating: null,
    notes: '',
    pitch: '',
    description: '',
    links: [],
    dates: {
      captured: today,
      consumed: today,
      start: null,
      end: null,
      idea: null,
      started: null,
      launched: null,
    },
    changelog: [],
    createdAt: new Date().toISOString(),
    ...overrides,
  };
}

export const SUBTYPES = {
  conteudo: ['artigo', 'notícia', 'livro', 'curso', 'treinamento', 'vídeo'],
  projeto: ['projeto'],
};

export const STATUS = {
  conteudo: ['consumido', 'em andamento', 'quero ler', 'abandonado'],
  projeto: ['ideia', 'iniciado', 'em andamento', 'pausado', 'lançado', 'arquivado'],
};
