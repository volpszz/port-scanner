# Material de estudo — redes e port scanner

O guia da versão atual está em [PDF](guia-do-projeto.pdf) e em [Markdown](GUIA-DO-PROJETO.md), com explicações em português e o código completo dos módulos principais no apêndice do PDF.

> **Material histórico:** para usar e modificar a implementação atual refatorada, consulte o [README](../README.md) e a [arquitetura](ARQUITETURA.md). O snapshot e a apostila abaixo descrevem a versão anterior.

- `guia-redes-port-scanner.pdf`: apostila final, com sumário clicável, capítulos, exercícios/gabarito e apêndices de código numerado.
- `guia-redes-port-scanner.md`: texto-fonte editável dos capítulos.
- `snapshot/`: versão congelada de `main.py`, `connection.py` e testes usada na apostila. A implementação atual da raiz foi refatorada em `port_scanner/` e não deve ser confundida com esse snapshot.
- `labs/`: servidores TCP/UDP e cliente de sondagem restritos ao loopback.
- `verificacao-laboratorios.txt`: saída real dos laboratórios e dos testes do snapshot.
- `guia-redes-port-scanner.manifest.json`: paginação e hashes dos arquivos reproduzidos no PDF.

## Executar os testes da versão estudada

A partir da raiz do projeto:

```sh
cd docs/snapshot
python -m unittest -v
cd ../..
```

## Executar um laboratório

Dois terminais na raiz do projeto. Terminal A:

```sh
python docs/labs/udp_server.py
```

Terminal B:

```sh
python docs/labs/probe_local.py udp 9999
```

Depois de encerrar o servidor com Ctrl+C, tente `--silent` para comparar os resultados. Para TCP, use `tcp_server.py` e `probe_local.py tcp 8000`.

## Reproduzir a verificação completa

```sh
python docs/verify_study_guide.py
```

O verificador usa as portas locais 8000 e 9999: precisam estar livres. Inicia os servidores temporários, testa TCP aberto/fechado e UDP com resposta/sem resposta/fechado, encerra os processos e executa os testes de `snapshot/`. Requer apenas a biblioteca padrão Python.

## Gerar novamente o PDF

O scanner não depende de ReportLab. Apenas o gerador do documento usa `reportlab` e `pypdf`, além das fontes Liberation em `/usr/share/fonts/liberation/` neste Linux:

```sh
python -m venv .venv-pdf
.venv-pdf/bin/python -m pip install reportlab pypdf
.venv-pdf/bin/python docs/build_study_guide.py
```

O gerador lê os capítulos, o snapshot, os laboratórios e as evidências. Não altera os módulos da raiz. O PDF foi revisado por extração de texto e inspeção de páginas renderizadas. Diagramas são conceituais; não há captura real de pacotes no material.
