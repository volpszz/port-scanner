# Arquitetura e guia do código

Este documento descreve a implementação atual do projeto **port-scanner** ([repositório oficial](https://github.com/volpszz/port-scanner)). A apostila e `docs/snapshot/` registram uma versão anterior e foram preservados sem reescrita.

## 1. Mapa do projeto

```text
port-scanner/
├── main.py                 # Entrada antiga, delega à CLI
├── connection.py           # Nomes antigos, sem implementação duplicada
├── port_scanner/
│   ├── __init__.py         # Identifica o pacote; não inicia varreduras
│   ├── __main__.py         # python -m port_scanner
│   ├── config.py           # Padrões e ScanConfig imutável
│   ├── probes.py           # Sockets TCP/UDP e interpretação de respostas
│   ├── scanner.py          # ScanResult e orquestração sequencial
│   └── cli.py              # Argumentos, menu, impressão, códigos de saída
├── test_connection.py      # Contratos legados
├── tests/                  # Testes da implementação atual por camada
├── README.md               # Uso e limites
├── CONTRIBUTING.md         # Fluxo de desenvolvimento
└── docs/                   # Este guia e material histórico
```

## 2. Fluxo de uma execução

```text
main.py ou port_scanner.__main__
                 ↓
cli.main → argumentos ou menu → ScanConfig
                 ↓
scanner.scan → resolve hostname uma vez
                 ↓
para cada porta, para cada protocolo
                 ↓
probes.probe_tcp / probes.probe_udp
                 ↓
ScanResult → cli.main imprime
```

A configuração é validada antes do acesso à rede. O resolvedor padrão é `socket.gethostbyname`, portanto o escopo é IPv4 e somente um endereço. O DNS é executado ao começar a iterar `scan`, não ao criar o gerador.

Não há threads, fila de tarefas, container de injeção, classe abstrata ou dependências externas: o problema atual não exige essas estruturas. A execução sequencial facilita a leitura e mantém a ordem dos resultados, mas é mais lenta quando muitas portas expiram.

## 3. Responsabilidades e contratos

### `config.py`: regras de entrada

`ScanConfig(target, ports, protocols, timeout)` é uma `dataclass(frozen=True)`. Ela normaliza espaços ao redor do alvo, copia portas/protocolos para tuplas e remove repetições sem ordenar os valores. Valida alvo não vazio, portas inteiras na faixa válida, protocolos conhecidos e timeout positivo/finito. Também verifica se `socket.settimeout` aceita o valor em um socket local sem conexão, fechado pelo context manager. O limite é o do ambiente, não um teto arbitrário: `OverflowError` ou `ValueError` dessa chamada viram `ValueError` de configuração (saída `2` na CLI). A validação não resolve nomes, não envia tráfego nem altera o timeout global.

Use `str` para o alvo, iteráveis de `int` para portas, iteráveis dos textos minúsculos `tcp`/`udp` para protocolos e número para timeout. As anotações orientam o uso: não são um conversor genérico de tipos. O objeto final não pode ter seus campos reatribuídos. Para mudar uma configuração, crie outra instância ou use `dataclasses.replace`.

Os padrões têm uma fonte única: `DEFAULT_PORTS` e `DEFAULT_TIMEOUT`.

### `probes.py`: contato com a rede

Cada função recebe `(target_ip: str, port: int, timeout: float)` e devolve um estado em texto. Um context manager fecha o socket tanto no sucesso quanto na exceção. `settimeout` é local ao socket: não altera padrões globais do processo.

- **TCP:** `connect_ex` retorna `0` quando a conexão funciona; `ECONNREFUSED` representa recusa; códigos de timeout/indisponibilidade temporária viram `filtered/unknown`; demais códigos viram `error: NOME`.
- **UDP:** conecta o socket ao par remoto, envia `UDP_PAYLOAD`, e aguarda uma resposta. Resposta é `open`, `ConnectionRefusedError` é `closed`, timeout é `open|filtered`. Um datagrama vazio recebido também é resposta válida.
- Outros `OSError` são propagados para o orquestrador. As sondagens de baixo nível pressupõem parâmetros já validados, como os fornecidos por `ScanConfig`.

UDP não faz handshake. Não se pode concluir que uma porta está aberta apenas porque `connect` ou `send` funcionou. O payload genérico não substitui uma consulta válida do protocolo de aplicação. Não tente uniformizar os estados TCP e UDP apagando essa diferença.

### `scanner.py`: execução sem interface

`scan(config, *, resolver=None, probe_functions=None)` devolve um iterador de `ScanResult`. O resultado imutável contém `target_ip`, `port`, `protocol` e `state`.

O scanner não pede entrada, não imprime, não decide código de saída e não conhece `argparse`. Resolve o destino uma vez; percorre primeiro as portas e depois os protocolos. Um erro de rede individual não impede as próximas sondagens. A falha de DNS é propagada. Somente ao chamar o resolvedor, `UnicodeError` de codificação do hostname é normalizado para `socket.gaierror`, preservando a causa; isso inclui rótulos longos demais e resulta em saída `1` na CLI. O tratamento não envolve as probes: seus `ValueError`, `UnicodeError` e `RuntimeError` se propagam para não esconder defeitos.

Os pontos de injeção são funções simples:

```python
from port_scanner.config import ScanConfig
from port_scanner.scanner import scan

observations = list(scan(
    ScanConfig('laboratorio.test', ports=(8000,)),
    resolver=lambda hostname: '127.0.0.1',
    probe_functions={'tcp': lambda ip, port, timeout: 'closed'},
))
assert observations[0].state == 'closed'
```

Esse exemplo demonstra substituição de dependências; **não mede uma porta real**. Um mapa injetado deve ter uma função para cada protocolo solicitado. O scanner não tenta consertar mapas incompletos nem estados inválidos de plugins fornecidos pelo chamador.

### `cli.py`: interação

- `build_parser`: define os argumentos públicos.
- `parse_ports`: traduz texto separado por vírgulas e rejeita valores inválidos.
- `choose_protocol`: mantém o menu e repete entrada inválida com um laço.
- `main`: monta a configuração, consome os resultados, imprime e traduz erros esperados em códigos de saída.

A CLI mantém os rótulos em inglês do programa anterior; a documentação é em português. Não coloque `input` nas sondagens para mudar a interface.

### Compatibilidade

`connection.connection_tcp`, `connection.connection_udp` e `connection.connection_choice` são aliases das implementações novas. Assinaturas e respostas foram preservadas. `main.py` injeta as sondagens expostas por essa fachada; os testes legados podem continuar substituindo essas funções. O pacote é o caminho recomendado para código novo.

## 4. Conceitos aplicados e seus limites

| Conceito | Aplicação concreta |
| --- | --- |
| Responsabilidade única | Configuração, sockets, execução e apresentação em módulos separados. |
| Nomes expressivos | `ScanConfig`, `ScanResult`, `probe_tcp`, `probe_udp`, `scan`. |
| DRY | Uma implementação de cada sondagem; arquivos antigos apenas delegam. |
| Baixo acoplamento | Scanner independe do terminal; dependências substituíveis por funções. |
| Imutabilidade | Configuração e resultados não são alterados durante o fluxo. |
| Tratamento explícito de falhas | DNS é falha global; erro de uma porta é resultado individual. |
| Simplicidade | Biblioteca padrão, sem frameworks e sem abstrações para requisitos futuros. |
| Testabilidade | Unidades isoladas e integração com sockets/processos reais no loopback. |

`state` continua como texto para manter compatibilidade e simplicidade. Caso surjam filtros, serialização e estados novos, considere uma enumeração e um campo de detalhe de erro em uma mudança própria, acompanhada de migração e testes.

## 5. Receitas de modificação

### Trocar portas ou timeout

Para uma execução, use a CLI ou `ScanConfig`. Para mudar o padrão do produto, altere as constantes em `config.py`, o teste de padrões em `tests/test_config.py` e a documentação. Não edite `main.PORTS` esperando modificar a configuração interna.

### Adicionar uma apresentação JSON

Mantenha o acesso à rede como está. Acrescente uma opção na CLI e um formatador que receba `ScanResult`. Defina primeiro testes para o formato e para a separação de `stdout`/`stderr`; avisos interativos não devem contaminar o JSON. Preserve o formato de texto atual como padrão.

### Adicionar uma sondagem específica de aplicação

Defina um teste com servidor local que receba a requisição esperada e retorne uma resposta controlada. Implemente uma função compatível com o contrato de sondagem. Para experimentos, injete-a em `probe_functions`; para mudar o produto, atualize também registro de sondagens, protocolos permitidos, seleção da CLI e documentação. Não declare serviços abertos por ausência de resposta.

### Adicionar IPv6 ou paralelismo

Não basta trocar uma constante. IPv6 exige mudar resolução, família e formato dos endereços, além dos testes. Paralelismo exige decidir ordenação, limite de sockets, cancelamento e efeito na carga do destino. Trate essas mudanças como requisitos separados em vez de complicar antecipadamente o código atual.

## 6. Material histórico

`docs/snapshot/`, laboratórios, PDF, manifesto e evidências anteriores não foram migrados. Eles continuam úteis para estudar os fundamentos, mas seus nomes de funções e números de linha não representam o pacote atual. O comando de testes atual roda na raiz; os testes do snapshot são executados separadamente dentro de `docs/snapshot`.
