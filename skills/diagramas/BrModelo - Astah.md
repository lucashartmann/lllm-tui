---
name: diagram-generator
description: >
  Use this skill whenever the user asks to create, draw, or generate any type of diagram.
  Triggers include: entity-relationship diagrams (ER, BR Modelo, conceptual model), UML diagrams
  (class, sequence, use case, activity, component, state), flowcharts, architecture diagrams,
  BPMN process flows, mind maps, data flow diagrams (DFD), network diagrams, and any other
  visual modeling notation. Also triggers on phrases like "draw me a diagram", "model this system",
  "create a schema", "show the relationships", "map out the flow", "design the architecture".
  Works for any domain: databases, software systems, business processes, infrastructure, etc.
---

# Diagram Generator

Generates any type of diagram automatically as an SVG rendered inline in chat.
No user configuration needed — the skill detects what type of diagram fits best and generates it.

Language rule: keep labels and prose in the same language used by the user request.

---

## Step 1 — Identify the diagram type

Read the user's request and pick the best fit from the table below.
If the user specifies a type explicitly, use that. Otherwise infer from the domain and phrasing.
If information is clearly missing (e.g., entities with no relationships), make reasonable assumptions and continue.

| User mentions / context                                      | Diagram type       |
|--------------------------------------------------------------|--------------------|
| entities, tables, foreign keys, database schema, ER, BR Modelo conceptual | ER Conceptual |
| lógico, logical model, relational schema, BR Modelo lógico, tabelas com FK/PK | Lógico brModelo |
| classes, objects, inheritance, methods, attributes, OOP      | UML Class          |
| messages, calls, requests, responses, flow between services  | UML Sequence       |
| actors, users, system features, use cases, <<include>>       | UML Use Case       |
| steps, decisions, yes/no branches, process, workflow         | Flowchart          |
| services, microservices, infrastructure, cloud, deploy       | Architecture       |
| business process, BPMN, swim lanes, events, gateways         | BPMN               |
| states, transitions, events, guards, finite automaton        | State Machine      |
| data flows, processes, external entities, data stores        | DFD                |
| topic, subtopics, brainstorm, concept map                    | Mind Map           |

If the request is ambiguous, pick the most common type for the domain (e.g. "model a library system" → ER).

---

## Step 2 — Extract elements from the description

Before writing SVG, parse the user's description into structured elements:

**For ER diagrams:**
- Entities (nouns that store data: Cliente, Produto, Pedido)
- Attributes per entity (include likely implicit ones: id, created_at, name fields)
- Primary keys (mark with underline)
- Relationships (verbs between entities: "has", "places", "belongs to")
- Cardinality in BR Modelo format: (0,1), (1,1), (0,n), (1,n)

**For UML Class:**
- Classes and interfaces
- Attributes with type and visibility (+, -, #)
- Methods with signature and visibility
- Relationships: inheritance (→▷), composition (◆—), aggregation (◇—), association (—>), dependency (-->)
- Multiplicity on association ends

**For UML Sequence:**
- Actors / objects (left to right)
- Messages in order (synchronous → solid arrow, async → open arrow, return → dashed)
- Activation bars (when object is active)
- Fragments (loop, alt, opt) if applicable

**For UML Use Case:**
- System boundary rectangle
- Actors (outside the rectangle)
- Use cases (ellipses inside the rectangle)
- Relationships: association (actor to use case), <<include>>, <<extend>>, generalization

**For Flowchart:**
- Start/end (rounded rect)
- Steps (rect)
- Decisions (diamond) with Yes/No branches
- Flow direction (top-down preferred)

**For Architecture:**
- System components / services
- External systems
- Databases / queues / storage
- Communication lines with protocol labels

---

## Step 3 — Layout planning

Before writing any SVG coordinates, plan the layout on paper:

1. Count elements and estimate space needed
2. Assign a grid: how many columns, how many rows
3. Compute positions so nothing overlaps
4. Reserve margin for labels and connecting lines

Use orthogonal routing (L-bends) when straight lines would cross unrelated shapes.

**Sizing rules:**
- Canvas width: always `680` (viewBox `0 0 680 H`)
- Safe drawing area: x = 20 to 660, y = 20 to (H - 20)
- Entity / class box: min width = longest label × 8px + 24px padding; min height = 44px (single line), 56px+ (multi-line)
- Leave at least 60px between boxes horizontally, 50px vertically
- Set H = bottom of lowest element + 40px

**Common grid templates:**

```
3 entities in a row:   x = 60, 270, 480   w = 160   gap = 50px
2 entities side by side: x = 120, 400   w = 200   gap = 80px
star layout (1 center + N around): center at (340, H/2), radiate
top-down flow: y steps of 80–100px
```

---

## Step 4 — Write the SVG

Follow these rules exactly. Violations cause broken or unreadable diagrams.

### Global rules

- Output raw SVG only — no markdown fences, no explanation before the SVG
- Start with `<svg width="100%" viewBox="0 0 680 H" xmlns="http://www.w3.org/2000/svg">`
- Transparent background (no background rect)
- All text: font-family="Arial, sans-serif"
- Only two font sizes: 14px for titles/labels, 12px for subtitles/descriptions
- Sentence case on all labels (not ALL CAPS, not Title Case For Every Word)
- No rotated text
- Every `<text>` needs explicit x, y, text-anchor, and dominant-baseline="central"
- Every connector `<path>` or `<line>` used as a line must have `fill="none"`
- `<defs>` must appear before all shapes
- Keep stroke widths consistent per diagram type (avoid random per-shape variations)

### Arrow marker (always include this defs block)

```svg
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5"
    markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
      stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
  <marker id="arrow-open" viewBox="0 0 10 10" refX="8" refY="5"
    markerWidth="6" markerHeight="6" orient="auto">
    <path d="M1 1L9 5L1 9" fill="none" stroke="context-stroke"
      stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
  <marker id="tri-open" viewBox="0 0 12 12" refX="10" refY="6"
    markerWidth="8" markerHeight="8" orient="auto">
    <polygon points="2,2 10,6 2,10" fill="none" stroke="context-stroke" stroke-width="1.2"/>
  </marker>
  <marker id="diamond-fill" viewBox="0 0 16 10" refX="0" refY="5"
    markerWidth="10" markerHeight="8" orient="auto">
    <polygon points="0,5 8,0 16,5 8,10" fill="context-stroke"/>
  </marker>
  <marker id="diamond-open" viewBox="0 0 16 10" refX="0" refY="5"
    markerWidth="10" markerHeight="8" orient="auto">
    <polygon points="0,5 8,0 16,5 8,10" fill="white" stroke="context-stroke" stroke-width="1.2"/>
  </marker>
</defs>
```

---

### ER Conceptual (BR Modelo style)

> ⚠️ CRITICAL — READ BEFORE DRAWING:
> **ENTITIES are RECTANGLES. Attributes are CIRCLES (small, ~r=5). NEVER use ellipses/balloons for entities or attributes.**
> The first version of this diagram used colored ellipses for entities — that is WRONG and was corrected by the user.
> brModelo is BLACK AND WHITE. No fill colors. Simple geometry only.

**Visual rules (strict brModelo):**
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

**Entity pattern (double border):**
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

**Attribute circle pattern (place around its entity):**
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

**Relationship diamond:**
```svg
<!-- Diamond centered at (CX, CY), fill white, stroke black — NO colors -->
<polygon points="CX,CY-HH  CX+HW,CY  CX,CY+HH  CX-HW,CY"
  fill="white" stroke="black" stroke-width="1.5"/>
<text x="CX" y="CY" text-anchor="middle" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="12" font-weight="bold" fill="black">
  has
</text>
```

**Cardinality label near connection:**
```svg
<text x="X" y="Y" font-family="Arial,sans-serif" font-size="11" fill="black">(1,n)</text>
```

**Layout strategy for ER:**
- Place entities first (spread across the canvas)
- Place relationship diamonds between connected entities
- Place attribute circles around their entity (top, bottom, left, right), spaced 60–80px from entity edge
- Draw connection lines last (entity edge → attribute center; entity edge → diamond; diamond → entity)
- Compute connection endpoints at the edge of the shape (not center-to-center, or lines will render through shapes)

---

### Lógico brModelo (Relational / Logical style)

> This is the LOGICAL model — different from the conceptual ER. It looks like database tables, not entity-relationship diagrams.

**Visual rules:**
- Each table: a rectangle with a colored header bar + list of attributes below, NO outer double border
- Header bar: fill="#4A7CC7" (blue), white bold text = table name
- Body: fill="white" stroke="#4A7CC7" stroke-width="1", attributes listed as rows
- Primary key attribute: 🔑 yellow key icon (use ★ or just bold + underline text if SVG icons unavailable) — draw a small `<polygon>` key shape or use text "🔑"
- Foreign key attribute: green key icon (different color) — text "🗝" or small colored indicator
- Simple attribute: plain text, left-aligned, font-size="12"
- Relationships: plain lines between tables (no diamond), with cardinality labels (0,1), (1,n) etc.
- NO relationship diamonds — those belong to the conceptual model
- Cardinality placed next to the line ends

**Table pattern:**
```svg
<!-- Header -->
<rect x="X" y="Y" width="W" height="28" fill="#4A7CC7" stroke="#2E5FA3" stroke-width="1"/>
<text x="CX" y="Y+14" text-anchor="middle" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="13" font-weight="bold" fill="white">
  TableName
</text>
<!-- Body -->
<rect x="X" y="Y+28" width="W" height="ROW_H * N_ATTRS" fill="white" stroke="#4A7CC7" stroke-width="1"/>
<!-- Each attribute row (ROW_H = 22px) -->
<!-- PK attribute -->
<text x="X+20" y="Y+28+11" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="11" fill="black">🔑 Codigo</text>
<!-- FK attribute -->
<text x="X+20" y="Y+28+33" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="11" fill="black">🗝 FK_Entidade_Cod</text>
<!-- Normal attribute -->
<text x="X+20" y="Y+28+55" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="11" fill="black">   Nome</text>
```

**Relationship line:**
```svg
<line x1="X1" y1="Y1" x2="X2" y2="Y2" stroke="black" stroke-width="1.2" fill="none"/>
<text x="X1+5" y="Y1-4" font-family="Arial,sans-serif" font-size="11" fill="black">(1,1)</text>
<text x="X2-20" y="Y2-4" font-family="Arial,sans-serif" font-size="11" fill="black">(0,n)</text>
```

---

### UML Class Diagram (Astah style)

**Color palette:**
- Class header: fill="#CECBF6" stroke="#534AB7"
- Attributes section: fill="#EEEDFE" stroke="#534AB7"
- Methods section: fill="#F5F4FF" stroke="#534AB7"
- Interface tag: italic, smaller, fill="#3C3489"
- All strokes: stroke-width="0.5"

**Class box pattern (3 sections stacked):**
```svg
<!-- Header -->
<rect x="X" y="Y" width="W" height="30" rx="0"
  fill="#CECBF6" stroke="#534AB7" stroke-width="0.5"/>
<text x="CX" y="Y+15" text-anchor="middle" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="13" font-weight="bold" fill="#26215C">
  ClassName
</text>

<!-- Attributes section -->
<rect x="X" y="Y+30" width="W" height="ATTR_H"
  fill="#EEEDFE" stroke="#534AB7" stroke-width="0.5"/>
<!-- One text per attribute, left-aligned, 12px, fill="#3C3489" -->
<text x="X+8" y="Y+30+16" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="12" fill="#3C3489">- name: String</text>

<!-- Methods section -->
<rect x="X" y="Y+30+ATTR_H" width="W" height="METHOD_H"
  fill="#F5F4FF" stroke="#534AB7" stroke-width="0.5"/>
<text x="X+8" y="Y+30+ATTR_H+16" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="12" fill="#3C3489">+ getName(): String</text>
```

**Relationship lines (always include multiplicity labels and optional role name):**
```svg
<!-- Inheritance (solid line + open triangle pointing to parent) -->
<line x1="X1" y1="Y1" x2="X2" y2="Y2"
  stroke="#534AB7" stroke-width="0.8" fill="none"
  marker-end="url(#tri-open)"/>

<!-- Association (solid line + filled arrowhead, with multiplicity + label) -->
<line x1="X1" y1="Y1" x2="X2" y2="Y2"
  stroke="#534AB7" stroke-width="0.8" fill="none"
  marker-end="url(#arrow)"/>
<!-- Multiplicity near source end -->
<text x="X1+8" y="Y1-6" font-family="Arial,sans-serif" font-size="11" fill="#333">1</text>
<!-- Multiplicity near target end -->
<text x="X2-20" y="Y2-6" font-family="Arial,sans-serif" font-size="11" fill="#333">0..*</text>
<!-- Role/label near midpoint -->
<text x="MID_X" y="MID_Y-8" text-anchor="middle"
  font-family="Arial,sans-serif" font-size="11" fill="#333">▶ role name</text>

<!-- Composition (solid line + filled diamond at owner end) -->
<line x1="X1" y1="Y1" x2="X2" y2="Y2"
  stroke="#534AB7" stroke-width="0.8" fill="none"
  marker-start="url(#diamond-fill)"/>

<!-- Aggregation (solid line + open diamond at whole end) -->
<line x1="X1" y1="Y1" x2="X2" y2="Y2"
  stroke="#534AB7" stroke-width="0.8" fill="none"
  marker-start="url(#diamond-open)"/>

<!-- Dependency (dashed line + open arrow) -->
<line x1="X1" y1="Y1" x2="X2" y2="Y2"
  stroke="#534AB7" stroke-width="0.8" fill="none"
  stroke-dasharray="6 3" marker-end="url(#arrow-open)"/>
```

**Multiplicity notation:** Use UML standard: `1`, `0..1`, `1..*`, `0..*`, `*`. Place near each line end, offset ~8px from the endpoint so it doesn't overlap the class box.

---

### UML Sequence Diagram (Astah style)

**Color palette:**
- Actor/object box: fill="#E6F1FB" stroke="#185FA5"
- Lifeline: stroke="#aaa" stroke-width="0.5" stroke-dasharray="4 4"
- Activation bar: fill="#B5D4F4" stroke="#185FA5" stroke-width="0.5"
- Sync message arrow: solid, marker-end="url(#arrow)"
- Return arrow: dashed, marker-end="url(#arrow-open)"
- Fragment rect: fill="none" stroke="#888" stroke-width="0.5" stroke-dasharray="5 3"

**Pattern:**
```svg
<!-- Object box at top -->
<rect x="X" y="20" width="100" height="34" rx="4"
  fill="#E6F1FB" stroke="#185FA5" stroke-width="0.5"/>
<text x="X+50" y="37" text-anchor="middle" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="13" font-weight="bold" fill="#0C447C">
  :ClassName
</text>

<!-- Lifeline below the box -->
<line x1="X+50" y1="54" x2="X+50" y2="BOTTOM"
  stroke="#aaa" stroke-width="0.5" stroke-dasharray="4 4"/>

<!-- Activation bar (when object is executing) -->
<rect x="X+44" y="Y_START" width="12" height="H_ACTIVE"
  fill="#B5D4F4" stroke="#185FA5" stroke-width="0.5"/>

<!-- Synchronous message -->
<line x1="SRC_X+50" y1="Y" x2="DST_X+50" y2="Y"
  stroke="#333" stroke-width="0.8" marker-end="url(#arrow)"/>
<text x="MID_X" y="Y-5" text-anchor="middle"
  font-family="Arial,sans-serif" font-size="11" fill="#333">1. methodName()</text>

<!-- Return message (dashed) -->
<line x1="DST_X+50" y1="Y" x2="SRC_X+50" y2="Y"
  stroke="#666" stroke-width="0.6" stroke-dasharray="5 3"
  marker-end="url(#arrow-open)"/>
<text x="MID_X" y="Y-5" text-anchor="middle"
  font-family="Arial,sans-serif" font-size="11" fill="#666">return value</text>
```

**Spacing:** Place objects at equal horizontal intervals. Messages spaced 40–50px vertically.

---

### UML Use Case Diagram (Astah style)

**Visual rules (from Astah screenshots):**
- System boundary: plain rectangle, fill="none" stroke="#888" stroke-width="1", label "uc" in top-left corner inside
- Use case ellipses: fill="#FFFACD" (light yellow) stroke="#888" stroke-width="1" — NOT blue
- Actor: stick figure, black strokes, name below
- Association line: plain solid line, no arrowhead, stroke="black" stroke-width="1"
- Generalization (actor inherits actor): solid line + open triangle pointing to parent actor
- <<include>>: dashed line + open arrowhead pointing TO the included use case, label «include»
- <<extend>>: dashed line + open arrowhead pointing TO the base use case, label «extend»

**System boundary:**
```svg
<rect x="X" y="Y" width="W" height="H" fill="none" stroke="#888" stroke-width="1"/>
<!-- "uc" label top-left inside boundary -->
<text x="X+8" y="Y+16" font-family="Arial,sans-serif" font-size="12" fill="#555">uc</text>
```

**Actor figure pattern (stick figure):**
```svg
<!-- Head -->
<circle cx="CX" cy="Y" r="10" fill="none" stroke="black" stroke-width="1.2"/>
<!-- Body -->
<line x1="CX" y1="Y+10" x2="CX" y2="Y+36" stroke="black" stroke-width="1.2"/>
<!-- Arms -->
<line x1="CX-14" y1="Y+20" x2="CX+14" y2="Y+20" stroke="black" stroke-width="1.2"/>
<!-- Legs -->
<line x1="CX" y1="Y+36" x2="CX-12" y2="Y+54" stroke="black" stroke-width="1.2"/>
<line x1="CX" y1="Y+36" x2="CX+12" y2="Y+54" stroke="black" stroke-width="1.2"/>
<!-- Name below -->
<text x="CX" y="Y+68" text-anchor="middle" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="12" fill="black">ActorName</text>
```

**Use case ellipse (yellow, as in Astah):**
```svg
<ellipse cx="CX" cy="CY" rx="75" ry="26"
  fill="#FFFACD" stroke="#888" stroke-width="1"/>
<text x="CX" y="CY" text-anchor="middle" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="12" fill="black">Use case name</text>
```

**Actor generalization (Dosen → User in image):**
```svg
<!-- Solid line + open triangle pointing to parent -->
<line x1="child_CX" y1="child_Y" x2="parent_CX" y2="parent_Y"
  stroke="black" stroke-width="1" marker-end="url(#tri-open)"/>
```

**Include / Extend (dashed + arrow + italic label):**
```svg
<!-- <<include>> dashed arrow -->
<line x1="X1" y1="Y1" x2="X2" y2="Y2"
  stroke="#555" stroke-width="1" stroke-dasharray="6 3"
  marker-end="url(#arrow)"/>
<text x="MID_X" y="MID_Y-7" text-anchor="middle"
  font-family="Arial,sans-serif" font-size="11" font-style="italic" fill="#333">
  «include»
</text>

<!-- <<extend>> dashed arrow -->
<line x1="X1" y1="Y1" x2="X2" y2="Y2"
  stroke="#555" stroke-width="1" stroke-dasharray="6 3"
  marker-end="url(#arrow)"/>
<text x="MID_X" y="MID_Y-7" text-anchor="middle"
  font-family="Arial,sans-serif" font-size="11" font-style="italic" fill="#333">
  «extend»
</text>
```

---

### Flowchart

**Color palette:**
- Start/End (rounded rect): fill="#E1F5EE" stroke="#0F6E56"
- Step (rect): fill="#F1EFE8" stroke="#5F5E5A"
- Decision (diamond): fill="#FAEEDA" stroke="#854F0B"
- Connector arrow: stroke="#555" stroke-width="0.8" marker-end="url(#arrow)"
- Labels on arrows: font-size="11" fill="#555"

**Patterns:**
```svg
<!-- Start/End -->
<rect x="X" y="Y" width="W" height="36" rx="18"
  fill="#E1F5EE" stroke="#0F6E56" stroke-width="0.8"/>
<text x="CX" y="CY" text-anchor="middle" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="13" fill="#085041">Start</text>

<!-- Step -->
<rect x="X" y="Y" width="W" height="44" rx="4"
  fill="#F1EFE8" stroke="#5F5E5A" stroke-width="0.5"/>
<text x="CX" y="CY" text-anchor="middle" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="13" fill="#2C2C2A">Process step</text>

<!-- Decision diamond: points computed from center (CX, CY) + half-sizes (HW, HH) -->
<polygon points="CX,CY-HH  CX+HW,CY  CX,CY+HH  CX-HW,CY"
  fill="#FAEEDA" stroke="#854F0B" stroke-width="0.8"/>
<text x="CX" y="CY" text-anchor="middle" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="12" fill="#633806">Decision?</text>

<!-- Yes/No labels on decision branches -->
<text x="X" y="Y" font-family="Arial,sans-serif" font-size="11" fill="#555">Yes</text>
```

**Arrow routing:** Draw lines that stop at the edge of shapes, not the center. For L-bends:
```svg
<path d="M X1 Y1 L X1 YMID L X2 YMID L X2 Y2" fill="none"
  stroke="#555" stroke-width="0.8" marker-end="url(#arrow)"/>
```

---

### Architecture Diagram

**Color palette:**
- Service box: fill="#E6F1FB" stroke="#185FA5" rx="8"
- Database cylinder: drawn as rect + ellipses, fill="#EAF3DE" stroke="#3B6D11"
- Queue/bus: fill="#FAEEDA" stroke="#854F0B" rx="4"
- External system: fill="#F1EFE8" stroke="#888" rx="4" stroke-dasharray="4 3"
- User/actor: stick figure or rounded rect, fill="#EEEDFE" stroke="#534AB7"
- Arrows: stroke="#555" stroke-width="0.8"
- Protocol labels on arrows: font-size="10" fill="#555"

**Database cylinder pattern:**
```svg
<!-- Body -->
<rect x="X" y="Y+10" width="W" height="H" fill="#EAF3DE" stroke="#3B6D11" stroke-width="0.5"/>
<!-- Top ellipse -->
<ellipse cx="X+W/2" cy="Y+10" rx="W/2" ry="8" fill="#C0DD97" stroke="#3B6D11" stroke-width="0.5"/>
<!-- Bottom ellipse (just arc for visual) -->
<ellipse cx="X+W/2" cy="Y+10+H" rx="W/2" ry="8" fill="#EAF3DE" stroke="#3B6D11" stroke-width="0.5"/>
<text x="X+W/2" y="Y+10+H/2+4" text-anchor="middle"
  font-family="Arial,sans-serif" font-size="12" fill="#1a4a10">DB Name</text>
```

---

## Step 5 — Output the result

After generating the SVG, output it directly without any preamble.

If the diagram is complex (many entities, many classes), split it into multiple SVGs — one per logical group. Put a single short plain-text heading before each SVG (for example: "Parte 1 - dominio principal").

Never explain the SVG code. The diagram speaks for itself.

---

## Checklist before finalizing SVG

Go through this list before outputting:

- [ ] viewBox height H covers all elements + 40px buffer
- [ ] No element has x < 20 or x + width > 660
- [ ] No two shapes overlap (check every pair in the same row)
- [ ] Every `<text>` has explicit x, y, text-anchor, dominant-baseline="central"
- [ ] Every connector path has fill="none"
- [ ] No arrow line passes through an unrelated shape (re-route with L-bend if so)
- [ ] Text inside boxes fits: chars × 8px + padding ≤ box width
- [ ] `<defs>` block is present with all needed markers
- [ ] No hardcoded dark background colors (background must be transparent)
- [ ] Multi-line text uses explicit `<tspan dy="1.2em">` — SVG does not auto-wrap
- [ ] **BR Modelo only:** Entities are RECTANGLES (double border), attributes are CIRCLES (r=5), PKs are FILLED circles — never ellipses/balloons for entities or attributes, never colored fills

---

## Examples of input → output type mapping

| User input | Detected type | What to draw |
|---|---|---|
| "Model a library with books and members" | ER Conceptual | Entities: Book, Member, Loan. Relationships: has, makes. Attributes per entity. |
| "Draw the class diagram for a banking system" | UML Class | Classes: Account, Client, Transaction, Bank. Inheritance if savings/checking. |
| "Show the login flow between frontend and backend" | UML Sequence | Objects: Browser, API, AuthService, DB. Messages: POST /login, validate(), SELECT user, return token. |
| "What are the use cases for a library app?" | UML Use Case | Actors: Student, Librarian. Use cases: Search book, Borrow, Return, Manage catalog. |
| "Map out the order checkout process" | Flowchart | Steps: Add to cart → Login check → Address → Payment → Confirm → Done. Decisions at login and payment. |
| "Design the microservices architecture for e-commerce" | Architecture | Services: API Gateway, Auth, Product, Order, Payment. DB per service. Message queue between Order and Payment. |