"""
Fetcher IBGE — tabelas SIDRA 7060 (IPCA) e 7062 (IPCA-15).

IDs de variáveis e categorias verificados nos metadados em jun/2026.
Não alterar sem re-verificar em:
  https://servicodados.ibge.gov.br/api/v3/agregados/{tabela}/metadados
"""
import re
import httpx

from .modelo import ItemInflacao, ResultadoInflacao

_BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"

# Variáveis por indicador — IDs verificados nos metadados em jun/2026
_CONF: dict[str, dict] = {
    "IPCA": {
        "tabela": 7060,
        "var_mensal": 63,
        "var_acum12m": 2265,
        "var_peso": 66,
    },
    "IPCA-15": {
        "tabela": 7062,
        "var_mensal": 355,
        "var_acum12m": 1120,
        "var_peso": 357,
    },
}

# Classificação 315 — IDs verificados nos metadados em jun/2026
_CAT_GERAL = 7169
_CATS_GRUPO = [7170, 7445, 7486, 7558, 7625, 7660, 7712, 7766, 7786]


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _mes_anterior(mes: str) -> str:
    ano, m = int(mes[:4]), int(mes[4:])
    return f"{ano - 1}12" if m == 1 else f"{ano}{m - 1:02d}"


def _mesmo_mes_ano_anterior(mes: str) -> str:
    return f"{int(mes[:4]) - 1}{mes[4:]}"


def _nivel_from_nome(nome: str) -> int:
    """
    Infere o nível hierárquico pelo comprimento do prefixo numérico no nome.
    Padrão IBGE:
      sem prefixo  → 0 (Índice geral)
      1 dígito     → 1 (grupo)
      2 dígitos    → 2 (subgrupo)
      4 dígitos    → 3 (item)
      7 dígitos    → 4 (subitem)
    """
    m = re.match(r"^(\d+)\.", nome)
    if not m:
        return 0
    n = len(m.group(1))
    if n == 1:
        return 1
    if n == 2:
        return 2
    if n == 4:
        return 3
    if n == 7:
        return 4
    return -1


def _parse_float(s) -> float | None:
    if s is None or str(s).strip() in ("...", "-", ""):
        return None
    try:
        return float(str(s).replace(",", "."))
    except (ValueError, TypeError):
        return None


def _fetch(
    tabela: int,
    periodo: str,
    variaveis: list[int],
    cats,
) -> dict[int, dict[int, tuple[str, float]]]:
    """
    Chama a API de Agregados e retorna {var_id: {cat_id: (nome, valor)}}.
    cats: lista de ints ou a string literal "all".
    Categorias sem dado disponível ("...") são omitidas do resultado.
    """
    vars_str = "|".join(str(v) for v in variaveis)
    cats_str = cats if cats == "all" else ",".join(str(c) for c in cats)
    url = (
        f"{_BASE}/{tabela}/periodos/{periodo}/variaveis/{vars_str}"
        f"?localidades=N1[all]&classificacao=315[{cats_str}]"
    )
    resp = httpx.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    result: dict[int, dict[int, tuple[str, float]]] = {}
    for bloco in data:
        var_id = int(bloco["id"])
        result[var_id] = {}
        for entrada in bloco.get("resultados", []):
            cat_d = entrada["classificacoes"][0]["categoria"]
            cat_id = int(next(iter(cat_d)))
            cat_nome = next(iter(cat_d.values()))
            series = entrada.get("series", [])
            if not series:
                continue
            val_str = series[0]["serie"].get(periodo)
            val = _parse_float(val_str)
            if val is not None:
                result[var_id][cat_id] = (cat_nome, val)
    return result


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def buscar_resultado(indicador: str, mes_ref: str) -> ResultadoInflacao:
    """
    Busca o resultado do IPCA ou IPCA-15 para o período informado (AAAAMM)
    e retorna um ResultadoInflacao com grupos e subitens ordenados por impacto.

    difusao, nucleo e projeções ficam None; preenchidos por bcb.enriquecer().
    """
    conf = _CONF[indicador]
    tab = conf["tabela"]
    vm, va12, vp = conf["var_mensal"], conf["var_acum12m"], conf["var_peso"]
    mes_ant = _mes_anterior(mes_ref)
    fonte = f"IBGE SIDRA tabela {tab}"

    # 1. Índice geral — mês de referência
    d_cur = _fetch(tab, mes_ref, [vm, va12], [_CAT_GERAL])
    variacao_mensal = d_cur[vm][_CAT_GERAL][1]
    acum_12m = d_cur[va12][_CAT_GERAL][1]

    # 2. Índice geral — mês anterior
    d_ant = _fetch(tab, mes_ant, [vm, va12], [_CAT_GERAL])
    variacao_mensal_anterior = d_ant[vm][_CAT_GERAL][1]
    acum_12m_anterior = d_ant[va12][_CAT_GERAL][1]

    # 2b. Mesmo mês do ano anterior (comparação interanual no bloco_resultado)
    mes_ano_ant = _mesmo_mes_ano_anterior(mes_ref)
    try:
        d_ano_ant = _fetch(tab, mes_ano_ant, [vm], [_CAT_GERAL])
        variacao_mesmo_mes_ano_anterior: float | None = d_ano_ant[vm][_CAT_GERAL][1]
    except Exception:
        variacao_mesmo_mes_ano_anterior = None

    # 3. Grupos — variação + peso, mês de referência
    d_g = _fetch(tab, mes_ref, [vm, vp], _CATS_GRUPO)
    grupos: list[ItemInflacao] = []
    for cat_id in _CATS_GRUPO:
        entry_vm = d_g.get(vm, {}).get(cat_id)
        entry_vp = d_g.get(vp, {}).get(cat_id)
        if entry_vm and entry_vp:
            grupos.append(ItemInflacao(
                cat_id=cat_id,
                nome=entry_vm[0],
                nivel=1,
                variacao=entry_vm[1],
                peso=entry_vp[1],
                fonte=f"{fonte} var {vm},{vp} periodo {mes_ref}",
            ))
    grupos.sort(key=lambda x: x.impacto, reverse=True)

    # 4. Todos os itens (nível >= 2) — variação + peso, mês de referência
    #    Usado para encontrar o subitem de maior impacto individual
    d_all = _fetch(tab, mes_ref, [vm, vp], "all")
    subitens: list[ItemInflacao] = []
    for cat_id, (cat_nome, variacao) in d_all.get(vm, {}).items():
        nivel = _nivel_from_nome(cat_nome)
        if nivel < 2:
            continue
        entry_vp = d_all.get(vp, {}).get(cat_id)
        if entry_vp is None:
            continue
        subitens.append(ItemInflacao(
            cat_id=cat_id,
            nome=cat_nome,
            nivel=nivel,
            variacao=variacao,
            peso=entry_vp[1],
            fonte=f"{fonte} var {vm},{vp} periodo {mes_ref}",
        ))
    subitens.sort(key=lambda x: x.impacto, reverse=True)

    return ResultadoInflacao(
        indicador=indicador,
        mes_ref=mes_ref,
        mes_ant=mes_ant,
        variacao_mensal=variacao_mensal,
        variacao_mensal_anterior=variacao_mensal_anterior,
        acum_12m=acum_12m,
        acum_12m_anterior=acum_12m_anterior,
        grupos=grupos,
        subitens=subitens,
        variacao_mesmo_mes_ano_anterior=variacao_mesmo_mes_ano_anterior,
        fonte_variacao=f"{fonte} var {vm} periodo {mes_ref}",
        fonte_acum=f"{fonte} var {va12} periodo {mes_ref}",
    )
