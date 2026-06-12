# Economia em Foco — Inflação (IPCA / IPCA-15)

Ferramenta da GPE/ECON que, na divulgação do IPCA ou do IPCA-15, busca os dados
via API (IBGE e Banco Central) e **monta a nota de WhatsApp do Economia em Foco**
no padrão da gerência, pronta para envio até as 09h15.

## Princípio central

A **nota é determinística** — montada por funções Python a partir dos dados das
APIs, sem IA. Cada número rastreia a uma fonte oficial. A **IA entra só na
"Leitura para a Indústria"**, um rascunho separado e rotulado, para o especialista
avaliar. (Mesma fronteira da ferramenta do Copom.)

## O que ela faz

- Busca resultado mensal, grupos/itens de maior impacto, acumulado 12 meses,
  média dos núcleos (só IPCA) e índice de difusão.
- Monta a nota com núcleo, se disponível; sem núcleo, caso contrário.
- Exibe a nota numa interface minimalista com identidade CNI e botão copiar.
- Sugere uma leitura para a indústria (em desenvolvimento).

## Documentação

| Arquivo | Conteúdo |
|---|---|
| `CLAUDE.md` | Regras do projeto (lido pelo Claude Code) |
| `docs/ESPECIFICACAO.md` | PRD, modelo de texto, regras de negócio |
| `docs/FONTES-DE-DADOS.md` | APIs, códigos verificados, gates de validação |
| `docs/IDENTIDADE-VISUAL.md` | Cores, fonte, logo, layout |
| `docs/GUIA-CLAUDE-CODE.md` | Passo a passo de construção |

## Início rápido

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload   # http://127.0.0.1:8000
pytest -q                       # validação (golden + impactos)
```

## Fontes verificadas (jun/2026)

- IBGE SIDRA tabela **7060** (IPCA); **7062** IPCA-15 (a confirmar nos metadados)
- BCB SGS **21379** (difusão IPCA), **433/13522** (IPCA), **7478** (IPCA-15),
  núcleos **4466/11426/16121/16122**
- Detalhes e ressalvas em `docs/FONTES-DE-DADOS.md`

## Limites

Não envia nem publica nada automaticamente — só exibe para cópia humana.
Circulação é sempre decisão humana.
