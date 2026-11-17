"""Junta os relatórios JSON de vários modelos numa tabela de comparação (Markdown).

    python -m motor.comparar relatorios/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from motor.casos import CATEGORIAS
from motor.relatorio import NOMES


def comparar(pasta: Path) -> str:
    relatorios = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(pasta).rglob("*.json"))]
    if not relatorios:
        return "Nenhum relatório encontrado.\n"
    linhas = ["# Comparação entre modelos", ""]
    for assistente in sorted({r["assistente"] for r in relatorios}):
        doa = [r for r in relatorios if r["assistente"] == assistente]
        modelos = [r["modelo"] for r in doa]
        linhas += [f"## {NOMES.get(assistente, assistente)}", "", "| Critério | " + " | ".join(f"`{m}`" for m in modelos) + " |",
                   "|---|" + "---|" * len(modelos)]
        for categoria, descricao in CATEGORIAS.items():
            celulas = []
            for r in doa:
                c = next((c for c in r["categorias"] if c["categoria"] == categoria), None)
                celulas.append("—" if c is None else f"{c['taxa']:.0%} {'✅' if c['aprovada'] else '❌'}")
            if any(x != "—" for x in celulas):
                linhas.append(f"| {descricao} | " + " | ".join(celulas) + " |")
        linhas.append("| **Geral** | " + " | ".join(f"**{r['taxa_geral']:.0%}**" for r in doa) + " |")
        linhas.append("| Resultado | " + " | ".join("✅ aprovado" if r["aprovado"] else "❌ reprovado" for r in doa) + " |")
        linhas.append("")
    return "\n".join(linhas)


if __name__ == "__main__":
    print(comparar(Path(sys.argv[1] if len(sys.argv) > 1 else "relatorios")))
