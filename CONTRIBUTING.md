# Como modificar o projeto

## Preparação

Use Python 3.10 ou superior e abra um terminal na raiz. Execução e testes precisam apenas da biblioteca padrão; nenhum pacote precisa ser instalado. Não use `sudo`.

Leia o [README](README.md) e a [arquitetura](docs/ARQUITETURA.md). O repositório oficial é [volpszz/port-scanner](https://github.com/volpszz/port-scanner). Antes de alterar o código, crie uma branch a partir de `main`, confira `git status` e preserve mudanças locais não relacionadas. Use commits pequenos e descritivos e nunca publique credenciais ou ambientes virtuais.

## Ciclo recomendado

1. Execute `python -m unittest -v` e confirme a linha de base.
2. Localize a camada responsável pelo comportamento.
3. Para corrigir ou acrescentar comportamento, escreva um teste e observe a falha esperada antes de implementar.
4. Faça a menor alteração necessária para passar.
5. Remova duplicação e melhore nomes sem mudar o comportamento.
6. Execute toda a suíte e o programa; atualize os documentos afetados.

Evite grandes reformulações sem necessidade. Não acrescente bibliotecas, heranças ou classes de serviço para substituir uma função simples.

## Mapa dos testes

| Arquivo | Responsabilidade |
| --- | --- |
| `tests/test_config.py` | Padrões, validação e cópia de entradas mutáveis. |
| `tests/test_probes.py` | TCP aberto/fechado, UDP com resposta/silêncio e erros do sistema. |
| `tests/test_scanner.py` | Ordem, DNS único, continuidade após erro e propagação de falhas. |
| `tests/test_cli.py` | Argumentos, menu, formatação e códigos de saída. |
| `tests/test_entrypoints.py` | Processos reais de `main.py` e `python -m port_scanner`, incluindo modo interativo. |
| `test_connection.py` | Compatibilidade com a interface anterior. |

```sh
# Tudo, incluindo compatibilidade.
python -m unittest -v

# Uma camada, durante o desenvolvimento.
python -m unittest tests.test_probes -v

# Detectar problemas de sintaxe nos módulos atuais.
python -m compileall -q main.py connection.py port_scanner tests test_connection.py
```

### Regras para testes de rede

- Use `127.0.0.1` e `bind(..., 0)` para o SO escolher uma porta disponível.
- Não use hosts públicos, portas fixas nem serviços já instalados como requisito dos testes.
- Abra o listener antes de chamar a sondagem; use deadlines e feche sockets com `with`.
- Threads de resposta precisam de timeout, `join` e propagação da falha ao teste principal.
- UDP silencioso deve resultar em `open|filtered`, nunca `closed`.
- Simule timeout/erros do sistema quando reproduzi-los com rede real depender de firewall ou plataforma.
- Substitua a rede nos testes de despacho da CLI, mas mantenha integração real para provar o funcionamento dos sockets.

### Validação manual segura

Em um terminal, inicie o laboratório histórico, que escuta somente no loopback:

```sh
python docs/labs/tcp_server.py
```

Em outro, execute a versão atual:

```sh
python -m port_scanner 127.0.0.1 --ports 8000 --timeout 0.2
```

Encerre o servidor com Ctrl+C. A porta 8000 precisa estar disponível para esse laboratório manual; os testes automatizados usam portas dinâmicas e não têm essa exigência. A apostila explica laboratórios UDP adicionais.

## Checklist de revisão

- A função continua fazendo uma coisa claramente identificável?
- Código de terminal ficou na CLI, e código de socket ficou nas sondagens?
- Entradas novas são validadas antes de acessar a rede?
- Exceções esperadas são tratadas sem esconder erros de programação?
- Sockets e processos são encerrados também em caso de falha?
- Estados inconclusivos continuam distintos de portas fechadas?
- O teste falha quando o comportamento está incorreto e passa após a alteração?
- README e arquitetura correspondem aos argumentos e contratos reais?
- Compatibilidade necessária foi testada ou sua quebra foi documentada?

## O que não atualizar por acidente

A documentação histórica em `docs/snapshot/` e o PDF representam uma versão congelada. Não copie a refatoração para o snapshot: isso invalidaria a correspondência da apostila com os fontes e hashes do manifesto. Se quiser publicar uma apostila nova, trate-a como uma nova edição e regenere/verifique seus artefatos separadamente.

As dependências opcionais do gerador do PDF estão explicadas em `docs/LEIA-ME.md`; elas não pertencem ao scanner nem à suíte atual.
