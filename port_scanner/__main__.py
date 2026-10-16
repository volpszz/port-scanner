"""Permite python -m port_scanner sem executar tarefas ao importar o módulo."""
from .cli import main

if __name__ == '__main__':
    raise SystemExit(main())
