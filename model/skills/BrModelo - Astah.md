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
| entities, tables, foreign keys, database schema, ER, BR Modelo | ER Conceptual   |
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

**Color palette (mais fiel ao brModelo):**
- Entity rectangle: fill="#FFF9E6" stroke="#1E4A7C" stroke-width="2" rx="6"
- Weak entity: fill="#FFF9E6" stroke="#1E4A7C" stroke-width="4" rx="6" (dupla borda simulada)
- Attribute ellipse: fill="#EAF3DE" stroke="#3B6D11" stroke-width="1"
- Key attribute (PK): same + text-decoration="underline"
- Relationship diamond: fill="#FFEBB8" stroke="#854F0B" stroke-width="1.5"
- Connection line: stroke="#333" stroke-width="1.5" fill="none"
- Cardinality text: fill="#222" font-size="11" font-weight="bold"

**Entity pattern:**
```svg
<rect x="X" y="Y" width="W" height="48" rx="6"
  fill="#FFF9E6" stroke="#1E4A7C" stroke-width="2"/>
<text x="CX" y="CY" text-anchor="middle" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="14" font-weight="bold" fill="#1E4A7C">
  EntityName
</text>
```

**Attribute ellipse pattern (place around its entity):**
```svg
<ellipse cx="CX" cy="CY" rx="45" ry="18"
  fill="#EAF3DE" stroke="#3B6D11" stroke-width="0.5"/>
<text x="CX" y="CY" text-anchor="middle" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="12" fill="#1a4a10">attr_name</text>
<line x1="entity_edge_x" y1="entity_edge_y" x2="ellipse_cx" y2="ellipse_cy"
  stroke="#555" stroke-width="0.5" fill="none"/>
```

**Key attribute (underline via tspan):**
```svg
<text ... text-decoration="underline">id</text>
```

**Relationship diamond:**
```svg
<!-- Diamond centered at (CX, CY) with half-width HW, half-height HH -->
<polygon points="CX,CY-HH  CX+HW,CY  CX,CY+HH  CX-HW,CY"
  fill="#FAEEDA" stroke="#854F0B" stroke-width="0.8"/>
<text x="CX" y="CY" text-anchor="middle" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="12" font-weight="bold" fill="#633806">
  has
</text>
```

**Cardinality label near connection:**
```svg
<text x="X" y="Y" font-family="Arial,sans-serif" font-size="11" fill="#444">1</text>
<text x="X" y="Y" font-family="Arial,sans-serif" font-size="11" fill="#444">N</text>
```

**Layout strategy for ER:**
- Place entities first (spread across the canvas)
- Place relationship diamonds between connected entities
- Place attribute ellipses around their entity (top, bottom, left, right), spaced 70–90px from entity center
- Draw connection lines last (entity edge → attribute center; entity edge → diamond; diamond → entity)
- Compute connection endpoints at the edge of the shape (not center-to-center, or lines will render through shapes)

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

**Relationship lines:**
```svg
<!-- Inheritance (solid line + open triangle at parent) -->
<line x1="X1" y1="Y1" x2="X2" y2="Y2"
  stroke="#534AB7" stroke-width="0.8" fill="none"
  marker-end="url(#tri-open)"/>

<!-- Composition (solid line + filled diamond at owner) -->
<line x1="X1" y1="Y1" x2="X2" y2="Y2"
  stroke="#534AB7" stroke-width="0.8" fill="none"
  marker-start="url(#diamond-fill)"/>

<!-- Aggregation (solid line + open diamond at whole) -->
<line x1="X1" y1="Y1" x2="X2" y2="Y2"
  stroke="#534AB7" stroke-width="0.8" fill="none"
  marker-start="url(#diamond-open)"/>

<!-- Association (solid line + open arrow) -->
<line x1="X1" y1="Y1" x2="X2" y2="Y2"
  stroke="#534AB7" stroke-width="0.8" fill="none"
  marker-end="url(#arrow-open)"/>

<!-- Dependency (dashed line + open arrow) -->
<line x1="X1" y1="Y1" x2="X2" y2="Y2"
  stroke="#534AB7" stroke-width="0.8" fill="none"
  stroke-dasharray="6 3" marker-end="url(#arrow-open)"/>
```

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

**Color palette:**
- System boundary: fill="none" stroke="#185FA5" stroke-width="1" rx="8"
- System title: font-size="14" font-weight="bold" fill="#185FA5"
- Use case ellipse: fill="#E6F1FB" stroke="#185FA5" stroke-width="0.5"
- Actor figure: stroke="#333" stroke-width="1" fill="none"
- Association line: stroke="#555" stroke-width="0.5"
- Include/extend: stroke="#555" stroke-width="0.5" stroke-dasharray="5 3"

**Actor figure pattern (stick figure):**
```svg
<!-- Head -->
<circle cx="CX" cy="Y+12" r="12" fill="none" stroke="#333" stroke-width="1"/>
<!-- Body -->
<line x1="CX" y1="Y+24" x2="CX" y2="Y+52" stroke="#333" stroke-width="1"/>
<!-- Arms -->
<line x1="CX-16" y1="Y+34" x2="CX+16" y2="Y+34" stroke="#333" stroke-width="1"/>
<!-- Legs -->
<line x1="CX" y1="Y+52" x2="CX-14" y2="Y+70" stroke="#333" stroke-width="1"/>
<line x1="CX" y1="Y+52" x2="CX+14" y2="Y+70" stroke="#333" stroke-width="1"/>
<!-- Actor name below -->
<text x="CX" y="Y+85" text-anchor="middle"
  font-family="Arial,sans-serif" font-size="12" fill="#333">ActorName</text>
```

**Use case ellipse:**
```svg
<ellipse cx="CX" cy="CY" rx="70" ry="24"
  fill="#E6F1FB" stroke="#185FA5" stroke-width="0.5"/>
<text x="CX" y="CY" text-anchor="middle" dominant-baseline="central"
  font-family="Arial,sans-serif" font-size="12" fill="#0C447C">Use case name</text>
```

**Include / Extend:**
```svg
<!-- <<include>> -->
<line x1="X1" y1="Y1" x2="X2" y2="Y2"
  stroke="#555" stroke-width="0.5" stroke-dasharray="5 3"
  marker-end="url(#arrow)"/>
<text x="MID_X" y="MID_Y-6" text-anchor="middle"
  font-family="Arial,sans-serif" font-size="10" font-style="italic" fill="#555">
  «include»
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
