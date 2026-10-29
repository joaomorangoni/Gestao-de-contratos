const TOKEN_KEY = 'accordo-session';
export const session = {
  get: () => sessionStorage.getItem(TOKEN_KEY),
  set: (token: string) => sessionStorage.setItem(TOKEN_KEY, token),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
};
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (session.get()) headers.set('Authorization', `Bearer ${session.get()}`);
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const response = await fetch(`/api${path}`, {...options, headers});
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 401 && path !== '/auth/login') {
      session.clear();
      window.dispatchEvent(new Event('session-expired'));
    }
    throw new Error(data.erro || 'Não foi possível concluir a operação.');
  }
  return data as T;
}
export async function download(path: string, name: string) {
  const response = await fetch(`/api${path}`, {headers: {Authorization: `Bearer ${session.get()}`}});
  if (!response.ok) throw new Error('Não foi possível baixar o documento.');
  const url = URL.createObjectURL(await response.blob());
  const a = document.createElement('a'); a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export const message = (error: unknown) => error instanceof Error ? error.message : 'Ocorreu um erro.';
