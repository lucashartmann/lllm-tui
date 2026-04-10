---
name: diagram-generator
description: >
  Use this skill to generate UML sequence diagrams (Astah style) as raw SVG.
  Trigger for requests about actors/objects, ordered messages, lifelines,
  activation bars, return messages, and interaction flow.
---

# UML Sequence Generator (Astah)

Gera diagrama de sequencia UML no estilo Astah em SVG bruto.

Regra de idioma: manter labels e textos no mesmo idioma da solicitacao do usuario.

---

## Escopo

Este arquivo e apenas para diagrama UML de sequencia.
Nao gerar ER, classes, caso de uso, fluxo ou arquitetura neste skill.

## Passo 1 - Extrair elementos

Antes de escrever SVG, identifique:

- Participantes (ator e objetos) da esquerda para direita
- Mensagens em ordem temporal
- Tipo da mensagem (sincrona, assincrona, retorno)
- Intervalos de ativacao dos participantes
- Fragmentos (alt, loop, opt) quando existirem

Se faltar informacao, assumir valores razoaveis e continuar.

---

## Passo 2 - Planejar layout

1. Posicionar participantes no topo com espacamento uniforme.
2. Definir altura total com base no numero de mensagens.
3. Colocar mensagens com passo vertical de 40 a 50 px.
4. Desenhar barras de ativacao alinhadas ao intervalo de execucao.

Tamanho e limites:
- Canvas fixo: viewBox="0 0 680 H"
- Area segura: x = 20..660, y = 20..(H-20)
- H = base da ultima mensagem + 60 px

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
</defs>
```

---

## Notacao UML Sequence Astah (obrigatorio)

Paleta:
- Box de participante: fill="#E6F1FB" stroke="#185FA5"
- Lifeline: stroke="#aaa" stroke-dasharray="4 4"
- Ativacao: fill="#B5D4F4" stroke="#185FA5"

Padrao de participante e lifeline:
```svg
<rect x="X" y="20" width="100" height="34" rx="4" fill="#E6F1FB" stroke="#185FA5" stroke-width="0.5"/>
<text x="X+50" y="37" text-anchor="middle" dominant-baseline="central" font-family="Arial,sans-serif" font-size="13" font-weight="bold" fill="#0C447C">:ClassName</text>
<line x1="X+50" y1="54" x2="X+50" y2="BOTTOM" stroke="#aaa" stroke-width="0.5" stroke-dasharray="4 4" fill="none"/>
```

Padrao de mensagem:
```svg
<!-- Mensagem sincrona -->
<line x1="SRC" y1="Y" x2="DST" y2="Y" stroke="#333" stroke-width="0.8" marker-end="url(#arrow)" fill="none"/>

<!-- Retorno -->
<line x1="DST" y1="Y2" x2="SRC" y2="Y2" stroke="#666" stroke-width="0.6" stroke-dasharray="5 3" marker-end="url(#arrow-open)" fill="none"/>
```

---

## Checklist final

- [ ] Participantes no topo e na ordem correta.
- [ ] Lifelines verticais visiveis.
- [ ] Mensagens na ordem temporal correta.
- [ ] Tipos de seta corretos para chamada e retorno.
- [ ] Nenhum elemento fora da area segura.
- [ ] Saida final contem somente o SVG.

---
