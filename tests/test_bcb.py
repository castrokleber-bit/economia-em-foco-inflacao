"""
Gates G3 e G4 — valida fontes BCB.

G3: difusao IPCA abr/2026 = 65,3% (SGS 21379)
    media nucleos 12m abr/2026 = 4,38% (±0,01 p.p.) — combo MS+EX0+EX3+DP

G4: difusao IPCA-15 mai/2026 = 65,1% (calculada dos subitens IBGE)
"""
import pytest
from fontes.bcb import media_nucleos_12m, enriquecer, _buscar_valor_mes, _SGS_DIFUSAO_IPCA
from fontes.ibge import buscar_resultado
from nucleo.impacto import calcular_difusao


@pytest.mark.integration
def test_gate_g3_difusao_ipca_abril2026():
    """Difusão IPCA abr/2026 via SGS 21379 deve ser ~65,3%."""
    val = _buscar_valor_mes(_SGS_DIFUSAO_IPCA, "202604")
    print(f"\nDifusao IPCA abr/2026 (SGS 21379): {val}")
    assert val is not None, "Serie SGS 21379 nao retornou valor"
    assert val == pytest.approx(65.3, abs=0.1), (
        f"Difusao esperada ~65.3%, obtida {val}%"
    )


@pytest.mark.integration
def test_gate_g3_media_nucleos_abril2026():
    """Media dos nucleos 12m abr/2026 deve ser 4,38% (±0,01 p.p.)."""
    media = media_nucleos_12m("202604")
    print(f"\nMedia nucleos 12m abr/2026 (MS+EX0+EX3+DP): {media:.4f}%")
    assert media is not None, "Nenhum nucleo retornou valor"
    assert media == pytest.approx(4.38, abs=0.01), (
        f"Media esperada ~4.38%, obtida {media:.4f}%"
    )


@pytest.mark.integration
def test_gate_g4_difusao_ipca15_maio2026():
    """Difusao IPCA-15 mai/2026 calculada dos subitens IBGE deve ser ~65,1%."""
    r = buscar_resultado("IPCA-15", "202605")
    difusao = calcular_difusao(r.subitens, nivel_min=4)
    print(f"\nDifusao IPCA-15 mai/2026 (IBGE subitens nivel>=4): {difusao:.2f}%")
    assert difusao is not None
    assert difusao == pytest.approx(65.1, abs=0.1), (
        f"Difusao esperada ~65.1%, obtida {difusao:.2f}%"
    )


@pytest.mark.integration
def test_enriquecer_ipca_completo():
    """enriquecer() preenche todos os campos BCB do IPCA abr/2026."""
    r = buscar_resultado("IPCA", "202604")
    enriquecer(r)

    print(f"\nIPCA abr/2026 apos enriquecer():")
    print(f"  difusao:            {r.difusao}")
    print(f"  difusao_anterior:   {r.difusao_anterior}")
    print(f"  nucleo_12m:         {r.nucleo_12m:.4f}%" if r.nucleo_12m else "  nucleo_12m: None")
    print(f"  nucleo_12m_ant:     {r.nucleo_12m_anterior:.4f}%" if r.nucleo_12m_anterior else "  nucleo_12m_ant: None")

    assert r.difusao is not None
    assert r.difusao_anterior is not None
    assert r.nucleo_12m is not None
    assert r.nucleo_12m == pytest.approx(4.38, abs=0.01)


@pytest.mark.integration
def test_enriquecer_ipca15_difusao():
    """enriquecer() calcula difusao para IPCA-15; nucleo fica None."""
    r = buscar_resultado("IPCA-15", "202605")
    enriquecer(r)

    print(f"\nIPCA-15 mai/2026 apos enriquecer():")
    print(f"  difusao:   {r.difusao}")
    print(f"  nucleo:    {r.nucleo_12m}")

    assert r.difusao is not None
    assert r.difusao == pytest.approx(65.1, abs=0.1)
    assert r.nucleo_12m is None


@pytest.mark.integration
def test_enriquecer_mes_sem_dado_retorna_none():
    """Para mes futuro inexistente, enriquecer() deixa campos None sem excepcao."""
    r = buscar_resultado("IPCA", "202604")
    r.mes_ref = "209901"  # data no futuro distante
    r.mes_ant = "208912"
    enriquecer(r)  # nao deve levantar excecao
    # campos ficam None silenciosamente
    assert r.difusao is None
    assert r.nucleo_12m is None


# ---------------------------------------------------------------------------
# Regressao: media dos nucleos e tudo-ou-nada (nao faz rede)
# ---------------------------------------------------------------------------

def test_media_nucleos_retorna_none_se_uma_serie_falhar(monkeypatch):
    """
    Uma serie que nao responde nao pode virar media parcial.

    Com 4 das 5 series a media desloca ate 0,09 p.p. (12m ate mar/2026:
    4,39% com as 5, 4,44% sem a DP) e a nota sairia com o numero errado sem
    nenhum sinal de erro. O bloco de nucleo e opcional — omitir e seguro.
    """
    import fontes.bcb as bcb

    def falha_so_na_dp(codigo, mes_ref):
        return None if codigo == bcb._NUCLEOS["DP"] else 4.50

    monkeypatch.setattr(bcb, "_acum12m_sgs", falha_so_na_dp)
    assert bcb.media_nucleos_12m("202604") is None


def test_media_nucleos_calcula_com_as_cinco_series(monkeypatch):
    """Com as 5 series presentes, a media e a aritmetica simples."""
    import fontes.bcb as bcb

    valores = {"MS": 4.40, "EX0": 4.50, "DP": 4.00, "EX3": 4.60, "P55": 4.50}
    por_codigo = {bcb._NUCLEOS[k]: v for k, v in valores.items()}
    monkeypatch.setattr(bcb, "_acum12m_sgs", lambda c, m: por_codigo[c])

    assert bcb.media_nucleos_12m("202604") == pytest.approx(4.40, abs=1e-9)
