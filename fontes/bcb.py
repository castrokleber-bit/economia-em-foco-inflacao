"""
Fetcher Banco Central — SGS séries temporais.

IDs verificados em jun/2026. Alterar somente após re-verificar na API:
  https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados

Combinação para média dos núcleos (MS+EX0+DP+EX3+P55):
  Atualizado jun/2026: 5 séries — 4466, 11427, 16122, 27839, 28750.
  Requer nova validação contra referência conhecida antes de marcar como estável.

Difusão IPCA-15:
  Não existe série SGS própria (verificado jun/2026).
  Calculada a partir dos subitens da tabela IBGE 7062 (parcela com var > 0).
  Validada: 65,12% (mai/2026) vs. 65,1% publicado — dif 0,02 p.p.
"""
import httpx
from typing import Optional

from .modelo import ItemInflacao, ResultadoInflacao

_BASE_SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{}/dados"

# Difusão IPCA — série verificada em jun/2026
_SGS_DIFUSAO_IPCA = 21379

# Núcleos IPCA — variação mensal (%) — IDs verificados em jun/2026
_NUCLEOS: dict[str, int] = {
    "MS":  4466,    # Médias aparadas com suavização
    "EX0": 11427,   # Por exclusão — EX0
    "DP":  16122,   # Dupla ponderação
    "EX3": 27839,   # Exclusão EX3
    "P55": 28750,   # Preços livres — P55
}

# Conjunto para média: MS+EX0+DP+EX3+P55 — atualizado jun/2026
_CONJUNTO_MEDIA: tuple[str, ...] = ("MS", "EX0", "DP", "EX3", "P55")


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _intervalo_12m(mes_ref: str) -> tuple[str, str]:
    """Retorna (dataInicial, dataFinal) dd/mm/aaaa para os 12m encerrados em mes_ref."""
    ano, m = int(mes_ref[:4]), int(mes_ref[4:])
    m_ini = m - 11
    ano_ini = ano
    if m_ini <= 0:
        m_ini += 12
        ano_ini -= 1
    return f"01/{m_ini:02d}/{ano_ini}", f"28/{m:02d}/{ano}"


def _sgs_fetch(codigo: int, ini: str, fim: str) -> list[dict]:
    """
    Busca registros da série SGS no intervalo de datas.
    Retorna [] silenciosamente em caso de erro ou série sem dados.
    """
    url = _BASE_SGS.format(codigo)
    try:
        resp = httpx.get(
            url,
            params={"formato": "json", "dataInicial": ini, "dataFinal": fim},
            timeout=30,
        )
        if resp.status_code != 200:
            return []
        return resp.json() or []
    except Exception:
        return []


def _parse_float(s) -> Optional[float]:
    try:
        return float(str(s).replace(",", "."))
    except (ValueError, TypeError):
        return None


def _buscar_valor_mes(codigo: int, mes_ref: str) -> Optional[float]:
    """Retorna o valor da série para mes_ref (AAAAMM), ou None se indisponível."""
    m, a = mes_ref[4:], mes_ref[:4]
    ini = fim = f"01/{m}/{a}"
    dados = _sgs_fetch(codigo, ini, fim)
    if not dados:
        return None
    return _parse_float(dados[0].get("valor"))


def _acum12m_sgs(codigo: int, mes_ref: str) -> Optional[float]:
    """
    Compõe o acumulado em 12 meses (composto) da série SGS encerrado em mes_ref.
    Retorna None se a série tiver menos de 12 observações no período.
    """
    ini, fim = _intervalo_12m(mes_ref)
    dados = _sgs_fetch(codigo, ini, fim)
    if len(dados) < 12:
        return None
    prod = 1.0
    for d in dados:
        val = _parse_float(d.get("valor"))
        if val is None:
            return None
        prod *= 1 + val / 100
    return round((prod - 1) * 100, 4)


def _difusao_from_subitens(
    subitens: list[ItemInflacao],
    nivel_min: int = 4,
) -> Optional[float]:
    """
    Parcela de subitens (nivel >= nivel_min) com variação positiva no mês.
    Usado para difusão do IPCA-15 na ausência de série SGS própria.
    """
    candidatos = [s for s in subitens if s.nivel >= nivel_min]
    if not candidatos:
        return None
    positivos = sum(1 for s in candidatos if s.variacao > 0)
    return round(positivos / len(candidatos) * 100, 2)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def media_nucleos_12m(mes_ref: str) -> Optional[float]:
    """
    Média aritmética dos acumulados em 12m dos núcleos MS+EX0+DP+EX3+P55.

    Retorna None se QUALQUER uma das séries falhar. Uma média parcial é pior
    que a ausência do dado: com 4 de 5 séries o número publicado desloca em
    até 0,09 p.p. (ex.: 12m até mar/2026 = 4,39% com as 5 séries, 4,44% sem a
    DP) sem qualquer sinal de erro. O bloco de núcleo é opcional na nota —
    omiti-lo é seguro, publicá-lo errado não é.
    """
    vals = []
    for nome in _CONJUNTO_MEDIA:
        v = _acum12m_sgs(_NUCLEOS[nome], mes_ref)
        if v is None:
            return None
        vals.append(v)
    return round(sum(vals) / len(vals), 4)


def enriquecer(resultado: ResultadoInflacao) -> None:
    """
    Preenche difusao, difusao_anterior, nucleo_12m e nucleo_12m_anterior
    no ResultadoInflacao fornecido. Falhas são silenciosas (campos ficam None).

    IPCA:
      difusao / difusao_anterior → SGS 21379
      nucleo_12m / nucleo_12m_anterior → média MS+EX0+DP+EX3+P55 em 12m

    IPCA-15:
      difusao → calculada dos subitens (nivel 4) já presentes em resultado
      difusao_anterior → None (requer fetch extra do IBGE; não implementado)
      nucleo_12m → None (BCB não publica núcleo do IPCA-15)
    """
    if resultado.indicador == "IPCA":
        resultado.difusao = _buscar_valor_mes(_SGS_DIFUSAO_IPCA, resultado.mes_ref)
        resultado.difusao_anterior = _buscar_valor_mes(_SGS_DIFUSAO_IPCA, resultado.mes_ant)
        resultado.nucleo_12m = media_nucleos_12m(resultado.mes_ref)
        resultado.nucleo_12m_anterior = media_nucleos_12m(resultado.mes_ant)
    else:
        resultado.difusao = _difusao_from_subitens(resultado.subitens, nivel_min=4)
        resultado.difusao_anterior = None
        resultado.nucleo_12m = None
        resultado.nucleo_12m_anterior = None
