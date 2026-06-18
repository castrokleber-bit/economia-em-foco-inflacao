"""
Cálculo e seleção de impactos em p.p. para a nota de inflação.

A fórmula é determinística: impacto (p.p.) = peso_mensal × variação / 100.
A propriedade ItemInflacao.impacto já aplica a fórmula; este módulo fornece
as funções de filtragem usadas pelo montador.
"""
from fontes.modelo import ItemInflacao


def calcular_impacto(variacao: float, peso: float) -> float:
    """impacto em p.p. = peso × variação / 100, arredondado a 4 casas."""
    return round(peso * variacao / 100, 4)


def grupos_relevantes(
    grupos: list[ItemInflacao],
    top_n: int = 3,
    threshold: float = 0.05,
) -> list[ItemInflacao]:
    """
    Retorna até top_n grupos com maior impacto absoluto acima de threshold p.p.
    A entrada deve estar ordenada por impacto desc (padrão de ibge.buscar_resultado).
    """
    return [g for g in grupos[:top_n] if abs(g.impacto) >= threshold]


def top_subitem(
    subitens: list[ItemInflacao],
    nivel: int = 4,
) -> ItemInflacao | None:
    """
    Retorna o item de maior impacto no nível solicitado, ou None se vazio.
    nivel=4 → subitem próprio; nivel=2 → subgrupo (fallback se não houver nivel 4).
    """
    candidatos = [s for s in subitens if s.nivel == nivel]
    return candidatos[0] if candidatos else None


def calcular_difusao(
    subitens: list[ItemInflacao],
    nivel_min: int = 4,
) -> float | None:
    """
    Parcela de subitens (nivel >= nivel_min) com variação positiva no mês, em %.
    Usado pelo montador e para difusão do IPCA-15 (sem série SGS própria).
    """
    candidatos = [s for s in subitens if s.nivel >= nivel_min]
    if not candidatos:
        return None
    positivos = sum(1 for s in candidatos if s.variacao > 0)
    return round(positivos / len(candidatos) * 100, 2)
