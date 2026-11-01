"""Fachada de compatibilidade e composição de DTOs, sem estado de negócio."""

from server.composition import criar_modulos
from server.modules.catalogo import filtrar_livros
from server.shared.context import atomico
from server.shared.errors import ErroLivraria
from server.shared.validation import NAO_INFORMADO


class Livraria:
    def __init__(self, livros=None, agora=None, *, modulos=None):
        self.modulos = modulos if modulos is not None else criar_modulos(livros, agora)
        self._contexto = self.modulos.contexto
        self.agora = self._contexto.agora

    def preferencias(self, cliente_id, generos=NAO_INFORMADO, temas_notificacao=NAO_INFORMADO):
        return self.modulos.clientes.preferencias(cliente_id, generos, temas_notificacao)

    def notificacoes(self, cliente_id):
        return self.modulos.clientes.notificacoes(cliente_id)

    def livro(self, livro_id, cliente_id=None):
        return self.modulos.catalogo.livro(livro_id, cliente_id)

    def buscar(self, q='', genero='', lancamentos=False):
        return self.modulos.catalogo.buscar(q, genero, lancamentos)

    def por_codigo(self, codigo):
        return self.modulos.catalogo.por_codigo(codigo)

    def buscar_por_titulo(self, titulo):
        return self.modulos.catalogo.buscar_por_titulo(titulo)

    def buscar_por_autor(self, autor):
        return self.modulos.catalogo.buscar_por_autor(autor)

    def filtrar_por_genero(self, genero):
        return self.modulos.catalogo.filtrar_por_genero(genero)

    def consultar_estoque(self, titulo):
        return self.modulos.catalogo.consultar_estoque(titulo)

    def listar_lancamentos(self):
        return self.modulos.catalogo.listar_lancamentos()

    def acompanhar_estoque(self, cliente_id, livro_id):
        return self.modulos.catalogo.acompanhar_estoque(cliente_id, livro_id)

    def atualizar_estoque(self, livro_id, quantidade):
        return self.modulos.catalogo.atualizar_estoque(livro_id, quantidade)

    def adicionar_desejo(self, cliente_id, livro_id):
        return self.modulos.catalogo.adicionar_desejo(cliente_id, livro_id)

    def desejos(self, cliente_id):
        return self.modulos.catalogo.desejos(cliente_id)

    def publicar_avaliacao(self, cliente_id, livro_id, nota, texto):
        return self.modulos.catalogo.publicar_avaliacao(cliente_id, livro_id, nota, texto)

    def reservar(self, cliente_id, livro_id, prazo, embrulho=False):
        return self.modulos.reservas.reservar(cliente_id, livro_id, prazo, embrulho)

    def reservas(self, cliente_id):
        return self.modulos.reservas.reservas(cliente_id)

    def alterar_prazo(self, cliente_id, reserva_id, prazo):
        return self.modulos.reservas.alterar_prazo(cliente_id, reserva_id, prazo)

    def cancelar_reserva(self, cliente_id, reserva_id):
        return self.modulos.reservas.cancelar_reserva(cliente_id, reserva_id)

    def marcar_pronta(self, reserva_id):
        return self.modulos.reservas.marcar_pronta(reserva_id)

    def entrar_fila(self, cliente_id):
        return self.modulos.visitas.entrar_fila(cliente_id)

    def oferecer_horario(self, livreiro, quando):
        return self.modulos.visitas.oferecer_horario(livreiro, quando)

    def agendar(self, cliente_id, horario_id):
        return self.modulos.visitas.agendar(cliente_id, horario_id)

    def configurar_loja(self, horario, lotacao):
        return self.modulos.visitas.configurar_loja(horario, lotacao)

    def informacoes_loja(self):
        return self.modulos.visitas.informacoes_loja()

    def registrar_compra(self, cliente_id, livro_id, pontos, expira_em=None, avisar_em=None):
        return self.modulos.fidelidade.registrar_compra(cliente_id, livro_id, pontos, expira_em, avisar_em)

    def historico(self, cliente_id):
        return self.modulos.fidelidade.historico(cliente_id)

    def fidelidade(self, cliente_id):
        return self.modulos.fidelidade.fidelidade(cliente_id)

    def conceder_cupom(self, cliente_id, codigo, termos):
        return self.modulos.fidelidade.conceder_cupom(cliente_id, codigo, termos)

    def recomendacoes(self, cliente_id):
        return self.modulos.fidelidade.recomendacoes(cliente_id)

    def cadastrar_evento(self, titulo, quando, local, capacidade=None, lembrar_em=None):
        return self.modulos.comunidade.cadastrar_evento(titulo, quando, local, capacidade, lembrar_em)

    def eventos(self, cliente_id=None):
        return self.modulos.comunidade.eventos(cliente_id)

    def inscrever(self, cliente_id, evento_id):
        return self.modulos.comunidade.inscrever(cliente_id, evento_id)

    def criar_clube(self, nome):
        return self.modulos.comunidade.criar_clube(nome)

    def participar_clube(self, cliente_id, clube_id):
        return self.modulos.comunidade.participar_clube(cliente_id, clube_id)

    def publicar_opiniao(self, cliente_id, clube_id, texto):
        return self.modulos.comunidade.publicar_opiniao(cliente_id, clube_id, texto)

    def clubes(self, cliente_id):
        return self.modulos.comunidade.clubes(cliente_id)

    @atomico
    def processar_lembretes(self):
        self.modulos.fidelidade.processar_lembretes()
        self.modulos.comunidade.processar_lembretes()

    @atomico
    def estado(self, cliente_id):
        self.processar_lembretes()
        return {
            'cliente': self.modulos.clientes.obter_perfil(cliente_id),
            'livros': self.modulos.catalogo.buscar(),
            'reservas': self.modulos.reservas.reservas(cliente_id),
            'fidelidade': self.modulos.fidelidade.fidelidade(cliente_id),
            'loja': self.modulos.visitas.informacoes_loja(),
            'fila': self.modulos.visitas.fila(cliente_id),
            'horarios': self.modulos.visitas.horarios(),
            'agendamentos': self.modulos.visitas.agendamentos(cliente_id),
            'eventos': self.modulos.comunidade.eventos(cliente_id),
            'clubes': self.modulos.comunidade.clubes(cliente_id),
            'desejos': self.modulos.catalogo.desejos(cliente_id),
            'historico': self.modulos.fidelidade.historico(cliente_id),
            'recomendacoes': self.modulos.fidelidade.recomendacoes(cliente_id),
            'notificacoes': self.modulos.clientes.notificacoes(cliente_id),
        }
