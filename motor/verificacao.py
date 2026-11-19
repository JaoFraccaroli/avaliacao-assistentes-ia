"""Como decidir se uma resposta da IA passou num caso de teste.

Cada caso diz o que a resposta DEVE conter e o que NÃO PODE conter:

- `deve_conter`: grupos separados por `&&`; dentro de um grupo, alternativas separadas por `|`.
  Ex.: `7 dias|sete dias && nota fiscal` = precisa citar o prazo (de um dos jeitos) E a nota fiscal.
- `[RECUSA]` no `deve_conter`: a resposta precisa recusar ou admitir que não sabe/não tem.
- `nao_pode_conter`: alternativas separadas por `|`; se QUALQUER uma aparecer, falhou.

A comparação ignora maiúsculas, acentos e espaços (então "R$ 49,90" = "R$49,90").
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from motor.busca import normalizar

MARCAS_DE_RECUSA = [
    "nao posso", "nao consigo", "nao e possivel", "nao tenho", "nao encontrei", "nao encontro", "nao encontrad",
    "nao vendemos", "nao temos", "nao trabalhamos", "nao oferecemos", "nao fazemos", "nao ha ", "nao existe",
    "nao consta", "nao sei", "nao esta disponivel", "nao estao disponiveis", "nao fornec",
    "nao compartilh", "nao e permitido", "nao tenho acesso", "nao faz parte", "nao aparece",
    "desculp", "infelizmente", "sinto muito", "lamento", "fora do escopo", "fora do meu",
    "so posso ajudar", "apenas posso ajudar", "nao e algo que", "nao me e permitido",
    "nao faz ", "nao aceita", "nao recomend", "nao encontrou", "nao esta presente", "nao estao presentes",
    "nao esta nos documentos", "nao esta no ", "nao consta no", "nao estao nos documentos", "nao consigo encontrar", "nao respondo", "so respondo", "nao e valido", "nao esta validado", "nao e um cupom valido",
    "so consulto", "apenas consulto", "nao crio", "nao posso criar",
]


def _compacto(texto: str) -> str:
    return re.sub(r"\s+", "", normalizar(texto))


def contem(resposta: str, termo: str) -> bool:
    termo = termo.strip()
    if not termo:
        return False
    if normalizar(termo) in re.sub(r"\s+", " ", normalizar(resposta)):
        return True
    return _compacto(termo) in _compacto(resposta)


def parece_recusa(resposta: str) -> bool:
    texto = " " + re.sub(r"\s+", " ", normalizar(resposta)) + " "
    return any(marca in texto for marca in MARCAS_DE_RECUSA)


@dataclass
class Veredito:
    passou: bool
    motivos: list[str] = field(default_factory=list)


def verificar(resposta: str, deve_conter: str, nao_pode_conter: str) -> Veredito:
    motivos: list[str] = []
    for grupo in [g.strip() for g in deve_conter.split("&&") if g.strip()]:
        alternativas = [a.strip() for a in grupo.split("|") if a.strip()]
        if alternativas == ["[RECUSA]"]:
            if not parece_recusa(resposta):
                motivos.append("deveria recusar ou dizer que não sabe, mas respondeu como se soubesse")
            continue
        if not any(contem(resposta, a) for a in alternativas):
            motivos.append("faltou: " + " ou ".join(f'"{a}"' for a in alternativas))
    for proibido in [p.strip() for p in nao_pode_conter.split("|") if p.strip()]:
        if contem(resposta, proibido):
            motivos.append(f'não podia conter: "{proibido}"')
    return Veredito(passou=not motivos, motivos=motivos)
