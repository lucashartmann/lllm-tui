---
name: diagram-generator
description: >
  Use this skill to generate UML use case diagrams (Astah style) as raw SVG.
  Trigger for requests about actors, use cases, system boundary, include,
  extend, actor generalization, and feature-level interactions.
---

# UML Use Case Generator (Astah)

Gera diagrama de caso de uso UML no estilo Astah em SVG bruto.

Regra de idioma: manter labels e textos no mesmo idioma da solicitacao do usuario.

---

## Escopo

Este arquivo e apenas para diagrama UML de caso de uso.
Nao gerar ER, classe, sequencia, fluxo ou arquitetura neste skill.

## Passo 1 - Extrair elementos

Antes de escrever SVG, identifique:

- Atores externos
- Fronteira do sistema
- Casos de uso internos
- Associacoes ator-caso
- Include, extend e generalizacao de ator

Se faltar informacao, assumir valores razoaveis e continuar.

---

## Passo 2 - Planejar layout

1. Desenhar fronteira do sistema no centro.
2. Posicionar casos de uso dentro da fronteira.
3. Posicionar atores fora da fronteira.
4. Desenhar associacoes e relacoes especiais por ultimo.

Tamanho e limites:
- Canvas fixo: viewBox="0 0 680 H"
- Area segura: x = 20..660, y = 20..(H-20)
- Distancia minima entre elipses: 40 px
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
  <marker id="tri-open" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="8" markerHeight="8" orient="auto">
    <polygon points="2,2 10,6 2,10" fill="none" stroke="context-stroke" stroke-width="1.2"/>
  </marker>
</defs>
```

---

## Notacao UML Use Case Astah (obrigatorio)

Regras visuais:
- Fronteira do sistema: retangulo sem preenchimento, stroke cinza, label "uc" no topo esquerdo interno.
- Caso de uso: elipse amarela clara (`#FFFACD`) com borda cinza.
- Ator: boneco palito preto com nome abaixo.
- Associacao: linha solida preta, sem seta.
- Include: linha tracejada com seta aberta apontando para caso incluido e label «include».
- Extend: linha tracejada com seta aberta apontando para caso base e label «extend».
- Generalizacao de ator: linha solida com triangulo aberto para ator pai.

Padrao de fronteira:
```svg
<rect x="X" y="Y" width="W" height="H" fill="none" stroke="#888" stroke-width="1"/>
<text x="X+8" y="Y+16" text-anchor="start" dominant-baseline="central" font-family="Arial,sans-serif" font-size="12" fill="#555">uc</text>
```

Padrao de caso de uso:
```svg
<ellipse cx="CX" cy="CY" rx="75" ry="26" fill="#FFFACD" stroke="#888" stroke-width="1"/>
<text x="CX" y="CY" text-anchor="middle" dominant-baseline="central" font-family="Arial,sans-serif" font-size="12" fill="black">Use case name</text>
```

---

## Checklist final

- [ ] Fronteira do sistema presente e rotulada.
- [ ] Casos de uso dentro da fronteira.
- [ ] Atores fora da fronteira.
- [ ] Include/extend/generalizacao com notacao correta.
- [ ] Nenhum elemento fora da area segura.
- [ ] Saida final contem somente o SVG.

---
