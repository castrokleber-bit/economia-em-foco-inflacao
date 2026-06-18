/* Economia em Foco — Inflação · CNI
   Frontend logic: busca /gerar, renderiza nota, botão copiar.
   Não envia dados para fora; circulação é sempre decisão humana.
*/

// ── Inicialização ──────────────────────────────────────────────
const form     = document.getElementById('form-gerar');
const btnGerar = document.getElementById('btn-gerar');
const btnCopiar = document.getElementById('btn-copiar');
const inputMes = document.getElementById('mes');
const loading  = document.getElementById('loading');
const erroBloco = document.getElementById('erro-bloco');
const erroMsg  = document.getElementById('erro-msg');
const resultado = document.getElementById('resultado');
const notaTexto = document.getElementById('nota-texto');
const provenencia = document.getElementById('provenencia');
const leituraCard = document.getElementById('leitura-card');
const leituraTexto = document.getElementById('leitura-texto');

let notaRaw = '';

// Padrão: mês anterior (dados costumam não estar disponíveis no mês corrente)
(function definirMesPadrao() {
  const agora = new Date();
  const mesAnt = new Date(agora.getFullYear(), agora.getMonth() - 1, 1);
  const ano = mesAnt.getFullYear();
  const mes = String(mesAnt.getMonth() + 1).padStart(2, '0');
  inputMes.value = `${ano}-${mes}`;
})();

// ── Submit ────────────────────────────────────────────────────
form.addEventListener('submit', async function (e) {
  e.preventDefault();
  await gerarNota();
});

async function gerarNota() {
  const indicador = document.querySelector('input[name="indicador"]:checked').value;
  const mesInput  = inputMes.value;          // "YYYY-MM"

  if (!mesInput) {
    mostrarErro('Informe o mês de referência.');
    return;
  }

  const mes = mesInput.replace('-', '');     // "YYYYMM"

  setEstado('loading');

  try {
    const url  = `/gerar?indicador=${encodeURIComponent(indicador)}&mes=${mes}`;
    const resp = await fetch(url);
    const data = await resp.json();

    if (!resp.ok) {
      mostrarErro(data.detail || 'Erro desconhecido na API.');
      return;
    }

    exibirResultado(data);
  } catch (err) {
    mostrarErro('Falha de conexão: ' + err.message);
  }
}

// ── Renderização ──────────────────────────────────────────────

/**
 * Converte markdown estilo WhatsApp para HTML.
 *   _*texto*_ → <em><strong>texto</strong></em>
 *   *texto*   → <strong>texto</strong>
 *   _texto_   → <em>texto</em>
 *   \n        → <br>
 * A correspondência é gulosa para evitar spans quebrados.
 */
function renderWA(texto) {
  return texto
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // bold-italic: _*...*_  (processar antes do bold e itálico separados)
    .replace(/_\*([^*\n]+)\*_/g, '<em><strong>$1</strong></em>')
    // bold: *...*
    .replace(/\*([^*\n]+)\*/g, '<strong>$1</strong>')
    // italic: _..._
    .replace(/_([^_\n]+)_/g, '<em>$1</em>')
    // quebras de linha
    .replace(/\n/g, '<br>');
}

function exibirResultado(data) {
  notaRaw = data.nota;
  notaTexto.innerHTML = renderWA(data.nota);

  // Proveniência
  provenencia.innerHTML = data.provenencia.map(p => `
    <div class="prov-linha">
      <span class="prov-campo">${p.campo}</span>
      <span class="prov-fonte">${p.fonte} · ${p.mes}</span>
      <span class="prov-valor">${p.valor}</span>
    </div>
  `).join('');

  // Leitura por IA (Etapa 7 — opcional)
  if (data.leitura_rascunho) {
    leituraTexto.textContent = data.leitura_rascunho;
    leituraCard.style.display = 'block';
  } else {
    leituraCard.style.display = 'none';
  }

  setEstado('resultado');
  resultado.style.display = 'block';
  resultado.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── Copiar ────────────────────────────────────────────────────
btnCopiar.addEventListener('click', async function () {
  if (!notaRaw) return;
  try {
    await navigator.clipboard.writeText(notaRaw);
    btnCopiar.textContent = '✓ Copiado';
    btnCopiar.classList.add('copiado');
    setTimeout(() => {
      btnCopiar.textContent = 'Copiar';
      btnCopiar.classList.remove('copiado');
    }, 2200);
  } catch {
    // Fallback para navegadores sem Clipboard API
    const ta = document.createElement('textarea');
    ta.value = notaRaw;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    btnCopiar.textContent = '✓ Copiado';
    btnCopiar.classList.add('copiado');
    setTimeout(() => {
      btnCopiar.textContent = 'Copiar';
      btnCopiar.classList.remove('copiado');
    }, 2200);
  }
});

// ── Estados da UI ─────────────────────────────────────────────
function setEstado(estado) {
  loading.style.display   = estado === 'loading'  ? 'flex'  : 'none';
  erroBloco.style.display = estado === 'erro'     ? 'block' : 'none';
  btnGerar.disabled       = estado === 'loading';
}

function mostrarErro(msg) {
  erroMsg.textContent = msg;
  setEstado('erro');
  resultado.style.display = 'none';
}
