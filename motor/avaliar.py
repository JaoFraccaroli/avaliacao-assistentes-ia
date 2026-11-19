"""Linha de comando: avalia um assistente com um modelo do Ollama.

    python -m motor.avaliar --assistente loja --modelo qwen2.5:1.5b
    python -m motor.avaliar --assistente dnd  --modelo llama3.2:1b --saida relatorios

Sai com código 1 se alguma categoria ficar abaixo do mínimo (para o CI ficar vermelho).
"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

from motor.avaliacao import avaliar
from motor.casos import carregar_casos
from motor.cliente_llm import ClienteOllama, ollama_disponivel
from motor.relatorio import em_markdown

RAIZ = Path(__file__).resolve().parent.parent


def criar_assistente(nome: str, usar_documentos_locais: bool = False):
    """A avaliação usa só os documentos públicos (resultado igual em qualquer máquina)."""
    if nome == "loja":
        from assistentes.loja.assistente import AssistenteLoja
        return AssistenteLoja()
    if nome == "dnd":
        from assistentes.dnd.assistente import AssistenteDnd
        return AssistenteDnd(usar_documentos_locais)
    raise ValueError(f"assistente desconhecido: {nome}")


def minimos(nome: str, arquivo: Path = RAIZ / "limites.toml") -> dict[str, float]:
    with open(arquivo, "rb") as f:
        return tomllib.load(f)[nome]


def main(argumentos: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--assistente", choices=["loja", "dnd"], required=True)
    p.add_argument("--modelo", required=True, help="nome do modelo no Ollama, ex.: qwen2.5:1.5b")
    p.add_argument("--saida", default="relatorios", help="pasta dos relatórios")
    a = p.parse_args(argumentos)

    if not ollama_disponivel():
        print("Ollama não está rodando. Instale em https://ollama.com e rode: ollama serve", file=sys.stderr)
        return 2

    casos = carregar_casos(RAIZ / "casos" / f"{a.assistente}.csv")
    relatorio = avaliar(criar_assistente(a.assistente), ClienteOllama(a.modelo), casos, minimos(a.assistente))

    saida = Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)
    base = f"{a.assistente}__{a.modelo.replace(':', '_').replace('/', '_')}"
    texto = em_markdown(relatorio)
    (saida / f"{base}.md").write_text(texto, encoding="utf-8")
    (saida / f"{base}.json").write_text(json.dumps(relatorio.como_dicionario(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(texto)
    return 0 if relatorio.aprovado else 1


if __name__ == "__main__":
    sys.exit(main())
