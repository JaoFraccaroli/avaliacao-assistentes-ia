"""A proteção dos pedidos é feita por CÓDIGO, não pela IA. Estes testes provam isso."""
import pytest

from assistentes.loja.assistente import AssistenteLoja, carregar_pedidos
from conftest import RAIZ
from motor.casos import carregar_casos

PEDIDOS = carregar_pedidos()


@pytest.fixture
def loja():
    return AssistenteLoja()


def test_pergunta_sem_pedido_nao_acrescenta_nada(loja):
    assert loja.contexto_extra("Qual o prazo de troca?") == ""


def test_pedido_sem_cpf_nao_revela_dados(loja):
    extra = loja.contexto_extra("Status do PED-10231?")
    assert "NÃO foi confirmada" in extra
    assert "Em transporte" not in extra and "Orion" not in extra


def test_pedido_com_cpf_correto_revela_so_aquele_pedido(loja):
    extra = loja.contexto_extra("PED-10231, CPF 529.982.247-25")
    assert "Em transporte" in extra and "Orion A35" in extra
    assert "Orion Pro 12" not in extra and "Orion Lite" not in extra


def test_cpf_sem_pontuacao_tambem_vale(loja):
    assert "Em transporte" in loja.contexto_extra("pedido ped 10231 cpf 52998224725")


def test_cpf_de_outra_pessoa_nao_libera(loja):
    extra = loja.contexto_extra("PED-10232, CPF 529.982.247-25")
    assert "NÃO foi confirmada" in extra and "Entregue" not in extra


def test_pedido_inexistente_nao_libera(loja):
    assert "NÃO foi confirmada" in loja.contexto_extra("PED-99999 CPF 529.982.247-25")


def test_nome_e_cpf_de_clientes_nunca_vao_para_a_ia(loja):
    """Nome e CPF dos clientes não aparecem na mensagem enviada à IA em nenhum caso de teste."""
    for caso in carregar_casos(RAIZ / "casos" / "loja.csv"):
        _, mensagem = loja.montar(caso.pergunta)
        for pedido in PEDIDOS.values():
            assert pedido["nome"] not in mensagem
            assert pedido["cpf"] not in mensagem.split("PERGUNTA:")[0], caso.id


def test_no_maximo_um_pedido_por_mensagem(loja):
    for caso in carregar_casos(RAIZ / "casos" / "loja.csv"):
        _, mensagem = loja.montar(caso.pergunta)
        assert sum(p["numero"] in mensagem.split("PERGUNTA:")[0] for p in PEDIDOS.values()) <= 1
