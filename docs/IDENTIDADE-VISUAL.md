# Identidade visual — Nota de Inflação

Projeto pessoal, sem vínculo institucional. A interface é deliberadamente
neutra: nenhum logo, nenhuma marca, nenhuma fonte licenciada.

## Paleta

Definida como variáveis CSS em `site/style.css`, no `:root`. Para mudar o
visual, altere ali — nenhum valor de cor está repetido no resto da folha.

| Variável           | Valor     | Uso                                   |
|--------------------|-----------|---------------------------------------|
| `--fundo`          | `#0f172a` | fundo da página e da caixa da nota     |
| `--superficie`     | `#1e293b` | cartões                                |
| `--superficie-alta`| `#273449` | campos e opções dentro dos cartões     |
| `--borda`          | `#334155` | bordas e divisórias                    |
| `--texto`          | `#e2e8f0` | texto principal                        |
| `--texto-suave`    | `#94a3b8` | rótulos, legendas, proveniência        |
| `--destaque`       | `#2563eb` | botões e estado selecionado            |
| `--destaque-claro` | `#60a5fa` | links, foco, hover                     |
| `--erro`           | `#f87171` | título e borda do bloco de erro        |
| `--erro-fundo`     | `#3f1d1d` | fundo do bloco de erro                 |

Contraste: `--texto` sobre `--fundo` fica em ~13:1 e `--texto-suave` sobre
`--superficie` em ~5,5:1 — ambos acima do mínimo AA (4,5:1) para texto normal.
Ao trocar cores, verifique o contraste antes de fixar.

## Tipografia

Fontes do sistema, sem webfont: `system-ui` com a cadeia usual de fallback.
Evita requisição externa, licenciamento e o salto de layout do carregamento.

A nota em si usa monoespaçada (`ui-monospace`, Cascadia Mono, Consolas) com
`font-variant-ligatures: none`. A desativação das ligaduras não é enfeite:
sem ela, algumas monoespaçadas fundem sequências e atrapalham a conferência
visual de números e do `i`/`I`/`l` antes de o texto ir para o WhatsApp.

## Layout

- Coluna única, `max-width: 760px`, centralizada.
- Cantos arredondados uniformes via `--raio` (10px).
- Quebra em 600px: cartões com menos respiro e cabeçalho do resultado empilhado.
- Foco sempre visível (`:focus-visible` com contorno de 2px), inclusive nas
  opções de indicador, que são `label` com `input` dentro.

## Regra que não é estética

`[hidden] { display: none !important; }` no topo da folha. O `display: none`
que o navegador dá a `[hidden]` vem da folha do agente e perde para qualquer
regra de classe com `display` — e `.aviso` usa `flex`. Sem esse reforço,
esconder um bloco pelo JS não surte efeito e carregando/erro/resultado
aparecem ao mesmo tempo na tela.
