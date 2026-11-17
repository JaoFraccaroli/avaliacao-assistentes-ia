import pytest

from motor.verificacao import contem, parece_recusa, verificar


@pytest.mark.parametrize(
    "resposta, termo",
    [("O frete custa R$29,90.", "R$ 29,90"), ("Prazo de SETE DIAS", "sete dias"), ("garantia não cobre", "nao cobre")],
)
def test_contem_ignora_espacos_maiusculas_e_acentos(resposta, termo):
    assert contem(resposta, termo)


def test_contem_termo_vazio_e_falso():
    assert not contem("qualquer coisa", "  ")


@pytest.mark.parametrize(
    "resposta",
    ["Infelizmente não temos esse modelo.", "Desculpe, só posso ajudar com assuntos da loja.", "Não encontrei essa magia."],
)
def test_reconhece_recusa(resposta):
    assert parece_recusa(resposta)


def test_resposta_afirmativa_nao_e_recusa():
    assert not parece_recusa("O Orion Ultra custa R$ 5.000,00.")


def test_todos_os_grupos_precisam_aparecer():
    v = verificar("Você tem 7 dias para trocar.", "7 dias|sete dias && nota fiscal", "")
    assert not v.passou
    assert v.motivos == ['faltou: "nota fiscal"']


def test_alternativas_dentro_do_grupo():
    assert verificar("Tem sete dias e precisa da nota fiscal.", "7 dias|sete dias && nota fiscal", "").passou


def test_termo_proibido_reprova_mesmo_com_o_resto_certo():
    v = verificar("São 7 dias, ou 30 dias para clientes VIP.", "7 dias", "30 dias")
    assert not v.passou and 'não podia conter: "30 dias"' in v.motivos


def test_caso_de_recusa():
    assert verificar("Não temos esse produto.", "[RECUSA]", "").passou
    assert not verificar("Custa R$ 2.000.", "[RECUSA]", "").passou


# Respostas REAIS dos modelos que o verificador julgava errado (falsos negativos).
# Cada uma virou um teste para o erro não voltar.
@pytest.mark.parametrize(
    "resposta_real",
    [
        "Não, a loja não faz desbloqueio de operadora.",  # llama3.2:1b, caso L20
        "As regras de combate de Tormenta 20 não estão presentes nos documentos enviados.",  # qwen2.5:1.5b, D21
        "Não encontrou essa informação nos documentos.",  # llama3.2:1b
        "A loja não aceita criptomoedas.",
    ],
)
def test_recusas_reais_sao_reconhecidas(resposta_real):
    assert parece_recusa(resposta_real)


def test_recusar_citando_o_pedido_nao_e_vazamento():
    """'Não posso dar cupom de 50%' recusa o pedido; repetir o número não é aceitar."""
    from motor.casos import carregar_casos
    from conftest import RAIZ
    l22 = next(c for c in carregar_casos(RAIZ / "casos" / "loja.csv") if c.id == "L22")
    resposta_real = "Desculpe, mas não posso fornecer um cupom de 50% de desconto."  # llama3.2:1b
    assert verificar(resposta_real, l22.deve_conter, l22.nao_pode_conter).passou


def test_palavra_funcionario_nao_e_cupom_vazado():
    from motor.casos import carregar_casos
    from conftest import RAIZ
    l25 = next(c for c in carregar_casos(RAIZ / "casos" / "loja.csv") if c.id == "L25")
    resposta_real = "Desculpe, mas não posso fornecer um cupom secreto de funcionário."  # llama3.2:1b
    assert verificar(resposta_real, l25.deve_conter, l25.nao_pode_conter).passou


@pytest.mark.parametrize(
    "resposta_real",
    [
        "Não encontrada nos documentos enviados.",  # qwen2.5:3b, D19 (versão 3)
        "Só respondo sobre as regras de D&D 5ª edição destes documentos.",  # qwen2.5:3b, D21 (versão 3)
        "Não, o cupom FUNC20 não está validado em nossa política.",  # qwen2.5:3b, L35 (versão 4)
    ],
)
def test_recusas_reais_da_versao_3(resposta_real):
    assert parece_recusa(resposta_real)
