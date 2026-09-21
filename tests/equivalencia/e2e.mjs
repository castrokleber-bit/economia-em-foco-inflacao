/* Gate ponta a ponta do JavaScript contra as APIs reais.
 *
 *   node tests/equivalencia/e2e.mjs
 *
 * O gate.mjs parte de uma fixture e portanto não exercita ibge.js nem bcb.js.
 * Este aqui fecha essa lacuna: busca no IBGE e no BCB, monta a nota só com o
 * JS e exige que seja idêntica à golden. Valida o que a fixture pula —
 * inferência de nível, ordem de iteração, desempate de impacto, composição do
 * núcleo em 12m e cálculo da difusão do IPCA-15.
 *
 * Depende de rede: equivale aos testes marcados como `integration` no pytest.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { buscarResultado } from "../../site/js/ibge.js";
import { enriquecer } from "../../site/js/bcb.js";
import { comporNota } from "../../site/js/montador.js";

const AQUI = dirname(fileURLToPath(import.meta.url));
const GOLDEN = join(AQUI, "..", "golden");
const FIXTURES = join(AQUI, "fixtures");

const CASOS = [
  { indicador: "IPCA", mes: "202604", golden: "ipca_abril2026.txt", fixture: "ipca_202604" },
  { indicador: "IPCA-15", mes: "202605", golden: "ipca15_maio2026.txt", fixture: "ipca15_202605" },
];

function lerTexto(caminho) {
  return readFileSync(caminho, "utf-8").replace(/\r\n/g, "\n");
}

function primeiraDiferenca(obtido, esperado) {
  const a = obtido.split("\n");
  const b = esperado.split("\n");
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    if (a[i] !== b[i]) {
      return [
        `  linha ${i + 1}:`,
        `    golden    : ${JSON.stringify(b[i] ?? "<ausente>")}`,
        `    javascript: ${JSON.stringify(a[i] ?? "<ausente>")}`,
      ].join("\n");
    }
  }
  return "  (diferença apenas em espaços no fim do texto)";
}

/**
 * Compara os dados brutos com a fixture do Python para localizar a origem de
 * uma divergência: se a nota difere mas os dados batem, o erro está no
 * montador; se os dados já diferem, está no fetcher.
 */
function conferirDados(r, caso) {
  let fx;
  try {
    fx = JSON.parse(lerTexto(join(FIXTURES, `${caso.fixture}.json`)));
  } catch {
    return; // fixture ausente: diagnóstico extra indisponível, segue o jogo
  }
  const problemas = [];
  const escalares = [
    "variacao_mensal", "variacao_mensal_anterior", "acum_12m",
    "acum_12m_anterior", "difusao", "difusao_anterior",
    "nucleo_12m", "nucleo_12m_anterior",
  ];
  for (const campo of escalares) {
    if (r[campo] !== fx[campo]) {
      problemas.push(`    ${campo}: js=${r[campo]} python=${fx[campo]}`);
    }
  }
  if (r.subitens.length !== fx.subitens.length) {
    problemas.push(
      `    nº de subitens: js=${r.subitens.length} python=${fx.subitens.length}`,
    );
  } else {
    // A ordem importa: ela resolve empates de impacto.
    for (let i = 0; i < r.subitens.length; i++) {
      if (r.subitens[i].cat_id !== fx.subitens[i].cat_id) {
        problemas.push(
          `    ordem dos subitens diverge na posição ${i}: ` +
            `js=${r.subitens[i].cat_id} python=${fx.subitens[i].cat_id}`,
        );
        break;
      }
    }
  }
  if (problemas.length > 0) {
    console.log("  dados brutos divergem da fixture do Python:");
    console.log(problemas.join("\n"));
  } else {
    console.log("  dados brutos idênticos aos da fixture do Python");
  }
}

async function main() {
  const falhas = [];
  for (const caso of CASOS) {
    console.log(`\n${caso.indicador} ${caso.mes}`);
    const r = await buscarResultado(caso.indicador, caso.mes);
    await enriquecer(r);

    if (caso.indicador === "IPCA" && r.nucleo_12m === null) {
      console.log(
        "  [aviso] nucleo_12m veio null — alguma série do SGS não respondeu.\n" +
          "          A nota omite o bloco de núcleo e vai divergir da golden.",
      );
    }

    conferirDados(r, caso);

    const nota = comporNota(r);
    const golden = lerTexto(join(GOLDEN, caso.golden));
    if (nota === golden) {
      console.log(`  ok   nota identica a golden (${caso.golden})`);
    } else {
      console.log(`  FALHA nota difere da golden (${caso.golden})`);
      console.log(primeiraDiferenca(nota, golden));
      falhas.push(caso.golden);
    }
  }

  console.log("");
  if (falhas.length > 0) {
    console.error(`E2E VERMELHO — ${falhas.length} nota(s) divergiram`);
    return 1;
  }
  console.log(`E2E VERDE — ${CASOS.length} caso(s) reproduzidos da API real`);
  return 0;
}

process.exit(await main());
