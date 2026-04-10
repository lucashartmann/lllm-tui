---
name: diagram-generator
description: >
  Use this skill to generate UML class diagrams (Astah style) as raw SVG.
  Trigger for requests about classes, attributes, methods, inheritance,
  association, composition, aggregation, dependency, and multiplicity.
---

# UML Class Generator (Astah)

Gera diagrama de classes UML no estilo Astah em SVG bruto.

Regra de idioma: manter labels e textos no mesmo idioma da solicitacao do usuario.

---

## Escopo

Este arquivo e apenas para diagrama UML de classes.
Nao gerar ER, sequencia, caso de uso, fluxo ou arquitetura neste skill.

## Passo 1 - Extrair elementos

Antes de escrever SVG, identifique:

- Classes e interfaces
- Atributos com tipo e visibilidade (+, -, #)
- Metodos com assinatura e visibilidade
- Relacoes: heranca, associacao, agregacao, composicao, dependencia
- Multiplicidade nas extremidades

Se faltar informacao, assumir valores razoaveis e continuar.

---

## Passo 2 - Planejar layout

1. Posicionar classes base no topo.
2. Posicionar subclasses abaixo.
3. Distribuir classes relacionadas lado a lado.
4. Reservar espaco para multiplicidades e rotulos de papel.

Tamanho e limites:
- Canvas fixo: viewBox="0 0 680 H"
- Area segura: x = 20..660, y = 20..(H-20)
- Distancia minima entre classes: 60 px horizontal, 50 px vertical
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
- `<defs>` deve aparecer antes das formas.

Bloco de marcadores obrigatorio:
```svg
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
  <marker id="arrow-open" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M1 1L9 5L1 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
  <marker id="tri-open" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="8" markerHeight="8" orient="auto">
    <polygon points="2,2 10,6 2,10" fill="none" stroke="context-stroke" stroke-width="1.2"/>
  </marker>
  <marker id="diamond-fill" viewBox="0 0 16 10" refX="0" refY="5" markerWidth="10" markerHeight="8" orient="auto">
    <polygon points="0,5 8,0 16,5 8,10" fill="context-stroke"/>
  </marker>
  <marker id="diamond-open" viewBox="0 0 16 10" refX="0" refY="5" markerWidth="10" markerHeight="8" orient="auto">
    <polygon points="0,5 8,0 16,5 8,10" fill="white" stroke="context-stroke" stroke-width="1.2"/>
  </marker>
</defs>
```

---

## Notacao UML Class Astah (obrigatorio)

Paleta:
- Header: fill="#CECBF6" stroke="#534AB7"
- Atributos: fill="#EEEDFE" stroke="#534AB7"
- Metodos: fill="#F5F4FF" stroke="#534AB7"

Padrao de classe (3 secoes):
```svg
<rect x="X" y="Y" width="W" height="30" fill="#CECBF6" stroke="#534AB7" stroke-width="0.5"/>
<text x="CX" y="Y+15" text-anchor="middle" dominant-baseline="central" font-family="Arial,sans-serif" font-size="13" font-weight="bold" fill="#26215C">ClassName</text>

<rect x="X" y="Y+30" width="W" height="ATTR_H" fill="#EEEDFE" stroke="#534AB7" stroke-width="0.5"/>
<text x="X+8" y="Y+46" text-anchor="start" dominant-baseline="central" font-family="Arial,sans-serif" font-size="12" fill="#3C3489">- attr: Type</text>

<rect x="X" y="Y+30+ATTR_H" width="W" height="METHOD_H" fill="#F5F4FF" stroke="#534AB7" stroke-width="0.5"/>
<text x="X+8" y="Y+30+ATTR_H+16" text-anchor="start" dominant-baseline="central" font-family="Arial,sans-serif" font-size="12" fill="#3C3489">+ method(): Return</text>
```

Relacoes:
- Heranca: linha solida com `marker-end="url(#tri-open)"`
- Associacao: linha solida com `marker-end="url(#arrow)"`
- Composicao: linha solida com `marker-start="url(#diamond-fill)"`
- Agregacao: linha solida com `marker-start="url(#diamond-open)"`
- Dependencia: linha tracejada com `marker-end="url(#arrow-open)"`
- Multiplicidade obrigatoria quando houver associacao

---

## Checklist final

- [ ] Cada classe tem header, atributos e metodos.
- [ ] Relacoes usam tipo de linha/seta correto.
- [ ] Multiplicidades estao posicionadas nas extremidades.
- [ ] Nenhum elemento fora da area segura.
- [ ] Saida final contem somente o SVG.

---
