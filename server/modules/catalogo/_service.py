"""Casos de uso do catálogo e autoridade sobre estoque e avaliações."""

from copy import deepcopy
from uuid import uuid4

from server.modules.clientes.api import ClientesAPI
from server.shared.context import atomico
from server.shared.errors import ErroLivraria
from server.shared.validation import inteiro_nao_negativo, texto_obrigatorio
from ._domain import Avaliacao
from ._repository import RepositorioCatalogo


class Catalogo:
    def __init__(self, livros, contexto, clientes: ClientesAPI):
        self._contexto = contexto
        self._clientes = clientes
        self._repo = RepositorioCatalogo(livros)

    @atomico
    def livro(self, livro_id, cliente_id=None):
        livro = deepcopy(self._repo.obter(livro_id))
        novas = [deepcopy(a) for (livro, _), a in self._repo.avaliacoes.items() if livro == livro_id]
        if novas:
            livro.setdefault('avaliacoes', []).extend(novas)
        if cliente_id is not None:
            livro['ja_avaliou'] = (livro_id, cliente_id) in self._repo.avaliacoes
        return livro

    @atomico
    def buscar(self, q='', genero='', lancamentos=False):
        termo = q.strip().casefold()
        return [self.livro(l['id']) for l in self._repo.livros
                if (not termo or termo in l['titulo'].casefold() or termo in l['autor'].casefold())
                and (not genero or genero.casefold() == l['genero'].casefold())
                and (not lancamentos or l.get('lancamento'))]

    @atomico
    def por_codigo(self, codigo):
        for livro in self._repo.livros:
            if livro.get('codigo') == codigo:
                return self.livro(livro['id'])
        raise ErroLivraria('Código de barras não encontrado.', 404)

    def buscar_por_titulo(self, titulo):
        termo = titulo.strip().casefold()
        return [l for l in self.buscar() if termo in l['titulo'].casefold()]

    def buscar_por_autor(self, autor):
        termo = autor.strip().casefold()
        return [l for l in self.buscar() if termo in l['autor'].casefold()]

    def filtrar_por_genero(self, genero):
        return self.buscar(genero=genero.strip())

    def consultar_estoque(self, titulo):
        termo = titulo.strip().casefold()
        return next((l['estoque'] for l in self.buscar() if l['titulo'].casefold() == termo), 0)

    def listar_lancamentos(self):
        return self.buscar(lancamentos=True)

    @atomico
    def reservar_exemplar(self, livro_id, embrulho=False):
        livro = self._repo.obter(livro_id)
        if type(embrulho) is not bool:
            raise ErroLivraria('Embrulho deve ser verdadeiro ou falso.')
        if livro['estoque'] <= 0:
            raise ErroLivraria('Livro sem exemplares disponíveis.', 409)
        livro['estoque'] -= 1
        return self.livro(livro_id)

    @atomico
    def devolver_exemplar(self, livro_id):
        return self.atualizar_estoque(livro_id, self._repo.obter(livro_id)['estoque'] + 1)

    @atomico
    def acompanhar_estoque(self, cliente_id, livro_id):
        self._repo.obter(livro_id)
        self._clientes.obter_perfil(cliente_id)
        self._repo.acompanhamentos.setdefault(livro_id, set()).add(cliente_id)
        return {'livro_id': livro_id, 'acompanhando': True}

    @atomico
    def atualizar_estoque(self, livro_id, quantidade):
        inteiro_nao_negativo(quantidade, 'Estoque')
        livro = self._repo.obter(livro_id)
        anterior = livro['estoque']
        livro['estoque'] = quantidade
        if anterior == 0 and quantidade > 0:
            for cliente_id in self._repo.acompanhamentos.get(livro_id, set()):
                self._clientes.notificar(cliente_id, 'estoque', f'{livro["titulo"]} voltou ao estoque.')
        return self.livro(livro_id)

    @atomico
    def adicionar_desejo(self, cliente_id, livro_id):
        livro = self.livro(livro_id)
        self._clientes.obter_perfil(cliente_id)
        desejos = self._repo.desejos.setdefault(cliente_id, [])
        if livro_id not in desejos:
            desejos.append(livro_id)
        return livro

    @atomico
    def desejos(self, cliente_id):
        self._clientes.obter_perfil(cliente_id)
        return [self.livro(i) for i in self._repo.desejos.get(cliente_id, [])]

    @atomico
    def publicar_avaliacao(self, cliente_id, livro_id, nota, texto):
        self._repo.obter(livro_id)
        conteudo = Avaliacao(nota, texto)
        texto_obrigatorio(cliente_id, 'o identificador do cliente')
        chave = (livro_id, cliente_id)
        if chave in self._repo.avaliacoes:
            raise ErroLivraria('Você já publicou uma avaliação deste livro.', 409)
        self._clientes.obter_perfil(cliente_id)
        avaliacao = {'id': uuid4().hex, 'cliente': f'Leitor {uuid4().hex[:8]}',
                     'nota': conteudo.nota, 'texto': conteudo.texto,
                     'data': self._contexto.agora().isoformat()}
        self._repo.avaliacoes[chave] = avaliacao
        return deepcopy(avaliacao)
