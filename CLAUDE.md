# CLAUDE.md — Economia em Foco | Inflação (IPCA / IPCA-15)

> Este arquivo é lido automaticamente pelo Claude Code. Ele define o que o
> projeto é, como construí-lo e — sobretudo — o que **não** fazer.

## 1. O que este projeto é

Aplicativo que, quando da divulgação do IPCA ou do IPCA-15, busca os
resultados automaticamente via API (IBGE e Banco Central) e **monta a nota de
WhatsApp do produto "Economia em Foco"** seguindo o padrão fixo da GPE/ECON.

O objetivo é velocidade: a nota é descritiva, padronizada e pronta para envio
até as **09h15** (regra de canal do WhatsApp). Não é um produto analítico.

## 2. Princípio de arquitetura inegociável: a fronteira determinística

A mesma regra da ferramenta do Copom se aplica aqui:

- **A NOTA é determinística.** É montada por funções Python puras a partir dos
  dados estruturados das APIs. **Nenhuma parte do texto da nota é gerada por
  IA.** Cada número no texto rastreia diretamente a um campo retornado pela API.
- **A IA entra apenas depois, e fora da nota**, para redigir um rascunho de
  *Leitura para a Indústria* — claramente rotulado como sugestão para avaliação
  do especialista, nunca enviado automaticamente.

Por quê: a nota carrega números oficiais sob a marca da CNI. Alucinação aqui é
risco institucional. Determinismo torna a saída auditável e reproduzível.

## 3. Stack

- Python 3.11+
- `httpx` (requisições às APIs; suporta async)
- `fastapi` + `uvicorn` (backend que serve a interface e expõe `/gerar`)
- Frontend estático (HTML/CSS/JS puro) — controle total sobre a identidade CNI
- `pytest` (testes, incl. o gate de validação)
- IA (opcional, só leitura): SDK Anthropic via variável de ambiente

Manter dependências mínimas. Sem framework de template no montador de texto —
usar f-strings/funções explícitas, para que cada bloco seja auditável.

## 4. Estrutura de pastas

```
economia-em-foco-inflacao/
├── CLAUDE.md                  # este arquivo
├── README.md
├── .env.example               # variáveis de ambiente (copiar p/ .env)
├── requirements.txt
├── docs/
│   ├── ESPECIFICACAO.md       # PRD + modelo de texto + regras de negócio
│   ├── FONTES-DE-DADOS.md     # APIs, códigos verificados, gates de validação
│   ├── IDENTIDADE-VISUAL.md   # cores, fonte, logo, layout
│   └── GUIA-CLAUDE-CODE.md    # passo a passo de construção
├── fontes/                    # camada de dados (1 módulo por fonte)
│   ├── ibge.py                # SIDRA tabela 7060 (IPCA) / 7062 (IPCA-15)
│   ├── bcb.py                 # SGS: núcleos, difusão; Olinda: Focus
│   └── modelo.py              # dataclass ResultadoInflacao
├── nucleo/                    # lógica de domínio (determinística)
│   ├── impacto.py             # cálculo do impacto em p.p.
│   ├── montador.py            # monta o texto da nota (1 função por bloco)
│   └── leitura.py             # rascunho de leitura p/ indústria (ÚNICO ponto de IA)
├── app/
│   ├── main.py                # FastAPI
│   └── static/                # index.html, style.css, app.js, logo, fonte
└── tests/
    ├── test_montador.py       # compara saída com as notas-padrão (golden)
    ├── test_impacto.py        # valida impacto vs. divulgação conhecida
    └── golden/                # notas de referência abril/2026 e maio/2026
```

## 5. Comandos

```bash
# setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# rodar a aplicação (interface local)
uvicorn app.main:app --reload   # abre em http://127.0.0.1:8000

# testes (inclui o gate de validação)
pytest -q
```

## 6. Regra de ouro de qualidade: validação contra divulgação conhecida

Antes de considerar qualquer módulo pronto, ele tem de **reproduzir as duas
notas-padrão** que estão em `tests/golden/`:

- **IPCA abril/2026** (variação 0,67%; acum. 12m 4,39%; núcleo médio 4,38%;
  difusão 65,3%; impactos por grupo conhecidos)
- **IPCA-15 maio/2026** (variação 0,62%; acum. 12m 4,64%; difusão 65,1%)

Se o `montador` + os `fetchers` + o cálculo de `impacto` não reconstroem esses
números (dentro de tolerância de 0,01 p.p. para impactos arredondados), há erro.
**Não avançar sem fechar o backtest.** Esta é a barreira central do projeto.

## 7. Convenções (o que sempre fazer)

- **Não inventar códigos de API.** Todos os códigos (SIDRA, SGS, Olinda) estão
  verificados em `docs/FONTES-DE-DADOS.md`. Usar de lá; se faltar, **buscar e
  confirmar nos metadados da fonte**, nunca chutar.
- **Núcleo é opcional.** O `montador` checa `if resultado.nucleo_12m is not
  None`. Núcleo do Bacen às vezes sai com defasagem; a nota tem de funcionar com
  e sem ele.
- **Todo número exibido tem proveniência.** Guardar, no objeto de dados, a
  fonte de cada campo (qual tabela/série/data).
- **Saídas em `/output/`**; nunca sobrescrever golden ou docs.

## 8. O que NÃO fazer

- ❌ Gerar qualquer trecho da **nota** com IA.
- ❌ Editorializar a nota (ela é descritiva; análise vai só na *leitura*, à parte).
- ❌ Enviar/circular qualquer coisa automaticamente. A interface só **exibe** o
  texto para cópia humana. Circulação externa é sempre decisão humana.
- ❌ Alterar dados numéricos sem fonte explícita da API.

## 9. Identidade visual

Especificada em `docs/IDENTIDADE-VISUAL.md`. Resumo: minimalista, azul CNI
`#164194` (escuro) e `#008BD2` (claro), fonte Neo Sans Pro, logomarca da CNI no
cabeçalho. Atenção ao licenciamento da fonte (ver doc).
