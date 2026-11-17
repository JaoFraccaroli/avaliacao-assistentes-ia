"""A busca entrega à IA o trecho com a resposta? Se não entregar, nem um modelo perfeito acertaria."""
import pytest

from assistentes.dnd.assistente import AssistenteDnd
from assistentes.loja.assistente import AssistenteLoja
from conftest import RAIZ
from motor.casos import carregar_casos
from motor.verificacao import contem

# Casos cuja resposta exige um cálculo (não aparece escrita no documento)
PRECISAM_DE_CALCULO = {"D16"}

ASSISTENTES = {"loja": AssistenteLoja(), "dnd": AssistenteDnd()}


def casos_de_fatos():
    for nome in ASSISTENTES:
        for caso in carregar_casos(RAIZ / "casos" / f"{nome}.csv"):
            if caso.categoria == "fatos" and caso.id not in PRECISAM_DE_CALCULO:
                yield pytest.param(nome, caso, id=caso.id)


@pytest.mark.parametrize("nome, caso", list(casos_de_fatos()))
def test_contexto_enviado_contem_a_resposta(nome, caso):
    _, mensagem = ASSISTENTES[nome].montar(caso.pergunta)
    contexto = mensagem.split("PERGUNTA:")[0]
    for grupo in caso.deve_conter.split("&&"):
        alternativas = [a.strip() for a in grupo.split("|") if a.strip()]
        assert any(contem(contexto, a) for a in alternativas), f"{caso.id}: o contexto não traz {alternativas}"


def test_creditos_do_srd_no_readme():
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    assert "System Reference Document 5.1" in readme and "CC-BY-4.0" in readme.replace(" ", "-")
