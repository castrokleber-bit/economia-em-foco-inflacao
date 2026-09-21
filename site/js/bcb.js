/* Fetcher Banco Central — séries temporais do SGS.
 * Par de fontes/bcb.py.
 *
 * IDs verificados em jun/2026. Alterar somente após re-verificar na API:
 *   https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados
 *
 * Difusão IPCA-15:
 *   Não existe série SGS própria (verificado jun/2026).
 *   Calculada a partir dos subitens da tabela IBGE 7062 (parcela com var > 0).
 */
import { arredondar } from "./numeros.js";
import { calcularDifusao } from "./impacto.js";

const BASE_SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{}/dados";

// Difusão IPCA — série verificada em jun/2026
const SGS_DIFUSAO_IPCA = 21379;

// Núcleos IPCA — variação mensal (%) — IDs verificados em jun/2026
const NUCLEOS = {
  MS: 4466, // Médias aparadas com suavização
  EX0: 11427, // Por exclusão — EX0
  DP: 16122, // Dupla ponderação
  EX3: 27839, // Exclusão EX3
  P55: 28750, // Preços livres — P55
};

// Conjunto para média: MS+EX0+DP+EX3+P55 — atualizado jun/2026
const CONJUNTO_MEDIA = ["MS", "EX0", "DP", "EX3", "P55"];

// ---------------------------------------------------------------------------
// Helpers internos
// ---------------------------------------------------------------------------

/** (dataInicial, dataFinal) dd/mm/aaaa para os 12m encerrados em mesRef. */
function intervalo12m(mesRef) {
  const ano = parseInt(mesRef.slice(0, 4), 10);
  const m = parseInt(mesRef.slice(4), 10);
  let mIni = m - 11;
  let anoIni = ano;
  if (mIni <= 0) {
    mIni += 12;
    anoIni -= 1;
  }
  const dois = (n) => String(n).padStart(2, "0");
  return [`01/${dois(mIni)}/${anoIni}`, `28/${dois(m)}/${ano}`];
}

/** Registros da série SGS no intervalo. Devolve [] em caso de erro. */
async function sgsFetch(codigo, ini, fim) {
  const url =
    BASE_SGS.replace("{}", String(codigo)) +
    `?formato=json&dataInicial=${encodeURIComponent(ini)}` +
    `&dataFinal=${encodeURIComponent(fim)}`;
  try {
    // Timeout espelha o httpx.get(timeout=30) do Python. Sem ele, uma serie
    // pendurada travaria a nota inteira; com ele, a falha vira [] e o bloco
    // correspondente some da nota — que e a politica do projeto.
    const resp = await fetch(url, { signal: AbortSignal.timeout(30000) });
    if (!resp.ok) return [];
    return (await resp.json()) ?? [];
  } catch {
    return [];
  }
}

function parseFloatBr(s) {
  if (s === null || s === undefined) return null;
  const v = Number(String(s).replace(",", "."));
  return Number.isNaN(v) ? null : v;
}

/** Valor da série para mesRef (AAAAMM), ou null se indisponível. */
async function buscarValorMes(codigo, mesRef) {
  const m = mesRef.slice(4);
  const a = mesRef.slice(0, 4);
  const data = `01/${m}/${a}`;
  const dados = await sgsFetch(codigo, data, data);
  if (dados.length === 0) return null;
  return parseFloatBr(dados[0].valor);
}

/**
 * Acumulado em 12 meses (composto) da série SGS encerrado em mesRef.
 * Devolve null se a série tiver menos de 12 observações no período.
 */
async function acum12mSgs(codigo, mesRef) {
  const [ini, fim] = intervalo12m(mesRef);
  const dados = await sgsFetch(codigo, ini, fim);
  if (dados.length < 12) return null;
  let prod = 1.0;
  for (const d of dados) {
    const val = parseFloatBr(d.valor);
    if (val === null) return null;
    prod *= 1 + val / 100;
  }
  return arredondar((prod - 1) * 100, 4);
}

// ---------------------------------------------------------------------------
// API pública
// ---------------------------------------------------------------------------

/**
 * Média aritmética dos acumulados em 12m dos núcleos MS+EX0+DP+EX3+P55.
 *
 * Devolve null se QUALQUER uma das séries falhar. Uma média parcial é pior
 * que a ausência do dado: com 4 de 5 séries o número publicado desloca em até
 * 0,09 p.p. (ex.: 12m até mar/2026 = 4,39% com as 5 séries, 4,44% sem a DP)
 * sem qualquer sinal de erro. O bloco de núcleo é opcional na nota — omiti-lo
 * é seguro, publicá-lo errado não é.
 */
export async function mediaNucleos12m(mesRef) {
  // NÃO paralelizar com Promise.all. Já foi tentado: disparar as 5 séries de
  // uma vez (12 requisições simultâneas somando os dois meses) faz o SGS
  // derrubar parte delas, e a nota sai sem a comparação com o mês anterior.
  // O ganho seria ~1s; o custo é perder um número. Mantém-se em série.
  const vals = [];
  for (const nome of CONJUNTO_MEDIA) {
    const v = await acum12mSgs(NUCLEOS[nome], mesRef);
    if (v === null) return null;
    vals.push(v);
  }
  const soma = vals.reduce((a, b) => a + b, 0);
  return arredondar(soma / vals.length, 4);
}

/**
 * Preenche difusao, difusao_anterior, nucleo_12m e nucleo_12m_anterior no
 * ResultadoInflacao fornecido. Falhas deixam os campos em null.
 *
 * IPCA:
 *   difusao / difusao_anterior → SGS 21379
 *   nucleo_12m / nucleo_12m_anterior → média MS+EX0+DP+EX3+P55 em 12m
 *
 * IPCA-15:
 *   difusao → calculada dos subitens (nivel 4) já presentes em resultado
 *   difusao_anterior → null (requer fetch extra do IBGE; não implementado)
 *   nucleo_12m → null (BCB não publica núcleo do IPCA-15)
 */
export async function enriquecer(resultado) {
  if (resultado.indicador === "IPCA") {
    // Em série, pelo mesmo motivo descrito em mediaNucleos12m: o SGS não
    // tolera a rajada e passa a devolver menos dados do que existe.
    resultado.difusao = await buscarValorMes(SGS_DIFUSAO_IPCA, resultado.mes_ref);
    resultado.difusao_anterior = await buscarValorMes(
      SGS_DIFUSAO_IPCA,
      resultado.mes_ant,
    );
    resultado.nucleo_12m = await mediaNucleos12m(resultado.mes_ref);
    resultado.nucleo_12m_anterior = await mediaNucleos12m(resultado.mes_ant);
  } else {
    resultado.difusao = calcularDifusao(resultado.subitens, 4);
    resultado.difusao_anterior = null;
    resultado.nucleo_12m = null;
    resultado.nucleo_12m_anterior = null;
  }
}
