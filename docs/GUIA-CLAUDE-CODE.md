# Guia de Construção no Claude Code

Sequência para construir o app **sem erros**, em etapas validadas. A ideia é
nunca avançar de etapa sem que a anterior passe no seu gate.

## 0. Pré-requisitos

- Python 3.11+ e `pip`
- Claude Code instalado e autenticado
- (Para a leitura por IA) chave da API Anthropic
- Nenhum ativo de marca: a interface usa fontes do sistema

## 1. Montar a pasta e ancorar a documentação

```bash
mkdir economia-em-foco-inflacao && cd economia-em-foco-inflacao
# copie para cá: CLAUDE.md, README.md, e a pasta docs/ (estes arquivos)
git init
```

Por que primeiro os docs: o `CLAUDE.md` é lido automaticamente pelo Claude Code
e ancora todo o comportamento. Com ele e os `docs/` no lugar, o Claude Code
trabalha dentro das suas regras (fronteira determinística, códigos verificados,
gates de validação) em vez de improvisar.

## 2. Abrir o Claude Code e checar o entendimento

```bash
claude
```

Primeiro prompt (não peça código ainda — peça o plano):

> "Leia CLAUDE.md e tudo em docs/. Resuma em até 10 linhas o que vamos construir,
> a fronteira determinística e os 5 gates de validação. Liste a ordem de
> implementação que você seguiria. Não escreva código ainda."

Confira se o resumo bate com a especificação. Corrija o entendimento antes de
qualquer linha de código. Isso evita 80% do retrabalho.

## 3. Ambiente e dependências

> "Crie `requirements.txt` (httpx e pytest — a implementacao de referencia
> em Python) e o esqueleto de pastas do CLAUDE.md com arquivos vazios.
> Crie e ative um venv e instale as dependências."

Gate: `pip install -r requirements.txt` roda sem erro.

## 4. Camada de dados primeiro (uma fonte por vez, com teste real)

Ordem: **IBGE → impacto → BCB difusão → BCB núcleo**.

> "Implemente `fontes/ibge.py` consumindo a tabela 7060 conforme
> docs/FONTES-DE-DADOS.md. **Antes**, leia os metadados em
> `…/agregados/7060/metadados` e confirme os IDs de variáveis e classificações —
> não hardcode IDs sem ler os metadados. Escreva um teste que busca abril/2026 e
> mostra variação geral, acum. 12m, e a lista de grupos com variação e peso."

Gate: o teste imprime 0,67% (mensal) e 4,39% (12m) para o IPCA de abr/2026.

> "Implemente `nucleo/impacto.py` (impacto = peso×variação/100) e valide contra
> os impactos divulgados de abr/2026 (Alim. e bebidas 0,29 p.p. etc.), tolerância
> 0,01 p.p. Se não bater, teste o peso do mês anterior."

Gate: impactos batem dentro da tolerância. **Não avance sem fechar.**

> "Implemente em `fontes/bcb.py` a difusão (SGS 21379) e a média dos núcleos
> conforme docs/FONTES-DE-DADOS.md. Para a média dos núcleos, valide o conjunto
> de séries contra 4,38% (abr/2026); documente qual conjunto fechou. O fetcher do
> núcleo deve retornar None (sem exceção) quando o mês ainda não existe."

Gate: difusão lê 65,3% (abr/2026); média dos núcleos reproduz 4,38%.

## 5. Montador determinístico + golden tests

> "Crie `tests/golden/` com as duas notas-padrão (vou colar o texto). Implemente
> `nucleo/montador.py` com **uma função por bloco** (título, resultado,
> explicação, acumulado, núcleo, difusão, assinatura, link) e uma função que
> compõe tudo. Sem biblioteca de template; f-strings. Trate concordância de
> direção (alta/queda, acima/abaixo) e o plural de p.p. Escreva
> `tests/test_montador.py` comparando a saída com os golden, caractere a
> caractere."

Gate: `pytest` passa — saída idêntica às duas notas. Inclua um teste de IPCA
**sem** núcleo (núcleo = None) que não quebra e omite o bloco.

## 6. Interface (página estática)

> "Implemente `site/js/app.js`, que busca os dados, monta a nota e exibe a
> proveniência dos números. Crie `site/` (index.html,
> style.css, app.js) seguindo docs/IDENTIDADE-VISUAL.md: paleta neutra escura
> definida em variáveis CSS, fontes do sistema, sem logo,
> minimalista. Botão copiar. A nota e o rascunho de leitura em cards separados."

Gate: `python -m http.server 8777 --directory site`, gerar IPCA abr/2026
reproduz a nota na tela.

## 7. Leitura por IA (último, isolado)

> "Implemente `nucleo/leitura.py`: recebe SÓ os dados já apurados e chama a API
> Anthropic para 2–4 frases de leitura para a indústria, conforme a seção 7 da
> especificação. Rotular 'RASCUNHO'. A IA não toca em número da nota. Se a chave
> não estiver configurada, o app funciona sem a leitura."

Gate: leitura aparece em bloco separado; desligar a chave não quebra o app.

## 8. Erros comuns a evitar

- **Códigos de API chutados** → sempre dos `docs/`/metadados. Causa nº 1 de bug.
- **Misturar IA na nota** → quebra a fronteira determinística; revisar o diff.
- **Núcleo obrigatório** → tem de ser opcional (None-safe), senão a nota falha
  nos meses sem núcleo.
- **Avançar com gate vermelho** → cada etapa valida antes da próxima.
- **Arredondamento** → fixar 2 casas e validar contra o golden; divergência de
  0,01 quase sempre é arredondamento/peso, não erro de fetch.
- **CSP/sandbox** → as APIs IBGE/BCB funcionam de um backend Python local; não
  tente chamá-las direto do JS do navegador (CORS/CSP).

## 9. Rotina de uso (depois de pronto)

1. IBGE divulga (IPCA ~9h; IPCA-15 em data própria).
2. Rodar o app → gerar a nota → conferir proveniência.
3. Copiar para o WhatsApp (até 09h15).
4. Avaliar/editar o rascunho de leitura, se for usar.
