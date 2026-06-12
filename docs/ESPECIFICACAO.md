# Especificação — Economia em Foco | Inflação

## 1. Objetivo

Reduzir a zero o trabalho manual de montagem da nota de WhatsApp de IPCA e
IPCA-15. No dia da divulgação (D0), o app busca os dados, monta a nota no padrão
GPE e a entrega pronta para cópia, em segundos — antes do prazo das 09h15.

## 2. Escopo

**Dentro:** IPCA e IPCA-15. Nota de WhatsApp (texto). Rascunho opcional de
"Leitura para a Indústria".

**Fora (por ora):** versão completa do Economia em Foco (texto longo), outros
indicadores, envio automático, publicação.

## 3. Requisitos funcionais

- **RF1.** Buscar, por API, o resultado mensal do indicador e do mês anterior.
- **RF2.** Buscar variação e impacto (p.p.) dos grupos/subgrupos/itens de maior
  contribuição, ordenados por impacto decrescente.
- **RF3.** Buscar o acumulado em 12 meses do mês de referência e do anterior.
- **RF4.** (IPCA) Buscar a média dos núcleos (12m) atual e anterior, do Bacen.
- **RF5.** Buscar o índice de difusão atual e anterior.
- **RF6.** (Opcional) Buscar projeção Focus; ler projeção CNI de configuração.
- **RF7.** Montar a nota no padrão fixo, **com** núcleo se disponível, **sem**
  núcleo caso contrário, sem erro nem campo vazio visível.
- **RF8.** Exibir a nota em interface com botão "copiar".
- **RF9.** Gerar, em bloco separado e rotulado, um rascunho de leitura p/ indústria.
- **RF10.** Indicar a proveniência (fonte/data) de cada número, para conferência.

## 4. Requisitos não-funcionais

- **Determinismo:** a nota é reprodutível; mesma entrada → mesma saída.
- **Velocidade:** geração em segundos após disponibilidade do dado.
- **Robustez:** núcleo/difusão indisponíveis não quebram a nota.
- **Auditabilidade:** cada número rastreia à API de origem.

## 5. Padrão da nota (modelo de texto)

A nota tem **blocos fixos**, nesta ordem. Tokens entre `{ }` vêm dos dados.

```
1. TÍTULO            🚨 *{INDICADOR} {MÊS}/{ANO}*
2. RESULTADO MENSAL  (+ comparação de projeções, só IPCA)
3. EXPLICAÇÃO        1 a 3 linhas: grupos/itens de maior impacto
4. ACUMULADO 12M
5. NÚCLEO            (apenas IPCA, apenas se disponível)
6. DIFUSÃO
7. ASSINATURA
8. LINK DA NOTÍCIA
```

### 5.1 Modelo IPCA (com núcleo)

```
🚨 *IPCA {MÊS}/{ANO}*

🚩 O IPCA registrou *alta de {VAR}%* em {mês} de {ano}, após {avanço|recuo} de
{VAR_ANT}% em {mês_anterior}. O resultado ficou {em linha com|acima de|abaixo de}
a projeção da CNI ({PROJ_CNI}%) e {abaixo|acima} da projeção da Pesquisa Focus do
Banco Central ({PROJ_FOCUS}%).

🟥 O resultado de {mês} *reflete a alta do grupo {GRUPO_1}*, com variação de
{VAR_G1}% e impacto de {IMP_G1} ponto(s) percentual(is) (p.p.) no índice do mês.
[detalhamento de subgrupo/item conforme dados] Em seguida, destaca-se o grupo
{GRUPO_2}, com variação de {VAR_G2}% e impacto de {IMP_G2} p.p. [...]

🟥 Também merece destaque a alta da/do *{ITEM}* ({VAR_ITEM}% e impacto de
{IMP_ITEM} p.p.), subitem de maior impacto individual no índice do mês.

📈 O *IPCA acumulado em 12 meses* até {mês} ficou em *{ACUM}%*, {acima|abaixo}
dos {ACUM_ANT}% registrados nos 12 meses encerrados em {mês_anterior}.

📉 *A média dos núcleos de inflação*, que suavizam os efeitos de itens mais
voláteis, ficou em *{NUCLEO}%* no acumulado em 12 meses até {mês},
{ligeiramente abaixo|acima} dos {NUCLEO_ANT}% no acumulado até {mês_anterior}.

📉 O *índice de difusão*, que mede a disseminação das altas de preços entre os
itens que compõem o IPCA, ficou em *{DIF}%*, {abaixo|acima} do registrado em
{mês_anterior} ({DIF_ANT}%).

_*Superintendência de Economia (ECON)*_
_*Diretoria de Desenvolvimento Industrial (DDI)*_
_*Confederação Nacional da Indústria (CNI)*_

Notícia: {URL_IBGE}
```

### 5.2 Modelo IPCA-15 (sem núcleo)

Idêntico, **sem o bloco 5 (núcleo)**. O IPCA-15 não tem núcleo médio divulgado
pelo Bacen. Demais blocos seguem o mesmo padrão. (Ver nota-padrão em
`tests/golden/`.)

### 5.3 Mapa de emojis (configurável)

As duas notas-fonte usam emojis ligeiramente diferentes. **Padronizar** num
único conjunto e deixar em config. Sugestão:

| Bloco | Emoji sugerido |
|---|---|
| Título | 🚨 |
| Resultado mensal | 🚩 |
| Explicação (linhas de alta) | 🔴 |
| Acumulado 12m | 📈 |
| Núcleo | 📉 |
| Difusão | 📊 |

> Decisão pendente do Kleber: a nota-fonte do IPCA usa 🟥 nas explicações e
> assina "Superintendência de Economia (ECON)"; a do IPCA-15 usa 🔴 e assina
> "Superintendência de Inteligência Econômica (SIECON)". **São assinaturas
> diferentes.** Definir um padrão único (provavelmente ECON) e fixar em config.

### 5.4 Regras de redação determinística

- **Concordância de direção:** escolher "avanço/recuo", "alta/queda",
  "acima/abaixo", "acelerou/desacelerou" comparando os números — nunca fixo.
- **Plural de p.p.:** "0,29 ponto percentual" (sing.) vs "1,20 pontos
  percentuais" — regra: singular se valor < 2,00... na prática o IBGE usa
  "ponto" para 1 e "pontos" para >1; replicar o uso do IBGE (validar no golden).
- **Número de grupos/itens citados:** 1 a 3, por impacto decrescente, com corte
  por relevância (ex.: só citar itens com impacto ≥ 0,05 p.p.). Parametrizar.
- **Formatação numérica:** vírgula decimal, 2 casas para variação, 2 casas para
  impacto, sem separador de milhar. "%", "p.p." conforme padrão.
- **Negrito WhatsApp:** `*texto*` nos pontos-chave (resultado, grupo, número).

## 6. Lógica de disponibilidade do núcleo

```
nucleo = bcb.media_nucleos_12m(indicador, mes_ref)   # pode retornar None
if indicador == "IPCA" and nucleo is not None:
    incluir_bloco_nucleo()
else:
    pular_bloco_nucleo()
```

O fetcher do núcleo deve falhar de forma silenciosa e segura (retornar `None`,
não exceção) quando a série ainda não tem o mês de referência.

## 7. Leitura para a Indústria (rascunho — ÚNICO ponto de IA)

Bloco **separado da nota**, exibido abaixo e rotulado:

> **RASCUNHO — LEITURA PARA A INDÚSTRIA (revisar antes de usar)**

Recebe **apenas os dados já apurados** (não texto livre) e produz 2–4 frases sob
a lente da indústria (custos/insumos, margens, massa salarial real, juros). Deve
seguir `docs` de estilo da GPE: voz ativa, sem clichê, foco no setor produtivo.
A IA **não** toca em nenhum número da nota — só interpreta os fatos já fixados.

Exemplo de prompt (sistema): "Você redige a *leitura para a indústria* de uma
nota de inflação da CNI. Receberá dados já apurados. Escreva 2 a 4 frases, voz
ativa, foco em custos de produção, margens e competitividade industrial. Não
invente números; use apenas os fornecidos. Não edite a nota."

## 8. Critérios de aceite

- [ ] Reproduz a nota golden do IPCA abril/2026 (texto idêntico ao padrão).
- [ ] Reproduz a nota golden do IPCA-15 maio/2026.
- [ ] Gera nota de IPCA sem o bloco de núcleo quando este é `None`.
- [ ] Impactos batem com a divulgação (tolerância 0,01 p.p.).
- [ ] Interface exibe a nota com botão copiar e o rascunho de leitura à parte.
