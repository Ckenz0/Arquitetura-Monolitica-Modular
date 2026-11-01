import {$, esc, dinheiro, vazio} from '../ui.js';

function capa(livro) {
  const indices = {'1984':0, bichos:1, hobbit:2, reino:3, esgotado:4};
  return `<div class="cover palette-${indices[livro.id] ?? 1}">${livro.lancamento ? '<span class="new-label">NOVIDADE</span>' : ''}<span class="author">${esc(livro.autor)}</span><span class="title">${esc(livro.titulo)}</span><span class="edition">Entrelinhas · ${esc(livro.genero)}</span></div>`;
}

export function renderizarCatalogo(estado) {
  if (!estado) return;
  const q = $('#busca').value.trim().toLocaleLowerCase('pt-BR');
  const genero = $('#genero').value;
  const livros = estado.livros.filter(l => (!q || l.titulo.toLocaleLowerCase('pt-BR').includes(q) || l.autor.toLocaleLowerCase('pt-BR').includes(q)) && (!genero || l.genero === genero) && (!$('#lancamentos').checked || l.lancamento));
  $('#catalog-count').textContent = `${livros.length} ${livros.length === 1 ? 'livro encontrado' : 'livros encontrados'}`;
  $('#catalogo-livros').setAttribute('aria-busy', 'false');
  const desejos = new Set(estado.desejos.map(l => l.id));
  $('#catalogo-livros').innerHTML = livros.length ? livros.map(l => `
    <article class="book-card">
      <button class="cover-button" data-action="detalhes" data-id="${esc(l.id)}" aria-label="Ver detalhes de ${esc(l.titulo)}">${capa(l)}</button>
      <div class="book-info"><span class="genre">${esc(l.genero)}</span><h3>${esc(l.titulo)}</h3><div class="subtle">${esc(l.autor)}</div>
      <div class="book-bottom"><span class="price">${dinheiro(l.preco)}</span><span class="stock ${l.estoque ? '' : 'zero'}">${l.estoque ? `${l.estoque} em estoque` : 'Esgotado'}</span></div>
      <div class="book-actions"><button class="btn secondary" data-action="${l.estoque ? 'reservar' : 'acompanhar'}" data-id="${esc(l.id)}">${l.estoque ? 'Reservar' : 'Avise-me'}</button><button class="wish-button ${desejos.has(l.id) ? 'saved' : ''}" data-action="desejo" data-id="${esc(l.id)}" aria-label="Guardar ${esc(l.titulo)} na lista de desejos" aria-pressed="${desejos.has(l.id)}">${desejos.has(l.id) ? '♥' : '♡'}</button></div></div>
    </article>`).join('') : vazio('Nenhum livro encontrado. Tente outro título, autor ou gênero.');
}

export function htmlAvaliacao(avaliacao) {
  return `<div class="opinion"><span class="label">${esc(avaliacao.cliente)}</span>${Number.isInteger(avaliacao.nota) ? `<strong class="review-rating">Nota ${esc(avaliacao.nota)} de 5</strong>` : ''}<p>${esc(avaliacao.texto)}</p></div>`;
}

export function htmlConfirmacaoAvaliacao() {
  return '<p id="avaliacao-confirmacao" role="status" tabindex="-1">Você já publicou uma avaliação deste livro. Obrigado por compartilhar sua leitura.</p>';
}

export async function abrirLivro(id, api) {
  const l = await api(`/api/livros/${encodeURIComponent(id)}`);
  const avaliacoes = l.avaliacoes?.length
    ? l.avaliacoes.map(htmlAvaliacao).join('')
    : '<p class="subtle review-empty">Este livro ainda não tem avaliações.</p>';
  const formulario = l.ja_avaliou
    ? htmlConfirmacaoAvaliacao()
    : `<form id="avaliacao-form" data-id="${esc(l.id)}">
        <p class="subtle" id="avaliacao-ajuda">Sua avaliação será pública e não poderá ser editada.</p>
        <div class="field"><label for="avaliacao-nota">Sua nota</label><select id="avaliacao-nota" name="nota" required><option value="">Escolha de 1 a 5</option>${[1,2,3,4,5].map(n => `<option value="${n}">${n} de 5</option>`).join('')}</select></div>
        <div class="field"><label for="avaliacao-texto">Seu comentário</label><textarea id="avaliacao-texto" name="texto" rows="4" required aria-describedby="avaliacao-ajuda" placeholder="O que você achou desta leitura?"></textarea></div>
        <p id="avaliacao-erro" class="form-error" role="alert" tabindex="-1" hidden></p>
        <button type="submit" class="btn">Publicar avaliação</button>
      </form>`;
  $('#book-details').innerHTML = `<div class="dialog-heading"><div><div class="eyebrow">${esc(l.genero)}</div><h2 id="book-title">${esc(l.titulo)}</h2></div><button class="close" data-close aria-label="Fechar">×</button></div><p class="subtle">${esc(l.autor)}</p><p>${esc(l.sinopse || 'Sinopse não informada.')}</p><div class="details-grid"><div><span class="label">Preço na loja</span><strong>${dinheiro(l.preco)}</strong></div><div><span class="label">Disponibilidade</span><strong>${l.estoque} exemplares</strong></div><div><span class="label">Seção</span><strong>${esc(l.secao || 'Não informada')}</strong></div><div><span class="label">Prateleira</span><strong>${esc(l.prateleira || 'Não informada')}</strong></div></div><h3>Quem leu, conta</h3><div id="book-reviews">${avaliacoes}</div><div class="details-actions"><button class="btn" data-action="${l.estoque ? 'reservar' : 'acompanhar'}" data-id="${esc(l.id)}">${l.estoque ? 'Reservar para retirada' : 'Avise-me quando chegar'}</button><button class="btn secondary" data-action="desejo" data-id="${esc(l.id)}">♡ Guardar</button></div><section class="review-section" aria-label="Sua avaliação"><h3>Sua avaliação</h3>${formulario}</section>`;
  if (!$('#book-dialog').open) $('#book-dialog').showModal();
}
