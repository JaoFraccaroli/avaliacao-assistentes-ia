"""Busca nos documentos (o "R" do RAG) com BM25, sem bibliotecas externas.

Os documentos são divididos em trechos pelos títulos `## `. Para cada pergunta,
os trechos mais parecidos vão para a IA como contexto.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

PALAVRAS_VAZIAS = set(
    """a o as os um uma uns umas de do da dos das no na nos nas em por para pra com sem
    e ou que qual quais quanto quantos quanta quantas como quando onde se ao aos à às é
    ser são foi tem ter há eu voce você vocês meu minha seu sua isso esse essa este esta
    me te lhe mais menos muito pode posso tenho the of""".split()
)


def normalizar(texto: str) -> str:
    """minúsculas e sem acentos: 'Garantia' e 'garantía' viram a mesma palavra"""
    sem_acento = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in sem_acento if not unicodedata.combining(c))


def radical(palavra: str, tamanho: int = 5) -> str:
    """Corta a palavra nas 5 primeiras letras: 'devolver' e 'devolução' viram 'devol'.
    É um jeito simples e conhecido de juntar variações em português."""
    return palavra if palavra.isdigit() else palavra[:tamanho]


def palavras(texto: str) -> list[str]:
    return [p for p in re.findall(r"[a-z0-9]+", normalizar(texto)) if p not in PALAVRAS_VAZIAS and len(p) > 1]


def radicais(texto: str) -> list[str]:
    return [radical(p) for p in palavras(texto)]


@dataclass(frozen=True)
class Trecho:
    fonte: str
    titulo: str
    texto: str


def dividir_em_trechos(nome: str, conteudo: str) -> list[Trecho]:
    trechos: list[Trecho] = []
    titulo, linhas = "", []
    for linha in conteudo.splitlines():
        if linha.startswith("## "):
            if linhas and "".join(linhas).strip():
                trechos.append(Trecho(nome, titulo, "\n".join(linhas).strip()))
            titulo, linhas = linha[3:].strip(), [linha]
        else:
            linhas.append(linha)
    if linhas and "".join(linhas).strip():
        trechos.append(Trecho(nome, titulo, "\n".join(linhas).strip()))
    return trechos


class Buscador:
    def __init__(self, trechos: list[Trecho], k1: float = 1.5, b: float = 0.75):
        if not trechos:
            raise ValueError("é preciso pelo menos um trecho para buscar")
        self.trechos = trechos
        self.k1, self.b = k1, b
        # o título conta duas vezes: costuma ser o melhor resumo do trecho
        self._termos = [Counter(radicais(t.titulo) * 2 + radicais(t.texto)) for t in trechos]
        # nome do trecho sem a parte em inglês: "Bola de Fogo (Fireball)" -> "bola de fogo"
        self._nomes = [normalizar(re.sub(r"\(.*?\)", "", t.titulo)).strip() for t in trechos]
        self._tamanhos = [sum(c.values()) for c in self._termos]
        self._media = sum(self._tamanhos) / len(self._tamanhos)
        n = len(trechos)
        frequencia_doc = Counter(p for c in self._termos for p in c)
        self._idf = {p: math.log(1 + (n - f + 0.5) / (f + 0.5)) for p, f in frequencia_doc.items()}

    @classmethod
    def da_pasta(cls, pasta: Path) -> "Buscador":
        trechos: list[Trecho] = []
        for arquivo in sorted(Path(pasta).glob("*.md")):
            trechos += dividir_em_trechos(arquivo.name, arquivo.read_text(encoding="utf-8"))
        return cls(trechos)

    def pontuar(self, pergunta: str) -> list[float]:
        termos = radicais(pergunta)
        pergunta_normalizada = " ".join(re.findall(r"[a-z0-9]+", normalizar(pergunta)))
        notas = []
        for contagem, tamanho, nome in zip(self._termos, self._tamanhos, self._nomes):
            nota = 0.0
            for termo in termos:
                f = contagem.get(termo, 0)
                if f:
                    nota += self._idf[termo] * f * (self.k1 + 1) / (
                        f + self.k1 * (1 - self.b + self.b * tamanho / self._media)
                    )
            # bônus quando a pergunta cita o nome exato do trecho (ex.: "Mísseis Mágicos")
            nome_limpo = " ".join(re.findall(r"[a-z0-9]+", nome))
            if nota and len(nome_limpo) > 3 and f" {nome_limpo} " in f" {pergunta_normalizada} ":
                nota *= 2
            notas.append(nota)
        return notas

    def buscar(self, pergunta: str, quantidade: int = 3) -> list[Trecho]:
        notas = self.pontuar(pergunta)
        ordem = sorted(range(len(notas)), key=lambda i: notas[i], reverse=True)
        return [self.trechos[i] for i in ordem[:quantidade] if notas[i] > 0]
