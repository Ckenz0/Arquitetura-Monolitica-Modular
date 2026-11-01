"""Fila, agenda e informações da loja pertencem ao módulo de visitas."""


class RepositorioVisitas:
    def __init__(self):
        self.fila = []
        self.horarios = {}
        self.loja = {'horario': 'Não informado', 'lotacao': 0}
