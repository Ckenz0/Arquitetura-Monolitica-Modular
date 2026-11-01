export const $ = selector => document.querySelector(selector);
export const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
export const dinheiro = value => Number(value ?? 0).toLocaleString('pt-BR', {style:'currency', currency:'BRL'});
export const data = value => new Date(value).toLocaleString('pt-BR', {dateStyle:'short', timeStyle:'short'});
export const localInput = value => { const d = new Date(value); return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0,16); };
export const vazio = texto => `<div class="empty">${esc(texto)}</div>`;
