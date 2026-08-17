"""
Gate G2 — valida que impacto = peso × variação / 100 reproduz os impactos
publicados na divulgação do IPCA de abril/2026 (tolerância ±0,01 p.p.).

Valores de variação e peso extraídos da API IBGE (tabela 7060) em jun/2026.
Impactos esperados: valores publicados na Comunicação Social do IBGE abr/2026.
"""
import pytest
from fontes.modelo import ItemInflacao
from nucleo.impacto import calcular_impacto, grupos_relevantes, grupos_queda, top_subitem, top_subitem_queda


# ---------------------------------------------------------------------------
# Fixture: valores verificados via API IBGE (tabela 7060, abr/2026)
# ---------------------------------------------------------------------------

def _item(cat_id, nome, variacao, peso):
    return ItemInflacao(
        cat_id=cat_id, nome=nome, nivel=1,
        variacao=variacao, peso=peso, fonte="fixture abr/2026",
    )


GRUPOS_ABRIL2026 = sorted([
    _item(7170, "1.Alimentação e bebidas",       1.34, 21.4524),
    _item(7445, "2.Habitação",                   0.63, 15.2007),
    _item(7486, "3.Artigos de residência",        0.65,  3.4660),
    _item(7558, "4.Vestuário",                   0.52,  4.6345),
    _item(7625, "5.Transportes",                 0.06, 20.6094),
    _item(7660, "6.Saúde e cuidados pessoais",   1.16, 13.5984),
    _item(7712, "7.Despesas pessoais",           0.35, 10.2667),
    _item(7766, "8.Educação",                    0.06,  6.2508),
    _item(7786, "9.Comunicação",                 0.57,  4.5210),
], key=lambda x: x.impacto, reverse=True)

# Impactos esperados publicados pelo IBGE na Comunicação Social abr/2026
# Tolerância ±0,01 p.p. conforme gate do projeto
IMPACTOS_ESPERADOS = {
    7170: 0.29,   # Alimentação e bebidas
    7660: 0.16,   # Saúde e cuidados pessoais
    7445: 0.10,   # Habitação
    7712: 0.04,   # Despesas pessoais
    7786: 0.03,   # Comunicação
    7558: 0.02,   # Vestuário
    7486: 0.02,   # Artigos de residência
    7625: 0.01,   # Transportes
    7766: 0.00,   # Educação
}


# ---------------------------------------------------------------------------
# Testes unitários (sem chamada à API)
# ---------------------------------------------------------------------------

def test_calcular_impacto_formula():
    """A função calcular_impacto aplica peso × variação / 100."""
    assert calcular_impacto(1.34, 21.4524) == pytest.approx(0.2875, abs=1e-4)
    assert calcular_impacto(0.0, 50.0) == pytest.approx(0.0, abs=1e-6)
    assert calcular_impacto(-0.5, 10.0) == pytest.approx(-0.05, abs=1e-4)


def test_item_inflacao_impacto_property():
    """ItemInflacao.impacto usa a mesma fórmula."""
    item = _item(7170, "Alimentação", 1.34, 21.4524)
    assert item.impacto == pytest.approx(calcular_impacto(1.34, 21.4524), abs=1e-6)


@pytest.mark.parametrize("cat_id,esperado", IMPACTOS_ESPERADOS.items())
def test_gate_g2_impactos_abril2026(cat_id, esperado):
    """
    Gate G2 — cada grupo de abr/2026 deve reproduzir o impacto publicado
    dentro de ±0,01 p.p.
    """
    grupo = next(g for g in GRUPOS_ABRIL2026 if g.cat_id == cat_id)
    calculado = round(grupo.impacto, 2)
    assert calculado == pytest.approx(esperado, abs=0.01), (
        f"{grupo.nome}: calculado={calculado}, publicado={esperado}"
    )


def test_gate_g2_todos_os_grupos():
    """Confirmação de cobertura: todos os 9 grupos têm impacto checado."""
    assert set(IMPACTOS_ESPERADOS.keys()) == {g.cat_id for g in GRUPOS_ABRIL2026}


def test_grupos_relevantes_padrao():
    """Top 3 grupos com impacto >= 0,05 p.p."""
    rel = grupos_relevantes(GRUPOS_ABRIL2026, top_n=3, threshold=0.05)
    assert len(rel) == 3
    assert rel[0].cat_id == 7170   # Alimentação — maior impacto
    assert rel[1].cat_id == 7660   # Saúde
    assert rel[2].cat_id == 7445   # Habitação


def test_grupos_relevantes_corte_threshold():
    """Com threshold alto, retorna menos grupos."""
    rel = grupos_relevantes(GRUPOS_ABRIL2026, top_n=9, threshold=0.10)
    # Alim. (0.2875) e Saúde (0.1577) passam; Habitação (0.0958) fica abaixo
    assert len(rel) == 2
    assert rel[0].cat_id == 7170
    assert rel[1].cat_id == 7660


def test_grupos_relevantes_lista_vazia():
    assert grupos_relevantes([], top_n=3, threshold=0.05) == []


def test_top_subitem_nivel_correto():
    """top_subitem retorna o primeiro item no nível pedido."""
    s4 = ItemInflacao(1, "item nivel4", 4, 2.0, 5.0, "x")
    s2 = ItemInflacao(2, "item nivel2", 2, 3.0, 10.0, "x")
    assert top_subitem([s2, s4], nivel=4) is s4
    assert top_subitem([s2, s4], nivel=2) is s2


def test_top_subitem_retorna_none_se_nivel_ausente():
    s2 = ItemInflacao(2, "item nivel2", 2, 3.0, 10.0, "x")
    assert top_subitem([s2], nivel=4) is None


def test_top_subitem_ignora_impacto_negativo():
    """top_subitem não retorna item com deflação — só impacto positivo."""
    s_neg = ItemInflacao(1, "item negativo", 4, -2.0, 5.0, "x")   # impacto -0.10
    s_pos = ItemInflacao(2, "item positivo", 4, 1.0, 5.0, "x")    # impacto 0.05
    assert top_subitem([s_neg, s_pos], nivel=4) is s_pos
    assert top_subitem([s_neg], nivel=4) is None


def test_grupos_queda_retorna_deflacionarios():
    """grupos_queda retorna grupos com impacto <= -threshold, ordenados mais negativo primeiro."""
    grupos = [
        ItemInflacao(1, "1.Alta A",   1,  2.0, 20.0, "x"),   # impacto  0.40
        ItemInflacao(2, "2.Alta B",   1,  1.0, 15.0, "x"),   # impacto  0.15
        ItemInflacao(3, "3.Queda C",  1, -1.5, 10.0, "x"),   # impacto -0.15
        ItemInflacao(4, "4.Queda D",  1, -0.3,  5.0, "x"),   # impacto -0.015 (abaixo do threshold)
    ]
    grupos.sort(key=lambda x: x.impacto, reverse=True)
    qs = grupos_queda(grupos, top_n=2, threshold=0.05)
    assert len(qs) == 1                   # só "Queda C" passa o threshold de 0.05
    assert qs[0].cat_id == 3


def test_grupos_queda_ordenado_mais_negativo_primeiro():
    grupos = [
        ItemInflacao(1, "1.X", 1, -2.0, 10.0, "x"),   # impacto -0.20
        ItemInflacao(2, "2.Y", 1, -1.0, 10.0, "x"),   # impacto -0.10
    ]
    qs = grupos_queda(grupos, top_n=2, threshold=0.05)
    assert qs[0].cat_id == 1   # -0.20 vem primeiro


def test_grupos_queda_lista_sem_deflacao():
    grupos = [ItemInflacao(1, "1.A", 1, 1.0, 20.0, "x")]
    assert grupos_queda(grupos, top_n=1, threshold=0.05) == []


def test_top_subitem_queda_retorna_mais_negativo():
    s1 = ItemInflacao(1, "a nivel4",   4, -2.0, 10.0, "x")   # impacto -0.20
    s2 = ItemInflacao(2, "b nivel4",   4, -0.5, 10.0, "x")   # impacto -0.05
    s3 = ItemInflacao(3, "c nivel4",   4,  1.0, 10.0, "x")   # impacto  0.10 (positivo)
    assert top_subitem_queda([s1, s2, s3], nivel=4, threshold=0.05) is s1


def test_top_subitem_queda_none_sem_deflacao_significativa():
    s = ItemInflacao(1, "x", 4, -0.01, 10.0, "x")   # impacto -0.001 (abaixo do threshold)
    assert top_subitem_queda([s], nivel=4, threshold=0.05) is None


# ---------------------------------------------------------------------------
# Teste de integração com API (marcado separadamente)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_gate_g2_via_api():
    """
    Gate G2 integração — busca abr/2026 ao vivo e verifica todos os impactos.
    """
    from fontes.ibge import buscar_resultado
    r = buscar_resultado("IPCA", "202604")

    print("\nImpactos por grupo (API ao vivo, abr/2026):")
    for g in r.grupos:
        esperado = IMPACTOS_ESPERADOS.get(g.cat_id)
        calc = round(g.impacto, 2)
        ok = "OK" if esperado is None or abs(calc - esperado) <= 0.01 else "FALHA"
        print(f"  {ok} {g.nome}: {calc:.2f} p.p. (esperado {esperado})")

    for g in r.grupos:
        esperado = IMPACTOS_ESPERADOS.get(g.cat_id)
        if esperado is not None:
            assert round(g.impacto, 2) == pytest.approx(esperado, abs=0.01), (
                f"{g.nome}: calculado={g.impacto:.4f}, publicado={esperado}"
            )
