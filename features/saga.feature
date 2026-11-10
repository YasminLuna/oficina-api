# language: pt
Funcionalidade: Orquestração da ordem de serviço com Saga
  Como cliente de uma oficina
  Quero solicitar um orçamento e acompanhar sua execução
  Para garantir consistência entre os serviços mesmo com mensagens duplicadas

  Cenário: Orçamento solicitado pela API é processado uma única vez
    Dado que existe um cliente autenticado e uma ordem de serviço criada
    Quando o cliente solicita um orçamento de 150 reais
    E repete a mesma solicitação de orçamento
    Então a API reutiliza o mesmo identificador de evento
    E o evento é publicado pelo transactional outbox
    E a Saga termina no estado COMPLETED
    E o orçamento fica no estado APPROVED
    E a execução fica no estado COMPLETED

  Cenário: Falha antes do início da execução é compensada
    Dado que a execução está na fila e o orçamento foi aprovado
    Quando ocorre uma falha ao iniciar a execução
    Então a execução é cancelada
    E o orçamento é cancelado
    E a Saga termina no estado COMPENSATED

  Cenário: Falha após início requer intervenção
    Dado que a execução já foi iniciada
    Quando ocorre uma falha irreversível
    Então a Saga termina no estado COMPENSATION_REQUIRED
