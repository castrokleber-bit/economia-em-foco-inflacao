# Fontes de Dados — códigos verificados e gates de validação

> Todos os códigos abaixo foram **verificados** (jun/2026). Onde há incerteza,
> está marcado **[VERIFICAR]** com o método de confirmação. Nunca chutar código.

## 1. IBGE — SIDRA / API de Agregados (v3)

Base da API: `https://servicodados.ibge.gov.br/api/v3/agregados/`
Alternativa (mais simples para tabelas): API SIDRA `https://apisidra.ibge.gov.br/`

### Tabelas

| Indicador | Tabela | Conteúdo | Período |
|---|---|---|---|
| **IPCA** | **7060** | Variação mensal, acum. no ano, **acum. 12 meses** e **peso mensal** — geral, grupos, subgrupos, itens, subitens | a partir de jan/2020 |
| **IPCA-15** | **7062** **[VERIFICAR]** | Equivalente do 7060 para o IPCA-15 | a partir de jan/2020 |

> **[VERIFICAR] 7062:** confirmar que é a tabela do IPCA-15 com as mesmas
> variáveis do 7060. Método: abrir `https://sidra.ibge.gov.br/tabela/7062` ou
> consultar metadados em `…/api/v3/agregados/7062/metadados`. (As tabelas
> "novas" pós-2020 são 7060 IPCA, 7062 IPCA-15, 7063 INPC — confirmar.)

### Variáveis da tabela 7060 (confirmar IDs nos metadados)

A tabela traz, por nível (geral → grupo → subgrupo → item → subitem):
- Variação mensal (%)
- Variação acumulada no ano (%)
- Variação acumulada em 12 meses (%)
- **Peso mensal (%)** ← usado para calcular o impacto

> Buscar os IDs exatos das variáveis em
> `…/api/v3/agregados/7060/metadados` (campo `variaveis`) e dos níveis
> territoriais/classificações no mesmo retorno. **Não hardcodar IDs sem ler os
> metadados.**

### Exemplo de chamada (API de Agregados)

```
GET /api/v3/agregados/7060/periodos/{AAAAMM}/variaveis/{IDvar}?localidades=N1[all]&classificacao={IDclass}[{categorias}]
```

Padrão prático: buscar o **índice geral** (variação mensal + acum. 12m) e, à
parte, a lista de **grupos** e de **subitens** com variação + peso, para montar a
explicação e calcular impactos.

## 2. Cálculo do impacto (p.p.)

A tabela 7060 **não traz o "impacto" pronto**; ela traz variação e peso. O
impacto é calculado:

```
impacto_pp ≈ (peso_mensal × variação) / 100
```

Validação do método (IPCA abril/2026): Alimentação e bebidas teve variação
1,34% e impacto 0,29 p.p. → peso implícito ≈ 21,6%, coerente com o peso do grupo
no IPCA. ✔️

> **GATE:** implementar o cálculo e conferir que ele reproduz os impactos
> divulgados em abril/2026 dentro de **0,01 p.p.**. Se houver descasamento
> sistemático, testar usar o peso do **mês anterior** (a metodologia do IBGE usa
> a estrutura de ponderação anterior). Só prosseguir após bater.

## 3. Banco Central — SGS (séries temporais)

Formato da API (JSON):
```
https://api.bcb.gov.br/dados/serie/bcdata.sgs.{CODIGO}/dados?formato=json
https://api.bcb.gov.br/dados/serie/bcdata.sgs.{CODIGO}/dados/ultimos/{N}?formato=json
```
Filtro por data: `&dataInicial=dd/mm/aaaa&dataFinal=dd/mm/aaaa`.
Retorno: `[{"data":"dd/mm/aaaa","valor":"x.xx"}, ...]`.

### Séries confirmadas

| Código | Série | Uso |
|---|---|---|
| **433** | IPCA — variação mensal (%) | conferência / fallback |
| **13522** | IPCA — acumulado 12 meses (%) | acum. 12m (fonte alternativa ao SIDRA) |
| **7478** | IPCA-15 — variação mensal (%) | conferência / fallback |
| **21379** | **IPCA — índice de difusão (%)** | bloco de difusão da nota ✔️ |
| **188** | INPC — variação mensal | (não usado, referência) |

> **21379** conceito oficial: "Parcela de subitens do IPCA com variação positiva
> no mês" (Fonte: BCB/Depto Econômico). É exatamente a difusão da nota.

### Núcleos de inflação do IPCA (médias e exclusão)

| Código | Núcleo |
|---|---|
| **4466** | Médias aparadas com suavização (IPCA-MS) |
| **11426** | Médias aparadas sem suavização (IPCA-MA) |
| **16121** | Por exclusão — EX0 |
| **16122** | Dupla ponderação (IPCA-DP) |
| **27838 / 27839** **[VERIFICAR]** | Exclusão EX1 / EX3 (confirmar) |

> **Média dos núcleos [VERIFICAR + COMPUTAR]:** a "média dos núcleos" da nota
> (4,38% em 12m até abr/2026) é a média do conjunto de núcleos que o Bacen
> acompanha. Não há garantia de uma série SGS única já pronta com esse valor.
> **Método:** (a) procurar série SGS de "média dos núcleos" nos metadados; se não
> existir, (b) computar a média (em 12 meses) das séries de núcleo acima e
> **validar contra 4,38% (abr/2026)** e 4,39% (mar/2026). Fechar qual conjunto
> reproduz o número antes de fixar. Esse é o ponto mais delicado das fontes.

### Disponibilidade temporal do núcleo

Os núcleos e a difusão saem com a divulgação do IPCA ou pouco depois. O fetcher
deve retornar `None` (não exceção) se o mês de referência ainda não existe na
série, para acionar a nota **sem núcleo**.

## 4. IPCA-15 — difusão **[GAP CONHECIDO]**

A série SGS 21379 é de difusão do **IPCA**, não do IPCA-15. A nota do IPCA-15
maio/2026 traz difusão de 65,1%.

> **Método:** verificar se o Bacen publica série de difusão do IPCA-15 (buscar
> nos metadados do SGS). Se não houver, a difusão do IPCA-15 vem da própria
> publicação do IBGE (release/Comunicação Social) — neste caso, computar a
> partir dos subitens da tabela 7062 (parcela de subitens com variação > 0) e
> **validar contra 65,1% (mai/2026)**. Se não fechar com precisão, deixar a
> difusão do IPCA-15 como campo de entrada manual no app (com aviso), em vez de
> publicar número não verificado.

## 5. Projeções (opcional, só IPCA)

- **Projeção CNI:** não vem de API. Ler de arquivo de configuração
  (`config/projecoes.json`) preenchido pela equipe, ou campo de input no app.
- **Projeção Focus:** API Olinda de Expectativas de Mercado:
  `https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativaMercadoMensais?$format=json&$filter=Indicador eq 'IPCA'`
  Filtrar por `DataReferencia` (mês) e pegar a **mediana** mais recente.
  **[VERIFICAR]** o nome exato do recurso/campos no Olinda antes de usar.

## 6. Resumo dos gates de validação (não pular)

1. **Tabela 7062** confirma IPCA-15 (metadados).
2. **Impacto** reproduz divulgação abr/2026 (±0,01 p.p.).
3. **Média dos núcleos** reproduz 4,38% (abr/2026) — definir conjunto de séries.
4. **Difusão IPCA-15** reproduz 65,1% (mai/2026) — ou vira input manual.
5. **Texto final** idêntico às notas golden (abr/2026 IPCA, mai/2026 IPCA-15).
