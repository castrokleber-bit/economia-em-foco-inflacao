"""
Montador da nota de inflação — determinístico, sem IA.

Cada bloco_*() retorna str. compor_nota() monta o texto completo.
Nenhum token do texto é gerado por IA; cada campo rastreia a um
valor retornado pela API (ResultadoInflacao).
"""
import math
from dataclasses import dataclass
from typing import Optional

from fontes.modelo import ItemInflacao, ResultadoInflacao
from nucleo.impacto import grupos_relevantes, top_subitem


# ---------------------------------------------------------------------------
# Configuração de montagem (parametrizável; não hard-coded no texto)
# ---------------------------------------------------------------------------

@dataclass
class ConfigNota:
    top_n_grupos: int = 3
    threshold_grupos: float = 0.05   # p.p. mínimo para citar um grupo
    assinatura: str = "SIECON"        # "ECON" ou "SIECON"
    emoji_titulo: str = "\U0001f6a8"      # 🚨
    emoji_resultado: str = "\U0001f6a9"   # 🚩
    emoji_explicacao: str = "\U0001f534"  # 🔴
    emoji_acumulado: str = "\U0001f4c8"   # 📈
    emoji_nucleo: str = "\U0001f4c9"      # 📉
    emoji_difusao: str = "\U0001f4ca"     # 📊


# ---------------------------------------------------------------------------
# Tabelas e auxiliares de formatação
# ---------------------------------------------------------------------------

_MESES = {
    "01": "janeiro", "02": "fevereiro", "03": "marco",   "04": "abril",
    "05": "maio",    "06": "junho",     "07": "julho",   "08": "agosto",
    "09": "setembro","10": "outubro",   "11": "novembro","12": "dezembro",
}

_MESES_ACENTUADOS = {
    "01": "janeiro", "02": "fevereiro", "03": "março",   "04": "abril",
    "05": "maio",    "06": "junho",     "07": "julho",   "08": "agosto",
    "09": "setembro","10": "outubro",   "11": "novembro","12": "dezembro",
}

# Prefixos de itens femininos — usados em "a alta da/do <item>"
_FEMININAS: set[str] = {
    "energia", "gasolina", "gasolina comum", "gasolina aditivada",
    "carne", "farinha", "batata", "batata-inglesa",
    "agua", "cerveja", "manteiga", "margarina",
    "fruta", "maca", "banana", "uva", "alface",
    "cenoura", "cebola", "ervilha", "abobrinha",
    "televisao", "geladeira", "passagem",
}


def _fmt(v: float, decimais: int = 2) -> str:
    """Formata float com vírgula decimal e arredondamento HALF_UP."""
    factor = 10 ** decimais
    arredondado = math.floor(abs(v) * factor + 0.5) / factor
    if v < 0:
        arredondado = -arredondado
    return f"{arredondado:.{decimais}f}".replace(".", ",")


def _mes(mes_ref: str) -> str:
    """'202604' -> 'abril'"""
    return _MESES_ACENTUADOS[mes_ref[4:6]]


def _ano(mes_ref: str) -> str:
    return mes_ref[:4]


def _strip(nome: str) -> str:
    """'1.Alimentação e bebidas' -> 'Alimentação e bebidas'"""
    if nome and nome[0].isdigit():
        partes = nome.split(".", 1)
        if len(partes) == 2:
            return partes[1].strip()
    return nome


def _artigo_de(nome: str) -> str:
    """Heuristica de genero para 'da' / 'do' antes do nome do item."""
    # remove acentos para comparacao simples
    import unicodedata
    nl = unicodedata.normalize("NFD", nome.lower())
    nl_ascii = "".join(c for c in nl if unicodedata.category(c) != "Mn")
    if any(nl_ascii.startswith(f) for f in _FEMININAS):
        return "da"
    # ultima palavra termina em 'a' e nome tem ate 3 palavras
    if nl_ascii.split()[-1].endswith("a") and len(nl_ascii.split()) <= 3:
        return "da"
    return "do"


def _direcao(v: float, alta: str = "alta", queda: str = "queda") -> str:
    return alta if v >= 0 else queda


def _avanco_recuo(v: float) -> str:
    return "avanço" if v >= 0 else "recuo"


def _acima_abaixo(atual: float, anterior: float) -> str:
    return "acima" if atual > anterior else "abaixo"


def _em_linha_ou_relativo(v: float, ref: float, tol: float = 0.05) -> str:
    if abs(v - ref) <= tol:
        return "em linha com"
    return "acima de" if v > ref else "abaixo de"


def _pp_longo(v: float) -> str:
    """'0,29 ponto percentual (p.p.)' — para o primeiro grupo."""
    txt = _fmt(v)
    if abs(v) > 1:
        return f"{txt} pontos percentuais (p.p.)"
    return f"{txt} ponto percentual (p.p.)"


def _pp(v: float) -> str:
    """'0,16 p.p.' — versao curta para grupos subsequentes."""
    return f"{_fmt(v)} p.p."


# ---------------------------------------------------------------------------
# Blocos individuais
# ---------------------------------------------------------------------------

def bloco_titulo(r: ResultadoInflacao, cfg: ConfigNota) -> str:
    mes = _mes(r.mes_ref).upper()
    return f"{cfg.emoji_titulo} *{r.indicador} {mes}/{_ano(r.mes_ref)}*"


def _mesmo_mes_ano_anterior(mes_ref: str) -> str:
    """'202605' -> '202505'"""
    return f"{int(mes_ref[:4]) - 1}{mes_ref[4:]}"


def bloco_resultado(r: ResultadoInflacao, cfg: ConfigNota) -> str:
    dir_mensal = _direcao(r.variacao_mensal)
    avanco = _avanco_recuo(r.variacao_mensal_anterior)
    mes_ano_ant = _mesmo_mes_ano_anterior(r.mes_ref)

    # Comparação com mês anterior
    comp_anterior = (
        f"após {avanco} de {_fmt(r.variacao_mensal_anterior)}% "
        f"em {_mes(r.mes_ant)}"
    )

    # Comparação com mesmo mês do ano anterior (quando disponível)
    if r.variacao_mesmo_mes_ano_anterior is not None:
        dir_ano_ant = _direcao(r.variacao_mesmo_mes_ano_anterior)
        comp_ano_ant = (
            f"e {dir_ano_ant} de {_fmt(r.variacao_mesmo_mes_ano_anterior)}% "
            f"em {_mes(mes_ano_ant)} de {_ano(mes_ano_ant)}"
        )
        comparacoes = f"{comp_anterior} {comp_ano_ant}."
    else:
        comparacoes = f"{comp_anterior}."

    texto = (
        f"{cfg.emoji_resultado} O {r.indicador} registrou "
        f"*{dir_mensal} de {_fmt(r.variacao_mensal)}%* "
        f"em {_mes(r.mes_ref)} de {_ano(r.mes_ref)}, "
        f"{comparacoes}"
    )

    if r.projecao_cni is not None and r.projecao_focus is not None:
        rel_cni = _em_linha_ou_relativo(r.variacao_mensal, r.projecao_cni)
        rel_foc = _acima_abaixo(r.variacao_mensal, r.projecao_focus)
        texto += (
            f" O resultado ficou {rel_cni} a projeção da CNI "
            f"({_fmt(r.projecao_cni)}%) e {rel_foc} da projeção "
            f"da Pesquisa Focus do Banco Central ({_fmt(r.projecao_focus)}%)."
        )

    return texto


def bloco_explicacao(r: ResultadoInflacao, cfg: ConfigNota) -> str:
    """Paragrafos dos grupos + subitem de destaque; pode conter \\n\\n interno."""
    grupos = grupos_relevantes(
        r.grupos, top_n=cfg.top_n_grupos, threshold=cfg.threshold_grupos
    )
    if not grupos:
        return ""

    g1 = grupos[0]
    g1n = _strip(g1.nome)
    dir_g1 = _direcao(g1.variacao)

    texto = (
        f"{cfg.emoji_explicacao} O resultado de {_mes(r.mes_ref)} "
        f"*reflete a {dir_g1} do grupo {g1n}*, "
        f"com variação de {_fmt(g1.variacao)}% e impacto de "
        f"{_pp_longo(g1.impacto)} no índice do mês."
    )

    if len(grupos) == 2:
        g2 = grupos[1]
        g2n = _strip(g2.nome)
        # _pp() já termina em "." (abreviatura "p.p."); não acrescentar segundo ponto
        texto += (
            f" Em seguida, destaca-se o grupo {g2n}, "
            f"com variação de {_fmt(g2.variacao)}% "
            f"e impacto de {_pp(g2.impacto)}"
        )
    elif len(grupos) >= 3:
        g2, g3 = grupos[1], grupos[2]
        g2n = _strip(g2.nome)
        g3n = _strip(g3.nome)
        texto += (
            f" Em seguida, destacam-se os grupos {g2n}, "
            f"com variação de {_fmt(g2.variacao)}% "
            f"e impacto de {_pp(g2.impacto)}, "
            f"e {g3n}, "
            f"com variação de {_fmt(g3.variacao)}% "
            f"e impacto de {_pp(g3.impacto)}"
        )

    # Subitem de maior impacto individual (nivel 4)
    subitem = top_subitem(r.subitens, nivel=4)
    if subitem is not None:
        sn = _strip(subitem.nome).lower()
        artigo = _artigo_de(sn)
        dir_sub = _direcao(subitem.variacao)
        texto_sub = (
            f"{cfg.emoji_explicacao} Também merece destaque a {dir_sub} "
            f"{artigo} *{sn}* "
            f"({_fmt(subitem.variacao)}% e impacto de {_pp(subitem.impacto)}), "
            f"subitem de maior impacto individual no índice do mês."
        )
        return f"{texto}\n\n{texto_sub}"

    return texto


def bloco_acumulado(r: ResultadoInflacao, cfg: ConfigNota) -> str:
    rel = _acima_abaixo(r.acum_12m, r.acum_12m_anterior)
    return (
        f"{cfg.emoji_acumulado} O *{r.indicador} acumulado em 12 meses* "
        f"até {_mes(r.mes_ref)} ficou em *{_fmt(r.acum_12m)}%*, "
        f"{rel} dos {_fmt(r.acum_12m_anterior)}% "
        f"registrados nos 12 meses encerrados em {_mes(r.mes_ant)}."
    )


def bloco_nucleo(r: ResultadoInflacao, cfg: ConfigNota) -> Optional[str]:
    """Apenas para IPCA e quando nucleo_12m nao e None."""
    if r.indicador != "IPCA" or r.nucleo_12m is None:
        return None
    ant = r.nucleo_12m_anterior if r.nucleo_12m_anterior is not None else r.nucleo_12m
    rel = _acima_abaixo(r.nucleo_12m, ant)
    return (
        f"{cfg.emoji_nucleo} *A média dos núcleos de inflação*, "
        f"que suavizam os efeitos de itens mais voláteis, "
        f"ficou em *{_fmt(r.nucleo_12m)}%* no acumulado em 12 meses "
        f"até {_mes(r.mes_ref)}, ligeiramente {rel} dos "
        f"{_fmt(ant)}% no acumulado até {_mes(r.mes_ant)}."
    )


def bloco_difusao(r: ResultadoInflacao, cfg: ConfigNota) -> Optional[str]:
    if r.difusao is None:
        return None
    dif = _fmt(r.difusao, decimais=1)
    if r.difusao_anterior is not None:
        rel = _acima_abaixo(r.difusao, r.difusao_anterior)
        ant = _fmt(r.difusao_anterior, decimais=1)
        return (
            f"{cfg.emoji_difusao} O *índice de difusão*, que mede a disseminação "
            f"das altas de preços entre os itens que compõem o {r.indicador}, "
            f"ficou em *{dif}%*, {rel} do registrado em "
            f"{_mes(r.mes_ant)} ({ant}%)."
        )
    return (
        f"{cfg.emoji_difusao} O *índice de difusão*, que mede a disseminação "
        f"das altas de preços entre os itens que compõem o {r.indicador}, "
        f"ficou em *{dif}%*."
    )


def bloco_assinatura(cfg: ConfigNota) -> str:
    if cfg.assinatura == "SIECON":
        sup = "Superintendência de Inteligência Econômica (SIECON)"
    else:
        sup = "Superintendência de Economia (ECON)"
    return (
        f"_*{sup}*_\n"
        "_*Diretoria de Desenvolvimento Industrial (DDI)*_\n"
        "_*Confederação Nacional da Indústria (CNI)*_"
    )


def bloco_link(r: ResultadoInflacao) -> Optional[str]:
    if not r.url_ibge:
        return None
    return f"Notícia: {r.url_ibge}"


# ---------------------------------------------------------------------------
# Composição final
# ---------------------------------------------------------------------------

def compor_nota(
    r: ResultadoInflacao,
    cfg: Optional[ConfigNota] = None,
) -> str:
    """
    Monta o texto completo da nota de WhatsApp.
    Retorna string com blocos separados por linha em branco.
    Determinístico: nenhum token gerado por IA.
    """
    if cfg is None:
        cfg = ConfigNota()

    blocos = [
        bloco_titulo(r, cfg),
        bloco_resultado(r, cfg),
        bloco_explicacao(r, cfg),
        bloco_acumulado(r, cfg),
        bloco_nucleo(r, cfg),
        bloco_difusao(r, cfg),
        bloco_assinatura(cfg),
        bloco_link(r),
    ]

    return "\n\n".join(b for b in blocos if b)
