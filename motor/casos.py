"""Leitura dos casos de teste (planilhas CSV separadas por ponto e vírgula)."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

CATEGORIAS = {
    "fatos": "Acerta fatos dos documentos",
    "nao_inventa": "Não inventa o que não está nos documentos",
    "recusa": "Recusa o que deve recusar",
    "manipulacao": "Resiste a tentativas de manipulação",
    "privacidade": "Protege dados de clientes",
    "escopo": "Mantém-se no assunto",
}


@dataclass(frozen=True)
class Caso:
    id: str
    categoria: str
    pergunta: str
    deve_conter: str
    nao_pode_conter: str
    observacao: str = ""


def carregar_casos(arquivo: Path) -> list[Caso]:
    casos: list[Caso] = []
    ids: set[str] = set()
    with open(arquivo, encoding="utf-8", newline="") as f:
        for numero, linha in enumerate(csv.DictReader(f, delimiter=";"), start=2):
            caso = Caso(**{k: (v or "").strip() for k, v in linha.items()})
            if caso.categoria not in CATEGORIAS:
                raise ValueError(f"{arquivo.name}, linha {numero}: categoria desconhecida '{caso.categoria}'")
            if not caso.pergunta or not caso.deve_conter and not caso.nao_pode_conter:
                raise ValueError(f"{arquivo.name}, linha {numero}: caso sem pergunta ou sem critério")
            if caso.id in ids:
                raise ValueError(f"{arquivo.name}, linha {numero}: id repetido '{caso.id}'")
            ids.add(caso.id)
            casos.append(caso)
    return casos
