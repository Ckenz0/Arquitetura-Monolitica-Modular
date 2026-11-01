# Livraria Entrelinhas

Aplicação de livraria em arquitetura monolítica modular. Catálogo, reservas, visitas, fidelidade, comunidade e perfis compartilham uma única aplicação Flask, com contratos públicos e armazenamento privado por módulo.

O frontend HTML, CSS e JavaScript é servido pela própria aplicação. Catálogo, visita, comunidade e perfil são módulos ES carregados pelo navegador. As ações usam HTTP/JSON na mesma origem; as chamadas entre módulos do backend são chamadas Python no mesmo processo.

## Organização

| Diretório | Responsabilidade |
| --- | --- |
| `web/` | Interface, transporte HTTP e quatro módulos de apresentação |
| `server/modules/clientes/` | Perfis anônimos, preferências e notificações |
| `server/modules/catalogo/` | Livros, estoque, avaliações, desejos e avisos de reposição |
| `server/modules/reservas/` | Reservas, prazo, preparação e cancelamento |
| `server/modules/visitas/` | Fila, atendimento e informações da loja |
| `server/modules/fidelidade/` | Compras, pontos, cupons e recomendações |
| `server/modules/comunidade/` | Eventos, inscrições, clubes e opiniões |
| `server/composition.py` | Composição e injeção das APIs dos módulos |
| `server/transport/` | Identificação, validação HTTP, erros e logs |
| `server/openapi.yaml` | Contrato da API |
| `tests/` | Regras de negócio, fronteiras, HTTP e fluxos de navegador |

Cada módulo expõe um `api.py` e uma factory pública. Serviços, repositórios e regras internas pertencem ao próprio módulo. Um módulo consulta outro pela API pública e recebe cópias dos dados. Não existe um repositório global de negócio.

Reservas e fidelidade dependem de catálogo e clientes. Catálogo, visitas e comunidade dependem de clientes. Clientes não depende dos demais. Um `RLock` da instância protege a execução das operações entre módulos, incluindo a baixa e a devolução de estoque.

## Execução local

Python 3.12. No PowerShell, na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m server.app
```

Interface: `http://127.0.0.1:5000/`. Saúde: `http://127.0.0.1:5000/api/health`.

A configuração está em `.env.example`. O servidor lê `.env`, quando presente. `PORT` escolhe a porta local; `ALLOWED_ORIGINS` contém origens externas exatas permitidas, sem barra final; a origem que serve o próprio monólito é aceita também em portas personalizadas. Em produção, `APP_ENV=production` exige `SECRET_KEY` estável de pelo menos 32 caracteres e origens explícitas. Segredos não pertencem ao frontend.

O servidor WSGI Waitress pode executar o mesmo aplicativo, em um processo com quatro threads:

```powershell
.\.venv\Scripts\python.exe -m waitress --host=127.0.0.1 --port=5000 --threads=4 --call server.app:create_app
```

## Validação

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes de interface usam Chrome ou Edge instalado; o caminho pode ser informado em `PLAYWRIGHT_BROWSER_EXECUTABLE`. Em ambientes sem navegador, `pytest -q -m "not interface"` executa as verificações de negócio, arquitetura e HTTP.

## Comportamento e limites

A sessão anônima tem token assinado, válido por 24 horas, armazenado em `sessionStorage` e enviado como `Authorization: Bearer`. Não há cadastro ou login. O servidor valida a identidade para isolar reservas, preferências e demais dados pessoais. Avaliações e opiniões são públicas. CORS restringe origens do navegador e não substitui identificação.

O catálogo é compartilhado entre os leitores da mesma instância. Todos os dados ficam em memória: reiniciar a aplicação apaga alterações. A execução exige um único processo e uma única instância; múltiplos workers teriam estados independentes. O lock não oferece persistência ou transações distribuídas.

A demonstração inclui livros, horários, eventos e clube de leitura. Cada nova sessão recebe pontos e um cupom ilustrativo; não há compra ou pagamento real. Lembretes são processados ao consultar o estado, sem agendador externo. Microsserviços e micro-frontends com publicação independente são uma possível evolução, não a topologia desta implementação.
