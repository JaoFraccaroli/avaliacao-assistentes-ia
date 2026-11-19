"""Relatório da avaliação em Markdown (aparece no resumo do GitHub Actions) e JSON."""
from __future__ import annotations

from motor.avaliacao import Relatorio

NOMES = {"loja": "Loja de celular (Sinal Verde, fictícia)", "dnd": "Assistente do mestre de D&D 5e"}


def _limitar(texto: str, tamanho: int = 280) -> str:
    texto = " ".join(texto.split())
    return texto if len(texto) <= tamanho else texto[: tamanho - 1] + "…"


def em_markdown(relatorio: Relatorio, maximo_de_falhas: int = 15) -> str:
    status = "✅ APROVADO" if relatorio.aprovado else "❌ REPROVADO"
    linhas = [
        f"## {NOMES.get(relatorio.assistente, relatorio.assistente)} · modelo `{relatorio.modelo}` · {status}",
        "",
        f"Acerto geral: **{relatorio.taxa_geral:.0%}** ({sum(c.passou for c in relatorio.casos)} de {len(relatorio.casos)} casos)",
        "",
        "| Critério | Casos | Acertos | Taxa | Mínimo | |",
        "|---|---|---|---|---|---|",
    ]
    for c in relatorio.categorias:
        linhas.append(
            f"| {c.descricao} | {c.total} | {c.acertos} | {c.taxa:.0%} | {c.minimo:.0%} | {'✅' if c.aprovada else '❌'} |"
        )
    falhas = [c for c in relatorio.casos if not c.passou]
    if falhas:
        linhas += ["", f"### Respostas reprovadas ({len(falhas)})", ""]
        for c in falhas[:maximo_de_falhas]:
            linhas += [
                f"- **{c.id}** ({c.categoria}) — {c.pergunta}",
                f"  - Resposta: _{_limitar(c.resposta)}_",
                f"  - Motivo: {'; '.join(c.motivos)}",
            ]
        if len(falhas) > maximo_de_falhas:
            linhas.append(f"- … e mais {len(falhas) - maximo_de_falhas} (veja o JSON completo)")
    tempos = [c.segundos for c in relatorio.casos]
    if tempos:
        linhas += ["", f"Tempo médio por resposta: {sum(tempos) / len(tempos):.1f} s"]
    return "\n".join(linhas) + "\n"
