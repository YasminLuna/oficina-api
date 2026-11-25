Feature: Compensacao da Saga de ordem de servico
  Para manter consistencia entre Billing e Execution
  Como orquestrador da oficina
  Quero cancelar o orcamento quando a execucao falhar antes de iniciar

  Scenario: Falha na criacao da execucao compensa o orcamento aprovado
    Given uma ordem de teste sem Saga registrada
    And o Billing aprova o orcamento e o Execution falha antes de criar o item
    When o evento ORDER_CREATED e processado
    Then a Saga termina no estado COMPENSATED
    And o Billing recebe a solicitacao de cancelamento
    And o Execution nao recebe solicitacao para iniciar o servico
