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


class IAQueNaoPodeSerChamada:
    nome = "proibida"

    def responder(self, sistema, mensagem):
        raise AssertionError("a IA não devia ter sido consultada")


@pytest.mark.parametrize(
    "pergunta",
    ["Qual o status do pedido PED-10231?", "Pedido PED-10232, CPF 529.982.247-25. Já foi entregue?", "PED-99999 CPF 529.982.247-25"],
)
def test_pedido_sem_confirmacao_e_respondido_pelo_codigo_sem_ia(loja, pergunta):
    """Na versão 1 a IA inventava a situação de pedidos que nunca viu. Agora ela nem é consultada."""
    resposta = loja.responder(IAQueNaoPodeSerChamada(), pergunta)
    assert "CPF do titular" in resposta


def test_pedido_confirmado_vai_para_a_ia_com_os_dados(loja):
    from conftest import IAFalsa
    ia = IAFalsa(padrao="ok")
    loja.responder(ia, "PED-10231, CPF 529.982.247-25, cadê meu pedido?")
    assert "Em transporte" in ia.chamadas[0][1]


@pytest.mark.parametrize("pergunta", ["Quem ganhou a última Copa do Mundo?", "Qual a capital da Austrália?"])
def test_pergunta_sem_relacao_com_a_loja_e_recusada_pelo_codigo(loja, pergunta):
    assert "só posso ajudar" in loja.responder(IAQueNaoPodeSerChamada(), pergunta)


def test_pergunta_da_loja_vai_para_a_ia(loja):
    from conftest import IAFalsa
    ia = IAFalsa(padrao="7 dias")
    assert loja.responder(ia, "Qual o prazo de troca?") == "7 dias" and len(ia.chamadas) == 1


def test_mensagem_termina_com_a_pergunta_sem_frase_pronta(loja):
    """Regressão da versão 2: uma frase pronta no fim fazia os modelos pequenos recusarem tudo."""
    _, mensagem = loja.montar("Qual o prazo de troca?")
    assert mensagem.endswith("PERGUNTA:\nQual o prazo de troca?")
    assert "Não encontrei essa informação." not in mensagem


def test_pergunta_sobre_pagamento_com_bitcoin_vai_para_a_ia(loja):
    """Falso 'fora do assunto' achado na versão 2: o documento dizia só 'criptomoedas'."""
    assert loja.resposta_direta("Posso pagar com bitcoin?") is None
