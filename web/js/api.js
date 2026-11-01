'use strict';

// Esta fronteira conhece HTTP e a sessão; não aplica regras de negócio.
(() => {
  const chave = 'entrelinhas.sessao';
  let token = null, inicializando = null, sessaoInvalida = false;
  try { token = sessionStorage.getItem(chave); } catch (_) { /* Fallback: memória da aba. */ }

  const base = () => String(window.LIVRARIA_CONFIG?.API_BASE_URL || '').replace(/\/+$/, '');

  function guardar(valor) {
    token = valor;
    try {
      if (valor) sessionStorage.setItem(chave, valor);
      else sessionStorage.removeItem(chave);
    } catch (_) { /* Armazenamento bloqueado: a identidade dura enquanto a página estiver aberta. */ }
  }

  function erroSessao() {
    sessaoInvalida = true;
    window.dispatchEvent(new Event('livraria:sessao-invalida'));
    return new Error('Sua sessão expirou ou é inválida. Inicie uma nova sessão para continuar.');
  }

  async function enviar(caminho, metodo, corpo, identidade) {
    if (!/^https?:\/\//.test(base())) throw new Error('O endereço da livraria não está configurado.');
    const controller = new AbortController();
    const prazo = Number(window.LIVRARIA_CONFIG?.TIMEOUT_MS) || 10000;
    const timer = setTimeout(() => controller.abort(), prazo);
    const options = {
      method: metodo, mode: 'cors', credentials: 'omit', cache: 'no-store',
      headers: {Accept: 'application/json'}, signal: controller.signal,
    };
    if (identidade) options.headers.Authorization = `Bearer ${identidade}`;
    if (corpo !== undefined) {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(corpo);
    }
    try {
      const response = await fetch(`${base()}${caminho}`, options);
      if (response.status === 401) {
        // Uma resposta atrasada da identidade anterior não invalida o token
        // que o leitor acabou de renovar. Só a operação antiga é rejeitada.
        if (identidade && identidade !== token) {
          throw new Error('A sessão desta operação foi substituída. Consulte o estado atual.');
        }
        throw erroSessao();
      }
      if (!response.headers.get('Content-Type')?.includes('application/json')) {
        throw new Error('A livraria retornou uma resposta inválida. Tente consultar novamente.');
      }
      let result;
      try { result = await response.json(); }
      catch (_) { throw new Error('A livraria retornou uma resposta inválida. Tente consultar novamente.'); }
      if (!response.ok) throw new Error(result?.erro || 'Não foi possível concluir a operação.');
      return result;
    } catch (erro) {
      if (controller.signal.aborted) throw new Error('A livraria demorou para responder. Consulte o estado antes de repetir a operação.');
      if (erro instanceof TypeError) throw new Error('Não foi possível conectar à livraria. Confira sua conexão e tente consultar novamente.');
      throw erro;
    } finally {
      clearTimeout(timer);
    }
  }

  function garantirSessao() {
    if (sessaoInvalida) return Promise.reject(erroSessao());
    if (token) return Promise.resolve(token);
    if (!inicializando) {
      inicializando = enviar('/api/sessoes', 'POST', {}, null).then(sessao => {
        if (typeof sessao?.token !== 'string' || sessao.tipo !== 'Bearer') {
          throw new Error('Não foi possível iniciar a sessão da livraria.');
        }
        guardar(sessao.token);
        return token;
      }).finally(() => { inicializando = null; });
    }
    return inicializando;
  }

  window.livrariaApi = async (caminho, metodo = 'GET', corpo) => {
    const identidade = await garantirSessao();
    // Não há retry automático: uma falha de rede pode ocorrer depois da gravação.
    return enviar(caminho, metodo, corpo, identidade);
  };

  window.novaSessaoLivraria = async () => {
    if (inicializando) await inicializando.catch(() => {});
    guardar(null);
    sessaoInvalida = false;
    await garantirSessao();
  };
})();
