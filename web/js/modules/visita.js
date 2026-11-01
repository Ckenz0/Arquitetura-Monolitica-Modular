import {$, esc, data, localInput, vazio} from '../ui.js';

export function renderizarVisita(estado) {
  $('#reservas').innerHTML = estado.reservas.length ? `<div class="list">${estado.reservas.map(r => `<article class="list-item"><div class="row"><h3>${esc(r.titulo)}</h3><span class="status ${esc(r.status)}">${esc(r.status)}</span></div><p class="subtle">Retirada até ${esc(data(r.prazo))}${r.embrulho ? ' · Presente com embrulho especial' : ''}</p>${r.status !== 'cancelada' ? `<div class="row"><button class="btn link" data-action="prazo" data-id="${esc(r.id)}">Alterar prazo</button><button class="btn secondary" data-action="cancelar" data-id="${esc(r.id)}">Cancelar reserva</button></div>` : ''}</article>`).join('')}</div>` : vazio('Sua próxima leitura ainda não está reservada. Escolha um livro no catálogo.');
  $('#loja-info').innerHTML = `<p><span class="label">Funcionamento</span><br><strong>${esc(estado.loja.horario)}</strong></p><p><span class="label">Lotação atual</span><br><strong>${estado.loja.lotacao} pessoas na loja</strong></p>`;
  $('#fila-posicao').textContent = estado.fila.posicao ? `Sua posição na fila: ${estado.fila.posicao}.` : 'Entre na fila ao chegar à loja.';
  $('#fila-button').disabled = Boolean(estado.fila.posicao);
  const selecionado = $('#agendamento-horario').value;
  $('#agendamento-horario').innerHTML = `<option value="">${estado.horarios.length ? 'Escolha um horário' : 'Nenhum horário disponível'}</option>` + estado.horarios.map(h => `<option value="${esc(h.id)}">${esc(h.livreiro)} · ${esc(data(h.quando))}</option>`).join('');
  if (estado.horarios.some(h => h.id === selecionado)) $('#agendamento-horario').value = selecionado;
  $('#agendamento-form button').disabled = !estado.horarios.length;
  $('#agendamentos').innerHTML = estado.agendamentos.map(a => `<div class="list-item"><strong>${esc(a.livreiro)}</strong><div class="subtle">Agendado para ${esc(data(a.quando))}</div></div>`).join('');
}

export function abrirReserva(id, estado) {
  if (!estado) return;
  const livro = estado.livros.find(l => l.id === id);
  $('#book-dialog').close();
  $('#reserve-form').reset();
  $('#reserve-form').elements.livro_id.value = id;
  $('#reserve-book').textContent = `${livro.titulo} · ${livro.autor}`;
  $('#reserve-deadline').min = localInput(new Date());
  $('#reserve-dialog').showModal();
}
