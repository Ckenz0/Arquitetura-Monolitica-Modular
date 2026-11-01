import {$, esc, data, vazio} from '../ui.js';

export function renderizarPerfil(estado, generos, preferenciasDirty) {
  const f = estado.fidelidade;
  $('#fidelidade').innerHTML = `<div class="loyalty-card"><div class="brand">entrelinhas</div><span class="label" style="color:#ced7c3">Seu saldo de fidelidade</span><strong>${f.saldo} <span style="font:14px system-ui">pontos</span></strong><div class="number">${esc(f.cartao.numero)}</div></div>`;
  $('#cupons').innerHTML = f.cupons.length ? f.cupons.map(c => `<div class="coupon"><strong>${esc(c.codigo)}</strong><div class="subtle">${esc(c.termos)}</div></div>`).join('') : vazio('Seus cupons da loja aparecerão aqui.');
  $('#historico').innerHTML = estado.historico.length ? estado.historico.map(c => `<article class="list-item"><h3>${esc(c.livro.titulo)}</h3><p class="subtle">Compra na loja física · ${esc(data(c.data))}</p><span class="status">${c.pontos} pontos recebidos</span>${c.expira_em ? `<p class="subtle">Validade dos pontos: ${esc(data(c.expira_em))}</p>` : ''}</article>`).join('') : vazio('Você ainda não tem compras físicas registradas.');
  $('#desejos').innerHTML = estado.desejos.length ? estado.desejos.map(l => `<article class="list-item row"><div><h3>${esc(l.titulo)}</h3><span class="subtle">${esc(l.autor)}</span></div><button class="btn secondary" data-action="detalhes" data-id="${esc(l.id)}">Ver livro</button></article>`).join('') : vazio('Toque no coração de um livro para guardá-lo aqui.');
  if (!preferenciasDirty) {
    const temas = {estoque:'Reposição de livros', reservas:'Minhas reservas', fidelidade:'Pontos e cupons', eventos:'Eventos e encontros'};
    $('#preferencias-opcoes').innerHTML = `<fieldset><legend>Gêneros favoritos</legend><div class="form-options">${generos.map(g => `<label class="check"><input type="checkbox" name="generos" value="${esc(g)}" ${estado.cliente.generos.some(s => s.toLocaleLowerCase('pt-BR') === g.toLocaleLowerCase('pt-BR')) ? 'checked' : ''}>${esc(g)}</label>`).join('')}</div></fieldset><fieldset><legend>Quero receber avisos sobre</legend><div class="form-options">${Object.entries(temas).map(([valor, nome]) => `<label class="check"><input type="checkbox" name="temas" value="${valor}" ${estado.cliente.temas_notificacao === null || estado.cliente.temas_notificacao.includes(valor) ? 'checked' : ''}>${nome}</label>`).join('')}</div></fieldset>`;
  }
}
