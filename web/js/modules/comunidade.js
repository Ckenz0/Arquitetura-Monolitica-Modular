import {$, esc, data, vazio} from '../ui.js';

// Rascunhos pertencem à página e sobrevivem à renovação da sessão.
const rascunhosOpinioes = new Map();

export function limparRascunho(id) { rascunhosOpinioes.delete(id); }

export function renderizarComunidade(estado) {
  $('#eventos').innerHTML = estado.eventos.length ? estado.eventos.map(e => `<article class="list-item"><span class="label">${esc(data(e.quando))}</span><h3>${esc(e.titulo)}</h3><p class="subtle">${esc(e.local)}${e.vagas !== null ? ` · ${e.vagas} vagas disponíveis` : ''}</p><button class="btn ${e.inscrito ? 'secondary' : ''}" data-action="inscrever" data-id="${esc(e.id)}" ${e.inscrito || e.vagas === 0 || new Date(e.quando) <= new Date() ? 'disabled' : ''}>${e.inscrito ? 'Inscrição confirmada ✓' : (e.vagas === 0 ? 'Sem vagas' : 'Quero participar')}</button></article>`).join('') : vazio('A loja ainda não divulgou novos eventos.');
  document.querySelectorAll('.opiniao-form').forEach(form => {
    rascunhosOpinioes.set(form.dataset.id, form.elements.texto.value);
  });
  $('#clubes').innerHTML = estado.clubes.length ? estado.clubes.map(c => `<article class="list-item"><h3>${esc(c.nome)}</h3><p class="subtle">${c.membros} ${c.membros === 1 ? 'participante' : 'participantes'} · Um espaço para trocar leituras.</p>${c.participando ? '<span class="status">Você participa deste clube</span>' : `<button class="btn secondary" data-action="clube" data-id="${esc(c.id)}">Participar do clube</button>`}${c.opinioes.map(o => `<div class="opinion"><span class="label">Leitor ${esc(o.cliente.slice(0,8))}</span><p>${esc(o.texto)}</p></div>`).join('')}${c.participando ? `<form class="opiniao-form" data-id="${esc(c.id)}" style="margin-top:18px"><div class="field"><label for="opiniao-${esc(c.id)}">Compartilhe sua opinião</label><textarea id="opiniao-${esc(c.id)}" name="texto" required placeholder="O que essa leitura deixou com você?">${esc(rascunhosOpinioes.get(c.id) || '')}</textarea></div><button class="btn" type="submit">Publicar opinião</button></form>` : ''}</article>`).join('') : vazio('Os clubes de leitura aparecerão aqui.');
}
