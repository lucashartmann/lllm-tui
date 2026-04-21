---
name: diagram-generator
description: >
  Use this skill to generate BR Modelo conceptual ER diagrams as raw SVG.
  Trigger for requests about ER conceptual modeling, entities/attributes/relationships,
  and cardinalities in BR Modelo notation.
---

# BR Modelo Conceitual Generator

Gera diagrama ER conceitual no estilo brModelo em SVG bruto.

Regra de idioma: manter labels e textos no mesmo idioma da solicitação do usuario.

---

## Escopo

Este arquivo e apenas para modelo conceitual (ER) em brModelo.
Nao gerar UML, fluxo, arquitetura, BPMN ou modelo logico neste skill.

## Passo 1 - Extrair elementos

Antes de escrever SVG, identifique:

- Entities (nouns that store data: Cliente, Produto, Pedido)
- Attributes per entity (include likely implicit ones: id, created_at, name fields)
- Primary keys (no visual: circulo preenchido)
- Relationships (verbs between entities: "has", "places", "belongs to")
- Cardinality in BR Modelo format: (0,1), (1,1), (0,n), (1,n)

Se faltar informacao, assumir valores razoaveis e continuar.

---

## Passo 2 - Planejar layout

1. Posicionar entidades primeiro.
2. Posicionar relacionamentos (losangos) entre entidades relacionadas.
3. Distribuir atributos ao redor de cada entidade (topo, base, esquerda, direita).
4. Conectar por ultimo, sempre de borda para borda.

Evite cruzamento de linhas desnecessario.

Layout padrao recomendado para diagramas simples:
- Use uma grade horizontal em 3 colunas para entidades principais.
- Centralize o relacionamento entre as entidades do meio.
- Coloque atributos abaixo de cada entidade, com espacamento vertical suficiente.
- Nao sobreponha textos, circulos, retangulos ou losangos.
- Nao compacte os elementos no topo da tela; deixe respiro visual.

Tamanho e limites:
- Canvas fixo: viewBox="0 0 680 H"
- Area segura: x = 20..660, y = 20..(H-20)
- Distancia minima entre entidades: 60 px horizontal, 50 px vertical
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
- Preto e branco apenas: sem paleta colorida.
- Gere um SVG limpo, legivel e com distribuicao visual equilibrada.
- Nao use coordenadas muito proximas entre si; deixe espacamento horizontal e vertical consistente.
- Nao coloque mais de uma entidade em linhas que se toquem visualmente.
- Nao envolva a resposta em blocos markdown como ```svg.
- Nao escreva qualquer texto antes ou depois do SVG.
- Nao inclua comentarios fora do proprio SVG.

---

## Notacao brModelo conceitual (obrigatorio)

> ⚠️ CRITICAL — READ BEFORE DRAWING:
> **ENTITIES are RECTANGLES. Attributes are CIRCLES (small, ~r=5). NEVER use ellipses/balloons for entities or attributes.**
> The first version of this diagram used colored ellipses for entities — that is WRONG and was corrected by the user.
> brModelo is BLACK AND WHITE. No fill colors. Simple geometry only.

Regras visuais:
- Entity: `<rect>` with double border (two nested rects, outer stroke-width="2", inner offset 4px all sides, stroke-width="1") — fill white, stroke black
- Weak entity: triple border (three nested rects)
- Attribute: small `<circle>` r=5, fill="white" stroke="black" stroke-width="1.2" — label as plain text next to circle
- Key attribute (PK): `<circle>` r=6, fill="black" stroke="black" — label next to circle
- Multivalued attribute: two concentric circles (r=5 inner, r=8 outer), both stroke="black"
- Composite attribute: circle connected to sub-circles with lines
- Relationship: `<polygon>` diamond, fill="white" stroke="black" stroke-width="1.5"
- Weak relationship: double diamond (two nested polygons)
- Generalization/specialization: triangle `<polygon>` pointing toward superclass, fill="white" stroke="black"
- Relationship attribute: small `<rect>` connected to relationship diamond with a dashed line
- Cardinality: plain text (0,1) (1,1) (0,n) (1,n) next to connecting lines
- Connection line: stroke="black" stroke-width="1.2" fill="none"
- ALL elements: black and white only — no color fills, no colored strokes

Padrao de entidade (borda dupla):
```svg
<!-- outer border -->
<rect x="X" y="Y" width="W" height="44" fill="white" stroke="black" stroke-width="2"/>
<!-- inner border (offset 4px) -->
<rect x="X+4" y="Y+4" width="W-8" height="36" fill="white" stroke="black" stroke-width="1"/>
<text x="CX" y="CY" text-anchor="middle" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="13" font-weight="bold" fill="black">
  EntityName
</text>
```

Padrao de atributo:
```svg
<!-- Normal attribute: small white circle + label as text beside it -->
<circle cx="CX" cy="CY" r="5" fill="white" stroke="black" stroke-width="1.2"/>
<text x="CX+8" y="CY" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="11" fill="black">attr_name</text>
<line x1="entity_edge_x" y1="entity_edge_y" x2="CX" y2="CY"
  stroke="black" stroke-width="1" fill="none"/>

<!-- Key attribute (PK): filled black circle -->
<circle cx="CX" cy="CY" r="6" fill="black" stroke="black" stroke-width="1.2"/>
<text x="CX+9" y="CY" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="11" fill="black">id_attr</text>

<!-- Multivalued attribute: double circle -->
<circle cx="CX" cy="CY" r="5" fill="white" stroke="black" stroke-width="1.2"/>
<circle cx="CX" cy="CY" r="9" fill="none" stroke="black" stroke-width="1"/>
<text x="CX+11" y="CY" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="11" fill="black">multi_attr</text>
```

Padrao de relacionamento:
```svg
<!-- Diamond centered at (CX, CY), fill white, stroke black — NO colors -->
<polygon points="CX,CY-HH  CX+HW,CY  CX,CY+HH  CX-HW,CY"
  fill="white" stroke="black" stroke-width="1.5"/>
<text x="CX" y="CY" text-anchor="middle" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="12" font-weight="bold" fill="black">
  has
</text>
```

Padrao de cardinalidade:
```svg
<text x="X" y="Y" font-family="Arial,sans-serif" font-size="11" fill="black">(1,n)</text>
```

---

## Checklist final

- [ ] Entidades sao retangulos com borda dupla.
- [ ] Atributos sao circulos pequenos; PK e circulo preenchido.
- [ ] Relacionamentos sao losangos.
- [ ] Sem cores (apenas preto e branco).
- [ ] Linhas conectam bordas, sem atravessar formas indevidamente.
- [ ] Cardinalidades presentes e legiveis.
- [ ] Nenhum elemento fora da area segura.
- [ ] Nenhum elemento esta sobreposto ou colado demais.
- [ ] Saida final contem somente o SVG.

---