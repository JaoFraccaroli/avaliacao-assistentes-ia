"""Conversa com memória curta e tolerância a erros de digitação (sem IA de verdade)."""
from assistentes.dnd.assistente import AssistenteDnd
from assistentes.loja.assistente import PEDIDO_SEM_CONFIRMACAO, AssistenteLoja, carregar_pedidos
from motor.conversa import Conversa, parece_continuacao
from tests.conftest import IAFalsa


def test_erro_de_digitacao_e_abreviacao_ainda_encontram_o_trecho():
    loja = AssistenteLoja()
    assert loja.trechos("qnto tempo de garamtia")[0].titulo == "Garantia"
    assert loja.trechos("trocaa de celualr")[0].titulo == "Troca e arrependimento"
    assert AssistenteDnd().trechos("envenenaddo")[0].titulo.startswith("Envenenado")


def test_correcao_nao_transforma_assunto_de_fora_em_assunto_da_loja():
    loja = AssistenteLoja()
    assert loja.trechos("qual a capital da franca") == []
    ia = IAFalsa()
    assert loja.responder(ia, "receita de bolo de cenoura") == loja.FORA_DO_ASSUNTO
    assert ia.chamadas == []


def test_reconhece_perguntas_de_continuacao():
    assert parece_continuacao("e quanto custa?")
    assert parece_continuacao("ele tem garantia?")
    assert not parece_continuacao("Qual o prazo para trocar um celular?")


def test_continuacao_usa_a_mensagem_anterior_na_busca_e_manda_o_historico():
    ia = IAFalsa(padrao="O Orion Pro 12 custa R$ 2.999.")
    conversa = Conversa(AssistenteDnd(), ia)
    conversa.enviar("Como funciona a magia Bola de Fogo?")
    troca = conversa.enviar("e quanto de dano?")
    assert "Bola de Fogo" in troca.consulta
    _, mensagem = ia.chamadas[-1]
    assert "Bola de Fogo (Fireball)" in mensagem.split("PERGUNTA:")[0]
    assert "CONVERSA ATÉ AGORA" in mensagem and "Cliente: Como funciona a magia Bola de Fogo?" in mensagem
    assert mensagem.endswith("PERGUNTA:\ne quanto de dano?")


def test_pergunta_nova_nao_carrega_o_assunto_anterior():
    conversa = Conversa(AssistenteLoja(), IAFalsa())
    conversa.enviar("Qual o prazo de garantia?")
    assert conversa.enviar("Quais as formas de pagamento disponíveis?").consulta == (
        "Quais as formas de pagamento disponíveis?")


def test_pedido_continua_exigindo_cpf_mesmo_na_conversa():
    ia = IAFalsa()
    conversa = Conversa(AssistenteLoja(), ia)
    assert conversa.enviar("cadê meu pedido PED-10234?").resposta == PEDIDO_SEM_CONFIRMACAO
    assert conversa.enviar("e agora, chega quando?").resposta == PEDIDO_SEM_CONFIRMACAO
    assert ia.chamadas == []


def test_pedido_e_cpf_em_mensagens_seguidas_sao_juntados_e_conferidos():
    pedido = next(iter(carregar_pedidos().values()))
    ia = IAFalsa(padrao="Seu pedido está a caminho.")
    conversa = Conversa(AssistenteLoja(), ia)
    conversa.enviar(f"quero saber do pedido {pedido['numero']}")
    conversa.enviar(f"meu cpf é {pedido['cpf']}")
    assert f"Pedido: {pedido['numero']}" in ia.chamadas[-1][1]


def test_cpf_errado_na_mensagem_seguinte_nao_libera_o_pedido():
    pedido = next(iter(carregar_pedidos().values()))
    ia = IAFalsa()
    conversa = Conversa(AssistenteLoja(), ia)
    conversa.enviar(f"quero saber do pedido {pedido['numero']}")
    assert conversa.enviar("meu cpf é 000.000.000-00").resposta == PEDIDO_SEM_CONFIRMACAO
    assert all(pedido["aparelho"] not in m for _, m in ia.chamadas)


def test_limpar_esquece_a_conversa():
    conversa = Conversa(AssistenteDnd(), IAFalsa())
    conversa.enviar("Como funciona a magia Bola de Fogo?")
    conversa.limpar()
    assert conversa.enviar("e quanto de dano?").consulta == "e quanto de dano?"


def test_linha_de_comando_conversa_e_sai(monkeypatch, capsys):
    import motor.conversar as conversar
    monkeypatch.setattr(conversar, "ollama_disponivel", lambda: True)
    monkeypatch.setattr(conversar, "ClienteOllama", lambda nome: IAFalsa(padrao="Bola de Fogo causa 8d6."))
    falas = iter(["Como funciona a magia Bola de Fogo?", "/sair"])
    assert conversar.main(["--assistente", "dnd"], entrada=lambda _: next(falas)) == 0
    saida = capsys.readouterr().out
    assert "Assistente: Bola de Fogo causa 8d6." in saida and "magias.md > Bola de Fogo" in saida
