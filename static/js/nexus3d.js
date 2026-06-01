(function(){
  // Minimal Three.js integration for builder page
  const ORDER = ['Case','Motherboard','CPU','GPU','RAM','PSU','Storage','Cooling'];
  const COLORS = {Case:0xC4B5FD,Motherboard:0x78BFFA,CPU:0xA78BFA,GPU:0x60A5FA,RAM:0x6EE7B7,PSU:0xF472B6,Storage:0xFBBF24,Cooling:0x67E8F9};
  let scene, camera, renderer, controls, root, resizeObserver;
  const meshes = {};

  function init() {
    const container = document.getElementById('nexus-canvas');
    if (!container) return;
    const W = container.clientWidth, H = container.clientHeight;
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 1000);
    camera.position.set(1.2, 1.0, 2.0);
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    renderer.setSize(W, H);
    container.appendChild(renderer.domElement);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;

    const amb = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(amb);
    const dir = new THREE.DirectionalLight(0xffffff, 0.8);
    dir.position.set(5,10,7);
    scene.add(dir);

    root = new THREE.Group();
    scene.add(root);

    const grid = new THREE.GridHelper(6, 12, 0x222222, 0x111111);
    grid.position.y = -0.8;
    scene.add(grid);

    window.requestAnimationFrame(animate);

    // responsive
    resizeObserver = new ResizeObserver(() => onWindowResize());
    resizeObserver.observe(container);

    const ld = document.getElementById('nexus-loader');
    if(ld) ld.style.display = 'none';
    console.log('nexus3d: init complete');
  }

  function onWindowResize(){
    const container = document.getElementById('nexus-canvas');
    if(!container || !renderer || !camera) return;
    const w = container.clientWidth, h = container.clientHeight;
    camera.aspect = w/h; camera.updateProjectionMatrix(); renderer.setSize(w,h);
  }

  function clearMeshes(){
    Object.values(meshes).forEach(m => { root.remove(m); if(m.geometry) m.geometry.dispose(); if(m.material) m.material.dispose(); });
    Object.keys(meshes).forEach(k => delete meshes[k]);
  }

  function buildPlaceholderMesh(cat, label){
    const geo = new THREE.BoxGeometry(0.28, 0.12, 0.14);
    const mat = new THREE.MeshStandardMaterial({ color: COLORS[cat] || 0xffffff, metalness:0.3, roughness:0.4 });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.userData.cat = cat; mesh.userData.label = label;
    return mesh;
  }

  function refreshFromSelected(){
    if (typeof window.selectedParts !== 'object') return;
    clearMeshes();
    // place items in ORDER along X axis
    const gap = 0.36; let i=0;
    ORDER.forEach(cat => {
      const p = window.selectedParts[cat];
      if(!p) return;
      const mesh = buildPlaceholderMesh(cat, p.name || cat);
      mesh.position.set((i - 3.5) * gap, 0, 0);
      root.add(mesh);
      meshes[cat] = mesh;
      i++;
    });
  }

  function animate(){
    requestAnimationFrame(animate);
    if(controls) controls.update();
    // subtle rotation
    if(root) root.rotation.y += 0.0015;
    if(renderer && scene && camera) renderer.render(scene, camera);
  }

  // Expose a public refresh method
  window.nexus3d = {
    init: init,
    refresh: refreshFromSelected
  };

  // try init on DOM ready, wait for THREE to become available
  document.addEventListener('DOMContentLoaded', () => {
    let attempts = 0;
    const maxAttempts = 50; // ~5s
    const iv = setInterval(() => {
      attempts++;
      if (typeof THREE !== 'undefined' && typeof THREE.OrbitControls !== 'undefined') {
        clearInterval(iv);
        try { init(); } catch (e) { console.error('nexus3d init error', e); }
        // initial render
        setTimeout(() => { try{ window.nexus3d.refresh(); }catch(e){} }, 300);
        // watch selectedParts changes periodically
        setInterval(() => { try{ window.nexus3d.refresh(); }catch(e){} }, 1000);
        return;
      }
      if (attempts >= maxAttempts) {
        clearInterval(iv);
        const ld = document.getElementById('nexus-loader');
        if (ld) {
          ld.style.display = 'flex';
          // show error text
          ld.innerHTML = '<div style="text-align:center;color:rgba(255,255,255,.6);">\n                <div style="font-size:13px;font-weight:800;color:#f87171;">Failed to load 3D libraries</div>\n                <div style="margin-top:6px;font-size:12px;color:rgba(255,255,255,.45);">Check your network or console for errors.</div>\n              </div>';
        }
        console.error('nexus3d: THREE or OrbitControls not available');
      }
    }, 100);
  });
})();
