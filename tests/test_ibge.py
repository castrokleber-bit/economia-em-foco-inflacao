"""
Gate 2 — valida que ibge.buscar_resultado reproduz os números publicados.

Executa chamadas reais às APIs do IBGE. Marque com -m integration para
separar dos testes unitários:
    pytest -m integration -v
"""
import pytest
from fontes.ibge import buscar_resultado


@pytest.mark.integration
def test_ipca_abril2026_geral():
    """Variação mensal e acum. 12m do IPCA abr/2026 devem bater com a divulgação."""
    r = buscar_resultado("IPCA", "202604")

    print(f"\nIPCA abr/2026: {r.variacao_mensal}% (mensal)  |  {r.acum_12m}% (12m)")

    assert r.variacao_mensal == pytest.approx(0.67, abs=0.005), (
        f"Variação mensal esperada 0.67%, obtida {r.variacao_mensal}%"
    )
    assert r.acum_12m == pytest.approx(4.39, abs=0.005), (
        f"Acum. 12m esperado 4.39%, obtido {r.acum_12m}%"
    )


@pytest.mark.integration
def test_ipca_abril2026_grupos():
    """Grupos devem estar presentes, ordenados por impacto, com Alim.&beb. = 0.29 p.p."""
    r = buscar_resultado("IPCA", "202604")

    print("\nGrupos IPCA abr/2026 (por impacto desc):")
    for g in r.grupos:
        print(f"  {g.nome}: var={g.variacao}%  peso={g.peso}%  impacto={g.impacto:.2f} p.p.")

    assert len(r.grupos) == 9, f"Esperados 9 grupos, obtidos {len(r.grupos)}"

    # Alimentação e bebidas (7170) deve ter impacto ~0.29 p.p.
    alim = next((g for g in r.grupos if g.cat_id == 7170), None)
    assert alim is not None, "Grupo Alimentação e bebidas não encontrado"
    assert alim.impacto == pytest.approx(0.29, abs=0.01), (
        f"Impacto de Alim.&beb. esperado ~0.29, obtido {alim.impacto:.4f}"
    )
    # Deve ser o grupo de maior impacto
    assert r.grupos[0].cat_id == 7170, (
        f"Grupo de maior impacto esperado Alim.&beb., obtido {r.grupos[0].nome}"
    )


@pytest.mark.integration
def test_ipca_abril2026_subitens():
    """Subitens devem existir e o de maior impacto deve ser não-nulo."""
    r = buscar_resultado("IPCA", "202604")

    assert len(r.subitens) > 0, "Nenhum subitem retornado"
    top = r.subitens[0]
    print(f"\nTop subitem IPCA abr/2026: {top.nome}  impacto={top.impacto:.3f} p.p.")
    assert top.impacto > 0


@pytest.mark.integration
def test_ipca15_maio2026_geral():
    """Variação mensal e acum. 12m do IPCA-15 mai/2026 devem bater com a divulgação."""
    r = buscar_resultado("IPCA-15", "202605")

    print(f"\nIPCA-15 mai/2026: {r.variacao_mensal}% (mensal)  |  {r.acum_12m}% (12m)")

    assert r.variacao_mensal == pytest.approx(0.62, abs=0.005), (
        f"Variação mensal esperada 0.62%, obtida {r.variacao_mensal}%"
    )
    assert r.acum_12m == pytest.approx(4.64, abs=0.005), (
        f"Acum. 12m esperado 4.64%, obtido {r.acum_12m}%"
    )
