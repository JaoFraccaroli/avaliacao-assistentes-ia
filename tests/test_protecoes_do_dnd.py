"""Proteções do mestre de D&D feitas por código (achadas na avaliação da versão 3)."""
import pytest

from assistentes.dnd.assistente import AssistenteDnd


@pytest.fixture(scope="module")
def dnd():
    return AssistenteDnd()


@pytest.mark.parametrize(
    "pergunta, nome",
    [
        ("Quanto dano causa a magia Tempestade de Meteoros Arco-Íris?", "Tempestade de Meteoros Arco-Íris"),
        ("Qual o dano da magia Desintegrar?", "Desintegrar"),
        ("Quais são as regras da condição Congelado?", "Congelado"),
    ],
)
def test_nome_que_nao_esta_nos_documentos_e_barrado(dnd, pergunta, nome):
    assert dnd.nome_desconhecido(pergunta) == nome
    assert "Não encontrei" in dnd.resposta_direta(pergunta)


@pytest.mark.parametrize(
    "pergunta",
    [
        "Quanto dano causa a magia Bola de Fogo?",
        "Como funciona a magia Fireball?",
        "O que faz a condição Envenenado?",
        "Quanto dano causa o truque Raio de Fogo?",
        "Quanto dano causa a Bola de Fogo?",  # sem a palavra "magia": vai para a IA
    ],
)
def test_nomes_que_existem_vao_para_a_ia(dnd, pergunta):
    assert dnd.nome_desconhecido(pergunta) is None
    assert dnd.resposta_direta(pergunta) is None


@pytest.mark.parametrize("pergunta", ["Como funciona a magia Bola de Fogo em Pathfinder?", "Quais as regras de combate de Tormenta 20?"])
def test_outros_sistemas_sao_recusados_pelo_codigo(dnd, pergunta):
    assert "Só respondo sobre as regras de Dungeons & Dragons" in dnd.resposta_direta(pergunta)


def test_instrucoes_mandam_corrigir_premissa_falsa(dnd):
    assert "diga que não é assim" in dnd.instrucoes


@pytest.mark.parametrize("pergunta", [
    "Crie um NPC taverneiro novo para a minha campanha.",
    "Invente uma aventura curta para o meu grupo de nível 1.",
    "me dá ideias de encontro pra sessão de sábado",
    "escreva a história do meu personagem",
])
def test_pedido_de_criacao_e_respondido_pelo_codigo_sem_ia(dnd, pergunta):
    from assistentes.dnd.assistente import NAO_CRIO
    from tests.conftest import IAFalsa
    ia = IAFalsa()
    assert dnd.responder(ia, pergunta) == NAO_CRIO
    assert ia.chamadas == []


@pytest.mark.parametrize("pergunta", [
    "Como crio um personagem?",
    "Quais os passos para criar um PdM rápido?",
    "Como funciona a magia Bola de Fogo?",
])
def test_pergunta_sobre_criacao_continua_indo_para_a_busca(dnd, pergunta):
    from assistentes.dnd.assistente import pede_criacao
    assert not pede_criacao(pergunta)
