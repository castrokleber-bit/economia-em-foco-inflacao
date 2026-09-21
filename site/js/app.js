/* Interface — busca os dados, monta a nota e exibe para cópia.
 *
 * Não envia nada para servidor nenhum: as chamadas vão direto do navegador
 * para as APIs públicas do IBGE e do Banco Central. Circular a nota é sempre
 * decisão humana — a página apenas exibe o texto.
 */
import { buscarResultado } from "./ibge.js";
import { enriquecer } from "./bcb.js";
import { comporNota } from "./montador.js";
import { fmt } from "./numeros.js";

const form = document.getElementById("form-gerar");
const btnGerar = document.getElementById("btn-gerar");
const btnCopiar = document.getElementById("btn-copiar");
const inputMes = document.getElementById("mes");
const loading = document.getElementById("loading");
const erroBloco = document.getElementById("erro-bloco");
const erroMsg = document.getElementById("erro-msg");
const resultado = document.getElementById("resultado");
const notaTexto = document.getElementById("nota-texto");
const tabelaProv = document.getElementById("provenencia");

let notaAtual = "";

const MESES_CURTO = {
  "01": "jan", "02": "fev", "03": "mar", "04": "abr",
  "05": "mai", "06": "jun", "07": "jul", "08": "ago",
  "09": "set", "10": "out", "11": "nov", "12": "dez",
};

// Padrão: mês anterior (os dados do mês corrente em geral ainda não saíram).
(function definirMesPadrao() {
  const agora = new Date();
  const anterior = new Date(agora.getFullYear(), agora.getMonth() - 1, 1);
  const ano = anterior.getFullYear();
  const m = String(anterior.getMonth() + 1).padStart(2, "0");
  inputMes.value = `${ano}-${m}`;
})();

function fmtMes(mesRef) {
  return `${MESES_CURTO[mesRef.slice(4)]}/${mesRef.slice(0, 4)}`;
}

function fmtPct(v, decimais = 2) {
  return `${fmt(v, decimais)}%`;
}

/** Tabela de proveniência: de qual tabela/série veio cada número exibido. */
function montarProveniencia(r) {
  const ipca = r.indicador === "IPCA";
  const tab = ipca ? "7060" : "7062";
  const vVar = ipca ? "V63" : "V355";
  const vAcum = ipca ? "V2265" : "V1120";
  const vPeso = ipca ? "V66" : "V357";
  const mes = fmtMes(r.mes_ref);

  const itens = [
    {
      campo: "Variação mensal",
      fonte: `IBGE SIDRA T${tab} ${vVar}`,
      mes,
      valor: fmtPct(r.variacao_mensal),
    },
    {
      campo: "Acumulado 12 meses",
      fonte: `IBGE SIDRA T${tab} ${vAcum}`,
      mes,
      valor: fmtPct(r.acum_12m),
    },
    {
      campo: "Pesos mensais (grupos)",
      fonte: `IBGE SIDRA T${tab} ${vPeso}`,
      mes,
      valor: "estrutura de pesos",
    },
  ];

  if (r.difusao !== null) {
    itens.push({
      campo: "Difusão",
      fonte: ipca
        ? "BCB SGS 21379"
        : `IBGE SIDRA T${tab} nível 4 (calculado)`,
      mes,
      valor: fmtPct(r.difusao, 1),
    });
  }

  if (r.nucleo_12m !== null) {
    itens.push({
      campo: "Núcleo médio 12m",
      fonte: "BCB SGS 4466 · 11427 · 16122 · 27839 · 28750 (MS+EX0+DP+EX3+P55)",
      mes,
      valor: fmtPct(r.nucleo_12m),
    });
  }

  return itens;
}

function renderProveniencia(itens) {
  const cabecalho =
    "<tr><th>Campo</th><th>Fonte</th><th>Período</th><th>Valor</th></tr>";
  const linhas = itens
    .map(
      (i) =>
        `<tr><td>${i.campo}</td><td class="fonte">${i.fonte}</td>` +
        `<td>${i.mes}</td><td>${i.valor}</td></tr>`,
    )
    .join("");
  tabelaProv.innerHTML = cabecalho + linhas;
}

function setEstado(estado) {
  loading.hidden = estado !== "loading";
  erroBloco.hidden = estado !== "erro";
  resultado.hidden = estado !== "ok";
  btnGerar.disabled = estado === "loading";
  btnGerar.textContent = estado === "loading" ? "Gerando…" : "Gerar nota";
}

function mostrarErro(msg) {
  erroMsg.textContent = msg;
  setEstado("erro");
}

async function gerarNota() {
  const indicador = document.querySelector(
    'input[name="indicador"]:checked',
  ).value;
  const mesInput = inputMes.value; // "AAAA-MM"

  if (!mesInput) {
    mostrarErro("Informe o mês de referência.");
    return;
  }
  const mes = mesInput.replace("-", ""); // "AAAAMM"

  setEstado("loading");

  let r;
  try {
    r = await buscarResultado(indicador, mes);
  } catch (e) {
    mostrarErro(
      `Dados não disponíveis para ${indicador} ${mes.slice(4)}/${mes.slice(0, 4)}. ` +
        "Verifique se o IBGE já divulgou o resultado do mês informado. " +
        `(${e.message})`,
    );
    return;
  }

  // Tudo daqui para baixo também precisa estar protegido: qualquer excecao
  // solta deixaria a interface presa em "Gerando…", sem erro e sem saida.
  try {
    // enriquecer() não lança: difusão e núcleo indisponíveis viram null e os
    // blocos correspondentes simplesmente não entram na nota.
    await enriquecer(r);

    notaAtual = comporNota(r);
    notaTexto.textContent = notaAtual;
    renderProveniencia(montarProveniencia(r));
    setEstado("ok");
  } catch (e) {
    mostrarErro(`Falha ao montar a nota: ${e.message}`);
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  gerarNota();
});

btnCopiar.addEventListener("click", async () => {
  if (!notaAtual) return;
  try {
    await navigator.clipboard.writeText(notaAtual);
    btnCopiar.textContent = "Copiado";
  } catch {
    // clipboard bloqueado (http, permissão negada): seleciona para Ctrl+C
    const sel = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(notaTexto);
    sel.removeAllRanges();
    sel.addRange(range);
    btnCopiar.textContent = "Selecionado — Ctrl+C";
  }
  setTimeout(() => {
    btnCopiar.textContent = "Copiar";
  }, 2000);
});
