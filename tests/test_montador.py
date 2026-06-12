"""
Gate G5 — saída do montador deve ser idêntica às notas golden
(caracter a caracter, UTF-8).

Notas golden em tests/golden/ representam o texto correto para
IPCA abr/2026 e IPCA-15 mai/2026. Qualquer mudança no montador
que altere o texto exige atualização explícita das notas golden.
"""
import difflib
from pathlib import Path

import pytest

from fontes.modelo import ItemInflacao, ResultadoInflacao
from nucleo.montador import compor_nota, ConfigNota

GOLDEN_DIR = Path(__file__).parent / "golden"


def _golden(nome: str) -> str:
    return (GOLDEN_DIR / nome).read_text(encoding="utf-8")


def _diff(obtido: str, esperado: str) -> str:
    """Gera diff legivel entre dois textos para mensagem de falha."""
    linhas_o = obtido.splitlines(keepends=True)
    linhas_e = esperado.splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(linhas_e, linhas_o, fromfile="golden", tofile="obtido")
    )


# ---------------------------------------------------------------------------
# Testes de integracao (chamam APIs reais)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_gate_g5_ipca_abril2026():
    """Gate G5 — IPCA abr/2026: texto identico ao golden."""
    from fontes.ibge import buscar_resultado
    from fontes.bcb import enriquecer

    esperado = _golden("ipca_abril2026.txt")
    r = buscar_resultado("IPCA", "202604")
    enriquecer(r)
    obtido = compor_nota(r)
    assert obtido == esperado, "\n" + _diff(obtido, esperado)


@pytest.mark.integration
def test_gate_g5_ipca15_maio2026():
    """Gate G5 — IPCA-15 mai/2026: texto identico ao golden."""
    from fontes.ibge import buscar_resultado
    from fontes.bcb import enriquecer

    esperado = _golden("ipca15_maio2026.txt")
    r = buscar_resultado("IPCA-15", "202605")
    enriquecer(r)
    obtido = compor_nota(r)
    assert obtido == esperado, "\n" + _diff(obtido, esperado)


# ---------------------------------------------------------------------------
# Testes unitarios (sem API — validam logica do montador)
# ---------------------------------------------------------------------------

def _resultado_simples(
    indicador: str = "IPCA",
    mes_ref: str = "202604",
    mes_ant: str = "202603",
    var: float = 0.67,
    var_ant: float = 0.88,
    acum: float = 4.39,
    acum_ant: float = 4.14,
    difusao: float = 65.25,
    difusao_anterior: float = 67.37,
    nucleo_12m: float = 4.39,
    nucleo_ant: float = 4.44,
    grupos=None,
    subitens=None,
) -> ResultadoInflacao:
    if grupos is None:
        grupos = [
            ItemInflacao(7170, "1.Alimentação e bebidas",   1, var,  21.45, "fixture"),
            ItemInflacao(7660, "6.Saúde e cuidados pessoais", 1, 1.16, 13.60, "fixture"),
            ItemInflacao(7445, "2.Habitação",               1, 0.63, 15.20, "fixture"),
        ]
        grupos.sort(key=lambda x: x.impacto, reverse=True)
    if subitens is None:
        subitens = [ItemInflacao(999, "gasolina", 4, 1.86, 5.28, "fixture")]
    return ResultadoInflacao(
        indicador=indicador, mes_ref=mes_ref, mes_ant=mes_ant,
        variacao_mensal=var, variacao_mensal_anterior=var_ant,
        acum_12m=acum, acum_12m_anterior=acum_ant,
        grupos=grupos, subitens=subitens,
        difusao=difusao, difusao_anterior=difusao_anterior,
        nucleo_12m=nucleo_12m, nucleo_12m_anterior=nucleo_ant,
    )


def test_sem_nucleo_nao_aparece_bloco():
    """Quando nucleo_12m e None, o bloco de nucleo nao e incluido."""
    r = _resultado_simples(nucleo_12m=None, nucleo_ant=None)
    nota = compor_nota(r)
    assert "\U0001f4c9" not in nota  # 📉 nao aparece
    assert "núcleo" not in nota


def test_sem_nucleo_nota_completa():
    """Nota sem nucleo ainda tem titulo, resultado, explicacao, acumulado, difusao."""
    r = _resultado_simples(nucleo_12m=None, nucleo_ant=None)
    nota = compor_nota(r)
    assert "*IPCA ABRIL/2026*" in nota
    assert "*alta de 0,67%*" in nota
    assert "*4,39%*" in nota          # acumulado
    assert "65,3%" in nota            # difusao


def test_ipca15_sem_nucleo_sem_difusao_anterior():
    """IPCA-15: sem nucleo, sem difusao_anterior — nota valida sem erros."""
    r = _resultado_simples(
        indicador="IPCA-15",
        nucleo_12m=None, nucleo_ant=None,
        difusao=65.1, difusao_anterior=None,
    )
    nota = compor_nota(r)
    assert "*IPCA-15 ABRIL/2026*" in nota
    assert "núcleo" not in nota
    assert "65,1%" in nota
    # sem comparacao de difusao anterior
    assert "abaixo do registrado" not in nota
    assert "acima do registrado" not in nota


def test_formato_numerico_virgula():
    """Numeros devem usar virgula decimal (padrao pt-BR)."""
    r = _resultado_simples()
    nota = compor_nota(r)
    assert "0,67%" in nota
    assert "0.67%" not in nota


def test_rounding_half_up():
    """_fmt usa HALF_UP: 65,25 -> 65,3 (nao 65,2 banker's rounding)."""
    from nucleo.montador import _fmt
    assert _fmt(65.25, decimais=1) == "65,3"
    assert _fmt(0.085, decimais=2) == "0,09"
    assert _fmt(4.3896, decimais=2) == "4,39"


def test_dois_grupos_relevantes():
    """Com 2 grupos acima do threshold, usa forma singular 'destaca-se'."""
    grupos = [
        ItemInflacao(1, "1.Grupo A", 1, 2.0, 15.0, "x"),   # impacto 0.30
        ItemInflacao(2, "2.Grupo B", 1, 1.0, 10.0, "x"),   # impacto 0.10
    ]
    grupos.sort(key=lambda x: x.impacto, reverse=True)
    r = _resultado_simples(grupos=grupos, subitens=[])
    nota = compor_nota(r)
    assert "destaca-se o grupo Grupo B" in nota
    assert "destacam-se" not in nota


def test_tres_grupos_usa_plural():
    """Com 3 grupos, usa 'destacam-se os grupos'."""
    r = _resultado_simples()
    nota = compor_nota(r)
    assert "destacam-se os grupos" in nota


def test_projecoes_aparecem_quando_presentes():
    """Linha de projecoes e incluida quando ambas projecao_cni e focus sao informadas."""
    r = _resultado_simples()
    r.projecao_cni = 0.65
    r.projecao_focus = 0.70
    nota = compor_nota(r)
    assert "projeção da CNI" in nota
    assert "Focus" in nota


def test_projecoes_omitidas_sem_dados():
    """Linha de projecoes e omitida quando projecao_cni/focus sao None."""
    r = _resultado_simples()
    r.projecao_cni = None
    r.projecao_focus = None
    nota = compor_nota(r)
    assert "projeção da CNI" not in nota


def test_assinatura_econ():
    r = _resultado_simples()
    nota = compor_nota(r)
    assert "Superintendência de Economia (ECON)" in nota


def test_assinatura_siecon():
    r = _resultado_simples()
    cfg = ConfigNota(assinatura="SIECON")
    nota = compor_nota(r, cfg)
    assert "Superintendência de Inteligência Econômica (SIECON)" in nota


def test_link_ibge_incluido():
    r = _resultado_simples()
    r.url_ibge = "https://ibge.gov.br/nota-exemplo"
    nota = compor_nota(r)
    assert "Notícia: https://ibge.gov.br/nota-exemplo" in nota


def test_link_ibge_omitido_quando_none():
    r = _resultado_simples()
    r.url_ibge = None
    nota = compor_nota(r)
    assert "Notícia:" not in nota


def test_artigo_gasolina():
    """'gasolina' e feminina — deve aparecer 'da gasolina'."""
    r = _resultado_simples(
        subitens=[ItemInflacao(1, "gasolina", 4, 1.86, 5.28, "x")]
    )
    nota = compor_nota(r)
    assert "da *gasolina*" in nota


def test_artigo_energia():
    """'energia elétrica residencial' e feminina — deve aparecer 'da energia'."""
    r = _resultado_simples(
        subitens=[ItemInflacao(1, "energia elétrica residencial", 4, 2.16, 3.93, "x")]
    )
    nota = compor_nota(r)
    assert "da *energia elétrica residencial*" in nota
