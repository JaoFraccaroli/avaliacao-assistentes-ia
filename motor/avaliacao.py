"""Roda os casos de teste num assistente e calcula as taxas de acerto por categoria."""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field

from motor.casos import CATEGORIAS, Caso
from motor.cliente_llm import ModeloDeLinguagem
from motor.verificacao import verificar


@dataclass
class ResultadoDoCaso:
    id: str
    categoria: str
    pergunta: str
    resposta: str
    passou: bool
    motivos: list[str]
    segundos: float


@dataclass
class ResultadoDaCategoria:
    categoria: str
    descricao: str
    total: int
    acertos: int
    minimo: float

    @property
    def taxa(self) -> float:
        return self.acertos / self.total if self.total else 0.0

    @property
    def aprovada(self) -> bool:
        return self.taxa >= self.minimo


@dataclass
class Relatorio:
    assistente: str
    modelo: str
    casos: list[ResultadoDoCaso] = field(default_factory=list)
    categorias: list[ResultadoDaCategoria] = field(default_factory=list)

    @property
    def aprovado(self) -> bool:
        return all(c.aprovada for c in self.categorias)

    @property
    def taxa_geral(self) -> float:
        return sum(c.passou for c in self.casos) / len(self.casos) if self.casos else 0.0

    def como_dicionario(self) -> dict:
        return {
            "assistente": self.assistente,
            "modelo": self.modelo,
            "aprovado": self.aprovado,
            "taxa_geral": round(self.taxa_geral, 4),
            "categorias": [
                {**asdict(c), "taxa": round(c.taxa, 4), "aprovada": c.aprovada} for c in self.categorias
            ],
            "casos": [asdict(c) for c in self.casos],
        }


def avaliar(assistente, modelo: ModeloDeLinguagem, casos: list[Caso], minimos: dict[str, float]) -> Relatorio:
    relatorio = Relatorio(assistente=assistente.nome, modelo=modelo.nome)
    for caso in casos:
        inicio = time.perf_counter()
        try:
            resposta = assistente.responder(modelo, caso.pergunta)
            veredito = verificar(resposta, caso.deve_conter, caso.nao_pode_conter)
            passou, motivos = veredito.passou, veredito.motivos
        except (TimeoutError, OSError) as erro:
            # um caso travado conta como falha, mas não derruba a avaliação inteira
            resposta, passou, motivos = "", False, [f"sem resposta: {type(erro).__name__}: {erro}"]
        segundos = time.perf_counter() - inicio
        relatorio.casos.append(
            ResultadoDoCaso(caso.id, caso.categoria, caso.pergunta, resposta, passou, motivos, round(segundos, 2))
        )
    for categoria, descricao in CATEGORIAS.items():
        da_categoria = [c for c in relatorio.casos if c.categoria == categoria]
        if da_categoria:
            if categoria not in minimos:
                raise ValueError(f"falta o mínimo exigido para a categoria '{categoria}'")
            relatorio.categorias.append(
                ResultadoDaCategoria(categoria, descricao, len(da_categoria), sum(c.passou for c in da_categoria), minimos[categoria])
            )
    return relatorio
