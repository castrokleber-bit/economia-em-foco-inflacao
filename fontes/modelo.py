from dataclasses import dataclass
from typing import Optional


@dataclass
class ItemInflacao:
    cat_id: int
    nome: str
    nivel: int      # 0=geral, 1=grupo, 2=subgrupo, 3=item, 4=subitem
    variacao: float
    peso: float
    fonte: str

    @property
    def impacto(self) -> float:
        """impacto em p.p. = peso × variação / 100"""
        return round(self.peso * self.variacao / 100, 4)


@dataclass
class ResultadoInflacao:
    indicador: str          # "IPCA" ou "IPCA-15"
    mes_ref: str            # "AAAAMM"
    mes_ant: str            # "AAAAMM"

    variacao_mensal: float
    variacao_mensal_anterior: float
    acum_12m: float
    acum_12m_anterior: float

    grupos: list[ItemInflacao]    # nivel 1, ordenados por impacto desc
    subitens: list[ItemInflacao]  # nivel >= 2, ordenados por impacto desc

    difusao: Optional[float] = None
    difusao_anterior: Optional[float] = None
    nucleo_12m: Optional[float] = None
    nucleo_12m_anterior: Optional[float] = None
    projecao_cni: Optional[float] = None
    projecao_focus: Optional[float] = None
    url_ibge: Optional[str] = None

    variacao_mesmo_mes_ano_anterior: Optional[float] = None  # ex: mai/25 quando mes_ref=mai/26

    fonte_variacao: str = ""
    fonte_acum: str = ""
