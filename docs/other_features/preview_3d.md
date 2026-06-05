# 3D Preview Feature

This file explains the 3D preview feature in a simple way.
It is written for people who know Python but may not know much JavaScript.

---

## What the 3D preview does

The 3D preview shows selected PC parts as simple colored boxes in a browser.
It is not a full game engine, but a lightweight visualization using Three.js.

The code lives in:

- `static/js/nexus3d.js`

It runs on the builder page and watches the current selected parts.

---

## How it works

### 1. Initialize the scene

When the page loads, the script creates a Three.js scene, camera, lighting, and renderer.
This is like setting up a canvas for drawing in Python.

```js
scene = new THREE.Scene();
camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 1000);
renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
```

### 2. Create placeholder meshes for parts

Each selected part becomes a simple box with a color.
These are not real component models, but they help users see a layout.

```js
const geo = new THREE.BoxGeometry(0.28, 0.12, 0.14);
const mat = new THREE.MeshStandardMaterial({ color: COLORS[cat] });
const mesh = new THREE.Mesh(geo, mat);
```

### 3. Place parts in order

The parts are arranged in a fixed order on the X axis:

```js
const ORDER = ['Case','Motherboard','CPU','GPU','RAM','PSU','Storage','Cooling'];
```

For each selected category, the code creates a box and positions it with a gap.

### 4. Animate and render

The scene is animated with a small rotation, and the browser redraws it continuously.
This is similar to a game loop in Python.

```js
function animate() {
  requestAnimationFrame(animate);
  root.rotation.y += 0.0015;
  renderer.render(scene, camera);
}
```

### 5. Refresh when selected parts change

The script expects a global object called `window.selectedParts`.
Every second it refreshes the preview from that object.

```js
function refreshFromSelected() {
  if (typeof window.selectedParts !== 'object') return;
  clearMeshes();
  ORDER.forEach(cat => {
    const p = window.selectedParts[cat];
    if (!p) return;
    const mesh = buildPlaceholderMesh(cat, p.name || cat);
    root.add(mesh);
  });
}
```

So in Python terms, think of `window.selectedParts` as the current build state, and `refreshFromSelected()` as the function that redraws the preview.

---

## Why it is useful

- gives the builder page a visual feel
- helps users see which components are selected
- makes the page more interactive without requiring a backend change

---

## What to change if you want more detail

If you want a better preview later, you can replace the placeholder boxes with real shapes:

- use custom geometry or external models
- load `nexus3d_model_shapes.json` for shape definitions
- add part-specific positioning and labels

The current version is intentionally simple so it is easy to understand.
