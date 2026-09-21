/* Aritmética e formatação — equivalentes exatos das funções Python.
 *
 * Este módulo é a fronteira mais delicada do port. Cada função aqui tem um
 * par em Python e precisa devolver o MESMO resultado bit a bit, senão a nota
 * sai com número diferente do backtest sem nada acusar.
 */

/**
 * Equivalente de round(x, n) do Python.
 *
 * Python arredonda para o par em caso de empate; toFixed do JS arredonda para
 * o maior. A diferença nunca se materializa aqui: um empate exato exigiria que
 * x * 10^n fosse exatamente k + 0,5, ou seja x = (2k+1)/(2*10^n). Para n >= 1
 * esse denominador carrega fator 5^n, então o número não é representável em
 * binário e o empate exato não existe entre doubles. Fora dos empates, ambos
 * arredondam corretamente para o mais próximo — logo são equivalentes.
 */
export function arredondar(x, n) {
  return Number(x.toFixed(n));
}

/**
 * Equivalente de montador._fmt — vírgula decimal e arredondamento HALF_UP.
 *
 * Porte literal, inclusive o erro de ponto flutuante embutido: em Python
 * 0,105 * 100 dá 10.499999999999998, que o floor derruba para 0,10 em vez de
 * 0,11. Reproduzir a fórmula (e não "consertá-la") é o que mantém o JS e o
 * Python idênticos.
 */
export function fmt(v, decimais = 2) {
  const factor = 10 ** decimais;
  let arredondado = Math.floor(Math.abs(v) * factor + 0.5) / factor;
  if (v < 0) arredondado = -arredondado;
  return arredondado.toFixed(decimais).replace(".", ",");
}

/** Substitui {chave} pelos valores de vars — equivalente do str.format nomeado. */
export function preencher(template, vars) {
  return template.replace(/\{(\w+)\}/g, (_, chave) => {
    if (!(chave in vars)) throw new Error(`chave ausente no template: ${chave}`);
    return vars[chave];
  });
}
