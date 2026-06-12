"""
Backend FastAPI — Economia em Foco | Inflação

Endpoint principal:
  GET /gerar?indicador=IPCA&mes=202604
    → { nota, provenencia, indicador, mes_ref, leitura_rascunho, erro }

A nota é montada deterministicamente; leitura_rascunho vem de nucleo/leitura.py
(Etapa 7, opcional).  Nenhuma parte da nota é gerada por IA.
"""
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from fontes.ibge import buscar_resultado
from fontes.bcb import enriquecer
from nucleo.montador import compor_nota

app = FastAPI(title="Economia em Foco — Inflação", docs_url=None, redoc_url=None)

_STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=_STATIC), name="static")

_MESES_CURTO = {
    "01": "jan", "02": "fev", "03": "mar", "04": "abr",
    "05": "mai", "06": "jun", "07": "jul", "08": "ago",
    "09": "set", "10": "out", "11": "nov", "12": "dez",
}


def _fmt_mes(mes_ref: str) -> str:
    return f"{_MESES_CURTO[mes_ref[4:]]}/{mes_ref[:4]}"


def _fmt_pct(v: float, decimais: int = 2) -> str:
    return f"{v:.{decimais}f}%".replace(".", ",")


def _montar_provenencia(r) -> list[dict]:
    tab = "7060" if r.indicador == "IPCA" else "7062"
    v_var = "V63" if r.indicador == "IPCA" else "V355"
    v_acum = "V2265" if r.indicador == "IPCA" else "V1120"
    v_peso = "V66" if r.indicador == "IPCA" else "V357"
    mes = _fmt_mes(r.mes_ref)
    itens = [
        {
            "campo": "Variação mensal",
            "fonte": f"IBGE SIDRA T{tab} {v_var}",
            "mes": mes,
            "valor": _fmt_pct(r.variacao_mensal),
        },
        {
            "campo": "Acumulado 12 meses",
            "fonte": f"IBGE SIDRA T{tab} {v_acum}",
            "mes": mes,
            "valor": _fmt_pct(r.acum_12m),
        },
        {
            "campo": "Pesos mensais (grupos)",
            "fonte": f"IBGE SIDRA T{tab} {v_peso}",
            "mes": mes,
            "valor": "estrutura de pesos",
        },
    ]
    if r.difusao is not None:
        fonte_dif = (
            "BCB SGS 21379" if r.indicador == "IPCA"
            else f"IBGE SIDRA T{tab} nível 4 (calculado)"
        )
        itens.append({
            "campo": "Difusão",
            "fonte": fonte_dif,
            "mes": mes,
            "valor": _fmt_pct(r.difusao, decimais=1),
        })
    if r.nucleo_12m is not None:
        itens.append({
            "campo": "Núcleo médio 12m",
            "fonte": "BCB SGS 4466 · 11427 · 16122 · 27839 · 28750 (MS+EX0+DP+EX3+P55)",
            "mes": mes,
            "valor": _fmt_pct(r.nucleo_12m),
        })
    return itens


@app.get("/")
def raiz():
    return FileResponse(_STATIC / "index.html")


@app.get("/gerar")
def gerar(
    indicador: str = Query(..., pattern=r"^IPCA(?:-15)?$"),
    mes: str = Query(..., pattern=r"^\d{6}$"),
):
    """
    Busca dados das APIs IBGE/BCB e retorna a nota montada + proveniência.
    Não gera nenhum token de texto por IA.
    """
    try:
        r = buscar_resultado(indicador, mes)
        enriquecer(r)
    except (KeyError, IndexError, ValueError):
        raise HTTPException(
            status_code=404,
            detail=f"Dados não disponíveis para {indicador} {mes[:4]}/{mes[4:]}. "
                   "Verifique se o IBGE já divulgou o resultado do mês informado.",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erro ao buscar dados: {exc}")

    nota = compor_nota(r)
    provenencia = _montar_provenencia(r)

    # Leitura por IA (Etapa 7 — importação opcional)
    leitura_rascunho = None
    try:
        from nucleo.leitura import gerar_leitura  # type: ignore
        leitura_rascunho = gerar_leitura(r)
    except ImportError:
        pass
    except Exception:
        pass  # leitura indisponível não quebra o app

    return {
        "nota": nota,
        "provenencia": provenencia,
        "indicador": r.indicador,
        "mes_ref": r.mes_ref,
        "leitura_rascunho": leitura_rascunho,
        "erro": None,
    }
