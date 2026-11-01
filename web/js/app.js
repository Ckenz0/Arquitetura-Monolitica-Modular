import {$, esc, data, localInput, vazio} from './ui.js';
import {renderizarCatalogo as exibirCatalogo, abrirLivro as exibirLivro, htmlAvaliacao, htmlConfirmacaoAvaliacao} from './modules/catalogo.js';
import {renderizarVisita as exibirVisita, abrirReserva as exibirReserva} from './modules/visita.js';
import {renderizarComunidade as exibirComunidade, limparRascunho} from './modules/comunidade.js';
import {renderizarPerfil as exibirPerfil} from './modules/perfil.js';

function renderizarCatalogo() { exibirCatalogo(estado); }
function renderizarVisita() { exibirVisita(estado); }
function renderizarComunidade() { exibirComunidade(estado); }
function renderizarPerfil(generos) { exibirPerfil(estado, generos, preferenciasDirty); }
function abrirLivro(id) { return exibirLivro(id, api); }
function abrirReserva(id) { exibirReserva(id, estado); }

let estado = null, assinatura = '', atualizando = null, atualizarDepois = false, preferenciasDirty = false;
let stream = null, cameraTimer = null, toastTimer = null;
function avisar(mensagem, erro=false) {
  const toast = $('#toast');
  clearTimeout(toastTimer);
  toast.textContent = mensagem;
  toast.classList.toggle('error', erro);
  toast.hidden = false;
  toastTimer = setTimeout(() => { toast.hidden = true; }, 6500);
}

const api = window.livrariaApi;

async function executar(button, tarefa) {
  if (button?.disabled || button?.getAttribute('aria-busy') === 'true') return;
  if (button) button.setAttribute('aria-busy', 'true');
  try { await tarefa(); }
  catch (erro) { avisar(erro.message || 'Não foi possível conectar à livraria.', true); }
  finally { if (button?.isConnected) button.removeAttribute('aria-busy'); }
}

function atualizar() {
  if (atualizando) { atualizarDepois = true; return atualizando; }
  atualizando = (async () => {
    do {
      atualizarDepois = false;
      try {
        const novo = await api('/api/estado');
        const novaAssinatura = JSON.stringify(novo);
        if (novaAssinatura !== assinatura) {
          estado = novo; assinatura = novaAssinatura; renderizar();
        }
        $('#connection-status').hidden = true;
      } catch (erro) {
        $('#connection-status span').textContent = erro.message || 'Não foi possível carregar a livraria.';
        $('#connection-status').hidden = false;
      }
    } while (atualizarDepois);
  })().finally(() => { atualizando = null; });
  return atualizando;
}

function trocarAba(aba) {
  document.querySelectorAll('[data-panel]').forEach(panel => { panel.hidden = panel.dataset.panel !== aba; });
  document.querySelectorAll('nav [data-tab]').forEach(button => {
    if (button.dataset.tab === aba) button.setAttribute('aria-current', 'page');
    else button.removeAttribute('aria-current');
  });
}

function renderizar() {
  $('#hero-hours').textContent = estado.loja.horario;
  $('#hero-occupancy').textContent = `${estado.loja.lotacao} pessoas na loja agora`;
  const generos = [...new Set(estado.livros.map(l => l.genero))].sort();
  const generoAtual = $('#genero').value;
  $('#genero').innerHTML = '<option value="">Todos os gêneros</option>' + generos.map(g => `<option value="${esc(g)}">${esc(g)}</option>`).join('');
  $('#genero').value = generoAtual;
  renderizarCatalogo(); renderizarVisita(); renderizarComunidade(); renderizarPerfil(generos);
  $('#recomendacoes').innerHTML = estado.recomendacoes.length ? `<div class="suggestions">${estado.recomendacoes.map(l => `<button class="suggestion" data-action="detalhes" data-id="${esc(l.id)}"><strong>${esc(l.titulo)}</strong><span class="subtle">${esc(l.autor)} · ${esc(l.genero)}</span></button>`).join('')}</div>` : vazio('Escolha seus gêneros em Meu perfil para descobrir novas leituras.');
  const count = $('#notification-count'); count.textContent = estado.notificacoes.length; count.hidden = !estado.notificacoes.length;
  $('#notificacoes').innerHTML = estado.notificacoes.length ? [...estado.notificacoes].reverse().map(n => `<article class="list-item"><span class="label">${esc(n.tema)} · ${esc(data(n.data))}</span><p style="margin:8px 0 0">${esc(n.mensagem)}</p></article>`).join('') : vazio('Nenhuma notificação por enquanto.');
}

function pararCamera() {
  clearTimeout(cameraTimer); cameraTimer = null;
  if (stream) stream.getTracks().forEach(track => track.stop());
  stream = null; $('#camera').srcObject = null; $('#camera').hidden = true;
}

async function iniciarCamera() {
  const status = $('#camera-status');
  if (!('BarcodeDetector' in window) || !navigator.mediaDevices?.getUserMedia) {
    status.textContent = 'A câmera não pode ler códigos neste navegador. Informe o número abaixo ou use um leitor USB.';
    return;
  }
  pararCamera();
  try {
    const detector = new BarcodeDetector({formats:['ean_13','ean_8','code_128','upc_a']});
    stream = await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}}});
    if (!$('#scan-dialog').open) { pararCamera(); return; }
    const video = $('#camera'); video.srcObject = stream; video.hidden = false;
    await video.play(); status.textContent = 'Aponte para o código de barras do livro.';
    const detectar = async () => {
      if (!stream) return;
      try {
        const codigos = await detector.detect(video);
        if (codigos.length) {
          const l = await api(`/api/codigo/${encodeURIComponent(codigos[0].rawValue)}`);
          $('#scan-dialog').close(); await abrirLivro(l.id); return;
        }
      } catch (erro) { status.textContent = 'Ainda não encontramos o livro. Tente novamente ou informe o código.'; }
      if (stream) cameraTimer = setTimeout(detectar, 450);
    };
    detectar();
  } catch (erro) { pararCamera(); status.textContent = 'Não foi possível acessar a câmera. Você pode informar o código abaixo.'; }
}

document.addEventListener('click', event => {
  const close = event.target.closest('[data-close]');
  if (close) { close.closest('dialog').close(); return; }
  const tab = event.target.closest('[data-tab]');
  if (tab) { trocarAba(tab.dataset.tab); return; }
  const button = event.target.closest('[data-action]');
  if (!button) return;
  const {action, id} = button.dataset;
  executar(button, async () => {
    if (action === 'nova-sessao') {
      await window.novaSessaoLivraria();
      document.querySelector('#session-notice')?.remove();
      await atualizar();
      avisar('Nova sessão iniciada. Seus rascunhos continuam nos formulários.');
      return;
    }
    if (action === 'atualizar') { await atualizar(); return; }
    if (action === 'detalhes') { await abrirLivro(id); return; }
    if (action === 'reservar') { abrirReserva(id); return; }
    if (action === 'notificacoes') { $('#notifications-dialog').showModal(); return; }
    if (action === 'escanear') { $('#camera-status').textContent = ''; $('#scan-dialog').showModal(); return; }
    if (action === 'camera') { await iniciarCamera(); return; }
    if (action === 'prazo') {
      const r = estado.reservas.find(r => r.id === id);
      $('#deadline-form').elements.reserva_id.value = id;
      $('#new-deadline').value = localInput(r.prazo); $('#new-deadline').min = localInput(new Date());
      $('#deadline-dialog').showModal(); return;
    }
    const acoes = {
      desejo: ['/api/desejos', {livro_id:id}, 'Livro guardado na sua lista de desejos.'],
      acompanhar: ['/api/avisos-estoque', {livro_id:id}, 'Você receberá um aviso de reposição conforme suas preferências.'],
      cancelar: [`/api/reservas/${encodeURIComponent(id)}/cancelar`, undefined, 'Reserva cancelada.'],
      fila: ['/api/fila', undefined, 'Você entrou na fila virtual.'],
      inscrever: [`/api/eventos/${encodeURIComponent(id)}/inscricoes`, undefined, 'Sua inscrição está confirmada.'],
      clube: [`/api/clubes/${encodeURIComponent(id)}/participar`, undefined, 'Bem-vindo ao clube de leitura!']
    };
    const tarefa = acoes[action];
    if (tarefa) { await api(tarefa[0], 'POST', tarefa[1]); await atualizar(); avisar(tarefa[2]); }
  });
});

document.addEventListener('submit', event => {
  const form = event.target;
  event.preventDefault();
  if (form.id === 'filtros') { renderizarCatalogo(); return; }
  executar(form.querySelector('button[type="submit"]'), async () => {
    const values = new FormData(form);
    if (form.id === 'avaliacao-form') {
      const erroPublicacao = $('#avaliacao-erro');
      erroPublicacao.hidden = true;
      let publicada;
      try {
        publicada = await api(`/api/livros/${encodeURIComponent(form.dataset.id)}/avaliacoes`, 'POST', {
          nota:Number(values.get('nota')), texto:values.get('texto')
        });
      } catch (erro) {
        erroPublicacao.textContent = erro.message || 'Não foi possível publicar. Tente novamente.';
        erroPublicacao.hidden = false;
        erroPublicacao.focus();
        return;
      }
      const listaAvaliacoes = $('#book-reviews');
      listaAvaliacoes.querySelector('.review-empty')?.remove();
      listaAvaliacoes.insertAdjacentHTML('beforeend', htmlAvaliacao(publicada));
      form.outerHTML = htmlConfirmacaoAvaliacao();
      $('#avaliacao-confirmacao').focus();
      await atualizar();
      return;
    } else if (form.id === 'reserve-form') {
      await api('/api/reservas', 'POST', {livro_id:values.get('livro_id'), prazo:new Date(values.get('prazo')).toISOString(), embrulho:$('#reserve-gift').checked});
      $('#reserve-dialog').close(); trocarAba('visita'); avisar('Livro reservado. Acompanhe a preparação por aqui.');
    } else if (form.id === 'deadline-form') {
      await api(`/api/reservas/${encodeURIComponent(values.get('reserva_id'))}`, 'PATCH', {prazo:new Date(values.get('prazo')).toISOString()});
      $('#deadline-dialog').close(); avisar('Prazo de retirada atualizado.');
    } else if (form.id === 'scan-form') {
      const l = await api(`/api/codigo/${encodeURIComponent(values.get('codigo').trim())}`);
      $('#scan-dialog').close(); await abrirLivro(l.id); return;
    } else if (form.id === 'agendamento-form') {
      await api('/api/agendamentos', 'POST', {horario_id:values.get('horario_id')}); avisar('Atendimento agendado.');
    } else if (form.id === 'preferencias-form') {
      await api('/api/preferencias', 'PATCH', {generos:values.getAll('generos'), temas_notificacao:values.getAll('temas')});
      preferenciasDirty = false; avisar('Suas preferências foram salvas.');
    } else if (form.classList.contains('opiniao-form')) {
      await api(`/api/clubes/${encodeURIComponent(form.dataset.id)}/opinioes`, 'POST', {texto:values.get('texto')});
      limparRascunho(form.dataset.id);
      form.elements.texto.value = ''; avisar('Opinião publicada.');
    }
    await atualizar();
  });
});

$('#busca').addEventListener('input', renderizarCatalogo);
$('#genero').addEventListener('change', renderizarCatalogo);
$('#lancamentos').addEventListener('change', renderizarCatalogo);
$('#preferencias-form').addEventListener('change', () => { preferenciasDirty = true; });
$('#scan-dialog').addEventListener('close', pararCamera);
window.addEventListener('pagehide', pararCamera);
window.addEventListener('livraria:sessao-invalida', () => {
  const aviso = document.querySelector('#session-notice') || document.createElement('div');
  aviso.id = 'session-notice';
  aviso.className = 'notice';
  aviso.setAttribute('role', 'alert');
  aviso.innerHTML = '<span>Sua sessão expirou ou é inválida. Iniciar uma nova sessão cria outro perfil de demonstração.</span><button class="btn secondary" data-action="nova-sessao">Iniciar nova sessão</button>';
  (document.querySelector('dialog[open]') || $('#conteudo')).prepend(aviso);
});
window.atualizar = atualizar;
atualizar();
setInterval(() => { if (!document.hidden) atualizar(); }, 15000);
