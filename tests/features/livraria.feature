Feature: Visitar e aproveitar a livraria física
  Como cliente da livraria
  Quero consultar livros e organizar minha visita
  Para aproveitar os serviços da loja física

  Background:
    Given que existem livros cadastrados no catálogo
    And que sou a cliente "ana"

  @E1-01
  Scenario: Buscar um livro existente pelo título
    When eu buscar pelo título "1984"
    Then o livro "1984" deve ser retornado

  @E1-01
  Scenario: Buscar livros pelo autor
    When eu buscar pelo autor "George Orwell"
    Then devem ser retornados 2 livros

  @E1-01
  Scenario: Buscar um livro inexistente
    When eu buscar pelo título "Livro Inexistente"
    Then nenhum livro deve ser retornado

  @E1-02
  Scenario: Consultar quantidade disponível em estoque
    When eu consultar a disponibilidade do livro "1984"
    Then devem ser informados 3 exemplares disponíveis

  @E1-03
  Scenario: Filtrar livros por gênero
    When eu filtrar os livros pelo gênero "Fantasia"
    Then devem ser retornados apenas livros do gênero "Fantasia"

  @E1-04
  Scenario: Consultar lançamentos da semana
    When eu consultar os lançamentos da semana
    Then deve ser retornado 1 lançamento

  @E1-05
  Scenario: Avisar quando um livro voltar ao estoque
    Given que acompanho a reposição de "Livro Esgotado"
    When a loja repuser 2 exemplares de "Livro Esgotado"
    Then devo receber uma notificação do tema "estoque"

  @E1-06
  Scenario: Recomendar livros com base nas compras anteriores
    Given que comprei "1984" e recebi 20 pontos
    When eu consultar minhas recomendações
    Then o livro "A Revolução dos Bichos" deve ser retornado
    And o livro "1984" não deve ser retornado

  @E1-07
  Scenario: Ler avaliações de outros clientes
    When eu consultar os detalhes de "1984"
    Then devo ver a avaliação "Uma leitura marcante."

  @E2-01
  Scenario: Encontrar o livro dentro da loja
    When eu consultar os detalhes de "1984"
    Then devo ver a seção "Literatura" e a prateleira "A1"

  @E2-02
  Scenario: Consultar informações pelo código de barras
    When eu consultar o código de barras "9788535914849"
    Then devo ver a sinopse "Uma sociedade sob vigilância."
    And devo ver o preço de 49.90 reais
    And devo ver a avaliação "Uma leitura marcante."

  @E2-03
  Scenario: Entrar na fila virtual
    When eu entrar na fila virtual
    Then minha posição na fila deve ser 1

  @E2-04
  Scenario: Agendar atendimento especializado
    Given que há um horário do livreiro "Carlos" em "2026-09-28T14:00:00+00:00"
    When eu agendar esse atendimento
    Then meu atendimento deve estar confirmado com "Carlos"

  @E2-05
  Scenario: Consultar funcionamento e lotação
    When eu consultar as informações da loja
    Then devo ver o horário "Seg–Sáb, 09h às 19h"
    And devo ver a lotação atual de 12 pessoas

  @E3-01
  Scenario: Reservar um exemplar disponível
    When eu reservar "1984" até "2026-09-29T18:00:00+00:00"
    Then minha reserva deve estar "pendente"
    And devem restar 2 exemplares de "1984"

  @E3-01
  Scenario: Não reservar um livro esgotado
    When eu tentar reservar "Livro Esgotado"
    Then a operação deve ser recusada
    And devem restar 0 exemplares de "Livro Esgotado"

  @E3-02
  Scenario: Alterar o prazo de retirada de uma reserva
    Given que reservei "1984" até "2026-09-29T18:00:00+00:00"
    When eu alterar o prazo para "2026-09-30T18:00:00+00:00"
    Then minha reserva deve ter prazo "2026-09-30T18:00:00+00:00"

  @E3-03
  Scenario: Avisar quando a reserva estiver separada
    Given que reservei "1984" até "2026-09-29T18:00:00+00:00"
    When a loja marcar minha reserva como pronta
    Then minha reserva deve estar "pronta"
    And devo receber uma notificação do tema "reservas"

  @E3-04
  Scenario: Cancelar uma reserva
    Given que reservei "1984" até "2026-09-29T18:00:00+00:00"
    When eu cancelar minha reserva
    Then minha reserva deve estar "cancelada"
    And devem restar 3 exemplares de "1984"

  @E4-01
  Scenario: Acumular os pontos informados na compra física
    When a loja registrar minha compra de "1984" com 20 pontos
    Then meu saldo de pontos deve ser 20

  @E4-02
  Scenario: Consultar saldo de fidelidade
    Given que comprei "1984" e recebi 20 pontos
    And que comprei "O Hobbit" e recebi 15 pontos
    When eu consultar minha fidelidade
    Then meu saldo de pontos deve ser 35

  @E4-03
  Scenario: Receber um cupom da loja
    When a loja conceder o cupom "LEITURA" com os termos "Desconto informado no caixa"
    Then devo ver o cupom "LEITURA"

  @E4-04
  Scenario: Apresentar o cartão digital
    When eu consultar minha fidelidade
    Then meu cartão digital deve identificar "ana"

  @E4-05
  Scenario: Receber aviso de pontos próximos da expiração
    Given que tenho 20 pontos válidos até "2026-09-30T12:00:00+00:00" com aviso em "2026-09-27T12:00:00+00:00"
    When o aplicativo processar os lembretes
    Then devo receber uma notificação do tema "fidelidade"

  @E5-01
  Scenario: Consultar a agenda de eventos
    Given que há um evento chamado "Conversa com autores"
    When eu consultar a agenda de eventos
    Then devo ver o evento "Conversa com autores"

  @E5-02
  Scenario: Garantir uma vaga no evento
    Given que há um evento chamado "Conversa com autores"
    When eu me inscrever nesse evento
    Then minha inscrição deve estar confirmada

  @E5-03
  Scenario: Receber lembrete de evento
    Given que há um evento chamado "Conversa com autores"
    And que estou inscrita nesse evento
    When o aplicativo processar os lembretes
    Then devo receber uma notificação do tema "eventos"

  @E5-04
  Scenario: Trocar opiniões no clube de leitura
    Given que há um clube chamado "Leituras compartilhadas"
    When eu participar desse clube e publicar "Gostei muito do livro do mês."
    Then o clube deve exibir minha opinião "Gostei muito do livro do mês."

  @E6-01
  Scenario: Guardar um livro na lista de desejos
    When eu adicionar "O Hobbit" à lista de desejos
    Then minha lista de desejos deve conter "O Hobbit"

  @E6-02
  Scenario: Consultar compras feitas na loja física
    Given que comprei "1984" e recebi 20 pontos
    When eu consultar meu histórico de compras
    Then meu histórico deve conter "1984"

  @E6-03
  Scenario: Configurar gêneros de interesse
    When eu escolher o gênero preferido "Fantasia"
    Then minhas recomendações devem incluir "O Hobbit"

  @E6-04
  Scenario: Receber apenas temas selecionados
    Given que aceito apenas notificações de "eventos"
    And que acompanho a reposição de "Livro Esgotado"
    When a loja repuser 2 exemplares de "Livro Esgotado"
    Then não devo receber notificações

  @E6-05
  Scenario: Reservar um presente com embrulho especial
    When eu reservar "O Hobbit" como presente até "2026-09-29T18:00:00+00:00"
    Then minha reserva deve ter embrulho especial

  @E1-08
  Scenario: Publicar uma avaliação visível a outros leitores
    When eu avaliar "1984" com nota 5 e comentário "Uma leitura excelente."
    Then outra cliente deve ver minha avaliação de "1984" com nota 5

  @E1-08
  Scenario: Recusar uma nota fora da escala
    When eu avaliar "1984" com nota 0 e comentário "Uma leitura excelente."
    Then a avaliação deve ser recusada com status 400
    And não deve existir uma avaliação minha de "1984"

  @E1-08
  Scenario: Impedir a repetição da avaliação pelo mesmo cliente
    When eu avaliar "1984" com nota 5 e comentário "Uma leitura excelente."
    And eu avaliar "1984" com nota 4 e comentário "Outra opinião."
    Then a avaliação deve ser recusada com status 409
    And deve existir apenas uma nova avaliação de "1984"
