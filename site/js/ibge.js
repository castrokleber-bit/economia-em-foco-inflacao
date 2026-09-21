/* Fetcher IBGE — tabelas SIDRA 7060 (IPCA) e 7062 (IPCA-15).
 * Par de fontes/ibge.py.
 *
 * IDs de variáveis e categorias verificados nos metadados em jun/2026.
 * Não alterar sem re-verificar em:
 *   https://servicodados.ibge.gov.br/api/v3/agregados/{tabela}/metadados
 */
import { ItemInflacao, ResultadoInflacao } from "./modelo.js";

const BASE = "https://servicodados.ibge.gov.br/api/v3/agregados";

// Variáveis por indicador — IDs verificados nos metadados em jun/2026
const CONF = {
  IPCA: { tabela: 7060, var_mensal: 63, var_acum12m: 2265, var_peso: 66 },
  "IPCA-15": { tabela: 7062, var_mensal: 355, var_acum12m: 1120, var_peso: 357 },
};

// Classificação 315 — IDs verificados nos metadados em jun/2026
const CAT_GERAL = 7169;
const CATS_GRUPO = [7170, 7445, 7486, 7558, 7625, 7660, 7712, 7766, 7786];

// ---------------------------------------------------------------------------
// Helpers internos
// ---------------------------------------------------------------------------

function mesAnterior(mes) {
  const ano = parseInt(mes.slice(0, 4), 10);
  const m = parseInt(mes.slice(4), 10);
  if (m === 1) return `${ano - 1}12`;
  return `${ano}${String(m - 1).padStart(2, "0")}`;
}

function mesmoMesAnoAnterior(mes) {
  return `${parseInt(mes.slice(0, 4), 10) - 1}${mes.slice(4)}`;
}

/**
 * Infere o nível hierárquico pelo comprimento do prefixo numérico no nome.
 * Padrão IBGE:
 *   sem prefixo  → 0 (Índice geral)
 *   1 dígito     → 1 (grupo)
 *   2 dígitos    → 2 (subgrupo)
 *   4 dígitos    → 3 (item)
 *   7 dígitos    → 4 (subitem)
 */
function nivelFromNome(nome) {
  const m = /^([0-9]+)\./.exec(nome);
  if (!m) return 0;
  const n = m[1].length;
  if (n === 1) return 1;
  if (n === 2) return 2;
  if (n === 4) return 3;
  if (n === 7) return 4;
  return -1;
}

function parseFloatBr(s) {
  if (s === null || s === undefined) return null;
  const t = String(s).trim();
  if (t === "..." || t === "-" || t === "") return null;
  const v = Number(t.replace(",", "."));
  return Number.isNaN(v) ? null : v;
}

/**
 * Chama a API de Agregados e devolve Map<varId, Map<catId, {nome, valor}>>.
 *
 * Usa Map, e não objeto literal, para preservar a ordem da resposta: o Python
 * itera o dict na ordem de inserção e empates de impacto são resolvidos por
 * ela. Chaves numéricas num objeto JS seriam reordenadas para ordem crescente
 * e mudariam qual item a nota cita.
 */
async function fetchAgregado(tabela, periodo, variaveis, cats) {
  const varsStr = variaveis.join("|");
  const catsStr = cats === "all" ? "all" : cats.join(",");
  const url =
    `${BASE}/${tabela}/periodos/${periodo}/variaveis/${varsStr}` +
    `?localidades=N1[all]&classificacao=315[${catsStr}]`;

  const resp = await fetch(url);
  if (!resp.ok) {
    throw new Error(`IBGE respondeu ${resp.status} para ${tabela}/${periodo}`);
  }
  const data = await resp.json();

  const result = new Map();
  for (const bloco of data) {
    const varId = parseInt(bloco.id, 10);
    const porCat = new Map();
    for (const entrada of bloco.resultados ?? []) {
      const catD = entrada.classificacoes[0].categoria;
      const catIdStr = Object.keys(catD)[0];
      const catId = parseInt(catIdStr, 10);
      const catNome = catD[catIdStr];
      const series = entrada.series ?? [];
      if (series.length === 0) continue;
      const valor = parseFloatBr(series[0].serie[periodo]);
      if (valor !== null) porCat.set(catId, { nome: catNome, valor });
    }
    result.set(varId, porCat);
  }
  return result;
}

function exigir(mapa, varId, catId, contexto) {
  const porCat = mapa.get(varId);
  const entrada = porCat ? porCat.get(catId) : undefined;
  if (!entrada) {
    throw new Error(`dado indisponível (${contexto})`);
  }
  return entrada;
}

// ---------------------------------------------------------------------------
// API pública
// ---------------------------------------------------------------------------

/**
 * Busca o resultado do IPCA ou IPCA-15 para o período (AAAAMM) e devolve um
 * ResultadoInflacao com grupos e subitens ordenados por impacto.
 *
 * difusao, nucleo e projeções ficam null; preenchidos por bcb.enriquecer().
 */
export async function buscarResultado(indicador, mesRef) {
  const conf = CONF[indicador];
  if (!conf) throw new Error(`indicador desconhecido: ${indicador}`);
  const tab = conf.tabela;
  const vm = conf.var_mensal;
  const va12 = conf.var_acum12m;
  const vp = conf.var_peso;
  const mesAnt = mesAnterior(mesRef);
  const fonte = `IBGE SIDRA tabela ${tab}`;

  // 1. Índice geral — mês de referência
  const dCur = await fetchAgregado(tab, mesRef, [vm, va12], [CAT_GERAL]);
  const variacaoMensal = exigir(dCur, vm, CAT_GERAL, `${indicador} ${mesRef}`).valor;
  const acum12m = exigir(dCur, va12, CAT_GERAL, `${indicador} ${mesRef}`).valor;

  // 2. Índice geral — mês anterior
  const dAnt = await fetchAgregado(tab, mesAnt, [vm, va12], [CAT_GERAL]);
  const variacaoMensalAnterior = exigir(dAnt, vm, CAT_GERAL, `${indicador} ${mesAnt}`).valor;
  const acum12mAnterior = exigir(dAnt, va12, CAT_GERAL, `${indicador} ${mesAnt}`).valor;

  // 2b. Mesmo mês do ano anterior (comparação interanual no blocoResultado)
  const mesAnoAnt = mesmoMesAnoAnterior(mesRef);
  let variacaoMesmoMesAnoAnterior = null;
  try {
    const dAnoAnt = await fetchAgregado(tab, mesAnoAnt, [vm], [CAT_GERAL]);
    variacaoMesmoMesAnoAnterior = exigir(dAnoAnt, vm, CAT_GERAL, mesAnoAnt).valor;
  } catch {
    variacaoMesmoMesAnoAnterior = null;
  }

  // 3. Grupos — variação + peso, mês de referência
  const dG = await fetchAgregado(tab, mesRef, [vm, vp], CATS_GRUPO);
  const grupos = [];
  for (const catId of CATS_GRUPO) {
    const entryVm = dG.get(vm)?.get(catId);
    const entryVp = dG.get(vp)?.get(catId);
    if (entryVm && entryVp) {
      grupos.push(
        new ItemInflacao({
          cat_id: catId,
          nome: entryVm.nome,
          nivel: 1,
          variacao: entryVm.valor,
          peso: entryVp.valor,
          fonte: `${fonte} var ${vm},${vp} periodo ${mesRef}`,
        }),
      );
    }
  }
  grupos.sort((a, b) => b.impacto - a.impacto);

  // 4. Todos os itens (nível >= 2) — variação + peso, mês de referência
  //    Usado para encontrar o subitem de maior impacto individual
  const dAll = await fetchAgregado(tab, mesRef, [vm, vp], "all");
  const subitens = [];
  for (const [catId, entrada] of dAll.get(vm) ?? new Map()) {
    const nivel = nivelFromNome(entrada.nome);
    if (nivel < 2) continue;
    const entryVp = dAll.get(vp)?.get(catId);
    if (!entryVp) continue;
    subitens.push(
      new ItemInflacao({
        cat_id: catId,
        nome: entrada.nome,
        nivel,
        variacao: entrada.valor,
        peso: entryVp.valor,
        fonte: `${fonte} var ${vm},${vp} periodo ${mesRef}`,
      }),
    );
  }
  subitens.sort((a, b) => b.impacto - a.impacto);

  return new ResultadoInflacao({
    indicador,
    mes_ref: mesRef,
    mes_ant: mesAnt,
    variacao_mensal: variacaoMensal,
    variacao_mensal_anterior: variacaoMensalAnterior,
    acum_12m: acum12m,
    acum_12m_anterior: acum12mAnterior,
    grupos,
    subitens,
    variacao_mesmo_mes_ano_anterior: variacaoMesmoMesAnoAnterior,
    fonte_variacao: `${fonte} var ${vm} periodo ${mesRef}`,
    fonte_acum: `${fonte} var ${va12} periodo ${mesRef}`,
  });
}
