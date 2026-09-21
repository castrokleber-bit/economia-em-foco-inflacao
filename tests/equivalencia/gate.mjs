/* Gate de equivalência Python ⇄ JavaScript.
 *
 *   node tests/equivalencia/gate.mjs
 *
 * Para cada fixture capturada por dump_python.py, reconstrói o mesmo
 * ResultadoInflacao, roda o montador JS e exige saída idêntica à do Python
 * (byte a byte) e idêntica à nota golden.
 *
 * É a barreira que substitui o pytest como prova do port: enquanto ela passar,
 * o JS publicado no site produz exatamente a nota que o Python validado produz.
 */
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { ItemInflacao, ResultadoInflacao } from "../../site/js/modelo.js";
import { comporNota } from "../../site/js/montador.js";

const AQUI = dirname(fileURLToPath(import.meta.url));
const FIXTURES = join(AQUI, "fixtures");
const GOLDEN = join(AQUI, "..", "golden");

// fixture -> nota golden correspondente
const GOLDEN_DE = {
  ipca_202604: "ipca_abril2026.txt",
  ipca15_202605: "ipca15_maio2026.txt",
};

/**
 * Lê texto normalizando CRLF para LF.
 *
 * Não afrouxa o gate: as duas implementações montam a nota com \n, e o fim de
 * linha no disco é artefato do git (core.autocrlf=true entrega CRLF no Windows
 * e LF no CI). Sem isso o mesmo commit passaria numa máquina e falharia noutra
 * por um motivo que não tem nada a ver com o texto da nota.
 */
function lerTexto(caminho) {
  return readFileSync(caminho, "utf-8").replace(/\r\n/g, "\n");
}

function reidratar(dados) {
  return new ResultadoInflacao({
    ...dados,
    grupos: dados.grupos.map((i) => new ItemInflacao(i)),
    subitens: dados.subitens.map((i) => new ItemInflacao(i)),
  });
}

/** Primeira divergência, com contexto — mais útil que um diff inteiro. */
function primeiraDiferenca(obtido, esperado) {
  const a = obtido.split("\n");
  const b = esperado.split("\n");
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    if (a[i] !== b[i]) {
      return [
        `  linha ${i + 1}:`,
        `    python/golden: ${JSON.stringify(b[i] ?? "<ausente>")}`,
        `    javascript   : ${JSON.stringify(a[i] ?? "<ausente>")}`,
      ].join("\n");
    }
  }
  return "  (diferença apenas em espaços no fim do texto)";
}

function comparar(rotulo, obtido, esperado, falhas) {
  if (obtido === esperado) {
    console.log(`  ok   ${rotulo}`);
  } else {
    console.log(`  FALHA ${rotulo}`);
    console.log(primeiraDiferenca(obtido, esperado));
    falhas.push(rotulo);
  }
}

function main() {
  let casos;
  try {
    casos = readdirSync(FIXTURES)
      .filter((f) => f.endsWith(".json"))
      .map((f) => f.replace(/\.json$/, ""));
  } catch {
    console.error(
      "fixtures ausentes — rode antes:\n" +
        "  python tests/equivalencia/dump_python.py",
    );
    return 1;
  }
  if (casos.length === 0) {
    console.error("nenhuma fixture encontrada em tests/equivalencia/fixtures");
    return 1;
  }

  const falhas = [];
  for (const caso of casos) {
    console.log(`\n${caso}`);
    const dados = JSON.parse(
      lerTexto(join(FIXTURES, `${caso}.json`)),
    );
    const notaJs = comporNota(reidratar(dados));

    const notaPy = lerTexto(join(FIXTURES, `${caso}.nota.txt`));
    comparar("JS identico ao Python", notaJs, notaPy, falhas);

    const arqGolden = GOLDEN_DE[caso];
    if (arqGolden) {
      const golden = lerTexto(join(GOLDEN, arqGolden));
      comparar(`JS identico ao golden (${arqGolden})`, notaJs, golden, falhas);
    }
  }

  console.log("");
  if (falhas.length > 0) {
    console.error(`GATE VERMELHO — ${falhas.length} comparacao(oes) falharam`);
    return 1;
  }
  console.log(`GATE VERDE — ${casos.length} caso(s), nota identica em todos`);
  return 0;
}

process.exit(main());
