---
name: diagram-generator
description: >
  Use this skill to generate BR Modelo logical (relational) diagrams as raw SVG.
  Trigger for requests about logical model, relational schema, tables, PK/FK,
  and cardinality between tables.
---

# BR Modelo Logico Generator

Gera diagrama logico (relacional) no estilo brModelo em SVG bruto.

Regra de idioma: manter labels e textos no mesmo idioma da solicitacao do usuario.

---

## Escopo

Este arquivo e apenas para modelo logico (tabelas) em brModelo.
Nao gerar ER conceitual, UML, fluxo, arquitetura ou BPMN neste skill.

## Passo 1 - Extrair elementos

Antes de escrever SVG, identifique:

- Tabelas
- Atributos de cada tabela
- PK de cada tabela
- FKs e tabela de referencia
- Relacionamentos e cardinalidades

Se faltar informacao, assumir valores razoaveis e continuar.

---

## Passo 2 - Planejar layout

1. Posicionar tabelas principais primeiro.
2. Posicionar tabelas dependentes nas laterais.
3. Reservar espaco para linhas e cardinalidades.
4. Conectar tabelas por ultimo.

Tamanho e limites:
- Canvas fixo: viewBox="0 0 680 H"
- Area segura: x = 20..660, y = 20..(H-20)
- Distancia minima entre tabelas: 60 px horizontal, 50 px vertical
- H = base do menor elemento + 40 px

---

## Passo 3 - Escrever SVG

Regras globais:
- Saida deve ser somente SVG bruto (sem markdown e sem explicacao).
- Iniciar com `<svg width="100%" viewBox="0 0 680 H" xmlns="http://www.w3.org/2000/svg">`
- Fundo transparente.
- Todo texto com `font-family="Arial, sans-serif"`.
- Todo `<text>` deve ter x, y, text-anchor e dominant-baseline="central".
- Toda linha/path usada como conector deve ter `fill="none"`.

---

## Notacao logica brModelo (obrigatorio)

Regras visuais:
- Tabela: retangulo com cabecalho azul e corpo branco.
- Cabecalho: nome da tabela em negrito e texto branco.
- Corpo: uma linha por atributo.
- PK: prefixo visual de chave (ex.: "PK" ou simbolo de chave).
- FK: prefixo visual diferente de PK (ex.: "FK").
- Relacionamento: linha simples entre tabelas.
- Cardinalidade: texto em cada ponta, por exemplo (1,1), (0,n).
- Sem losango de relacionamento no modelo logico.

Padrao de tabela:
```svg
<!-- Header -->
<rect x="X" y="Y" width="W" height="28" fill="#4A7CC7" stroke="#2E5FA3" stroke-width="1"/>
<text x="CX" y="Y+14" text-anchor="middle" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="13" font-weight="bold" fill="white">
  TableName
</text>

<!-- Body -->
<rect x="X" y="Y+28" width="W" height="ROW_H" fill="white" stroke="#4A7CC7" stroke-width="1"/>
<text x="X+14" y="Y+39" text-anchor="start" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="11" fill="black">PK id_table</text>
```

Padrao de relacionamento:
```svg
<line x1="X1" y1="Y1" x2="X2" y2="Y2" stroke="black" stroke-width="1.2" fill="none"/>
<text x="X1+6" y="Y1-6" text-anchor="start" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="11" fill="black">(1,1)</text>
<text x="X2-6" y="Y2-6" text-anchor="end" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="11" fill="black">(0,n)</text>
```

---

## Checklist final

- [ ] Todas as tabelas possuem cabecalho e corpo.
- [ ] PK e FK estao identificadas.
- [ ] Relacoes desenhadas com linha simples.
- [ ] Cardinalidades presentes e legiveis.
- [ ] Nenhum elemento fora da area segura.
- [ ] Saida final contem somente o SVG.

---
