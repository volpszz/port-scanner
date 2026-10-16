# port-scanner

Projeto de estudo de redes e segurança de [volpszz](https://github.com/volpszz), com código organizado por responsabilidade e documentação em português.

Repositório: [volpszz/port-scanner](https://github.com/volpszz/port-scanner).

Scanner didático de portas **IPv4**, com sondagens TCP e UDP, escrito em Python e sem dependências externas de execução.

> Use somente em máquinas próprias ou com autorização explícita. Mesmo uma conexão simples pode gerar logs e alertas. O programa não verifica se você tem autorização.

## Comece aqui

Requisito: **Python 3.10 ou superior**. A versão usada na validação desta refatoração foi Python 3.14.7, em Linux. As demais versões não foram executadas nesta validação.

Para obter uma cópia do projeto:

```sh
git clone https://github.com/volpszz/port-scanner.git
cd port-scanner
```

Execute os comandos a partir da raiz do projeto; não é necessário instalar o pacote nem usar `sudo`.

```sh
# Menu interativo: TCP, UDP ou ambos; depois informe o destino.
python main.py

# A mesma interface como módulo.
python -m port_scanner

# Sem perguntas: alvo explícito usa TCP por padrão.
python -m port_scanner 127.0.0.1 --ports 22,80,443 --timeout 0.2

# TCP e UDP, na ordem informada de portas.
python -m port_scanner 127.0.0.1 --protocol both --ports 8000,9999 --timeout 0.2

python -m port_scanner --help
```

`main.py` também aceita esses argumentos. Sem `--ports`, preserva a lista original: `53,22,80,111,139,443,32768`. Timeout padrão: `1.0` segundo por operação de socket. Sem alvo, há menu de protocolo, exceto quando `--protocol` já foi informado.

- `--protocol`: `tcp`, `udp` ou `both`.
- `--ports`: inteiros entre 1 e 65535, separados por vírgulas; não aceita intervalos. Repetições são removidas, preservando a ordem.
- `--timeout`: número positivo e finito em segundos, aceito por `socket.settimeout` no ambiente atual. A configuração verifica esse limite com um socket local, fechado sem conexão; valores finitos grandes demais (como `1e20`) são configuração inválida, com saída `2`. Não há teto arbitrário fixado pelo projeto. Não é um prazo global da varredura e não limita o tempo da resolução DNS.
- O alvo pode ser um endereço IPv4 ou hostname. Um único endereço retornado pelo resolvedor é utilizado.

## Como interpretar a saída

Cada linha de resultado tem o formato `porta/protocolo: estado`.

| Estado | Interpretação |
| --- | --- |
| `open` | O handshake TCP funcionou ou houve resposta UDP. |
| `closed` | Houve recusa explícita. A entrega da recusa UDP depende do sistema operacional. |
| `filtered/unknown` | A conexão TCP não foi conclusiva por timeout/indisponibilidade temporária. Não prova presença de firewall. |
| `open\|filtered` | Não houve resposta UDP no prazo; não distingue porta aberta de tráfego filtrado. |
| `error: ...` | Outro erro de rede. Não deve ser interpretado como porta fechada. |

O datagrama UDP é apenas `b'probe'`: DNS e outros serviços podem ignorá-lo mesmo estando abertos. O scanner não identifica serviço, versão nem vulnerabilidade. Também não oferece IPv6, SYN scan, paralelismo, descoberta de hosts ou varredura de sub-redes.

### Códigos de saída

| Código | Significado |
| --- | --- |
| `0` | A execução terminou; pode conter portas fechadas, resultados inconclusivos ou erros individuais. |
| `1` | Não foi possível resolver o destino. |
| `2` | Argumentos ou configuração inválidos. |
| `130` | Interrupção por Ctrl+C ou fim da entrada interativa. |

Erros de configuração/DNS e interrupções vão para `stderr`; resultados e perguntas ficam em `stdout`. Erros de programação não são convertidos em resultados de rede.

## Testar

```sh
python -m unittest -v
```

Os testes cobrem configuração, orquestração, CLI, compatibilidade e sockets reais em `127.0.0.1`. Servidores de teste usam portas temporárias; não dependem de hosts públicos. Consulte o [guia de contribuição](CONTRIBUTING.md) para o detalhamento.

## Usar como biblioteca

```python
from port_scanner.config import ScanConfig
from port_scanner.scanner import scan

config = ScanConfig(
    target='127.0.0.1',
    ports=(8000, 9999),
    protocols=('tcp', 'udp'),
    timeout=0.2,
)
for result in scan(config):
    print(result.target_ip, result.port, result.protocol, result.state)
```

`scan()` é um gerador: a resolução DNS e as sondagens começam quando ele é iterado. `socket.gaierror` é propagado para quem usa a biblioteca; falhas de codificação do hostname durante a resolução (por exemplo, um rótulo ASCII de 64 caracteres) são normalizadas para essa exceção, com saída `1` na CLI. Essa conversão não envolve as sondagens. Um `OSError` individual é convertido em `ScanResult` com estado de erro.

## Documentação completa em português

- [Guia em PDF](docs/guia-do-projeto.pdf): fundamentos, leitura por módulo, testes, receitas de alteração e código-fonte numerado.
- [Texto editável do guia](docs/GUIA-DO-PROJETO.md): conteúdo usado para gerar o PDF.
- Para regenerar: siga o capítulo 12 do guia; dependências do PDF são opcionais e não afetam o scanner.

## Onde entender e modificar

- [Arquitetura e decisões](docs/ARQUITETURA.md): mapa do código, fluxo, contratos e exemplos de extensão.
- [Guia de contribuição](CONTRIBUTING.md): como alterar, testar e revisar.
- [Material de estudo anterior](docs/LEIA-ME.md): apostila, snapshot e laboratórios históricos. Eles não descrevem a nova estrutura de módulos.

## O que mudou na refatoração

A lógica antes concentrada em `main.py` e `connection.py` foi dividida por responsabilidade em `port_scanner/`. Foram mantidos o menu, os nomes legados das sondagens, os estados TCP/UDP, as portas e o timeout padrão. Foram acrescentados argumentos de linha de comando, configuração validada e testes por camada.

`connection.py` é uma fachada de compatibilidade; código novo deve importar o pacote. Os atributos legados `main.PORTS` e `main.TIMEOUT` continuam disponíveis para leitura, mas alterá-los não reconfigura o scanner: use `ScanConfig` ou as opções da CLI. Mensagens de erro passaram a usar `stderr`. O script remoto anterior, `simplePort_scanner.py`, foi substituído por `main.py` e pelo pacote `port_scanner/`; seu conteúdo continua disponível no histórico Git.

## Licença

[MIT](LICENSE), mantendo a autoria original de volpsz.
