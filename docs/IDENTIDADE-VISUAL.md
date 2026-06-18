# Identidade Visual — interface do app

> Baseado no **Manual de Marcas do Sistema Indústria (CNI), v1.0, ago/2024**.
> Estética minimalista, com a logomarca da CNI e a fonte institucional.

## 1. Cores oficiais (Manual de Marcas 2024)

| Cor | HEX | RGB | Pantone | Uso |
|---|---|---|---|---|
| **Azul CNI (escuro)** | `#164194` | 22 / 65 / 148 | 293 C | Cor principal: cabeçalho, títulos, marca |
| **Azul CNI (claro)** | `#008BD2` | 0 / 139 / 210 | Medium Blue C | Detalhe/realce (o "pingo do i", botões, links) |

Neutros sugeridos (não normativos, para o minimalismo):
- Fundo: `#FFFFFF` / `#F5F7FA`
- Texto: `#1A1A1A`
- Bordas/divisores: `#E2E8F0`

> Observação: registros internos antigos citavam `#002F6C`/`#005CA9`. **O padrão
> vigente do manual 2024 é `#164194` e `#008BD2`** — usar estes.

## 2. Tipografia — Neo Sans Pro

O manual define **Neo Sans Pro** (Italic e Black Italic) como fonte das marcas.
Para a interface, usar Neo Sans Pro como fonte principal.

> ⚠️ **Licenciamento:** Neo Sans Pro é fonte comercial (Monotype). Não é
> gratuita nem redistribuível. Para usar no app:
> - obter os arquivos licenciados (`.woff2`/`.otf`) com a área responsável (a
>   CNI já licencia a fonte para suas peças — verificar com a DIRCOM/comunicação);
> - hospedar localmente em `app/static/fonts/` e declarar via `@font-face`;
> - **não** baixar de fontes piratas.
>
> **Fallback para desenvolvimento** (enquanto a fonte não está disponível), usar
> uma sans-serif geométrica próxima e deixar claro que é provisória:
> ```css
> font-family: "Neo Sans Pro", "Manrope", "Segoe UI", system-ui, sans-serif;
> ```
> (Manrope/Mulish, gratuitas no Google Fonts, têm proporção arredondada
> semelhante ao "design mais arredondado" descrito no manual.)

## 3. Logomarca

- Usar a **versão oficial** fornecida pela DIRCOM/Comunicação da CNI. **Não
  recriar** a marca (regra explícita do manual).
- Versão preferencial: **principal em cores**; em fundo escuro, usar a
  **negativa (branca)**.
- **Área de proteção:** margem livre mínima de `2x` ao redor, onde `x` = o pingo
  do "i" da marca. Não colocar texto/elemento dentro dessa margem.
- **Redução máxima** (digital desktop): altura mínima ~30 px; em cards/topo do
  app, manter a marca confortavelmente acima disso.
- **Não** distorcer proporções, **não** remover nem alterar elementos.
- Arquivo em `app/static/img/cni-logo.svg` (preferir SVG).

## 4. Layout minimalista (proposta)

Tela única, foco na nota:

```
┌──────────────────────────────────────────────┐
│  [logo CNI]        Economia em Foco · Inflação │  ← faixa #164194, texto branco
├──────────────────────────────────────────────┤
│  Indicador: ( IPCA ) ( IPCA-15 )   Mês: [....] │
│  [ Gerar nota ]                                │  ← botão #008BD2
├──────────────────────────────────────────────┤
│  ┌──────────────────────────────┐  [Copiar]   │
│  │  texto da nota (monoespaçado  │             │
│  │  ou Neo Sans, com os *negritos*)            │
│  └──────────────────────────────┘             │
│                                                │
│  Proveniência: IPCA 7060 · difusão SGS 21379…  │  ← rodapé discreto, cinza
├──────────────────────────────────────────────┤
│  RASCUNHO — Leitura para a Indústria (revisar) │  ← card separado, borda clara
│  …                                             │
└──────────────────────────────────────────────┘
```

Princípios:
- Muito espaço em branco; uma ação principal por vez.
- Azul escuro só em cabeçalho/títulos; azul claro só em ações/realces.
- Sem sombras pesadas, sem gradientes; bordas finas, cantos levemente
  arredondados (coerente com o "arredondado" da marca).
- A nota e o rascunho de leitura **visualmente separados**, para não confundir o
  texto oficial (determinístico) com a sugestão de IA.

## 5. Acessibilidade

- Texto sobre `#164194` deve ser branco (contraste ok).
- `#008BD2` sobre branco serve para realce/links, mas para texto corrido pequeno
  preferir o azul escuro ou cinza-escuro (contraste).
