/* Estruturas de dados — par de fontes/modelo.py.
 * Nomes de campo em snake_case de propósito: facilita comparar lado a lado
 * com o Python no gate de equivalência.
 */
import { arredondar } from "./numeros.js";

export class ItemInflacao {
  constructor({ cat_id, nome, nivel, variacao, peso, fonte }) {
    this.cat_id = cat_id;
    this.nome = nome;
    this.nivel = nivel; // 0=geral, 1=grupo, 2=subgrupo, 3=item, 4=subitem
    this.variacao = variacao;
    this.peso = peso;
    this.fonte = fonte;
  }

  /** impacto em p.p. = peso × variação / 100 */
  get impacto() {
    return arredondar((this.peso * this.variacao) / 100, 4);
  }
}

export class ResultadoInflacao {
  constructor(campos) {
    this.indicador = campos.indicador; // "IPCA" ou "IPCA-15"
    this.mes_ref = campos.mes_ref; // "AAAAMM"
    this.mes_ant = campos.mes_ant; // "AAAAMM"

    this.variacao_mensal = campos.variacao_mensal;
    this.variacao_mensal_anterior = campos.variacao_mensal_anterior;
    this.acum_12m = campos.acum_12m;
    this.acum_12m_anterior = campos.acum_12m_anterior;

    this.grupos = campos.grupos ?? []; // nivel 1, ordenados por impacto desc
    this.subitens = campos.subitens ?? []; // nivel >= 2, ordenados por impacto desc

    this.difusao = campos.difusao ?? null;
    this.difusao_anterior = campos.difusao_anterior ?? null;
    this.nucleo_12m = campos.nucleo_12m ?? null;
    this.nucleo_12m_anterior = campos.nucleo_12m_anterior ?? null;
    this.projecao_focus = campos.projecao_focus ?? null;
    this.url_ibge = campos.url_ibge ?? null;

    // ex.: mai/25 quando mes_ref = mai/26
    this.variacao_mesmo_mes_ano_anterior =
      campos.variacao_mesmo_mes_ano_anterior ?? null;

    this.fonte_variacao = campos.fonte_variacao ?? "";
    this.fonte_acum = campos.fonte_acum ?? "";
  }
}
