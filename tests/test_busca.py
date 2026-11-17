import pytest

from motor.busca import Buscador, Trecho, dividir_em_trechos, normalizar, palavras
from assistentes.loja.assistente import AssistenteLoja
from assistentes.dnd.assistente import AssistenteDnd


def test_normalizar_tira_acentos_e_maiusculas():
    assert normalizar("Garantia ÁGUA Ação") == "garantia agua acao"


def test_palavras_ignora_palavras_vazias():
    assert palavras("Qual o prazo de troca da loja?") == ["prazo", "troca", "loja"]


def test_radicais_juntam_variacoes():
    from motor.busca import radicais
    assert radicais("devolver devolução") == ["devol", "devol"]
    assert radicais("acerta acertos 2d10") == ["acert", "acert", "2d10"]


def test_dividir_em_trechos_pelos_titulos():
    texto = "# Título\nintro\n## Parte A\nconteúdo A\n## Parte B\nconteúdo B"
    trechos = dividir_em_trechos("doc.md", texto)
    assert [t.titulo for t in trechos] == ["", "Parte A", "Parte B"]
    assert "conteúdo B" in trechos[-1].texto


def test_buscador_sem_trechos_da_erro():
    with pytest.raises(ValueError):
        Buscador([])


def test_pergunta_sem_relacao_nao_traz_nada():
    b = Buscador([Trecho("x", "Frete", "o frete custa 10")])
    assert b.buscar("zebra marciana") == []


@pytest.mark.parametrize(
    "pergunta, titulo_esperado",
    [
        ("Quanto custa o frete?", "Frete e entrega"),
        ("Posso devolver o celular?", "Troca e arrependimento"),
        ("Quanto custa o Orion A15?", "Orion A15"),
        ("Meu Wi-Fi não conecta", "Wi-Fi não conecta"),
        ("Qual o desconto no Pix?", "Formas de pagamento"),
        ("Como vejo meu pedido?", "Acompanhamento de pedidos"),
    ],
)
def test_busca_da_loja_entrega_o_trecho_certo_para_a_ia(pergunta, titulo_esperado):
    # a IA recebe os 3 melhores trechos; o certo precisa estar entre eles
    assert titulo_esperado in [t.titulo for t in AssistenteLoja().trechos(pergunta)]


@pytest.mark.parametrize(
    "pergunta, titulo_esperado",
    [
        ("Quanto dano causa a Bola de Fogo?", "Bola de Fogo (Fireball)"),
        ("Como funciona a vantagem?", "Vantagem e desvantagem"),
        ("O que faz a condição envenenado?", "Envenenado (Poisoned)"),
        ("Quanto tempo dura o descanso longo?", "Descanso longo"),
        ("Mísseis Mágicos acerta sempre?", "Mísseis Mágicos (Magic Missile)"),
    ],
)
def test_busca_do_dnd_poe_o_trecho_certo_em_primeiro(pergunta, titulo_esperado):
    assert AssistenteDnd().trechos(pergunta)[0].titulo == titulo_esperado
