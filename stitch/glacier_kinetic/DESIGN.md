# Design System Strategy: The Neon Glacial Aesthetic

## 1. Overview & Creative North Star
**The Creative North Star: "Hyper-Fluid Precision"**

This design system is a rebellion against the "Bento Box" monotony of modern SaaS. It evolves the cold, sterile nature of "Glacier" into a high-energy, Gen Z-focused aesthetic that feels both professional and uninhibited. We achieve this through **Intentional Asymmetry** and **Tonal Depth**.

Instead of rigid, boxed-in layouts, we use a "Fluid Layering" approach. UI elements should feel like they are floating in a pressurized, dark-matter environment—stable but kinetic. We break the template look by pairing massive, chunky display typography with ultra-refined, pill-shaped containers and "glass" surfaces that allow the deep background textures to breathe through.

---

## 2. Colors & Surface Logic

### The Palette
We utilize a deep, nocturnal foundation (`#060e20`) to make our high-energy accents feel radioactive.
*   **Primary (`#7bd1fa`):** Our "Oxygen Blue." Used for high-priority actions and focus states.
*   **Secondary/Tertiary (`#ff716a` to `#ff8439`):** The "Heat Map." These are used for urgency, alerts, and badges.
*   **Surfaces:** We avoid flat grey. Every surface is a variant of our deep navy (`#060e20`), maintaining a cohesive chromatic temperature.

### The "No-Line" Rule
**Explicit Instruction:** Do not use 1px solid borders to define sections.
Boundaries must be established through **Background Color Shifts**. For example, a `surface-container-high` card should sit on a `surface` background without a stroke. Separation is achieved through the contrast in tonal values, not architectural lines.

### The "Glass & Gradient" Rule
To elevate the UI from "standard" to "premium," we utilize **Material-Glass Transitioning**. 
*   **Floating Elements:** Use `surface-variant` with a 60% opacity and `backdrop-blur-xl`.
*   **Signature Textures:** Main CTAs and high-energy badges should never be flat. Use a linear gradient from `secondary` (`#ff716a`) to `tertiary` (`#ff8439`) at a 45-degree angle. This provides the "visual soul" required for a high-end experience.

---

## 3. Typography: The Scale of Authority

Our typography is a study in contrast: the brute force of **Plus Jakarta Sans** against the Swiss precision of **Inter**.

*   **Display (Plus Jakarta Sans):** Bold and chunky. Use `display-lg` (3.5rem) for hero numbers and high-impact metrics. This font carries the brand's "High Energy" personality.
*   **Body (Inter):** The "Information Workhorse." Use `body-md` (0.875rem) for the majority of UI text. It provides the "Professional" counterweight to the display font.
*   **The Hierarchy Rule:** Never use the Display font for long-form reading. It is a graphic element, not a legibility tool. Use `headline-sm` for section titles to maintain a punchy, editorial rhythm.

---

## 4. Elevation & Depth: Tonal Layering

We reject traditional drop shadows in favor of **Ambient Tonal Stacking**.

*   **The Layering Principle:** 
    1.  **Base:** `surface` (The deep void).
    2.  **Sectioning:** `surface-container-low` (Subtle grouping).
    3.  **Interaction:** `surface-container-highest` (Elevated cards/modals).
*   **Ambient Shadows:** For floating elements (Modals, Popovers), use a shadow with a blur radius of `48px` and an opacity of `8%`. The shadow color must be sampled from `surface-container-lowest` (`#000000`)—never pure grey.
*   **The Ghost Border:** If a container requires further definition (e.g., in high-density data views), use the `outline-variant` token at **15% opacity**. This creates a "light-leak" effect rather than a hard boundary.

---

## 5. Component Logic

### Buttons & Chips
*   **The Shape:** All buttons and chips are **Full Radius** (pill-shaped). 
*   **Primary Button:** `primary` background with `on-primary` text. No border.
*   **Action Chips:** Use `surface-container-high` with a `primary` "Ghost Border" (15% opacity). On hover, transition to 100% opacity `primary` background.

### Cards & Lists
*   **The "Anti-Divider" Rule:** Dividers are strictly forbidden. To separate list items, use a `4px` vertical gap and alternate between `surface` and `surface-container-low` backgrounds, or simply use white space.
*   **Cards:** Use `rounded-xl` (3rem) for large dashboard cards. This extreme rounding communicates the Gen Z "Soft Brutalist" aesthetic.

### Input Fields
*   **The Interaction State:** Inputs use `surface-container-lowest` with a subtle `outline-variant` border. On focus, the border disappears and is replaced by a `2px` glow of `primary` (`#7bd1fa`) and a `backdrop-blur` effect.

### Tooltips & Overlays
*   **The Frosted Effect:** Tooltips must use `surface-bright` with `backdrop-blur-md` and 80% opacity. This ensures they feel like they are floating in the same atmosphere as the content below.

---

## 6. Do’s and Don'ts

### Do:
*   **Use Intentional Asymmetry:** Align text to the left but allow large display numbers to bleed slightly off the grid or overlap container edges.
*   **Embrace the Grid Background:** Use a subtle `1px` grid pattern (Color: `outline-variant`, Opacity: 5%) on the `background` layer to give the dark theme a sense of scale and technical precision.
*   **Stack Surfaces:** Think in 3D. A `surface-container-high` card should look like it’s physically closer to the user than the `surface` background.

### Don’t:
*   **Don't use #000000 for everything:** Pure black is for the "Lowest" container depth only. Use our specific surface tokens to maintain tonal richness.
*   **Don't use sharp corners:** Any radius below `1rem` is a violation of the system's "Fluid" philosophy.
*   **Don't use standard blue for errors:** Use the `secondary` (`#ff716a`) and `tertiary` (`#ff8439`) tokens for warnings. It feels more "emergency-luxe" than "standard-error."