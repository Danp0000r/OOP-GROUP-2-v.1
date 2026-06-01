
    // =====================================================
    // COMPONENT DATABASE — loaded from Flask + SQLite
    // =====================================================
    const DB = {
        cpus: [],
        gpus: [],
        motherboards: [],
        ram: [],
        psus: [],
        storage: [],
        coolers: [],
        cases: []
    };

    let build = {
        cpu: null,
        gpu: null,
        motherboard: null,
        ram: null,
        psu: null,
        storage: null,
        cooler: null,
        case: null
    };

    function setDefaultBuild() {
        build = {
            cpu: null,
            gpu: null,
            motherboard: null,
            ram: null,
            psu: null,
            storage: null,
            cooler: null,
            case: null
        };
    }

    
    function syncBuildFromPageSelectedParts() {
        try {
            if (typeof window.selectedParts !== 'object') return;
            const map = {
                'Case': ['case', 'cases'],
                'Motherboard': ['motherboard', 'motherboards'],
                'CPU': ['cpu', 'cpus'],
                'GPU': ['gpu', 'gpus'],
                'RAM': ['ram', 'ram'],
                'PSU': ['psu', 'psus'],
                'Storage': ['storage', 'storage'],
                'Cooling': ['cooler', 'coolers']
            };
            Object.keys(map).forEach(slot => {
                const [bkey, dbkey] = map[slot];
                const sel = window.selectedParts[slot];
                const prev = build[bkey];
                if (!sel) {
                    if (prev) { build[bkey] = null; try { rebuildMesh(bkey); } catch(e){} }
                    return;
                }
                const list = DB[dbkey] || [];
                const found = list.find(it => String(it.componentId || it.id) === String(sel.id));
                if (found) {
                    if (!prev || String(prev.componentId || prev.id) !== String(found.componentId || found.id)) {
                        build[bkey] = found;
                        try { rebuildMesh(bkey); } catch(e){}
                    }
                } else if (prev) {
                    build[bkey] = null;
                    try { rebuildMesh(bkey); } catch(e){}
                }
            });
        } catch (e) {
            console.warn('syncBuildFromPageSelectedParts failed', e);
        }
    }

function normalizeCase(caseData) {
        if(!caseData || typeof caseData !== 'object') return caseData;
        const idMap = {
            'case_tecware_m2': 'case-nexm2',
            'case_tecware_atx': 'case-nexair',
            'case_montech_air100': 'case-air100'
        };
        const normalized = Object.assign({}, caseData);
        normalized.id = idMap[normalized.id] || normalized.id;
        normalized.fans = normalized.fans || { top: 0 };
        return normalized;
    }

    function normalizeCooler(coolerData) {
        if(!coolerData || typeof coolerData !== 'object') return coolerData;
        const idMap = {
            'cooler_stock': 'cool-stock',
            'cooler_ak400': 'cool-ak400',
            'aio_coolermaster_ml240l': 'cool-ml240l',
            'aio_deepcool_le520': 'cool-le520',
            'aio_arctic_lf2_360': 'cool-arctic360'
        };
        const normalized = Object.assign({}, coolerData);
        const rawId = normalized.external_id || normalized.id;
        normalized.id = idMap[rawId] || rawId;
        return normalized;
    }

    function normalizeComponentForScene(component) {
        if(!component || typeof component !== 'object') return component;
        const normalized = Object.assign({}, component);
        normalized.componentId = component.id;
        normalized.id = component.external_id || normalized.id;
        const specs = component.specs || {};

        normalized.socket = specs.socket_type || specs.socket || (specs.compatibility && specs.compatibility.cpu_socket) || '';
        normalized.ddr = specs.ram_type || specs.ddr || '';
        normalized.factor = specs.form_factor || specs.formFactor || specs.factor || '';
        normalized.perf = component.performance_score || component.perf || 0;
        normalized.tdp = specs.tdp || component.tdp || 0;
        normalized.rgb = normalized.rgb || specs.rgb || false;
        normalized.type = specs.type || '';
        normalized.wattage = specs.wattage || specs.wattage_w || 0;
        normalized.length = specs.length_mm || specs.length || specs.gpu_length_limit || 0;
        normalized.width = specs.width_mm || specs.width || 0;
        normalized.thick = specs.thickness_mm || specs.thickness || specs.thick || 0;
        normalized.fans = specs.fans || normalized.fans || ((normalized.length || 0) > 240 ? 3 : 2);
        normalized.sticks = specs.sticks || specs.modules || 2;
        normalized.height = specs.height_mm || specs.height || 0;
        normalized.radiator = specs.radiator_size || specs.radiator || '';
        normalized.supportedFactors = [];

        if(component.category === 'Case') {
            const form = normalized.factor.toUpperCase();
            normalized.supportedFactors = form === 'ATX' ? ['ATX', 'MATX'] : (form ? [form] : []);
            normalized.gpuClearance = specs.gpu_length_limit || specs.gpu_length_limit_mm || 0;
            normalized.cpuCoolerLimit = specs.cpu_cooler_limit_mm || specs.cpu_cooler_limit || 0;
            normalized.radiatorSupport = specs.radiator_support || specs.radiator_supports || [];
            normalized.dims = {
                w: (specs.width_mm || specs.width || 400) * MM_TO_UNITS,
                h: (specs.height_mm || specs.height || 420) * MM_TO_UNITS,
                d: (specs.depth_mm || specs.depth || 390) * MM_TO_UNITS
            };
            normalized.fans = { top: specs.top_fans || specs.fans_top || 0 };
        }

        if(component.category === 'Motherboard') {
            normalized.socket = specs.socket_type || specs.socket || '';
            normalized.ddr = specs.ram_type || '';
            normalized.factor = specs.form_factor || specs.formFactor || specs.factor || '';
            normalized.width = specs.width_mm || specs.width || 244;
            normalized.depth = specs.depth_mm || specs.depth || 244;
        }

        if(component.category === 'CPU') {
            normalized.socket = specs.socket_type || specs.socket || '';
            normalized.ddr = specs.ram_type || '';
        }

        if(component.category === 'GPU') {
            normalized.length = specs.length_mm || specs.length || specs.gpu_length_limit || normalized.length;
            normalized.width = specs.width_mm || specs.width || normalized.width;
            normalized.thick = specs.thickness_mm || specs.thickness || specs.thick || normalized.thick || 38;
            normalized.rgb = normalized.rgb || specs.rgb || false;
        }

        if(component.category === 'RAM') {
            normalized.sticks = specs.sticks || specs.modules || 2;
            normalized.height = specs.height_mm || specs.height || 40;
            normalized.rgb = normalized.rgb || specs.rgb || false;
            normalized.ddr = specs.ram_type || specs.ddr || '';
        }

        if(component.category === 'Storage') {
            normalized.type = specs.type || normalized.type || '';
            if(!normalized.type && normalized.name && normalized.name.toLowerCase().includes('nvme')) normalized.type = 'nvme';
        }

        if(component.category === 'Cooling') {
            normalized.type = specs.type || (specs.radiator_size ? 'liquid' : 'air');
            normalized.height = specs.height_mm || specs.cooler_height_mm || normalized.height || 0;
            normalized.radiator = specs.radiator_size || specs.radiator || '';
            normalized.rgb = normalized.rgb || specs.rgb || false;
        }

        return normalized;
    }

    async function loadComponentDB() {
        try {
            const response = await fetch('/api/components');
            if (!response.ok) throw new Error(`Failed to load components: ${response.status}`);
            const data = await response.json();
            const components = Array.isArray(data) ? data : Array.isArray(data.components) ? data.components : [];
            const normalized = components.map(normalizeComponentForScene);
            DB.cpus = normalized.filter(c => c.category === 'CPU');
            DB.gpus = normalized.filter(c => c.category === 'GPU');
            DB.motherboards = normalized.filter(c => c.category === 'Motherboard');
            DB.ram = normalized.filter(c => c.category === 'RAM');
            DB.psus = normalized.filter(c => c.category === 'PSU');
            DB.storage = normalized.filter(c => c.category === 'Storage');
            DB.coolers = normalized.filter(c => c.category === 'Cooling').map(normalizeCooler);
            DB.cases = normalized.filter(c => c.category === 'Case').map(normalizeCase);
        } catch (error) {
            console.error(error);
            DB.cpus = DB.cpus || [];
            DB.gpus = DB.gpus || [];
            DB.motherboards = DB.motherboards || [];
            DB.ram = DB.ram || [];
            DB.psus = DB.psus || [];
            DB.storage = DB.storage || [];
            DB.coolers = DB.coolers || [];
            DB.cases = DB.cases || [];
        }

        setDefaultBuild();
    }

    // Physical coordinate calculation map (unified scale: 1mm = 0.0032 WebGL units)
    const MM_TO_UNITS = 0.0032;

    // State
    let rgbOn = true, rainbowMode = true, rgbHue = 185;
    let glassMode = 'on', exploded = false, wireMode = false;
    let fanSpeed = 0.18, fanTick = 0;
    
    // Component selection + saved positions
    const positionOverrides = {};
    // Embedded default positions (falls back when nexus3d_positions.json is missing)
    const DEFAULT_POSITION_PAYLOAD = {
  "savedPositions": {
    "case-nexair": {
      "cooler-rad": { "x": 0.316, "y": -0.56, "z": 0.373 },
      "case-fan-rear-1": { "x": 0.0033046948885176453, "y": 0.48462080674279706, "z": -0.7709395251332163 },
      "psu": { "x": -0.050382856308510804, "y": -0.9061040775749991, "z": -0.3436 },
      "case": { "x": 0, "y": -0.31096949338244406, "z": 0 },
      "ram": { "x": -0.31965000000000005, "y": 0.07037499999786673, "z": -0.1304926336768 },
      "cooler": { "x": -0.32465000000000005, "y": 0.07037499999786673, "z": -0.23987503530228868 },
      "gpu": { "x": -0.1410499999999999, "y": -0.355291879758159, "z": 0.12153936632320002 },
      "motherboard": { "x": -0.3596500000000001, "y": -0.2182770000021334, "z": 0.037363366323199976 },
      "cooler-block": { "x": 0, "y": -0.12007828670814108, "z": 0.19721729893106932 },
      "case-fan-front-1": { "x": 0, "y": -0.3352365789669381, "z": 0.6900000000000001 },
      "case-fan-front-2": { "x": 0, "y": 0.08401342103306192, "z": 0.6900000000000001 },
      "case-fan-front-3": { "x": 0, "y": 0.503263421033062, "z": 0.6900000000000001 },
      "cooler-cool-ak400": { "x": -0.32499999999999996, "y": 0.6278800811949878, "z": -0.33545600000000003 },
      "cooler-cool-le520": { "x": -0.32499999999999996, "y": -0.14284800000000003, "z": -0.33545600000000003 },
      "cooler-rad-cool-le520": { "x": 0, "y": 0, "z": 0 },
      "cooler-block-cool-le520": { "x": 0, "y": 0.08851226044981306, "z": 0.28507075741976484 },
      "cooler-cool-arctic360": { "x": -0.32499999999999996, "y": -0.08404908868620414, "z": -0.0447044967406357 },
      "cooler-cool-ml240l": { "x": -0.32499999999999996, "y": -0.14284800000000003, "z": -0.33545600000000003 },
      "cooler-rad-cool-ml240l": { "x": 0, "y": 0, "z": 0 },
      "cooler-liquid": { "x": 0.032475622023406814, "y": -0.14284800000000003, "z": -0.4262890543232145 },
      "cooler-air": { "x": -0.32499999999999996, "y": -0.057960347259035594, "z": -0.046154844582732 },
      "cooler-block-liquid": { "x": -0.35418089477157977, "y": 0.0852046549034195, "z": 0.373650011556119 },
      "cooler-rad-liquid": { "x": 0, "y": -0.3127786058892463, "z": 0.5921191913415846 }
    },
    "case-air100": {
      "case-fan-rear-1": { "x": -0.011013108382441072, "y": 0.4618019840169406, "z": -0.7809933819482299 },
      "case": { "x": 0, "y": -0.4209409368163248, "z": 0 },
      "cooler-rad": { "x": 0.3162032244763089, "y": -0.41405908518245904, "z": 0.2723876547320706 },
      "psu": { "x": -0.050890210497739674, "y": -0.8745780872396708, "z": -0.3374 },
      "cooler": { "x": -0.315, "y": -0.13873043644489083, "z": -0.0663508995143865 },
      "ram": { "x": -0.31, "y": -0.13873043644489083, "z": -0.0663508995143865 },
      "motherboard": { "x": -0.35000000000000003, "y": -0.28942643644489086, "z": 0.02235310048561348 },
      "gpu": { "x": -0.1458, "y": -0.40663443644489083, "z": 0.1691051004856135 },
      "cooler-block": { "x": 0, "y": -0.030826436444890776, "z": 0.005638484474569938 },
      "case-fan-front-3": { "x": 0, "y": 0.47287569772283783, "z": 0.67 },
      "case-fan-front-2": { "x": 0, "y": 0.06437569772283785, "z": 0.67 },
      "case-fan-front-1": { "x": 0, "y": -0.3441243022771621, "z": 0.67 },
      "cooler-air": { "x": -0.315, "y": -0.10790400000000006, "z": -0.024415907147717852 },
      "cooler-block-liquid": { "x": 0, "y": -0.0337068197016101, "z": 0.10490332645172651 },
      "cooler-rad-liquid": { "x": 0.27696444783752305, "y": -0.41559994248659504, "z": 0.45754239776150063 },
      "cooler-liquid": { "x": -0.315, "y": -0.10790400000000006, "z": -0.17589064604337468 }
    },
    "case-nexm2": {
      "case": { "x": 0, "y": -0.4360249062512466, "z": 0 },
      "case-fan-rear-1": { "x": 0.00620935968785824, "y": 0.427099508271067, "z": -0.6652261091703573 },
      "cooler-rad": { "x": 0.316, "y": -0.3063721926693336, "z": 0.06738708898976475 },
      "case-fan-front-1": { "x": 0, "y": -0.09588300606598399, "z": 0.5850000000000001 },
      "psu": { "x": -0.09960000000000002, "y": -0.8621996895729026, "z": -0.2723 },
      "motherboard": { "x": -0.33, "y": -0.32178308209365536, "z": 0.002379474162122114 },
      "cooler": { "x": -0.295, "y": -0.2124561268834869, "z": -0.0035763297206485856 },
      "ram": { "x": -0.29, "y": -0.2124561268834869, "z": 0.03831195216038469 },
      "gpu": { "x": -0.1258, "y": -0.45872812688348696, "z": 0.04694450168771497 },
      "cooler-block": { "x": 0, "y": 0.03800713382706333, "z": -0.057617844146383546 },
      "cooler-air": { "x": -0.295, "y": -0.17225862247877666, "z": -0.07064391079978663 },
      "cooler-liquid": { "x": -0.295, "y": -0.08627200000000004, "z": -0.15637194991837916 },
      "cooler-block-liquid": { "x": 0, "y": -0.08617683735191192, "z": 0.08591972067241901 },
      "cooler-rad-liquid": { "x": 0.30760019218194856, "y": -0.4037107503484756, "z": 0.36473329502314433 }
    }
  },
  "exportedCase": "case-nexair",
  "exportedAt": "2026-05-31T00:00:00.000Z"
    };
    const savedPositions = {};
    // initialize defaults immediately from the embedded hardcoded positions
    Object.assign(savedPositions, DEFAULT_POSITION_PAYLOAD.savedPositions || {});
    const partGroups = {};
    const undoStack = [];
    let currentUndoStep = null;
    const POSITION_STORAGE_KEY = 'nexus3d_positions_v2';
    let envLights = {};
    let envFloor = null;
    let envGrid = null;
    let environmentMode = 'dark';
    let airflowVisible = false;
    let airflowGroup = null;
    const sceneSelectedParts = [];
    let lastSelectedAverage = new THREE.Vector3();
    let moboWPos = new THREE.Vector3();
    let moboHeight = 0, moboWidth = 0;
    let socketRelPos = new THREE.Vector3();
    let pcieRelPos = new THREE.Vector3();
    let raycaster, pointer;
    let coolerBlockGroup = null;
    let coolerRadGroup = null;
    let coolerTubeGroup = null;

    // Three.js refs
    let scene, cam, renderer, controls, chassis;
    let mCase, mGlass, mMobo, mGpu, mCooler, mRam, mPsu;
    let rgbMats = [], fans3d = [], wireMeshes = [];
    // materials that switch transparency when camera is below a fan (GPU bottom-only transparency)
    let fanVisibilityMats = [];
    let wireEnabled = false;
    let highlightOverlays = [];

    let incompatibilityIndicator = null;
    let incompatibilityIndicatorBaseY = 0;
    let incompatibilityAlertVisible = false;
    let incompatibilityColor = 0xff0000;

    let gizmoRoot, gizmoAxis = null, gizmoDrag = false;
    let gizmoPlane = null, gizmoPlaneOrigin = new THREE.Vector3();
    let gizmoDragAxis = new THREE.Vector3();
    let gizmoDragStartScalar = 0;
    let gizmoDragStartPositions = [];
    let adminModeEnabled = false;
    let serverSaveTimeout = null;
    // Snapshot of baseline positions used for explode/revert so offsets don't accumulate
    let explodeBaselinePositions = null;

    // =====================================================
    // UI LOGIC
    // =====================================================
    function switchTab(id) {
        ['parts','rgb'].forEach(t => {
            document.getElementById('section-'+t).classList.remove('active');
            const btn = document.getElementById('tab-'+t);
            if(t===id){
                document.getElementById('section-'+t).classList.add('active');
                btn.className = btn.className.replace('border-transparent text-slate-500','border-cyan-500 text-cyan-400');
            } else {
                btn.className = btn.className.replace('border-cyan-500 text-cyan-400','border-transparent text-slate-500');
            }
        });
    }

    function setEnvironmentMode(mode) {
        environmentMode = mode === 'dark' ? 'dark' : 'light';
        if(!scene || !envLights.ambient || !envFloor || !envGrid) return;

        if(environmentMode === 'light') {
            scene.background = new THREE.Color(0xf3f5f7);
            scene.fog.color.setHex(0xf3f5f7);
            scene.fog.density = 0.025;

            envLights.ambient.color.setHex(0xf1f5f9);
            envLights.ambient.intensity = 1.5;
            envLights.sun.color.setHex(0xffffff);
            envLights.sun.intensity = 2.2;
            envLights.fill.color.setHex(0xdbeafe);
            envLights.fill.intensity = 1.4;
            envLights.rim.color.setHex(0x93c5fd);
            envLights.rim.intensity = 0.55;

            envFloor.material.color.setHex(0x03050a);
            envFloor.material.roughness = 0.7;
            envFloor.material.metalness = 0.9;

            envGrid.material.color.setHex(0x94a3b8);
            envGrid.material.opacity = 0.32;
            envGrid.material.transparent = true;
        } else {
            scene.background = new THREE.Color(0x03050b);
            scene.fog.color.setHex(0x03050b);
            scene.fog.density = 0.045;

            envLights.ambient.color.setHex(0x0a0d18);
            envLights.ambient.intensity = 1.4;
            envLights.sun.color.setHex(0xffffff);
            envLights.sun.intensity = 2.2;
            envLights.fill.color.setHex(0x1e40af);
            envLights.fill.intensity = 1.8;
            envLights.rim.color.setHex(0x0e7490);
            envLights.rim.intensity = 0.8;

            envFloor.material.color.setHex(0x03050a);
            envFloor.material.roughness = 0.7;
            envFloor.material.metalness = 0.9;

            envGrid.material.color.setHex(0x0f1f35);
            envGrid.material.opacity = 1;
            envGrid.material.transparent = false;
        }

        const btn = document.getElementById('env-mode-btn');
        if(btn) {
            btn.innerHTML = environmentMode === 'light'
                ? '<i class="fa-solid fa-sun text-amber-300 mr-1"></i>Light Studio'
                : '<i class="fa-solid fa-moon text-sky-300 mr-1"></i>Dark Studio';
        }
    }

    function toggleEnvironmentMode() {
        setEnvironmentMode(environmentMode === 'dark' ? 'light' : 'dark');
    }

    function toggleAirflow() {
        airflowVisible = !airflowVisible;
        if(airflowVisible) {
            createAirflowVisualization();
        } else {
            if(airflowGroup && airflowGroup.parent) {
                airflowGroup.parent.remove(airflowGroup);
            }
            airflowGroup = null;
        }
        const btn = document.getElementById('airflow-btn');
        if(btn) {
            btn.classList.toggle('border-blue-500/60', airflowVisible);
            btn.classList.toggle('bg-blue-500/10', airflowVisible);
        }
    }

    const COLOR_INTAKE = 0x00ffff; // cyan
    const COLOR_EXHAUST = 0xff4444; // red

    // Create an arrow between two world-space points. Tail = start, Tip = end.
    function createArrowBetween(start, end, color, opts = {}) {
        const dir = end.clone().sub(start);
        const length = dir.length();
        if(length < 0.02) return null;
        const unit = dir.clone().normalize();

        const headLen = Math.min(0.12, length * 0.25);
        const shaftLen = Math.max(0.02, length - headLen);

        // Use an unlit material so arrow colors remain constant regardless of scene lighting
        const mat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 1.0 });
        mat.depthTest = false; mat.depthWrite = false;

        const group = new THREE.Group();

        // Shaft: cylinder aligned on +Z from z=0 to z=shaftLen
        const shaftGeo = new THREE.CylinderGeometry(0.015, 0.015, shaftLen, 8);
        const shaft = new THREE.Mesh(shaftGeo, mat.clone());
        shaft.rotation.x = Math.PI/2; // align to Z
        shaft.position.z = shaftLen / 2; // place so base at z=0
        group.add(shaft);

        // Head: cone pointing along +Z. Default cone tip is at +Y/2; rotate to Z and position so tip at length
        const headGeo = new THREE.ConeGeometry(0.04, headLen, 8);
        const head = new THREE.Mesh(headGeo, mat.clone());
        head.rotation.x = Math.PI/2; // point along +Z
        // place head so its center is at shaftLen + headLen/2, which makes tip at shaftLen + headLen = length
        head.position.z = shaftLen + headLen / 2;
        group.add(head);

        // Orient group so local +Z points along dir, then place at start
        const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,0,1), unit);
        group.quaternion.copy(q);
        group.position.copy(start);

        // render on top
        group.traverse(m => { if(m.isMesh){ m.renderOrder = 9999; m.material.depthTest = false; m.material.depthWrite = false; } });

        // store metadata for animation/updates
        group.userData = {
            start: start.clone(),
            end: end.clone(),
            dir: unit.clone(),
            isRad: !!opts.isRad,
            sideSeed: Math.random() * Math.PI * 2
        };
        return group;
    }

    function createAirflowVisualization() {
        if(airflowGroup && airflowGroup.parent) {
            airflowGroup.parent.remove(airflowGroup);
        }
        
        airflowGroup = new THREE.Group();
        scene.add(airflowGroup);
        
        // FRONT: intake arrows placed from slightly outside -> inside near motherboard
        const frontKeys = ['case-fan-front-1','case-fan-front-2','case-fan-front-3'];
        frontKeys.forEach(key => {
            const g = partGroups[key];
            if(!g) return;
            // ensure world matrices up to date
            if(g.updateMatrixWorld) g.updateMatrixWorld(true);
            // world position and forward vector (local +Z)
            const worldPos = g.getWorldPosition(new THREE.Vector3());
            const forward = new THREE.Vector3(0,0,1).applyQuaternion(g.getWorldQuaternion(new THREE.Quaternion())).normalize();
            // start slightly in front of the fan (outside)
            const start = worldPos.clone().add(forward.clone().multiplyScalar(0.14));
            // end a bit inside the case toward motherboard
            const end = worldPos.clone().add(forward.clone().multiplyScalar(-0.18));
            const arrow = createArrowBetween(start, end, COLOR_INTAKE);
            if(arrow) airflowGroup.add(arrow);
        });

        // REAR: arrow (flipped orientation) — create from outside -> inside (opposite of previous)
        if(partGroups['case-fan-rear-1']){
            const g = partGroups['case-fan-rear-1'];
            if(g.updateMatrixWorld) g.updateMatrixWorld(true);
            const worldPos = g.getWorldPosition(new THREE.Vector3());
            const forward = new THREE.Vector3(0,0,1).applyQuaternion(g.getWorldQuaternion(new THREE.Quaternion())).normalize();
            // flip: start outside, end inside (opposite direction)
            const start = worldPos.clone().add(forward.clone().multiplyScalar(0.14)); // outside
            const end = worldPos.clone().add(forward.clone().multiplyScalar(-0.18)); // inside
            const arrow = createArrowBetween(start, end, COLOR_EXHAUST);
            if(arrow) airflowGroup.add(arrow);
        }

        // 2nd rear fan arrow (if exists)
        if(partGroups['case-fan-rear-2']){
            const g = partGroups['case-fan-rear-2'];
            if(g.updateMatrixWorld) g.updateMatrixWorld(true);
            const worldPos = g.getWorldPosition(new THREE.Vector3());
            const forward = new THREE.Vector3(0,0,1).applyQuaternion(g.getWorldQuaternion(new THREE.Quaternion())).normalize();
            const start = worldPos.clone().add(forward.clone().multiplyScalar(0.14)); // outside
            const end = worldPos.clone().add(forward.clone().multiplyScalar(-0.18)); // inside
            const arrow = createArrowBetween(start, end, COLOR_EXHAUST);
            if(arrow) airflowGroup.add(arrow);
        }

        // RADIATOR: if AIO installed, add one arrow per radiator fan pointing upward (exhaust)
        if(coolerRadGroup && build.cooler && build.cooler.type === 'liquid'){
            if(coolerRadGroup.updateMatrixWorld) coolerRadGroup.updateMatrixWorld(true);
            // radiator children: radiator mesh + fan groups
            coolerRadGroup.children.forEach(child => {
                if(child.type === 'Group'){
                    if(child.updateMatrixWorld) child.updateMatrixWorld(true);
                    const fanWorld = child.getWorldPosition(new THREE.Vector3());
                    // start slightly above the fan's face (inside side below radiator), end above radiator
                    const start = fanWorld.clone().add(new THREE.Vector3(0,0.02,0));
                    const end = fanWorld.clone().add(new THREE.Vector3(0,0.22,0));
                    const arrow = createArrowBetween(start, end, COLOR_EXHAUST, { isRad:true });
                    if(arrow) airflowGroup.add(arrow);
                }
            });
        }
    }

    function buildAccordion() {
        const cats = [
            { key:'case',        label:'PC Case',        icon:'fa-folder-open',    db:'cases' },
            { key:'cpu',         label:'Processor',      icon:'fa-microchip',      db:'cpus' },
            { key:'gpu',         label:'Graphics Card',  icon:'fa-tv',             db:'gpus' },
            { key:'motherboard', label:'Motherboard',    icon:'fa-circle-nodes',   db:'motherboards' },
            { key:'ram',         label:'System Memory',  icon:'fa-memory',         db:'ram' },
            { key:'cooler',      label:'CPU Cooler',     icon:'fa-wind',           db:'coolers' },
            { key:'psu',         label:'Power Supply',   icon:'fa-plug',           db:'psus' },
            { key:'storage',     label:'Storage Drive',  icon:'fa-database',       db:'storage' }
        ];

        const cont = document.getElementById('category-accordion');
        if(!cont) return; // defensive: some pages use a different DOM structure
        cont.innerHTML = '';

        cats.forEach(cat => {
            const sel = build[cat.key] || null;
            const div = document.createElement('div');
            div.className = 'rounded-xl glass-lite overflow-hidden';

            let items = `<div onclick="selectItem(event,'${cat.key}','none')" class="item-card ${sel===null?'selected':''}">
                    <div class="flex items-center gap-2 min-w-0">
                        <div class="dot"></div>
                        <div class="min-w-0">
                            <div class="text-[10px] font-bold truncate ${sel===null?'text-white':'text-slate-300'}">None</div>
                        </div>
                    </div>
                    <span class="orbitron text-[10px] font-black text-slate-400 shrink-0 ml-2">—</span>
                </div>`;
            const itemsList = DB[cat.db] || [];
            items += itemsList.map(item => {
                const isSelected = sceneSelectedParts.includes(cat.key) && sel && sel.id === item.id;
                const phpPrice = item.price === 0 ? 'Free' : `₱${item.price.toLocaleString()}`;
                return `<div onclick="selectItem(event,'${cat.key}','${item.id}')" 
                            class="item-card ${isSelected?'selected':''}">
                    <div class="flex items-center gap-2 min-w-0">
                        <div class="dot"></div>
                        <div class="min-w-0">
                            <div class="text-[10px] font-bold truncate ${isSelected?'text-white':'text-slate-300'}">${item.name}</div>
                        </div>
                    </div>
                    <span class="orbitron text-[10px] font-black text-emerald-400 shrink-0 ml-2">${phpPrice}</span>
                </div>`;
            }).join('');
            if(cat.key === 'case') {
                // expose case-mounted fans as selectable/movable items
                const fanKeys = Object.keys(partGroups).filter(k => k.startsWith('case-fan-'));
                fanKeys.forEach(fk => {
                    const isSelected = sceneSelectedParts.includes(fk);
                    // human-friendly label
                    let label = fk.replace('case-fan-','').replace(/-/g,' ').toUpperCase();
                    label = label.split(' ').map(s=>s.charAt(0).toUpperCase()+s.slice(1)).join(' ');
                    items += `<div onclick="selectItem(event,'case-fan','${fk}')" class="item-card ${isSelected?'selected':''}">
                        <div class="flex items-center gap-2 min-w-0">
                            <div class="dot"></div>
                            <div class="min-w-0">
                                <div class="text-[10px] font-bold truncate ${isSelected?'text-white':'text-slate-300'}">${label}</div>
                            </div>
                        </div>
                        <span class="orbitron text-[10px] font-black text-slate-400 shrink-0">—</span>
                    </div>`;
                });
            }
            if(cat.key === 'cooler' && build.cooler) {
                const coolerBlockSelected = sceneSelectedParts.includes('cooler-block');
                if(build.cooler.type === 'liquid') {
                    const coolerHeadSelected = sceneSelectedParts.includes('cooler-rad');
                    items += `<div onclick="selectItem(event,'cooler-rad','cooler-rad')" class="item-card ${coolerHeadSelected?'selected':''}">
                        <div class="flex items-center gap-2 min-w-0">
                            <div class="dot"></div>
                            <div class="min-w-0">
                                <div class="text-[10px] font-bold truncate ${coolerHeadSelected?'text-white':'text-slate-300'}">Cooler Radiator</div>
                            </div>
                        </div>
                        <span class="orbitron text-[10px] font-black text-slate-400 shrink-0">—</span>
                    </div>`;
                }
                items += `<div onclick="selectItem(event,'cooler-block','cooler-block')" class="item-card ${coolerBlockSelected?'selected':''}">
                    <div class="flex items-center gap-2 min-w-0">
                        <div class="dot"></div>
                        <div class="min-w-0">
                            <div class="text-[10px] font-bold truncate ${coolerBlockSelected?'text-white':'text-slate-300'}">Cooler Block</div>
                        </div>
                    </div>
                    <span class="orbitron text-[10px] font-black text-slate-400 shrink-0">—</span>
                </div>`;
            }

            const activePrice = sel ? (sel.price===0 ? 'Free' : `₱${sel.price.toLocaleString()}`) : 'None';
            div.innerHTML = `
                <div class="px-3 py-2.5 flex items-center justify-between bg-black/20 cursor-pointer hover:bg-black/40 transition" onclick="focusMesh('${cat.key}')">
                    <div class="flex items-center gap-2">
                        <div class="w-6 h-6 rounded-md bg-white/5 flex items-center justify-center text-slate-400 text-xs">
                            <i class="fa-solid ${cat.icon}"></i>
                        </div>
                        <div>
                            <div class="text-[8px] text-slate-600 uppercase tracking-widest mono">${cat.key}</div>
                            <div class="orbitron text-[10px] font-bold text-slate-300 uppercase">${cat.label}</div>
                        </div>
                    </div>
                    <span class="orbitron text-[9px] font-black text-emerald-400">${activePrice}</span>
                </div>
                <div class="px-2 pb-2 pt-1 space-y-1 border-t border-white/5">${items}</div>`;
            cont.appendChild(div);
        });

        updateBuildStats();
    }

    function selectItem(event, cat, id) {
        const dbMap = { case:'cases', cpu:'cpus', gpu:'gpus', motherboard:'motherboards',
                        ram:'ram', cooler:'coolers', psu:'psus', storage:'storage' };
        // case fans selection (front/rear/top) — keys look like 'case-fan-front-1' etc.
        const multiSelect = event.ctrlKey || event.metaKey;
        if(cat === 'case-fan' || cat === 'case-fan') {
            // id parameter contains the fan key
            const fanKey = id;
            selectComponentGroup(fanKey, multiSelect);
            document.getElementById('active-cat').textContent = 'CASE FAN';
            // friendly name
            let name = fanKey.replace('case-fan-','').replace(/-/g,' ');
            name = name.split(' ').map(s=>s.charAt(0).toUpperCase()+s.slice(1)).join(' ');
            document.getElementById('active-name').textContent = name;
            document.getElementById('active-price').textContent = '—';
            document.getElementById('active-desc').textContent = 'Inspect this fan inside the current case preview.';
            buildAccordion();
            return;
        }
        if(cat === 'cooler-rad' || cat === 'cooler-block') {
            selectComponentGroup(cat, multiSelect);
            document.getElementById('active-cat').textContent = 'COOLER PART';
            document.getElementById('active-name').textContent = cat === 'cooler-rad' ? 'Radiator Assembly' : 'CPU Pump Block';
            document.getElementById('active-price').textContent = '—';
            document.getElementById('active-desc').textContent = 'Inspect cooling parts in the assembly preview.';
            buildAccordion();
            return;
        }
        if(id === 'none') {
            build[cat] = null;
            document.getElementById('active-cat').textContent = cat.toUpperCase();
            document.getElementById('active-name').textContent = 'None';
            document.getElementById('active-price').textContent = '—';
            document.getElementById('active-desc').textContent = 'No component selected for this slot.';
            rebuildMesh(cat);
            buildAccordion();
            return;
        }
        const item = DB[dbMap[cat]].find(x=>x.id===id);
        if(!item) return;

        if(event.ctrlKey || event.metaKey) {
            toggleSelection(cat);
            return;
        }

        if(exploded) {
            exploded = false;
            const btn = document.getElementById('explode-btn');
            if(btn) btn.classList.remove('border-pink-500/40','text-pink-300');
            const focusLabel = document.getElementById('focus-label');
            if(focusLabel) focusLabel.innerHTML = `<i class="fa-solid fa-expand mr-1"></i><span class="mono text-[9px]">Free Orbit Mode</span>`;
            if(mGlass) mGlass.position.set(build.case.dims.w/2, 0, 0);
            if(mCase) mCase.position.set(0, 0, 0);
            applySavedPositionsForCurrentCase();
        }

        build[cat] = item;
        selectComponentGroup(cat, false);

        document.getElementById('active-cat').textContent = cat.toUpperCase();
        document.getElementById('active-name').textContent = item.name;
        const phpPrice = item.price===0 ? 'Included' : `₱${item.price.toLocaleString()}`;
        document.getElementById('active-price').textContent = phpPrice;
        document.getElementById('active-desc').textContent = item.desc;

        rebuildMesh(cat);
        if(airflowVisible) createAirflowVisualization();
        buildAccordion();
    }

    function updateBuildStats() {
        // Totals
        let total = 0, draw = 0;
        Object.values(build).forEach(v => {
            total += v?.price || 0;
            if(v?.tdp) draw += v.tdp;
            if(v?.power) draw += v.power;
        });
        const psuW = build.psu?.wattage || 0;
        const safePsuW = psuW || 1;
        draw += 60; // board + RAM + storage overhead

        document.getElementById('top-price').textContent = `₱${total.toLocaleString()}`;
        document.getElementById('top-wattage').textContent = `${draw}W / ${psuW || 'N/A'}W`;

        // Power bar
        const pct = Math.min(100, Math.round((draw/safePsuW)*100));
        const bar = document.getElementById('power-bar-fill');
        if(bar) {
            bar.style.width = pct+'%';
            bar.className = 'metric-bar-fill ' + (pct>90?'bg-red-500':pct>75?'bg-amber-500':'bg-emerald-500');
        }
        const pwLabel = document.getElementById('pw-label');
        if(pwLabel) pwLabel.textContent = `${draw}W used / ${psuW ? psuW + 'W' : 'N/A'}`;
        const pwPct = document.getElementById('pw-pct');
        if(pwPct) pwPct.textContent = pct+'%';
        const pwPsu = document.getElementById('pw-psu-label');
        if(pwPsu) pwPsu.textContent = psuW ? `${psuW}W` : 'N/A';
        const pwAdvice = document.getElementById('pw-advice');
        if(pwAdvice) pwAdvice.textContent = !psuW ? '⚠ Add a power supply to complete the system.' :
            pct>90 ? '⚠ PSU overloaded! Upgrade power supply.' :
            pct>75 ? '⚡ Tight headroom. Consider higher wattage PSU.' :
            pct>50 ? '✓ Comfortable headroom for safe operation.' : '✓ PSU well within limits.';

        // Compatibility checks
        const checks = [];
        const cpuSock = build.cpu?.socket || 'N/A', moboSock = build.motherboard?.socket || 'N/A';
        const cpuDdr = build.cpu?.ddr || 'N/A', moboDdr = build.motherboard?.ddr || 'N/A', ramDdr = build.ram?.ddr || 'N/A';
        const caseF = build.case?.factor || 'N/A', moboF = build.motherboard?.factor || 'N/A';
        const caseSupportsMobo = !build.case || !build.motherboard ? true : build.case.supportedFactors.includes(moboF);
        const gpuFits = !build.gpu || !build.case ? true : build.gpu.length <= build.case.gpuClearance;
        
        // Cooler compatibility
        let coolerOk = true, coolerDetail = 'N/A';
        if(build.cooler && build.case) {
            if(build.cooler.type === 'air') {
                coolerOk = (build.cooler.height || 0) <= build.case.cpuCoolerLimit;
                coolerDetail = `${build.cooler.height || 0}mm / ${build.case.cpuCoolerLimit}mm`;
            } else if(build.cooler.type === 'liquid') {
                coolerOk = build.case.radiatorSupport.includes(build.cooler.radiator);
                coolerDetail = `${build.cooler.radiator} / ${build.case.radiatorSupport.join(', ')}`;
            }
        }

        checks.push({ label:'CPU ↔ Socket', ok: cpuSock===moboSock, detail: cpuSock+' / '+moboSock });
        checks.push({ label:'Mobo ↔ RAM DDR', ok: moboDdr===ramDdr, detail: moboDdr+' / '+ramDdr });
        checks.push({ label:'CPU ↔ RAM DDR', ok: cpuDdr===ramDdr, detail: cpuDdr+' / '+ramDdr });
        checks.push({ label:'Case ↔ Mobo Form', ok: caseSupportsMobo, detail: caseF+' / '+moboF });
        checks.push({ label:'GPU Clearance', ok: gpuFits, detail: build.gpu && build.case ? `${build.gpu.length}mm / ${build.case.gpuClearance}mm` : 'N/A' });
        checks.push({ label:'CPU Cooler ↔ Case', ok: coolerOk, detail: coolerDetail });
        checks.push({ label:'PSU Headroom', ok: draw<=safePsuW*0.9, detail: pct+'% load' });

        const allOk = checks.every(c=>c.ok);
        document.getElementById('diagnostic-badge').innerHTML = allOk
            ? `<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping inline-block"></span> NOMINAL`
            : `<span class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse inline-block"></span> <span class="text-red-400">WARNINGS</span>`;

        updateModelHighlights(caseSupportsMobo, gpuFits, coolerOk);

        const cl = document.getElementById('compat-list');
        if(cl) {
            cl.innerHTML = checks.map(c=>`
                <div class="compat-row">
                    <span class="text-slate-400">${c.label}</span>
                    <div class="flex items-center gap-1.5">
                        <span class="mono text-[9px] ${c.ok?'text-slate-500':'text-red-400'}">${c.detail}</span>
                        <i class="fa-solid ${c.ok?'fa-check text-emerald-400':'fa-xmark text-red-400'} text-[10px]"></i>
                    </div>
                </div>`).join('');
        }

        // FPS estimate (rough CPU×GPU combined)
        const cpuPerf = build.cpu?.perf || 50;
        const gpuPerf = build.gpu?.perf || 40;
        const bottleneck = Math.min(cpuPerf, gpuPerf) / Math.max(cpuPerf, gpuPerf);
        const sysPower = (cpuPerf * 0.35 + gpuPerf * 0.65) * bottleneck * 0.95 + 5;
        const fpsGames = [
            { game:'Valorant 1080p Low',  mult:2.8 },
            { game:'CS2 1080p High',      mult:2.0 },
            { game:'Fortnite 1080p Med',  mult:1.4 },
            { game:'GTA V 1080p High',    mult:1.1 },
            { game:'Cyberpunk 1080p Low', mult:0.5 }
        ];
        const fl = document.getElementById('fps-list');
        if(fl) {
            fl.innerHTML = fpsGames.map(g=>{
                const fps = Math.round(sysPower * g.mult);
                const pct = Math.min(100, (fps/240)*100);
                const col = fps>=144?'bg-emerald-500':fps>=60?'bg-blue-500':fps>=30?'bg-amber-500':'bg-red-500';
                return `<div>
                    <div class="flex justify-between mb-0.5">
                        <span class="text-[9px] text-slate-400 mono">${g.game}</span>
                        <span class="orbitron text-[9px] font-bold text-slate-200">${fps} FPS</span>
                    </div>
                    <div class="metric-bar-bg"><div class="${col} metric-bar-fill" style="width:${pct}%"></div></div>
                </div>`;
            }).join('');
        }

        // Build summary
        const sl = document.getElementById('summary-list');
        const cats = [['CPU','cpu'],['GPU','gpu'],['Mobo','motherboard'],['RAM','ram'],['PSU','psu'],['Case','case'],['Cooler','cooler'],['Storage','storage']];
        if(sl) {
            sl.innerHTML = cats.map(([label,key])=>{
                const item = build[key];
                const name = item?.name || 'None';
                const price = item ? (item.price===0 ? 'Free' : `₱${item.price.toLocaleString()}`) : '—';
                return `<div class="flex justify-between items-start">
                    <span class="text-[9px] text-slate-500 mono uppercase w-14 shrink-0">${label}</span>
                    <span class="text-[9px] text-slate-300 flex-1 mx-2 truncate">${name}</span>
                    <span class="text-[9px] text-emerald-400 mono shrink-0">${price}</span>
                </div>`;
            }).join('');
        }
        const summaryTotal = document.getElementById('summary-total');
        if(summaryTotal) summaryTotal.textContent = `₱${total.toLocaleString()}`;
    }

    function getGroupByKey(key) {
        if(partGroups[key]) return partGroups[key];
        return {
            case: mCase,
            motherboard: mMobo,
            gpu: mGpu,
            cooler: mCooler,
            ram: mRam,
            psu: mPsu
        }[key] || null;
    }

    function pushUndoStep(changes) {
        if(!changes || !changes.length) return;
        undoStack.push(changes.map(item => ({ key:item.key, pos:item.pos.clone() })));
        if(undoStack.length > 50) undoStack.shift();
    }

    function undoLastAction() {
        if(undoStack.length === 0) return;
        const changes = undoStack.pop();
        changes.forEach(({key, pos}) => {
            const group = getGroupByKey(key);
            if(!group) return;
            group.position.copy(pos);
            setSavedPosition(key, group.position);
        });
        if(mCooler) refreshCoolerTubes();
        updateSelectedUI();
    }

    function findGizmoAxis(object) {
        let current = object;
        while(current && !current.userData.axis) {
            current = current.parent;
        }
        return current ? current.userData.axis : null;
    }

    function createTransformGizmo() {
        gizmoRoot = new THREE.Group();
        gizmoRoot.visible = false;

        ['x','y','z'].forEach(axis => {
            const arrow = makeGizmoArrow(axis);
            arrow.userData.axis = axis;
            arrow.name = `gizmo-${axis}`;
            gizmoRoot.add(arrow);
        });

        scene.add(gizmoRoot);
    }

    function makeGizmoArrow(axis) {
        const color = axis === 'x' ? 0xff3b3b : axis === 'y' ? 0x22c55e : 0x2563eb;
        const dir = axis === 'x' ? new THREE.Vector3(1,0,0) : axis === 'y' ? new THREE.Vector3(0,1,0) : new THREE.Vector3(0,0,1);
        const g = new THREE.Group();
        g.renderOrder = 9999;

        const shaft = new THREE.Mesh(
            new THREE.CylinderGeometry(0.01, 0.01, 0.45, 10),
            new THREE.MeshBasicMaterial({color, opacity:0.85, transparent:true, depthTest:false, depthWrite:false})
        );
        shaft.position.copy(dir.clone().multiplyScalar(0.225));
        if(axis === 'x') shaft.rotation.z = -Math.PI/2;
        if(axis === 'z') shaft.rotation.x = Math.PI/2;
        shaft.renderOrder = 9999;

        const head = new THREE.Mesh(
            new THREE.ConeGeometry(0.035, 0.12, 12),
            new THREE.MeshBasicMaterial({color, opacity:0.95, transparent:true, depthTest:false, depthWrite:false})
        );
        head.position.copy(dir.clone().multiplyScalar(0.48));
        if(axis === 'x') head.rotation.z = -Math.PI/2;
        if(axis === 'z') head.rotation.x = -Math.PI/2;
        head.renderOrder = 9999;

        const pick = new THREE.Mesh(
            new THREE.CylinderGeometry(0.08, 0.08, 0.6, 6),
            new THREE.MeshBasicMaterial({color:0x000000, transparent:true, opacity:0.001, depthTest:false, depthWrite:false})
        );
        pick.position.copy(dir.clone().multiplyScalar(0.25));
        if(axis === 'x') pick.rotation.z = -Math.PI/2;
        if(axis === 'z') pick.rotation.x = Math.PI/2;
        pick.userData.axis = axis;
        pick.renderOrder = 9999;

        g.add(shaft, head, pick);
        g.userData.axis = axis;
        return g;
    }

    function updateTransformGizmo() {
        if(!gizmoRoot) return;
        if(!adminModeEnabled || sceneSelectedParts.length === 0) {
            gizmoRoot.visible = false;
            return;
        }
        gizmoRoot.visible = true;
        gizmoRoot.position.copy(lastSelectedAverage);
        const distance = Math.max(0.8, cam.position.distanceTo(lastSelectedAverage));
        gizmoRoot.scale.setScalar(distance * 0.12);
        gizmoRoot.updateMatrixWorld();
    }

    function startGizmoDrag(axis) {
        if(!adminModeEnabled || !axis || sceneSelectedParts.length === 0) return;
        gizmoDrag = true;
        gizmoAxis = axis;
        controls.enabled = false;

        const origin = gizmoRoot.getWorldPosition(new THREE.Vector3());
        gizmoPlaneOrigin.copy(origin);
        const planeNormal = cam.getWorldDirection(new THREE.Vector3()).clone().normalize();
        gizmoPlane = new THREE.Plane().setFromNormalAndCoplanarPoint(planeNormal, origin);

        gizmoDragAxis.set(axis === 'x' ? 1 : axis === 'y' ? 0 : 0, axis === 'x' ? 0 : axis === 'y' ? 1 : 0, axis === 'z' ? 1 : 0);
        if(axis === 'z') gizmoDragAxis.set(0,0,1);

        const intersectStart = new THREE.Vector3();
        raycaster.ray.intersectPlane(gizmoPlane, intersectStart);
        gizmoDragStartScalar = gizmoDragAxis.dot(intersectStart.clone().sub(gizmoPlaneOrigin));

        gizmoDragStartPositions = sceneSelectedParts.map(key => ({
            key,
            position: getGroupByKey(key).position.clone()
        }));
        currentUndoStep = gizmoDragStartPositions.map(item => ({ key:item.key, pos:item.position.clone() }));
    }

    function updateGizmoDrag(event) {
        if(!gizmoDrag) return;
        const rect = renderer.domElement.getBoundingClientRect();
        pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(pointer, cam);
        const intersection = new THREE.Vector3();
        if(!raycaster.ray.intersectPlane(gizmoPlane, intersection)) return;

        const scalar = gizmoDragAxis.dot(intersection.clone().sub(gizmoPlaneOrigin));
        const delta = scalar - gizmoDragStartScalar;
        if(Math.abs(delta) < 0.0001) return;

        sceneSelectedParts.forEach(key => {
            const saved = gizmoDragStartPositions.find(item => item.key === key);
            if(!saved) return;
            const group = getGroupByKey(key);
            const offset = gizmoDragAxis.clone().multiplyScalar(delta);
            group.position.copy(saved.position.clone().add(offset));
            positionOverrides[key] = group.position.clone();
            setSavedPosition(key, group.position);
        });
        updateSelectedUI();
    }

    function endGizmoDrag() {
        if(!gizmoDrag) return;
        gizmoDrag = false;
        gizmoAxis = null;
        controls.enabled = true;
        if(currentUndoStep && currentUndoStep.some(item => {
            const group = getGroupByKey(item.key);
            return group && !group.position.equals(item.pos);
        })) {
            pushUndoStep(currentUndoStep);
        }
        currentUndoStep = null;
    }

    function isValidSavedPosition(pos) {
        return pos && typeof pos === 'object'
            && Number.isFinite(pos.x) && Number.isFinite(pos.y) && Number.isFinite(pos.z);
    }

    function sanitizeSavedPositions(source) {
        if(!source || typeof source !== 'object') return {};
        const sanitized = {};
        Object.keys(source).forEach(caseId => {
            if(!source[caseId] || typeof source[caseId] !== 'object') return;
            const caseMap = {};
            Object.keys(source[caseId]).forEach(key => {
                if(isValidSavedPosition(source[caseId][key])) {
                    caseMap[key] = source[caseId][key];
                }
            });
            if(Object.keys(caseMap).length) sanitized[caseId] = caseMap;
        });
        return sanitized;
    }

    async function loadSavedPositions() {
        try {
            const resp = await fetch('nexus3d_positions.json');
            if(resp.ok) {
                const data = await resp.json();
                const source = data && typeof data === 'object' ? (data.savedPositions || data) : null;
                if(source && typeof source === 'object') {
                    Object.assign(savedPositions, source);
                }
            }
        } catch (e) {
            console.warn('Could not load saved positions from JSON', e);
        }

        // Load persisted position overrides from localStorage if available.
        // This preserves user adjustments, but server-provided positions remain authoritative.
        try {
            const raw = window.localStorage.getItem(POSITION_STORAGE_KEY);
            if (raw) {
                const stored = JSON.parse(raw);
                if (stored && typeof stored === 'object') {
                    Object.keys(stored).forEach(caseId => {
                        if (!stored[caseId] || typeof stored[caseId] !== 'object') return;
                        if (!savedPositions[caseId]) savedPositions[caseId] = {};
                        Object.keys(stored[caseId]).forEach(key => {
                            if (!isValidSavedPosition(stored[caseId][key])) return;
                            if (savedPositions[caseId][key] === undefined) {
                                savedPositions[caseId][key] = stored[caseId][key];
                            }
                        });
                    });
                }
            }
        } catch (e) {
            console.warn('Could not load saved positions from localStorage', e);
        }

        // Remove the old storage key if it exists from prior builds.
        try {
            window.localStorage.removeItem('nexus3d_positions_v1');
        } catch (e) {
            console.warn('Could not clear old saved positions', e);
        }
    }

    async function persistPositionsToServer() {
        if (!window.builderIsAdmin) return;
        try {
            const response = await fetch('/nexus3d_positions.json', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ savedPositions })
            });
            if (!response.ok) {
                const detail = await response.text();
                console.warn('Failed to persist positions to server', response.status, detail);
            }
        } catch (e) {
            console.warn('Could not persist positions to server', e);
        }
    }

    function saveSavedPositions() {
        try {
            window.localStorage.setItem(POSITION_STORAGE_KEY, JSON.stringify(savedPositions));
        } catch (e) {
            console.warn('Could not persist positions', e);
        }

        if (window.builderIsAdmin) {
            if (serverSaveTimeout) {
                clearTimeout(serverSaveTimeout);
            }
            serverSaveTimeout = setTimeout(persistPositionsToServer, 300);
        }
    }

    function getCurrentCaseId() {
        return build && build.case && build.case.id ? build.case.id : 'default';
    }

    function getCasePositionMap() {
        const caseId = getCurrentCaseId();
        if(!savedPositions[caseId]) savedPositions[caseId] = {};
        return savedPositions[caseId];
    }

    function getSaveKey(key) {
        if(!build || !build.cooler) return key;
        if(key === 'cooler' || key === 'cooler-block' || key === 'cooler-rad') {
            const liquidGroup = new Set(['cool-ml240l', 'cool-le520', 'cool-arctic360']);
            if(liquidGroup.has(build.cooler.id)) {
                return `${key}-liquid`;
            }
            if(build.cooler.type === 'air' || build.cooler.type === 'air-cooler' || build.cooler.id === 'cool-stock' || build.cooler.id === 'cool-ak400') {
                return `${key}-${build.cooler.id}`;
            }
        }
        return key;
    }

    function getSavedPosition(key) {
        const caseId = getCurrentCaseId();
        const map = savedPositions[caseId];
        if(!map) return null;
        const saveKey = getSaveKey(key);
        if(map[saveKey]) return map[saveKey];
        // Backwards compatibility: allow older saved JSON using the generic key.
        if(saveKey !== key && map[key]) return map[key];
        return null;
    }

    function setSavedPosition(key, vector) {
        const map = getCasePositionMap();
        const saveKey = getSaveKey(key);
        const savedValue = { x: vector.x, y: vector.y, z: vector.z };
        map[saveKey] = savedValue;
        if(saveKey !== key) {
            map[key] = savedValue;
        }
        saveSavedPositions();
    }

    function mergeImportedPositions(obj) {
        if(!obj || typeof obj !== 'object') return;
        const source = obj.savedPositions && typeof obj.savedPositions === 'object' ? obj.savedPositions : obj;
        Object.keys(source).forEach(caseId => {
            if(typeof source[caseId] === 'object') {
                savedPositions[caseId] = Object.assign({}, savedPositions[caseId] || {}, source[caseId]);
            }
        });
        saveSavedPositions();
    }

    function getCurrentPositionExportPayload() {
        const caseId = getCurrentCaseId();
        const exportMap = {};
        const keys = new Set([
            ...Object.keys(savedPositions[caseId] || {}),
            ...Object.keys(partGroups || {})
        ]);
        keys.forEach(key => {
            const group = partGroups[key] || getGroupByKey(key);
            let pos = null;
            if(group && group.position && isValidSavedPosition(group.position)) {
                pos = { x: group.position.x, y: group.position.y, z: group.position.z };
            } else {
                const saved = savedPositions[caseId] && savedPositions[caseId][key];
                if(isValidSavedPosition(saved)) pos = saved;
            }
            if(pos) {
                exportMap[key] = pos;
            }
        });
        return {
            exportedCase: caseId,
            exportedAt: new Date().toISOString(),
            savedPositions: {
                [caseId]: exportMap
            }
        };
    }

    function exportPositionJSON() {
        if(!adminModeEnabled) {
            alert('Admin mode is required to export component positions.');
            return;
        }
        const payload = getCurrentPositionExportPayload();
        const caseId = payload.exportedCase || 'case';
        const safeName = caseId.replace(/[^a-zA-Z0-9_-]/g, '_');
        const filename = `nexus3d_positions_${safeName}_${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function triggerImportPositions() {
        if(!adminModeEnabled) {
            alert('Admin mode is required to import component positions.');
            return;
        }
        const input = document.getElementById('position-import-input');
        if(input) input.click();
    }

    function handlePositionImport(event) {
        if(!adminModeEnabled) {
            alert('Admin mode is required to import component positions.');
            if(event.target) event.target.value = '';
            return;
        }
        const file = event.target && event.target.files && event.target.files[0];
        if(!file) return;
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const data = JSON.parse(e.target.result);
                const imported = importPositionPayload(data);
                if(!imported) {
                    alert('No valid position data found in the imported file.');
                    return;
                }
                alert('Position file imported successfully.');
                applySavedPositionsForCurrentCase();
            } catch (err) {
                console.error('Position import failed:', err);
                alert('Unable to parse the imported JSON file.');
            } finally {
                if(event.target) event.target.value = '';
            }
        };
        reader.readAsText(file);
    }

    function importPositionPayload(obj) {
        if(!obj || typeof obj !== 'object') return false;
        const source = obj.savedPositions && typeof obj.savedPositions === 'object' ? obj.savedPositions : obj;
        const sanitized = sanitizeSavedPositions(source);
        const importedKeys = Object.keys(sanitized);
        if(importedKeys.length === 0) return false;
        importedKeys.forEach(caseId => {
            savedPositions[caseId] = Object.assign({}, savedPositions[caseId] || {}, sanitized[caseId]);
        });
        saveSavedPositions();
        return true;
    }

    function applySavedPosition(key) {
        const group = partGroups[key] || getGroupByKey(key);
        const saved = getSavedPosition(key);
        if(group && isValidSavedPosition(saved)) {
            group.position.set(saved.x, saved.y, saved.z);
            positionOverrides[key] = group.position.clone();
        }
    }

    function clearSavedPositionsForCurrentCase() {
        const caseId = getCurrentCaseId();
        if(savedPositions[caseId]) {
            delete savedPositions[caseId];
            saveSavedPositions();
        }
    }

    function applySavedPositionsForCurrentCase() {
        Object.keys(partGroups).forEach(key => {
            applySavedPosition(key);
        });
        if(mCooler) refreshCoolerTubes();
    }

    // Diagnostic helpers: detect and visualize large mismatches between computed
    // baseline positions and stored saved positions. Exposed on `window.nexus3d_full`
    function diagnoseSavedPositionMismatches(threshold = 0.03) {
        if(!chassis) return [];
        const markers = [];
        Object.keys(partGroups).forEach(key => {
            const group = partGroups[key] || getGroupByKey(key);
            if(!group) return;
            const baseline = group.position ? group.position.clone() : new THREE.Vector3();
            const saved = getSavedPosition(key);
            if(!isValidSavedPosition(saved)) return;
            const savedVec = new THREE.Vector3(saved.x, saved.y, saved.z);
            const dist = baseline.distanceTo(savedVec);
            if(dist > threshold) {
                console.warn(`Saved mismatch ${key}: ${dist.toFixed(3)}`, { baseline, saved: savedVec });
                // red = baseline, green = saved
                const red = new THREE.Mesh(new THREE.SphereGeometry(0.02,8,8), new THREE.MeshBasicMaterial({ color: 0xff4444 }));
                red.position.copy(baseline); red.renderOrder = 9999; chassis.add(red);
                const green = new THREE.Mesh(new THREE.SphereGeometry(0.02,8,8), new THREE.MeshBasicMaterial({ color: 0x44ff44 }));
                green.position.copy(savedVec); green.renderOrder = 9999; chassis.add(green);
                markers.push({ key, dist, baseline, saved: savedVec, red, green });
            }
        });
        return markers;
    }

    function clearBadSavedPositions(threshold = 0.05) {
        const caseId = getCurrentCaseId();
        const map = savedPositions[caseId] || {};
        let removed = 0;
        Object.keys(map).forEach(key => {
            const saved = map[key];
            if(!isValidSavedPosition(saved)) return;
            const group = partGroups[key] || getGroupByKey(key);
            if(!group) return;
            const baseline = group.position ? group.position.clone() : new THREE.Vector3();
            const savedVec = new THREE.Vector3(saved.x, saved.y, saved.z);
            const dist = baseline.distanceTo(savedVec);
            if(dist > threshold) {
                delete map[key];
                removed++;
            }
        });
        if(removed > 0) {
            savedPositions[caseId] = map;
            saveSavedPositions();
            console.log(`Removed ${removed} saved positions for case ${caseId}`);
            rebuildAll();
        } else {
            console.log('No saved positions exceeded threshold');
        }
    }

    function getSlotPartKeys(slotCat) {
        const key = String(slotCat || '').toLowerCase();
        if(key === 'case') {
            return ['case'].concat(Object.keys(partGroups).filter(k => k.startsWith('case-fan-')));
        }
        if(key === 'cooling') {
            if(build.cooler && build.cooler.type === 'liquid') return ['cooler-rad','cooler-block'];
            return ['cooler-block'];
        }
        if(key === 'motherboard' || key === 'cpu' || key === 'storage') return ['motherboard'];
        if(key === 'gpu') return ['gpu'];
        if(key === 'ram') return ['ram'];
        if(key === 'psu') return ['psu'];
        return [];
    }

    function selectSlotParts(slotCat, multi = false) {
        const keys = getSlotPartKeys(slotCat).filter(k => getGroupByKey(k));
        if(!keys.length) return;
        if(!multi) {
            sceneSelectedParts.length = 0;
        }
        keys.forEach(k => {
            if(sceneSelectedParts.indexOf(k) === -1) sceneSelectedParts.push(k);
        });
        updateSelectedUI();
    }

    // Expose diagnostics to the page console
    window.nexus3d_full = window.nexus3d_full || {};
    window.nexus3d_full.diagnoseSavedPositionMismatches = diagnoseSavedPositionMismatches;
    window.nexus3d_full.clearBadSavedPositions = clearBadSavedPositions;
    window.nexus3d_full.undoLastAction = undoLastAction;
    window.nexus3d_full.selectSlot = selectSlotParts;
    window.nexus3d_full.setAdminMode = function(enabled) {
        adminModeEnabled = Boolean(enabled);
        updateTransformGizmo();
    };

    window.nexus3d_full.setCompatibilityAlert = function(active) {
        if(active) {
            showIncompatibilityIndicator();
        } else {
            hideIncompatibilityIndicator();
        }
    };
    
    function parseHexInput(v) {
        if(!v) return 0xffc4c4;
        if(typeof v === 'number') return v;
        if(typeof v === 'string') {
            let s = v.trim();
            if(s.startsWith('#')) s = s.slice(1);
            if(s.startsWith('0x')) s = s.slice(2);
            const n = parseInt(s, 16);
            return isNaN(n) ? 0xffc4c4 : n;
        }
        return 0xffc4c4;
    }

    function setCompatibilityColor(val) {
        const hex = parseHexInput(val);
        incompatibilityColor = hex;
        // update any existing indicator materials
        if(incompatibilityIndicator) {
            incompatibilityIndicator.traverse(obj => {
                if(obj.isMesh && obj.material) {
                    try {
                        if(obj.material.color) obj.material.color.setHex(hex);
                        if(obj.material.emissive) obj.material.emissive.setHex(hex);
                        if(typeof obj.material.emissiveIntensity !== 'undefined') obj.material.emissiveIntensity = 1.6;
                        if(typeof obj.material.roughness !== 'undefined') obj.material.roughness = 0.06;
                    } catch(e) {
                        // ignore
                    }
                } else if(obj.isLine && obj.material) {
                    try { if(obj.material.color) obj.material.color.setHex(0x111827); } catch(e){}
                }
            });
        }
    }
    window.nexus3d_full.setCompatibilityColor = setCompatibilityColor;
    window.nexus3d_full.isAdminModeEnabled = function() {
        return adminModeEnabled;
    };
    window.nexus3d_full.selectSubpart = function(event, key) {
        const multi = event && (event.ctrlKey || event.metaKey);
        selectComponentGroup(key, multi);
    };

    function getCanvasSubpartButtons() {
        const buttons = [];
        if(build.case) {
            buttons.push({ key:'case', label:'Case' });
            const fanKeys = Object.keys(partGroups).filter(k => k.startsWith('case-fan-'));
            const rank = subkey => {
                if(subkey.includes('front')) return Number(subkey.match(/front-(\d+)/)?.[1] || 0);
                if(subkey.includes('rear')) return 100;
                if(subkey.includes('top')) return 200;
                return 300;
            };
            fanKeys.sort((a,b) => rank(a) - rank(b)).forEach(key => {
                let label = key.replace('case-fan-','').replace(/-/g,' ');
                label = label.split(' ').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');
                buttons.push({ key, label });
            });
        }
        if(build.cooler) {
            if(build.cooler.type === 'liquid') {
                buttons.push({ key:'cooler-rad', label:'Radiator' });
            }
            buttons.push({ key:'cooler-block', label:'Block' });
        }
        return buttons.filter(btn => getGroupByKey(btn.key));
    }

    function renderSubpartSelector() {
        const container = document.getElementById('subpart-selector');
        const buttonRow = document.getElementById('subpart-selector-buttons');
        if(!container || !buttonRow) return;
        if(!adminModeEnabled) {
            buttonRow.innerHTML = '';
            container.style.display = 'none';
            return;
        }
        const buttons = getCanvasSubpartButtons();
        if(!buttons.length) {
            container.style.display = 'none';
            return;
        }
        buttonRow.innerHTML = buttons.map(btn => {
            const active = sceneSelectedParts.includes(btn.key);
            const style = active
                ? 'background:rgba(59,130,246,.98);color:#fff;'
                : 'background:rgba(255,255,255,.18);color:#0f172a;border:1px solid rgba(148,163,184,0.3);';
            return `<button type="button" onclick="window.nexus3d_full.selectSubpart(event,'${btn.key}')" style="border:none;padding:8px 12px;border-radius:999px;cursor:pointer;${style}">${btn.label}</button>`;
        }).join('');
        container.style.display = 'flex';
    }

    function updateSelectedUI() {
        const count = sceneSelectedParts.length;
        const label = document.getElementById('selected-count');
        if(label) {
            label.textContent = count > 0 ? `${count} selected` : 'No parts selected';
        }
        buildAccordion();
        updateSelectionHighlights();
        renderSubpartSelector();
        if(count === 0) {
            ['position-input-x','position-input-y','position-input-z'].forEach(id => {
                const el = document.getElementById(id);
                if(el) { el.value = ''; el.disabled = true; }
            });
            lastSelectedAverage.set(0,0,0);
            updateTransformGizmo();
            return;
        }

        let sum = new THREE.Vector3();
        sceneSelectedParts.forEach(key => {
            const group = getGroupByKey(key);
            if(group) sum.add(group.position);
        });
        const avg = sum.multiplyScalar(1 / count);
        lastSelectedAverage.copy(avg);

        ['x','y','z'].forEach(axis => {
            const el = document.getElementById('position-input-' + axis);
            if(el) {
                el.value = avg[axis].toFixed(3);
                el.disabled = false;
            }
        });
        updateTransformGizmo();
    }

    let selectionOverlays = [];
    function clearSelectionHighlights() {
        selectionOverlays.forEach(obj => { if(chassis && obj) chassis.remove(obj); });
        selectionOverlays.length = 0;
    }

    function updateSelectionHighlights() {
        clearSelectionHighlights();
        sceneSelectedParts.forEach(key => {
            const group = getGroupByKey(key);
            if(group) addSelectionBox(group, 0x22d3ee);
        });
    }

    function getIndicatorAnchorPosition() {
        const target = mCase || chassis;
        if(!target) return new THREE.Vector3(0, 0.8, 0);
        const box = new THREE.Box3().setFromObject(target);
        const pos = new THREE.Vector3();
        box.getCenter(pos);
        pos.y = box.max.y + Math.max(0.18, box.getSize(new THREE.Vector3()).y * 0.1);
        return pos;
    }

    function getRoundedTriangleShape(size, radius) {
        const shape = new THREE.Shape();
        const angle1 = Math.PI / 2;
        const angle2 = Math.PI / 2 + (2 * Math.PI / 3);
        const angle3 = Math.PI / 2 + (4 * Math.PI / 3);
        const p1 = new THREE.Vector2(size * Math.cos(angle1), size * Math.sin(angle1));
        const p2 = new THREE.Vector2(size * Math.cos(angle2), size * Math.sin(angle2));
        const p3 = new THREE.Vector2(size * Math.cos(angle3), size * Math.sin(angle3));
        const d = radius * Math.sqrt(3);
        const dir12 = new THREE.Vector2().subVectors(p2, p1).normalize();
        const dir23 = new THREE.Vector2().subVectors(p3, p2).normalize();
        const dir31 = new THREE.Vector2().subVectors(p1, p3).normalize();
        const startX = p1.x - d * dir31.x;
        const startY = p1.y - d * dir31.y;
        shape.moveTo(startX, startY);
        const p1_tan2 = new THREE.Vector2(p1.x + d * dir12.x, p1.y + d * dir12.y);
        shape.quadraticCurveTo(p1.x, p1.y, p1_tan2.x, p1_tan2.y);
        const p2_tan1 = new THREE.Vector2(p2.x - d * dir12.x, p2.y - d * dir12.y);
        shape.lineTo(p2_tan1.x, p2_tan1.y);
        const p2_tan2 = new THREE.Vector2(p2.x + d * dir23.x, p2.y + d * dir23.y);
        shape.quadraticCurveTo(p2.x, p2.y, p2_tan2.x, p2_tan2.y);
        const p3_tan1 = new THREE.Vector2(p3.x - d * dir23.x, p3.y - d * dir23.y);
        shape.lineTo(p3_tan1.x, p3_tan1.y);
        const p3_tan2 = new THREE.Vector2(p3.x + d * dir31.x, p3.y + d * dir31.y);
        shape.quadraticCurveTo(p3.x, p3.y, p3_tan2.x, p3_tan2.y);
        shape.closePath();
        return shape;
    }

    function getCapsuleShape(width, height, radius) {
        const shape = new THREE.Shape();
        const w = width;
        const h = height;
        const r = radius;
        shape.moveTo(-w / 2 + r, -h / 2);
        shape.lineTo(w / 2 - r, -h / 2);
        shape.quadraticCurveTo(w / 2, -h / 2, w / 2, -h / 2 + r);
        shape.lineTo(w / 2, h / 2 - r);
        shape.quadraticCurveTo(w / 2, h / 2, w / 2 - r, h / 2);
        shape.lineTo(-w / 2 + r, h / 2);
        shape.quadraticCurveTo(-w / 2, h / 2, -w / 2, h / 2 - r);
        shape.lineTo(-w / 2, -h / 2 + r);
        shape.quadraticCurveTo(-w / 2, -h / 2, -w / 2 + r, -h / 2);
        return shape;
    }

    function buildIncompatibilityIndicator() {
        if(!scene) return null;
        const group = new THREE.Group();
        const borderMat = new THREE.MeshStandardMaterial({
            color: incompatibilityColor,
            emissive: incompatibilityColor,
            emissiveIntensity: 1.6,
            roughness: 0.08,
            metalness: 0.18,
            side: THREE.DoubleSide
        });
        const plateMat = new THREE.MeshStandardMaterial({
            color: 0xf2f4f8,
            emissive: 0xfafafa,
            emissiveIntensity: 0.35,
            roughness: 0.18,
            metalness: 0.08,
            side: THREE.DoubleSide
        });
        const markMat = new THREE.MeshStandardMaterial({
            color: incompatibilityColor,
            emissive: incompatibilityColor,
            emissiveIntensity: 1.6,
            roughness: 0.06,
            metalness: 0.05,
            side: THREE.DoubleSide
        });

        const outerShape = getRoundedTriangleShape(0.32, 0.04);
        const innerHole = getRoundedTriangleShape(0.22, 0.022);
        outerShape.holes.push(innerHole);
        const borderGeo = new THREE.ExtrudeGeometry(outerShape, {
            depth: 0.05,
            bevelEnabled: true,
            bevelThickness: 0.01,
            bevelSize: 0.01,
            bevelSegments: 3,
            curveSegments: 24
        });
        borderGeo.center();
        const borderMesh = new THREE.Mesh(borderGeo, borderMat);
        borderMesh.castShadow = true;
        borderMesh.receiveShadow = true;
        group.add(borderMesh);

        // interior left hollow (no plate) so the triangle is a framed warning sign

        const barShape = getCapsuleShape(0.045, 0.18, 0.022);
        const markGeo = new THREE.ExtrudeGeometry(barShape, {
            depth: 0.03,
            bevelEnabled: true,
            bevelThickness: 0.005,
            bevelSize: 0.005,
            bevelSegments: 2,
            curveSegments: 16
        });
        markGeo.center();
        const barMesh = new THREE.Mesh(markGeo, markMat);
        barMesh.position.y = 0.06;
        barMesh.position.z = 0.039;
        barMesh.castShadow = true;
        barMesh.receiveShadow = true;
        group.add(barMesh);

        const dotShape = new THREE.Shape();
        dotShape.absarc(0, 0, 0.03, 0, Math.PI * 2, false);
        const dotGeo = new THREE.ExtrudeGeometry(dotShape, {
            depth: 0.03,
            bevelEnabled: true,
            bevelThickness: 0.005,
            bevelSize: 0.005,
            bevelSegments: 2,
            curveSegments: 16
        });
        dotGeo.center();
        const dotMesh = new THREE.Mesh(dotGeo, markMat);
        dotMesh.position.y = -0.12;
        dotMesh.position.z = 0.039;
        dotMesh.castShadow = true;
        dotMesh.receiveShadow = true;
        group.add(dotMesh);

        const edgeLines = new THREE.LineSegments(
            new THREE.EdgesGeometry(borderGeo),
            new THREE.LineBasicMaterial({ color: incompatibilityColor, opacity: 0.95, transparent: true })
        );
        group.add(edgeLines);

        group.scale.setScalar(0.01);
        group.userData.basePosition = getIndicatorAnchorPosition();
        group.position.copy(group.userData.basePosition);
        group.position.y += 0.28;
        group.userData.visible = false;
        scene.add(group);
        return group;
    }

    function showIncompatibilityIndicator() {
        incompatibilityAlertVisible = true;
        // rebuild indicator to pick up any runtime color/geometry changes
        if(incompatibilityIndicator) {
            try { scene.remove(incompatibilityIndicator); } catch(e){}
            incompatibilityIndicator = null;
        }
        incompatibilityIndicator = buildIncompatibilityIndicator();
        if(!incompatibilityIndicator) return;
        // set base position and apply the visual height offset so the animation loop uses it
        incompatibilityIndicator.userData.basePosition = getIndicatorAnchorPosition();
        incompatibilityIndicator.userData.basePosition.y += 0.28;
        incompatibilityIndicator.position.copy(incompatibilityIndicator.userData.basePosition);
        incompatibilityIndicator.visible = true;
        gsap.killTweensOf(incompatibilityIndicator.scale);
        incompatibilityIndicator.scale.setScalar(0.01);
        gsap.to(incompatibilityIndicator.scale, { x: 1.12, y: 1.12, z: 1.12, duration: 0.8, ease: 'back.out(2)' });
    }

    function hideIncompatibilityIndicator() {
        if(!incompatibilityIndicator || !incompatibilityIndicator.visible) return;
        incompatibilityAlertVisible = false;
        gsap.killTweensOf(incompatibilityIndicator.scale);
        gsap.to(incompatibilityIndicator.scale, {
            x: 0.01,
            y: 0.01,
            z: 0.01,
            duration: 0.45,
            ease: 'power2.in',
            onComplete() {
                if(incompatibilityIndicator) {
                    incompatibilityIndicator.visible = false;
                }
            }
        });
    }

    function addSelectionBox(target, color = 0xff3b3b) {
        if(!target || !chassis) return;
        const box = new THREE.Box3().setFromObject(target);
        const size = new THREE.Vector3();
        const center = new THREE.Vector3();
        box.getSize(size);
        box.getCenter(center);
        const geometry = new THREE.EdgesGeometry(new THREE.BoxGeometry(size.x*1.06, size.y*1.06, size.z*1.06));
        const material = new THREE.LineBasicMaterial({color});
        const outline = new THREE.LineSegments(geometry, material);
        outline.position.copy(center);
        outline.renderOrder = 999;
        chassis.add(outline);
        selectionOverlays.push(outline);
    }

    function selectComponentGroup(key, multi = false) {
        if(!key) return;
        const idx = sceneSelectedParts.indexOf(key);
        if(multi) {
            if(idx === -1) sceneSelectedParts.push(key);
            else sceneSelectedParts.splice(idx, 1);
        } else {
            sceneSelectedParts.length = 0;
            sceneSelectedParts.push(key);
        }
        updateSelectedUI();
    }

    function toggleSelection(key) {
        selectComponentGroup(key, true);
    }

    function onPositionInputChange() {
        if(sceneSelectedParts.length === 0) return;
        const x = parseFloat(document.getElementById('position-input-x').value);
        const y = parseFloat(document.getElementById('position-input-y').value);
        const z = parseFloat(document.getElementById('position-input-z').value);
        if(Number.isNaN(x) || Number.isNaN(y) || Number.isNaN(z)) return;

        const target = new THREE.Vector3(x, y, z);
        const delta = target.clone().sub(lastSelectedAverage);
        if(delta.lengthSq() === 0) return;
        moveSelected(delta.x, delta.y, delta.z);
    }

    function moveSelected(dx, dy, dz) {
        if(!adminModeEnabled || sceneSelectedParts.length === 0) return;
        const before = sceneSelectedParts.map(key => {
            const group = getGroupByKey(key);
            return group ? { key, pos: group.position.clone() } : null;
        }).filter(Boolean);
        sceneSelectedParts.forEach(key => {
            const group = getGroupByKey(key);
            if(!group) return;
            group.position.add(new THREE.Vector3(dx, dy, dz));
            positionOverrides[key] = group.position.clone();
            setSavedPosition(key, group.position);
        });
        if(before.length) pushUndoStep(before);
        if(mCooler) refreshCoolerTubes();
        updateSelectedUI();
        updateTransformGizmo();
    }

    function exportPositions() {
        if(!adminModeEnabled) {
            alert('Admin mode is required to export component positions.');
            return;
        }
        const payload = {
            savedPositions,
            exportedCase: build.case.id,
            exportedAt: new Date().toISOString()
        };
        downloadFile('nexus3d_positions.json', JSON.stringify(payload, null, 2));
    }

    function triggerImport() {
        if(!adminModeEnabled) {
            alert('Admin mode is required to import component positions.');
            return;
        }
        const input = document.getElementById('positions-import-file');
        if(input) input.click();
    }

    function importPositions(event) {
        if(!adminModeEnabled) {
            alert('Admin mode is required to import component positions.');
            return;
        }
        const file = event.target.files && event.target.files[0];
        if(!file) return;
        const reader = new FileReader();
        reader.onload = () => {
            try {
                const data = JSON.parse(reader.result);
                mergeImportedPositions(data);
                rebuildAll();
                updateSelectedUI();
            } catch (err) {
                console.warn('Invalid import file', err);
            }
        };
        reader.readAsText(file);
        event.target.value = '';
    }

    function downloadFile(filename, text) {
        const link = document.createElement('a');
        const mime = filename.endsWith('.json') ? 'application/json' : 'text/plain';
        link.href = `data:${mime};charset=utf-8,` + encodeURIComponent(text);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    function findPartKey(obj) {
        let current = obj;
        while(current && !current.userData.partKey) {
            current = current.parent;
        }
        return current ? current.userData.partKey : null;
    }

    function onCanvasPointerDown(event) {
        if(event.button !== 0) return;
        const rect = renderer.domElement.getBoundingClientRect();
        pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(pointer, cam);

        if(gizmoRoot && gizmoRoot.visible) {
            const gizmoIntersects = raycaster.intersectObjects(gizmoRoot.children, true);
            if(gizmoIntersects.length > 0) {
                const axis = findGizmoAxis(gizmoIntersects[0].object);
                if(axis) {
                    startGizmoDrag(axis);
                    event.preventDefault();
                    return;
                }
            }
        }

        const intersects = raycaster.intersectObjects(chassis.children, true);
        if(intersects.length > 0) {
            const partKey = findPartKey(intersects[0].object);
            if(partKey) {
                const multiSelect = event.ctrlKey || event.metaKey;
                selectComponentGroup(partKey, multiSelect);
            }
        }
    }

    function onCanvasPointerMove(event) {
        if(gizmoDrag) {
            updateGizmoDrag(event);
            renderer.domElement.style.cursor = 'grabbing';
            event.preventDefault();
            return;
        }

        if(!renderer || !cam) return;
        const rect = renderer.domElement.getBoundingClientRect();
        pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(pointer, cam);
        let hoverGizmo = false;
        if(gizmoRoot && gizmoRoot.visible) {
            const gizmoIntersects = raycaster.intersectObjects(gizmoRoot.children, true);
            if(gizmoIntersects.length > 0) hoverGizmo = true;
        }
        renderer.domElement.style.cursor = hoverGizmo ? 'grab' : 'grab';
    }

    function onCanvasPointerUp() {
        endGizmoDrag();
    }

    function onKeyDown(event) {
        if(event.ctrlKey && event.key.toLowerCase() === 'z') {
            undoLastAction();
            event.preventDefault();
        }
    }

    function clearModelHighlights() {
        highlightOverlays.forEach(obj=>{ if(chassis && obj){ chassis.remove(obj); }});
        highlightOverlays.length = 0;
    }

    function addHighlightBox(target) {
        if(!target || !chassis) return;
        const box = new THREE.Box3().setFromObject(target);
        const size = new THREE.Vector3();
        const center = new THREE.Vector3();
        box.getSize(size);
        box.getCenter(center);
        const geometry = new THREE.EdgesGeometry(new THREE.BoxGeometry(size.x*1.06, size.y*1.06, size.z*1.06));
        const material = new THREE.LineBasicMaterial({color:0xff3b3b});
        const outline = new THREE.LineSegments(geometry, material);
        outline.position.copy(center);
        outline.renderOrder = 999;
        chassis.add(outline);
        highlightOverlays.push(outline);
    }

    function updateModelHighlights(caseOk, gpuOk, coolerOk) {
        clearModelHighlights();
        if(!caseOk && mMobo) addHighlightBox(mMobo);
        if(!gpuOk && mGpu) addHighlightBox(mGpu);
        if(!coolerOk && mCooler) addHighlightBox(mCooler);
    }

    function toggleRgb() { rgbOn = document.getElementById('rgb-toggle').checked; }
    function setRgbHue(h) { if(h==='rainbow'){rainbowMode=true;}else{rainbowMode=false;rgbHue=h;} }
    function setFanSpeed(v) { fanSpeed = parseFloat(v); }
    function setGlass(mode) {
        glassMode = mode;
        document.getElementById('glass-on-btn').className = mode==='on'
            ? 'py-2 rounded-lg border border-cyan-500 bg-cyan-600/10 text-white text-[10px] font-bold transition'
            : 'py-2 rounded-lg border border-white/10 bg-white/5 text-slate-400 text-[10px] font-bold transition';
        document.getElementById('glass-off-btn').className = mode==='off'
            ? 'py-2 rounded-lg border border-pink-500 bg-pink-600/10 text-white text-[10px] font-bold transition'
            : 'py-2 rounded-lg border border-white/10 bg-white/5 text-slate-400 text-[10px] font-bold transition';
        if(mGlass) {
            mGlass.material.opacity = glassMode==='on' ? 0.12 : 0;
            mGlass.material.transmission = glassMode==='on' ? 0.9 : 0;
        }
    }

    function resetConfiguration() {
        setDefaultBuild();
        sceneSelectedParts.length = 0;
        undoStack.length = 0;
        Object.keys(positionOverrides).forEach(k => delete positionOverrides[k]);
        clearSavedPositionsForCurrentCase();
        updateSelectedUI();
        buildAccordion();
        rebuildAll();
    }


    // =====================================================
    // 3D ENGINE
    // =====================================================
    function makeStackedFins(w,h,d,n,color) {
        const g = new THREE.Group();
        const mat = new THREE.MeshStandardMaterial({color,metalness:0.85,roughness:0.2});
        const sp = h/n;
        for(let i=0;i<n;i++){
            const fin = new THREE.Mesh(new THREE.BoxGeometry(w,0.008,d),mat);
            fin.position.y = -h/2 + i*sp;
            fin.castShadow=true;
            g.add(fin);
        }
        return g;
    }

    function makeFan(r, hasRgb, thick=false, visibleThroughGrey=false, visibleFromBottom=false, visibilityMode=null) {
        if(visibilityMode === null) visibilityMode = visibleFromBottom ? 'bottom' : (visibleThroughGrey ? 'always' : 'none');
        const g = new THREE.Group();
        const ringDepth = thick ? r*0.12 : r*0.065;
        const plateDepth = thick ? r*0.22 : r*0.1;
        const hubHeight = thick ? r*0.32 : r*0.18;
        // Outer frame ring (can be RGB if fan hasRgb)
        const ringMat = hasRgb ? new THREE.MeshBasicMaterial({color:0x0b0e17}) : new THREE.MeshStandardMaterial({color:0x0b0e17,roughness:0.7});
        const ring = new THREE.Mesh(new THREE.TorusGeometry(r, ringDepth, 10, 28), ringMat);
        if(hasRgb) rgbMats.push(ringMat);
        g.add(ring);
        // Square mount plate
        const plate = new THREE.Mesh(new THREE.BoxGeometry(r*2.1, r*2.1, plateDepth),
            new THREE.MeshStandardMaterial({color:0x080b12,roughness:0.8}));
        plate.position.z = -plateDepth/2;
        g.add(plate);
        // RGB back circle and spinner behind the blades
        if(hasRgb){
            const backRingMat = new THREE.MeshBasicMaterial({
                color:0xffffff,
                transparent:true,
                opacity:0.35,
                depthTest: visibilityMode === 'always' ? false : true,
                depthWrite:false
            });
            backRingMat.userData = { visibilityMode, owner: g };
            if(visibilityMode !== 'none') fanVisibilityMats.push(backRingMat);
            const backRing = new THREE.Mesh(new THREE.TorusGeometry(r*0.95, r*0.02, 8, 40), backRingMat);
            backRing.position.z = -plateDepth - 0.02;
            if(visibilityMode !== 'none') backRing.renderOrder = 2;
            g.add(backRing);
            rgbMats.push(backRingMat);
            const spinner = new THREE.Group();
            if(visibilityMode !== 'none') spinner.renderOrder = 3;
            const spinnerMat = new THREE.MeshStandardMaterial({
                color:0x1a2030,
                roughness:0.4,
                depthTest: visibilityMode === 'always' ? false : true,
                depthWrite:false
            });
            spinnerMat.userData = { visibilityMode, owner: g };
            if(visibilityMode !== 'none') fanVisibilityMats.push(spinnerMat);
            const spinRing = new THREE.Mesh(new THREE.TorusGeometry(r*0.75, r*0.01, 8, 40), spinnerMat);
            spinner.add(spinRing);
            const cross1 = new THREE.Mesh(new THREE.BoxGeometry(r*1.4, 0.01, 0.01), spinnerMat);
            const cross2 = new THREE.Mesh(new THREE.BoxGeometry(0.01, r*1.4, 0.01), spinnerMat);
            spinner.add(cross1, cross2);
            spinner.position.z = -plateDepth - 0.03;
            g.add(spinner);
            fans3d.push(spinner);
        }
        // Hub
        const hubMat = hasRgb ? new THREE.MeshBasicMaterial({color:0xffffff}) :
            new THREE.MeshStandardMaterial({color:0x1a2030,roughness:0.4});
        const hub = new THREE.Mesh(new THREE.CylinderGeometry(r*0.3, r*0.3, hubHeight, 14), hubMat);
        hub.rotation.x = Math.PI/2; g.add(hub);
        if(hasRgb) rgbMats.push(hubMat);
        // Blades
        const bladeHolder = new THREE.Group();
        const bGeo = new THREE.BoxGeometry(r*0.1, r*0.62, 0.016);
        bGeo.translate(0, r*0.31, 0);
        // Blades remain dark/glossy even on RGB fans to keep visuals clean
        const bMat = new THREE.MeshStandardMaterial({color:0x07090f,roughness:0.35,metalness:0.15});
        for(let i=0;i<9;i++){
            const b=new THREE.Mesh(bGeo,bMat);
            b.rotation.z=(i/9)*Math.PI*2; b.rotation.y=0.28;
            bladeHolder.add(b);
        }
        g.add(bladeHolder);
        fans3d.push(bladeHolder);
        return g;
    }

    function makeCurve(p1,cp,p2,r,col) {
        const curve = new THREE.QuadraticBezierCurve3(p1,cp,p2);
        const geo = new THREE.TubeGeometry(curve,14,r,7,false);
        const mat = new THREE.MeshStandardMaterial({color:col,roughness:0.85});
        return new THREE.Mesh(geo,mat);
    }

    function createCoolerTube(p1, p2, radius = 0.02, color = 0x111622) {
        const mid = p1.clone().lerp(p2, 0.5);
        mid.y += Math.max(0.12, Math.abs(p2.y - p1.y) * 0.55, p1.distanceTo(p2) * 0.22);
        const control = mid.add(new THREE.Vector3(0, 0.06, 0));
        return makeCurve(p1, control, p2, radius, color);
    }

    function cleanCoolerHoses() {
        const root = chassis || scene || mCooler;
        if(!root) return;
        const toRemove = [];
        root.traverse(obj => {
            if(obj.isMesh && obj.geometry && obj.geometry.type === 'TubeGeometry') {
                toRemove.push(obj);
            }
        });
        toRemove.forEach(obj => obj.parent && obj.parent.remove(obj));
    }

    function getWorldPortPoint(group) {
        if(!group) return null;
        if(group.updateMatrixWorld) group.updateMatrixWorld(true);
        const offset = group.userData.portOffset ? group.userData.portOffset.clone() : new THREE.Vector3();
        return group.localToWorld(offset);
    }

    function getGpuBackSurfacePoint(blockPoint) {
        if(!mGpu || !blockPoint) return null;
        if(mGpu.updateMatrixWorld) mGpu.updateMatrixWorld(true);
        if(mGpu.userData.portOffset) {
            return getWorldPortPoint(mGpu);
        }
        const box = new THREE.Box3().setFromObject(mGpu);
        if(!box.isEmpty()) {
            const x = THREE.MathUtils.clamp(blockPoint.x, box.min.x, box.max.x);
            const y = THREE.MathUtils.clamp(blockPoint.y, box.min.y, box.max.y);
            return new THREE.Vector3(x, y, box.min.z);
        }
        return null;
    }

    function refreshCoolerTubes() {
        if(scene && scene.updateMatrixWorld) scene.updateMatrixWorld(true);
        if(coolerTubeGroup && coolerTubeGroup.parent) {
            while(coolerTubeGroup.children.length) coolerTubeGroup.remove(coolerTubeGroup.children[0]);
        }
        if(!coolerTubeGroup) {
            coolerTubeGroup = new THREE.Group();
            chassis.add(coolerTubeGroup);
        }
        if(!coolerBlockGroup || !coolerRadGroup || !mCooler) {
            return;
        }

        const blockPoint = getWorldPortPoint(coolerBlockGroup);
        const radPoint = getWorldPortPoint(coolerRadGroup);
        if(blockPoint && radPoint) {
            coolerTubeGroup.add(createCoolerTube(blockPoint, radPoint, 0.02, 0x111622));
        }
        if(blockPoint && mGpu) {
            const gpuPoint = getGpuBackSurfacePoint(blockPoint);
            if(gpuPoint) {
                coolerTubeGroup.add(createCoolerTube(blockPoint, gpuPoint, 0.018, 0x44536a));
            }
        }
    }

    function initEngine() {
        loadSavedPositions();
        const el = document.getElementById('nexus-canvas-frame');
        const W = el ? el.clientWidth : window.innerWidth;
        const H = el ? (el.clientHeight||500) : window.innerHeight;

        scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x03050b,0.045);

        cam = new THREE.PerspectiveCamera(40, W/H, 0.1, 80);
        cam.position.set(3.5, 2.5, 4.5);

        renderer = new THREE.WebGLRenderer({antialias:true,alpha:false});
        renderer.setSize(W,H);
        renderer.setPixelRatio(Math.min(devicePixelRatio,2));
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.4;
        el.appendChild(renderer.domElement);

        controls = new THREE.OrbitControls(cam, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.06;
        controls.minDistance = 2;
        controls.maxDistance = 11;

        raycaster = new THREE.Raycaster();
        pointer = new THREE.Vector2();
        renderer.domElement.addEventListener('pointerdown', onCanvasPointerDown, false);
        renderer.domElement.addEventListener('pointermove', onCanvasPointerMove, false);
        window.addEventListener('pointerup', onCanvasPointerUp, false);
        window.addEventListener('keydown', onKeyDown, false);

        // Lighting
        envLights.ambient = new THREE.AmbientLight(0x0a0d18, 1.4);
        scene.add(envLights.ambient);

        envLights.sun = new THREE.DirectionalLight(0xffffff, 2.2);
        envLights.sun.position.set(5,9,5);
        envLights.sun.castShadow = true;
        envLights.sun.shadow.mapSize.set(1024,1024);
        envLights.sun.shadow.bias = -0.0005;
        scene.add(envLights.sun);

        envLights.fill = new THREE.DirectionalLight(0x1e40af, 1.8);
        envLights.fill.position.set(-5,2,-5);
        scene.add(envLights.fill);

        envLights.rim = new THREE.DirectionalLight(0x0e7490, 0.8);
        envLights.rim.position.set(0,5,-6);
        scene.add(envLights.rim);

        // Floor
        envFloor = new THREE.Mesh(new THREE.PlaneGeometry(28,28),
            new THREE.MeshStandardMaterial({color:0x03050a,roughness:0.7,metalness:0.9}));
        envFloor.rotation.x = -Math.PI/2;
        envFloor.position.y = -1.22;
        envFloor.receiveShadow = true;
        scene.add(envFloor);

        envGrid = new THREE.GridHelper(22,22,0x0f1f35,0x060c15);
        envGrid.position.y = -1.21;
        scene.add(envGrid);

        setEnvironmentMode(environmentMode);

        chassis = new THREE.Group();
        scene.add(chassis);
        createTransformGizmo();

        rebuildAll();

        window.addEventListener('resize',()=>{
            const W2=el.clientWidth, H2=el.clientHeight;
            cam.aspect=W2/H2; cam.updateProjectionMatrix();
            renderer.setSize(W2,H2);
        });

        setTimeout(()=>{
            const ld = document.getElementById('nexus-loader');
            if(ld){ ld.style.opacity='0'; ld.style.pointerEvents='none'; }
        }, 900);

        loop();
    }

    function rebuildAll() {
        while(chassis.children.length>0) chassis.remove(chassis.children[0]);
        Object.keys(partGroups).forEach(k => delete partGroups[k]);
        rgbMats=[]; fans3d=[]; wireMeshes=[];
        if(airflowGroup && airflowGroup.parent) {
            airflowGroup.parent.remove(airflowGroup);
        }
        airflowGroup = null;
        buildCase(); buildMobo(); buildPsu(); buildGpu(); buildCooler(); buildRam();
        refreshCoolerTubes();
        if(airflowVisible) createAirflowVisualization();
    }

    function rebuildMesh(cat) {
        // Prune fans related to replaced mesh
        if(cat==='case') {
            rebuildAll();
        }
        else if(cat==='motherboard') {
            buildMobo();
            buildGpu();
            buildCooler();
            buildRam();
        }
        else if(cat==='gpu') buildGpu();
        else if(cat==='cooler') buildCooler();
        else if(cat==='ram') buildRam();
        else if(cat==='psu') buildPsu();
        else if(cat==='cpu' || cat==='storage') buildMobo();

        if(['gpu','cooler','motherboard','case'].includes(cat) && coolerBlockGroup && coolerRadGroup) {
            refreshCoolerTubes();
        }

        gsap.from(chassis.scale,{x:0.96,y:0.96,z:0.96,duration:0.35,ease:"back.out(2)"});
    }

    // =====================================================
    // CASE BUILDER — Highly differentiated per model
    // =====================================================
    function buildCase() {
        if(mCase) chassis.remove(mCase);
        if(mGlass) chassis.remove(mGlass);
        const c = build.case;
        if(!c) {
            delete partGroups['case'];
            mCase = null;
            return;
        }
        const d = c.dims;
        mCase = new THREE.Group();
        Object.keys(partGroups).forEach(key => {
            if(key && key.startsWith('case-fan-')) delete partGroups[key];
        });
        partGroups['case'] = mCase;

        const steel = new THREE.MeshStandardMaterial({color:0x0e1420,metalness:0.85,roughness:0.35});
        const darkSteel = new THREE.MeshStandardMaterial({color:0x080c13,metalness:0.8,roughness:0.4});

        // === COMMON STRUCTURAL PANELS ===
        // Bottom plate
        const bot = new THREE.Mesh(new THREE.BoxGeometry(d.w,0.04,d.d),steel);
        bot.position.y=-d.h/2; bot.castShadow=true; bot.receiveShadow=true; mCase.add(bot);
        // Top cover
        const top = new THREE.Mesh(new THREE.BoxGeometry(d.w,0.04,d.d),steel);
        top.position.y=d.h/2; top.castShadow=true; mCase.add(top);
        // Rear spine
        const rear = new THREE.Mesh(new THREE.BoxGeometry(0.04,d.h,d.d-0.04),steel);
        rear.position.x=-d.w/2+0.02; rear.castShadow=true; mCase.add(rear);
        // Add a solid back panel so the case has a visible rear wall
        const backPanel = new THREE.Mesh(new THREE.BoxGeometry(d.w, d.h, 0.04), steel);
        backPanel.position.set(0, 0, -d.d/2 + 0.02);
        backPanel.castShadow = true;
        mCase.add(backPanel);
        // Shroud inside bottom
        const shroudW = d.w - 0.08;
        const shroudH = 0.22;
        const shroudD = d.d * 0.92;
        const shroud = new THREE.Mesh(new THREE.BoxGeometry(shroudW, shroudH, shroudD), darkSteel);
        shroud.position.set(0.04, -d.h/2 + shroudH/2 + 0.02, 0);
        shroud.castShadow = true; shroud.receiveShadow = true; mCase.add(shroud);

        // === FRONT I/O STRIP ===
        const ioMat = new THREE.MeshStandardMaterial({color:0x0a0f1a,roughness:0.6});
        const io = new THREE.Mesh(new THREE.BoxGeometry(d.w*0.6,0.06,0.03),ioMat);

        // PCIe slot covers at rear
        const slotMat = new THREE.MeshStandardMaterial({color:0x1a2030,metalness:0.7,roughness:0.3});
        const nSlots = c.factor==='ATX' ? 7 : 4;
        for(let i=0;i<nSlots;i++){
            const slot = new THREE.Mesh(new THREE.BoxGeometry(0.03,0.05,0.38),slotMat);
            slot.position.set(-d.w/2+0.025, -d.h/2+0.28+(i*0.065), -d.d/2+0.22);
            mCase.add(slot);
        }

        // ==========================================
        // CASE-SPECIFIC FRONT PANEL DESIGNS
        // ==========================================
        if(c.id === 'case-nexm2') {
            // TECWARE NEXUS AIR M2 — Compact mATX
            // Flat full-mesh front with TWO large side channel vents
            const meshMat = new THREE.MeshStandardMaterial({color:0x0c1020,wireframe:true,opacity:0.8,transparent:true});
            const frontMesh = new THREE.Mesh(new THREE.BoxGeometry(d.w-0.08,d.h-0.08,0.015),meshMat);
            frontMesh.position.z=d.d/2-0.01; mCase.add(frontMesh);

            // Two distinct side channel air intake strips (hallmark design feature)
            const ventMat = new THREE.MeshStandardMaterial({color:0x0f1828,metalness:0.4,roughness:0.7});
            [-d.w/2+0.06, d.w/2-0.06].forEach(xPos=>{
                const strip = new THREE.Mesh(new THREE.BoxGeometry(0.04,d.h-0.12,0.03),ventMat);
                strip.position.set(xPos,0,d.d/2-0.02); mCase.add(strip);
                // Horizontal louvres
                for(let y=-d.h/2+0.15;y<d.h/2-0.1;y+=0.06){
                    const louv = new THREE.Mesh(new THREE.BoxGeometry(0.04,0.008,0.025),ventMat);
                    louv.position.set(xPos,y,d.d/2-0.015); mCase.add(louv);
                }
            });

            // Front power button (top-right of front panel)
            const pwrMat = new THREE.MeshStandardMaterial({color:0x3b82f6,emissive:0x1d4ed8,emissiveIntensity:0.3});
            const pwr = new THREE.Mesh(new THREE.CylinderGeometry(0.025,0.025,0.03,12),pwrMat);
            pwr.rotation.z=Math.PI/2; pwr.position.set(d.w/2-0.08,d.h/2-0.07,d.d/2+0.01); mCase.add(pwr);

            // 2× USB 3.0 ports (top panel)
            [-.04,.04].forEach(xOff=>{
                const usb = new THREE.Mesh(new THREE.BoxGeometry(0.04,0.025,0.02),ioMat);
                usb.position.set(xOff,d.h/2-0.02,d.d/2-0.2); usb.rotation.x=Math.PI/2; mCase.add(usb);
            });

            // 2 front intake fans
            const sideFanR = 0.2;
            const sideFanY = sideFanR * 2.15;
            [-sideFanY, sideFanY].forEach((yPos,index)=>{
                const fanGroup = new THREE.Group();
                fanGroup.userData.partKey = `case-fan-front-${index+1}`;
                const fan = makeFan(sideFanR,true,false,false,false,'plane');
                fan.rotation.y = 0;
                fanGroup.add(fan);
                fanGroup.position.set(0, yPos, d.d/2-0.08);
                partGroups[fanGroup.userData.partKey] = fanGroup;
                applySavedPosition(fanGroup.userData.partKey);
                mCase.add(fanGroup);
            });
            // 1 rear exhaust fan
            const rearFanGroup = new THREE.Group();
            rearFanGroup.userData.partKey = 'case-fan-rear-1';
            const rFan = makeFan(0.19,true,true,false,false,'plane');
            rFan.rotation.y=Math.PI;
            rearFanGroup.add(rFan);
            rearFanGroup.position.set(-d.w/2+0.06,0,-d.d/2+0.06);
            partGroups[rearFanGroup.userData.partKey] = rearFanGroup;
            applySavedPosition(rearFanGroup.userData.partKey);
            mCase.add(rearFanGroup);

            // HINGED TG panel hinge at top
            const hingeMat=new THREE.MeshStandardMaterial({color:0x9ca3af,metalness:0.95,roughness:0.1});
            [d.h/2-0.05, -d.h/2+0.05].forEach(y=>{
                const h=new THREE.Mesh(new THREE.CylinderGeometry(0.015,0.015,0.06,8),hingeMat);
                h.position.set(d.w/2,y,0); mCase.add(h);
            });

        } else if(c.id === 'case-nexair') {
            // TECWARE NEXUS AIR — ATX Mid-Tower
            // Full flat-mesh front with 3 fan positions, magnetic top filter, slide-in TG
            const meshMat = new THREE.MeshStandardMaterial({color:0x0c1020,wireframe:true,opacity:0.75,transparent:true});
            const frontMesh = new THREE.Mesh(new THREE.BoxGeometry(d.w-0.04,d.h-0.1,0.015),meshMat);
            frontMesh.position.z=d.d/2-0.01; mCase.add(frontMesh);

            // Slim top edge trim (ATX Nexus Air has a subtle raised edge)
            const trimMat=new THREE.MeshStandardMaterial({color:0x1a2535,metalness:0.6,roughness:0.4});
            const topTrim=new THREE.Mesh(new THREE.BoxGeometry(d.w,0.04,d.d*0.12),trimMat);
            topTrim.position.set(0,d.h/2+0.02,-d.d/2+d.d*0.06); mCase.add(topTrim);

            // Magnetic top dust filter mesh
            const filterMat=new THREE.MeshStandardMaterial({color:0x111827,wireframe:true});
            const filter=new THREE.Mesh(new THREE.BoxGeometry(d.w-0.1,0.01,d.d*0.55),filterMat);
            filter.position.set(0,d.h/2,d.d/2-d.d*0.28); mCase.add(filter);

            // Top panel I/O cluster (USB 3.0 × 2, USB-C × 1)
            [-.06, -.02, .06].forEach((x,i)=>{
                const port=new THREE.Mesh(new THREE.BoxGeometry(0.034,0.022,0.02),ioMat);
                port.position.set(x,d.h/2-0.025,d.d/2-0.12); port.rotation.x=Math.PI/2; mCase.add(port);
            });

            // Power button (top panel)
            const pwrMat=new THREE.MeshStandardMaterial({color:0x22d3ee,emissive:0x0891b2,emissiveIntensity:0.4});
            const pwr=new THREE.Mesh(new THREE.CylinderGeometry(0.022,0.022,0.025,12),pwrMat);
            pwr.position.set(-d.w/2+0.18,d.h/2-0.025,d.d/2-0.06); mCase.add(pwr);

            // 3 front 120mm intake fans (this is the defining visual)
            const frontFanR = 0.195;
            const frontFanSpacing = frontFanR * 2.15;
            [-frontFanSpacing, 0, frontFanSpacing].forEach((yPos,index)=>{
                const fanGroup = new THREE.Group();
                fanGroup.userData.partKey = `case-fan-front-${index+1}`;
                const fan = makeFan(frontFanR,true,false,false,false,'plane');
                fan.rotation.y = 0;
                fanGroup.add(fan);
                fanGroup.position.set(0, yPos, d.d/2-0.09);
                partGroups[fanGroup.userData.partKey] = fanGroup;
                applySavedPosition(fanGroup.userData.partKey);
                mCase.add(fanGroup);
            });
            // 1 rear exhaust aligned with the top front intake
            const rearFanGroup = new THREE.Group();
            rearFanGroup.userData.partKey = 'case-fan-rear-1';
            const rFan = makeFan(frontFanR,true,true,false,false,'plane');
            rFan.rotation.y=Math.PI;
            rearFanGroup.add(rFan);
            rearFanGroup.position.set(-d.w/2+0.07, frontFanSpacing, -d.d/2+0.07);
            partGroups[rearFanGroup.userData.partKey] = rearFanGroup;
            applySavedPosition(rearFanGroup.userData.partKey);
            mCase.add(rearFanGroup);

            // Slide-in TG panel track groove at top/bottom edges
            const trackMat=new THREE.MeshStandardMaterial({color:0x1e2d42,metalness:0.7,roughness:0.3});
            [-d.h/2+0.03, d.h/2-0.03].forEach(y=>{
                const track=new THREE.Mesh(new THREE.BoxGeometry(0.02,0.025,d.d-0.08),trackMat);
                track.position.set(d.w/2-0.01,y,0); mCase.add(track);
            });

        } else if(c.id === 'case-air100') {
            // MONTECH AIR 100 ARGB — Ultra-fine mesh, side-swivel TG, I/O on top
            // Super fine mesh front plate (single unified piece, no gaps)
            const fineMeshMat = new THREE.MeshStandardMaterial({color:0x0d1424,wireframe:true,opacity:0.9,transparent:true});
            // The Air 100 front is perfectly flat and square-cornered
            const frontFace = new THREE.Mesh(new THREE.BoxGeometry(d.w,d.h-0.06,0.018),fineMeshMat);
            frontFace.position.z=d.d/2-0.01; mCase.add(frontFace);

            // Outer plastic bezel frame (no exposed metal border, pure mesh)
            const bezelMat=new THREE.MeshStandardMaterial({color:0x060911,roughness:0.5,metalness:0.3});
            // Top bezel strip
            const bTop=new THREE.Mesh(new THREE.BoxGeometry(d.w,0.05,0.02),bezelMat);
            bTop.position.set(0,d.h/2-0.03,d.d/2); mCase.add(bTop);
            // Bottom bezel strip
            const bBot=new THREE.Mesh(new THREE.BoxGeometry(d.w,0.04,0.02),bezelMat);
            bBot.position.set(0,-d.h/2+0.03,d.d/2); mCase.add(bBot);

            // Signature top I/O panel cluster (Air 100 has all ports on TOP)
            const topIo=new THREE.Mesh(new THREE.BoxGeometry(d.w*0.65,0.03,0.14),bezelMat);
            topIo.position.set(0,d.h/2,d.d/2-0.12); topIo.rotation.x=-Math.PI/8; mCase.add(topIo);
            // USB ports on top
            [-.09,-.05,.04,.08].forEach(x=>{
                const p=new THREE.Mesh(new THREE.BoxGeometry(0.025,0.02,0.015),ioMat);
                p.position.set(x,d.h/2+0.01,d.d/2-0.11); p.rotation.x=-Math.PI/8; mCase.add(p);
            });
            // LED button (distinctive feature — controls ARGB fans)
            const ledBtnMat=new THREE.MeshBasicMaterial({color:0xff22cc});
            const ledBtn=new THREE.Mesh(new THREE.CylinderGeometry(0.016,0.016,0.02,10),ledBtnMat);
            ledBtn.position.set(-d.w/2+0.12,d.h/2+0.005,d.d/2-0.11);
            mCase.add(ledBtn); rgbMats.push(ledBtn.material);

            // Power button (round, inset on top strip)
            const pwrMat=new THREE.MeshStandardMaterial({color:0x334155,roughness:0.3,metalness:0.8});
            const pwr=new THREE.Mesh(new THREE.CylinderGeometry(0.018,0.018,0.02,10),pwrMat);
            pwr.position.set(d.w/2-0.12,d.h/2+0.005,d.d/2-0.11); mCase.add(pwr);

            // 3× ARGB intake fans on front (pre-installed, defining feature)
            const air100FanR = 0.19;
            const air100FanSpacing = air100FanR * 2.15;
            [-air100FanSpacing, 0, air100FanSpacing].forEach((yPos,index)=>{
                const fanGroup = new THREE.Group();
                fanGroup.userData.partKey = `case-fan-front-${index+1}`;
                const fan = makeFan(air100FanR,true,false,false,false,'plane');
                fan.rotation.y = 0;
                fanGroup.add(fan);
                fanGroup.position.set(0, yPos, d.d/2-0.1);
                partGroups[fanGroup.userData.partKey] = fanGroup;
                applySavedPosition(fanGroup.userData.partKey);
                mCase.add(fanGroup);
            });
            // 1× rear ARGB exhaust aligned with the top front intake
            const rearFanGroup = new THREE.Group();
            rearFanGroup.userData.partKey = 'case-fan-rear-1';
            const rFan = makeFan(air100FanR,true,true,false,false,'plane');
            rFan.rotation.y=Math.PI;
            rearFanGroup.add(rFan);
            rearFanGroup.position.set(-d.w/2+0.07, air100FanSpacing, -d.d/2+0.07);
            partGroups[rearFanGroup.userData.partKey] = rearFanGroup;
            applySavedPosition(rearFanGroup.userData.partKey);
            mCase.add(rearFanGroup);

            // Side-swivel TG hinge (bottom hinge, swings out from bottom — unique to Montech)
            const hingeMat=new THREE.MeshStandardMaterial({color:0xd1d5db,metalness:0.95,roughness:0.1});
            [-d.d/2+0.08, d.d/2-0.08].forEach(z=>{
                const h=new THREE.Mesh(new THREE.BoxGeometry(0.025,0.025,0.04),hingeMat);
                h.position.set(d.w/2,d.h/2-0.04,z); mCase.add(h);
            });

            // Bottom dust filter strip (visible at bottom)
            const dfMat=new THREE.MeshStandardMaterial({color:0x111827,wireframe:true});
            const df=new THREE.Mesh(new THREE.BoxGeometry(d.w-0.1,0.015,d.d*0.6),dfMat);
            df.position.set(0,-d.h/2,0); mCase.add(df);
        }

        // Top fan mounting positions
        if(c.fans.top > 0) {
            const topY = d.h/2 - 0.06;
            const spacing = d.w / (c.fans.top + 1);
            for(let i=1;i<=c.fans.top;i++){
                const fanGroup = new THREE.Group();
                fanGroup.userData.partKey = `case-fan-top-${i}`;
                const topFan = makeFan(0.16,true);
                topFan.rotation.x = -Math.PI/2;
                fanGroup.add(topFan);
                fanGroup.position.set(-d.w/2 + spacing*i, topY, -d.d/2 + 0.08);
                partGroups[fanGroup.userData.partKey] = fanGroup;
                applySavedPosition(fanGroup.userData.partKey);
                mCase.add(fanGroup);
            }
        }

        // === SHARED: RUBBER GROMMET HOLES at rear panel ===
        const grommMat=new THREE.MeshStandardMaterial({color:0x1f2937,roughness:0.9});
        [-0.1,0.05,0.2].forEach(y=>{
            const g=new THREE.Mesh(new THREE.TorusGeometry(0.025,0.008,6,12),grommMat);
            g.position.set(-d.w/2+0.025,y,0); g.rotation.y=Math.PI/2; mCase.add(g);
        });

        // === TEMPERED GLASS SIDE PANEL ===
        const glassMat = new THREE.MeshPhysicalMaterial({
            color:0xd4e8ff, transparent:true,
            opacity: glassMode==='on'?0.12:0.0,
            transmission: glassMode==='on'?0.9:0.0,
            roughness:0.05, side:THREE.DoubleSide
        });
        mGlass = new THREE.Mesh(new THREE.BoxGeometry(0.02,d.h-0.06,d.d-0.06),glassMat);
        mGlass.position.x = d.w/2;
        mGlass.userData.partKey = 'case';

        // case-mounted visual elements (no separate camera module)

        mCase.userData.partKey = 'case';
        mCase.add(mGlass);
        applySavedPosition('case');

        // Ensure at least one rear fan exists on every case (default placement)
        const hasRear = Object.keys(partGroups).some(k => k && k.startsWith && k.startsWith('case-fan-rear'));
        if(!hasRear) {
            const rearFanGroup = new THREE.Group();
            rearFanGroup.userData.partKey = 'case-fan-rear-1';
            const rFan = makeFan(0.19, true, true);
            rFan.rotation.y = Math.PI;
            rearFanGroup.add(rFan);
            rearFanGroup.position.set(-d.w/2 + 0.07, 0, -d.d/2 + 0.07);
            partGroups[rearFanGroup.userData.partKey] = rearFanGroup;
            applySavedPosition(rearFanGroup.userData.partKey);
            mCase.add(rearFanGroup);
        }

        chassis.add(mCase);
    }

    // MOTHERBOARD — detailed layout
    function buildMobo() {
        if(mMobo) chassis.remove(mMobo);
        mMobo = new THREE.Group();
        partGroups['motherboard'] = mMobo;
        if(!build.case || !build.motherboard) {
            delete partGroups['motherboard'];
            return;
        }
        const c = build.case;
        const d = c.dims;
        const mb = build.motherboard;
        const isATX = mb.factor === 'ATX';

        // Set dimensions to dynamically fit the upper chamber room perfectly
        moboWidth = isATX ? d.d * 0.58 : d.d * 0.48;
        moboHeight = isATX ? d.h * 0.65 : d.h * 0.52;
        const moboThick = 0.02;

        const pcbMat = new THREE.MeshStandardMaterial({color: 0x090c12, roughness: 0.8});
        const pcb = new THREE.Mesh(new THREE.BoxGeometry(moboThick, moboHeight, moboWidth), pcbMat);
        pcb.receiveShadow = true; 
        mMobo.add(pcb);
        
        // Propagate dynamic motherboard coordinates back to world scale
        const shroudH = 0.22;
        const baselineY = -d.h/2 + shroudH + 0.02; // Top level of PSU shroud
        const roomH = d.h - shroudH - 0.04;
        
        moboWPos.set(
            -d.w/2 + 0.05, // Flush slightly off back tray (X-axis)
            baselineY + (roomH - moboHeight)/2 + 0.05, // Dynamic vertical center
            -d.d/2 + moboWidth/2 + 0.16 // Dynamic rear offset
        );
        mMobo.position.copy(moboWPos);

        // PCB trace lines
        const traceMat=new THREE.MeshStandardMaterial({color:0x1d4ed8,roughness:0.1,metalness:1,transparent:true,opacity:0.35});
        for(let i=0;i<7;i++){
            const t=new THREE.Mesh(new THREE.BoxGeometry(0.002,0.002,moboWidth*(0.35+Math.random()*0.5)),traceMat);
            t.position.set(0.021,-0.5+(i*0.18),-0.25+Math.random()*0.4); mMobo.add(t);
        }

        // Heatsinks (VRM + Chipset)
        const armorMat=new THREE.MeshStandardMaterial({color:0x141b27,metalness:0.95,roughness:0.15});
        const vrmBlock=new THREE.Mesh(new THREE.BoxGeometry(0.09,0.15,0.18),armorMat);
        vrmBlock.position.set(0.04,0.52,0.1); mMobo.add(vrmBlock);
        const vrmFins=makeStackedFins(0.09,0.12,0.18,8,0x1c2436);
        vrmFins.position.set(0.09,0.52,0.1); mMobo.add(vrmFins);

        // VRM arm heatsink
        const vrmArm=new THREE.Mesh(new THREE.BoxGeometry(0.09,0.38,0.1),armorMat);
        vrmArm.position.set(0.04,0.25,-0.22); mMobo.add(vrmArm);

        // CPU Socket (IHS anchor point)
        const sockMat = new THREE.MeshStandardMaterial({color: 0x111622, metalness: 0.8, roughness: 0.4});
        const sock = new THREE.Mesh(new THREE.BoxGeometry(0.022, moboHeight*0.22, moboWidth*0.22), sockMat);
        socketRelPos.set(0.02, moboHeight * 0.18, -moboWidth*0.12);
        sock.position.copy(socketRelPos);
        mMobo.add(sock);

        const ihsMat = new THREE.MeshStandardMaterial({color:0x94a3b8, metalness:0.95, roughness:0.2});
        const ihs = new THREE.Mesh(new THREE.BoxGeometry(0.008, moboHeight*0.12, moboWidth*0.12), ihsMat);
        ihs.position.set(socketRelPos.x + 0.015, socketRelPos.y, socketRelPos.z);
        mMobo.add(ihs);
        // Retention arm
        const arm=new THREE.Mesh(new THREE.BoxGeometry(0.006,0.24,0.004),ihsMat);
        arm.position.set(0.045,0.28,0.15); mMobo.add(arm);

        // DRAM slots
        const slotsMat = new THREE.MeshStandardMaterial({color: 0x05070a, roughness: 0.9});
        const slotD = 0.012;
        for(let i=0; i<4; i++) {
            const slot = new THREE.Mesh(new THREE.BoxGeometry(0.03, moboHeight * 0.25, slotD), slotsMat);
            // Placed beautifully to the front side of the CPU (positive Z-axis)
            slot.position.set(0.02, moboHeight * 0.18, moboWidth * 0.16 + (i * 0.025));
            mMobo.add(slot);
        }

        // PCIe slots (armored + standard)
        const pcieMat = new THREE.MeshStandardMaterial({color: 0x2d3748, metalness: 0.9, roughness: 0.1});
        const pcie = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.024, moboWidth * 0.68), pcieMat);
        pcieRelPos.set(0.025, -moboHeight*0.14, moboWidth*0.06);
        pcie.position.copy(pcieRelPos);
        mMobo.add(pcie);

        // Capacitors
        const capMat=new THREE.MeshStandardMaterial({color:0xa1a8b5,metalness:0.9,roughness:0.1});
        for(let i=0;i<5;i++){
            const cap=new THREE.Mesh(new THREE.CylinderGeometry(0.016,0.016,0.07,8),capMat);
            cap.position.set(0.04,0.44,-0.07+(i*0.06)); mMobo.add(cap);
        }

        // CMOS battery
        const coinMat=new THREE.MeshStandardMaterial({color:0x6b7280,metalness:0.9,roughness:0.2});
        const coin=new THREE.Mesh(new THREE.CylinderGeometry(0.05,0.05,0.018,14),coinMat);
        coin.rotation.z=Math.PI/2; coin.position.set(0.028,-0.26,-0.14); mMobo.add(coin);

        // Chipset heatsink
        const chipHS=new THREE.Mesh(new THREE.BoxGeometry(0.06,0.22,0.22),armorMat);
        chipHS.position.set(0.04,-0.4,-0.24); mMobo.add(chipHS);
        const chipFins=makeStackedFins(0.09,0.16,0.22,6,0x1c2436);
        chipFins.position.set(0.09,-0.4,-0.24); mMobo.add(chipFins);

        // 24-pin ATX connector
        const dimmMat = new THREE.MeshStandardMaterial({color:0x1e2937, metalness:0.92, roughness:0.25});
        const conn24=new THREE.Mesh(new THREE.BoxGeometry(0.04,0.38,0.06),dimmMat);
        conn24.position.set(0.03,0.06,-0.5); mMobo.add(conn24);

        // NVMe M.2 slot
        if(build.storage?.type==='nvme'){
            const m2Mat=new THREE.MeshStandardMaterial({color:0x065f46,roughness:0.5});
            const m2=new THREE.Mesh(new THREE.BoxGeometry(0.03,0.08,0.32),m2Mat);
            m2.position.set(0.04,-0.32,0.06); mMobo.add(m2);
            const ctrl=new THREE.Mesh(new THREE.BoxGeometry(0.032,0.05,0.05),armorMat);
            ctrl.position.set(0.042,-0.32,-0.04); mMobo.add(ctrl);
        } else {
            // SATA drive cable indicator
            const sataMat=new THREE.MeshStandardMaterial({color:0x1e3a5f,roughness:0.5});
            const sata=new THREE.Mesh(new THREE.BoxGeometry(0.04,0.06,0.08),sataMat);
            sata.position.set(0.03,-0.48,-0.5); mMobo.add(sata);
        }

        mMobo.userData.partKey = 'motherboard';
        applySavedPosition('motherboard');
        chassis.add(mMobo);
    }

    // PSU
    function buildPsu() {
        if(mPsu) chassis.remove(mPsu);
        if(!build.case || !build.psu) {
            delete partGroups['psu'];
            return;
        }
        const c = build.case;
        const d = c.dims;
        mPsu = new THREE.Group();
        partGroups['psu'] = mPsu;

        const psuMat = new THREE.MeshStandardMaterial({color:0x090d14, metalness:0.8, roughness:0.5});
        // Scale PSU to look robust inside bottom shroud
        const psuW = Math.min(0.5, d.w * 0.58);
        const psuH = 0.18;
        const psuD = d.d * 0.38;
        const core = new THREE.Mesh(new THREE.BoxGeometry(psuW, psuH, psuD), psuMat);
        core.castShadow = true; 
        mPsu.add(core);

        // Golden efficiency rating label
        const rColor = build.psu.name.includes('Gold') ? 0xeab308 : 0xcd8229;
        const badge = new THREE.Mesh(new THREE.BoxGeometry(0.015, 0.06, 0.12), new THREE.MeshBasicMaterial({color: rColor}));
        badge.position.set(psuW/2 + 0.005, 0.02, 0);
        mPsu.add(badge);

        // Dynamic position above the bottom shroud so the PSU is visible
        const shroudH = 0.22;
        mPsu.position.set(
            -d.w/2 + psuW/2 + 0.06,
            -d.h/2 + shroudH + psuH/2 + 0.02,
            -d.d/2 + psuD/2 + 0.14
        );
        mPsu.userData.partKey = 'psu';
        applySavedPosition('psu');
        chassis.add(mPsu);
    }

    // GPU
    function buildGpu() {
        if(mGpu) chassis.remove(mGpu);
        mGpu = new THREE.Group();
        partGroups['gpu'] = mGpu;
        if(!build.case || !build.motherboard || !build.gpu) {
            delete partGroups['gpu'];
            return;
        }
        const g = build.gpu;

        // Dynamic dimensional scaling tied to dynamic conversion metrics
        const cardL = g.length * MM_TO_UNITS;
        const cardH = g.thick * MM_TO_UNITS;
        const cardW = g.width * MM_TO_UNITS;

        const bodyMat = new THREE.MeshStandardMaterial({color:0x0f1420, metalness:0.95, roughness:0.2});
        const block = new THREE.Mesh(new THREE.BoxGeometry(cardW, cardH, cardL), bodyMat);
        block.castShadow = true; 
        mGpu.add(block);

        // Gold connector edge (PCIe fingers)
        const goldMat = new THREE.MeshStandardMaterial({color:0xeab308, metalness:1, roughness:0.05});
        const fingers = new THREE.Mesh(new THREE.BoxGeometry(0.01, 0.03, cardL * 0.65), goldMat);
        // Connects underneath, off center
        fingers.position.set(-cardW/2 + 0.01, -cardH/2 - 0.015, -cardL * 0.08);
        mGpu.add(fingers);

        // Heatsink grid fins visible behind fan blades
        const finBlocks = g.fans === 3 ? 3 : 2;
        const finW = cardW * 0.85;
        const finH = cardH * 0.6;
        const finL = (cardL / finBlocks) * 0.85;
        for(let i=0; i<finBlocks; i++) {
            const zPos = -cardL/2 + (cardL/finBlocks) * (i + 0.5);
            const fins = makeStackedFins(finW, finH, finL, 16, 0x8a99ad);
            fins.position.set(0, -cardH * 0.05, zPos);
            mGpu.add(fins);
        }

        // Beautiful ARGB lighting features
        if(g.rgb) {
            const neonMat = new THREE.MeshBasicMaterial({color:0x22d3ee});
            const strip = new THREE.Mesh(new THREE.BoxGeometry(0.01, cardH * 0.35, cardL * 0.58), neonMat);
            strip.position.set(cardW/2 + 0.005, cardH * 0.12, 0);
            mGpu.add(strip);
            rgbMats.push(neonMat);
        }

        // Fans mounted on the downward surface (Facing side panel in real orientation)
        const fanR = cardW * 0.42;
        const fanOffsets = g.fans === 3 ? [-cardL/3, 0, cardL/3] : [-cardL/4, cardL/4];
        fanOffsets.forEach(z => {
            const fan = makeFan(fanR, g.rgb, false, false, true, 'bottom');
            fan.rotation.x = Math.PI/2; 
            fan.position.set(0, -cardH/2 - 0.01, z);
            mGpu.add(fan);
        });

        // 100% Correct Positioning plugged inside PCIe slot of active motherboard
        const gpuTargetX = moboWPos.x + pcieRelPos.x + cardW/2;
        const gpuTargetY = moboWPos.y + pcieRelPos.y;
        const gpuTargetZ = moboWPos.z + pcieRelPos.z + cardL * 0.16;
        mGpu.position.set(gpuTargetX, gpuTargetY, gpuTargetZ);
        mGpu.userData.partKey = 'gpu';
        mGpu.userData.portOffset = new THREE.Vector3(0, cardH * 0.12, -cardL/2 - 0.005);
        applySavedPosition('gpu');
        chassis.add(mGpu);
        if(coolerBlockGroup && coolerRadGroup) refreshCoolerTubes();
    }

    // CPU Cooler
    function buildCooler() {
        if(mCooler) {
            chassis.remove(mCooler);
            cleanCoolerHoses();
        }
        if(coolerTubeGroup && coolerTubeGroup.parent) {
            coolerTubeGroup.parent.remove(coolerTubeGroup);
        }
        coolerBlockGroup = null;
        coolerRadGroup = null;
        coolerTubeGroup = null;
        mCooler = new THREE.Group();
        delete partGroups['cooler-block'];
        delete partGroups['cooler-rad'];
        for(let i = sceneSelectedParts.length - 1; i >= 0; i--) {
            if(sceneSelectedParts[i] === 'cooler-block' || sceneSelectedParts[i] === 'cooler-rad') {
                sceneSelectedParts.splice(i, 1);
            }
        }
        partGroups['cooler'] = mCooler;
        if(!build.cooler || !build.case || !build.motherboard) {
            if(coolerTubeGroup && coolerTubeGroup.parent) coolerTubeGroup.parent.remove(coolerTubeGroup);
            coolerTubeGroup = null;
            delete partGroups['cooler'];
            return;
        }
        const co = build.cooler;
        const c = build.case;
        const d = c.dims;

        // Compute CPU world position from motherboard socket coordinates
        const cpuWorld = new THREE.Vector3(
            moboWPos.x + socketRelPos.x + 0.015,
            moboWPos.y + socketRelPos.y,
            moboWPos.z + socketRelPos.z
        );
        mCooler.position.copy(cpuWorld);

        if(co.id === 'cool-stock') {
            coolerBlockGroup = new THREE.Group();
            coolerBlockGroup.userData.partKey = 'cooler-block';
            coolerBlockGroup.userData.portOffset = new THREE.Vector3(0,0,0);
            partGroups['cooler-block'] = coolerBlockGroup;
            applySavedPosition('cooler-block');
            mCooler.add(coolerBlockGroup);

            const frameMat = new THREE.MeshStandardMaterial({color:0x121720, roughness:0.75});
            const frame = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.07, 18), frameMat);
            frame.rotation.z = Math.PI/2;
            frame.position.set(0.035, 0, 0);
            coolerBlockGroup.add(frame);

            const fan = makeFan(0.1, true, false, true);
            fan.rotation.y = Math.PI/2;
            fan.position.set(0.072, 0, 0);
            coolerBlockGroup.add(fan);

        } else if(co.id === 'cool-ak400') {
            coolerBlockGroup = new THREE.Group();
            coolerBlockGroup.userData.partKey = 'cooler-block';
            coolerBlockGroup.userData.portOffset = new THREE.Vector3(0,0,0);
            partGroups['cooler-block'] = coolerBlockGroup;
            applySavedPosition('cooler-block');
            mCooler.add(coolerBlockGroup);

            const hScale = co.height * MM_TO_UNITS;
            const finW = 0.28, finH = hScale * 0.72, finD = 0.26;

            const matrixFins = makeStackedFins(finW, finH, finD, 44, 0x8a9cb0);
            matrixFins.position.set(finW/2 + 0.04, 0, 0);
            coolerBlockGroup.add(matrixFins);

            const pipeOffsets = [-0.07, -0.022, 0.022, 0.07];
            pipeOffsets.forEach(z => {
                const pipe = makeCurve(
                    new THREE.Vector3(0, 0, z),
                    new THREE.Vector3(finW*0.4, -finH*0.1, z),
                    new THREE.Vector3(finW/2, finH/2 + 0.015, z),
                    0.012, 0xcd8229
                );
                coolerBlockGroup.add(pipe);
            });

            const cap = new THREE.Mesh(new THREE.BoxGeometry(finW + 0.012, 0.024, finD + 0.012), 
                new THREE.MeshStandardMaterial({color:0x0a0f18, roughness:0.5}));
            cap.position.set(finW/2 + 0.04, finH/2 + 0.01, 0);
            coolerBlockGroup.add(cap);

            const coolerFan = makeFan(0.14, true, false, true);
            coolerFan.rotation.y = Math.PI/2;
            coolerFan.position.set(finW + 0.05, 0, 0);
            coolerBlockGroup.add(coolerFan);

        } else if(['cool-ml240l','cool-le520'].includes(co.id)) {
            const isML240 = co.id === 'cool-ml240l';
            const pumpMat = new THREE.MeshStandardMaterial({color:0x0d121c, metalness:0.9, roughness:0.25});
            coolerBlockGroup = new THREE.Group();
            coolerBlockGroup.userData.partKey = 'cooler-block';
            coolerBlockGroup.userData.portOffset = new THREE.Vector3(0.05, 0, 0);
            partGroups['cooler-block'] = coolerBlockGroup;
            // restore any saved offsets for the pump/block
            applySavedPosition('cooler-block');
            mCooler.add(coolerBlockGroup);
            let pump;
            if(isML240) {
                pump = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.1, 24), pumpMat);
                pump.rotation.z = Math.PI/2;
            } else {
                pump = new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.11, 0.11), pumpMat);
            }
            pump.position.set(0.05, 0, 0);
            pump.castShadow = true;
            coolerBlockGroup.add(pump);

            const ringMat = new THREE.MeshBasicMaterial({color:0x22d3ee});
            const ring = new THREE.Mesh(new THREE.TorusGeometry(0.045, 0.01, 8, 24), ringMat);
            ring.rotation.y = Math.PI/2;
            ring.position.set(0.106, 0, 0);
            coolerBlockGroup.add(ring);
            rgbMats.push(ringMat);

            const radL = 0.72;
            const radH = 0.06;
            const radW = 0.32;
            const radMat = new THREE.MeshStandardMaterial({color:0x111622, metalness:0.8, roughness:0.4});
            const ceilingY = d.h/2 - radH/2 - 0.02 - cpuWorld.y;
            const radZ = c.id === 'case-nexair'
                ? radL/2 - 0.02
                : c.id === 'case-air100'
                    ? 0
                    : -radL/2 + 0.02;
            coolerRadGroup = new THREE.Group();
            coolerRadGroup.userData.partKey = 'cooler-rad';
            coolerRadGroup.userData.portOffset = new THREE.Vector3(0, ceilingY, radZ);
            partGroups['cooler-rad'] = coolerRadGroup;
            // restore any saved offsets for the radiator/fans
            applySavedPosition('cooler-rad');
            const radiator = new THREE.Mesh(new THREE.BoxGeometry(radW, radH, radL), radMat);
            radiator.position.set(0, ceilingY, 0);
            coolerRadGroup.add(radiator);
            mCooler.add(coolerRadGroup);

            for(let i=-1; i<=1; i+=2) {
                const rFan = makeFan(0.14, true, false, false, false, 'plane');
                rFan.rotation.x = Math.PI/2;
                rFan.position.set(0, ceilingY - 0.038, i * 0.18);
                coolerRadGroup.add(rFan);
            }

            if(coolerTubeGroup && coolerTubeGroup.parent) coolerTubeGroup.parent.remove(coolerTubeGroup);
            coolerTubeGroup = new THREE.Group();
            chassis.add(coolerTubeGroup);
            refreshCoolerTubes();

        } else if(co.id === 'cool-arctic360') {
            const blockMat = new THREE.MeshStandardMaterial({color:0x151d2a, metalness:0.8, roughness:0.3});
            coolerBlockGroup = new THREE.Group();
            coolerBlockGroup.userData.partKey = 'cooler-block';
            coolerBlockGroup.userData.portOffset = new THREE.Vector3(0.05, 0, 0);
            partGroups['cooler-block'] = coolerBlockGroup;
            applySavedPosition('cooler-block');
            mCooler.add(coolerBlockGroup);

            const baseBlock = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.13, 0.13), blockMat);
            baseBlock.position.set(0.05, 0, 0);
            coolerBlockGroup.add(baseBlock);
            // Arctic AIO: add a small RGB ring on the pump for visual feedback
            const arcticRingMat = new THREE.MeshBasicMaterial({color:0xffffff});
            const arcticRing = new THREE.Mesh(new THREE.TorusGeometry(0.045, 0.01, 8, 24), arcticRingMat);
            arcticRing.rotation.y = Math.PI/2;
            arcticRing.position.set(0.106, 0, 0);
            coolerBlockGroup.add(arcticRing);
            rgbMats.push(arcticRingMat);

            const vrmExhaust = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.01, 16), 
                new THREE.MeshStandardMaterial({color:0x07090f, roughness:0.5}));
            vrmExhaust.rotation.z = Math.PI/2;
            vrmExhaust.position.set(0.105, 0.035, 0);
            coolerBlockGroup.add(vrmExhaust);

            const radL = 0.98;
            const radH = 0.07;
            const radW = 0.34;
            const radMat = new THREE.MeshStandardMaterial({color:0x0f121a, metalness:0.8, roughness:0.5});
            const ceilingY = d.h/2 - radH/2 - 0.02 - cpuWorld.y;
            const radZ = c.id === 'case-nexair'
                ? radL/2 - 0.02
                : c.id === 'case-air100'
                    ? 0
                    : -radL/2 + 0.02;
            coolerRadGroup = new THREE.Group();
            coolerRadGroup.userData.partKey = 'cooler-rad';
            coolerRadGroup.userData.portOffset = new THREE.Vector3(0, ceilingY, radZ);
            partGroups['cooler-rad'] = coolerRadGroup;
            applySavedPosition('cooler-rad');
            const radiator = new THREE.Mesh(new THREE.BoxGeometry(radW, radH, radL), radMat);
            radiator.position.set(0, ceilingY, 0);
            coolerRadGroup.add(radiator);

            [-0.3, 0, 0.3].forEach(z => {
                const rFan = makeFan(0.14, true, false, false, false, 'plane');
                rFan.rotation.x = Math.PI/2;
                rFan.position.set(0, ceilingY - 0.042, z);
                coolerRadGroup.add(rFan);
            });

            mCooler.add(coolerRadGroup);
            if(coolerTubeGroup && coolerTubeGroup.parent) coolerTubeGroup.parent.remove(coolerTubeGroup);
            coolerTubeGroup = new THREE.Group();
            chassis.add(coolerTubeGroup);
            refreshCoolerTubes();

        }

        mCooler.userData.partKey = 'cooler';
        if(['cool-ml240l','cool-le520','cool-arctic360'].includes(co.id)) {
            applySavedPosition('cooler');
        }
        chassis.add(mCooler);
    }

    // RAM
    function buildRam() {
        if(mRam) chassis.remove(mRam);
        mRam = new THREE.Group();
        partGroups['ram'] = mRam;
        if(!build.case || !build.ram || !build.motherboard) {
            delete partGroups['ram'];
            return;
        }
        const r = build.ram;
        const nSticks = r.sticks;
        const ramH = r.height * MM_TO_UNITS;
        const ramW = moboWidth * 0.28;
        const ramThick = 0.012;

        const cpuWorld = new THREE.Vector3(
            moboWPos.x + socketRelPos.x + 0.02,
            moboWPos.y + socketRelPos.y,
            moboWPos.z + socketRelPos.z
        );
        mRam.position.copy(cpuWorld);

        const pcbMat = new THREE.MeshStandardMaterial({color:0x111625, metalness:0.9, roughness:0.3});

        for(let i=0; i<nSticks; i++) {
            const index = i === 1 ? 2 : i;
            const slotOffsetZ = moboWidth * 0.16 + (index * 0.025);
            const zRel = slotOffsetZ - socketRelPos.z;

            const stick = new THREE.Mesh(new THREE.BoxGeometry(ramThick, ramH, ramW), pcbMat);
            stick.position.set(0.02, 0, zRel);
            stick.castShadow = true;
            mRam.add(stick);

            if(r.rgb) {
                const barMat = new THREE.MeshBasicMaterial({color:0x22d3ee});
                const bar = new THREE.Mesh(new THREE.BoxGeometry(0.014, 0.025, ramW * 0.94), barMat);
                bar.position.set(0.014, ramH/2, zRel);
                mRam.add(bar);
                rgbMats.push(barMat);
            }
        }

        mRam.userData.partKey = 'ram';
        applySavedPosition('ram');
        chassis.add(mRam);
    }

    // Camera helpers
    function focusMesh(cat) {
        const targets = {case:mCase,gpu:mGpu,cooler:mCooler,ram:mRam,psu:mPsu,motherboard:mMobo};
        const tg = targets[cat]; if(!tg) return;
        document.getElementById('focus-label').innerHTML=`<i class="fa-solid fa-crosshairs text-pink-500 mr-1"></i><span class="mono text-[9px] text-pink-400">Inspecting: ${cat.toUpperCase()}</span>`;
        gsap.to(tg.scale,{x:1.12,y:1.12,z:1.12,duration:0.2,yoyo:true,repeat:1});
        const wp=new THREE.Vector3(); tg.getWorldPosition(wp);
        gsap.to(controls.target,{x:wp.x,y:wp.y,z:wp.z,duration:0.7});
    }

    function setCam(a) {
        const presets = {
            diag:   [3.2,1.8,4.2, 0,0,0],
            inside: [1.6,0.2,1.6,-0.1,0.1,0.1],
            top:    [0.1,5,0.1, 0,0,0],
            rear:   [-4,0.5,-0.1,-0.4,0,0],
            side:   [0.1,0.5,4.5, 0,0,0]
        };
        const [px,py,pz,tx,ty,tz]=presets[a]||presets.diag;
        gsap.to(cam.position,{x:px,y:py,z:pz,duration:0.9});
        gsap.to(controls.target,{x:tx,y:ty,z:tz,duration:0.9});
    }

    function toggleExplode() {
        // Toggle exploded state, but animate relative to a saved baseline so repeated presses don't accumulate offsets.
        const btn = document.getElementById('explode-btn');
        const offsets = {
            'case':        new THREE.Vector3(0, 0, -1.76),
            'gpu':         new THREE.Vector3(1.6, 0.44, -0.36),
            'cooler':      new THREE.Vector3(0, 1.64, 0),
            'ram':         new THREE.Vector3(1.0, 0, -0.36),
            'psu':         new THREE.Vector3(0, 0.32, 1.2),
            'motherboard': new THREE.Vector3(0.64, 0.36, -0.36)
        };

        if(!exploded) {
            // Enter exploded state: snapshot baseline positions and animate to exploded offsets
            exploded = true;
            explodeBaselinePositions = {};
            if(btn) btn.classList.add('border-pink-500/40','text-pink-300');
            const focusLabel = document.getElementById('focus-label');
            if(focusLabel) focusLabel.innerHTML = `<i class="fa-solid fa-arrows-up-down-left-right text-pink-500 mr-1"></i><span class="mono text-[9px] text-pink-400">Exploded View</span>`;

            Object.keys(offsets).forEach(key => {
                const group = getGroupByKey(key);
                if(!group) return;
                // snapshot baseline
                explodeBaselinePositions[key] = group.position.clone();
                const target = explodeBaselinePositions[key].clone().add(offsets[key]);
                gsap.to(group.position, { x: target.x, y: target.y, z: target.z, duration: 0.8, ease: "power2.out" });
            });
            // hide airflow arrows while exploded for visual clarity
            if(airflowGroup) airflowGroup.visible = false;
        } else {
            // Exit exploded state: animate back to saved positions (JSON/localStorage) if present, otherwise baseline
            exploded = false;
            if(btn) btn.classList.remove('border-pink-500/40','text-pink-300');
            const focusLabel = document.getElementById('focus-label');
            if(focusLabel) focusLabel.innerHTML = `<i class="fa-solid fa-expand mr-1"></i><span class="mono text-[9px]">Free Orbit Mode</span>`;

            Object.keys(offsets).forEach(key => {
                const group = getGroupByKey(key);
                if(!group) return;
                const saved = getSavedPosition(key);
                const baseline = explodeBaselinePositions && explodeBaselinePositions[key] ? explodeBaselinePositions[key] : group.position.clone();
                const target = saved ? new THREE.Vector3(saved.x, saved.y, saved.z) : baseline;
                gsap.to(group.position, { x: target.x, y: target.y, z: target.z, duration: 0.8, ease: "power2.out" });
            });
            // clear snapshot after animating back
            explodeBaselinePositions = null;
            // restore airflow arrows visibility after exiting exploded view
            if(airflowGroup) airflowGroup.visible = !!airflowVisible;
        }
    }

    function toggleWireframe() {
        wireEnabled=!wireEnabled;
        const btn=document.getElementById('wire-btn');
        if(wireEnabled){ btn.classList.add('border-cyan-500/50','text-cyan-300'); }
        else { btn.classList.remove('border-cyan-500/50','text-cyan-300'); }
        chassis.traverse(obj=>{
            if(obj.isMesh && obj.material && !obj.material.transparent){
                obj.material.wireframe=wireEnabled;
            }
        });
    }

    // =====================================================
    // ANIMATION LOOP
    // =====================================================
    let tick=0;
    function loop() {
        requestAnimationFrame(loop);
        tick+=0.006;

        // RGB processing
        if(rgbOn && rgbMats.length){
            const h = rainbowMode ? (tick%1) : rgbHue/360;
            rgbMats.forEach(m=>{ if(m) m.color.setHSL(h,0.95,0.55); });
        } else if(!rgbOn) {
            rgbMats.forEach(m=>{ if(m) m.color.setHex(0x1e2d42); });
        }

        // Fan spin
        fans3d.forEach(f=>{ if(f) f.rotation.z+=fanSpeed; });

        // Gentle float
        if(!exploded && chassis) chassis.position.y=Math.sin(Date.now()*0.0011)*0.022;

        // Airflow arrows: animate radiator arrows and scale arrows with camera distance
        if(airflowGroup){
            const now = Date.now()*0.001;
            airflowGroup.children.forEach(g => {
                const ud = g.userData || {};
                if(ud.isRad){
                    // gentle upward bobbing along dir
                    const pulse = Math.sin(now*4 + (ud.start.x+ud.start.y+ud.start.z))*0.02 + 0.01;
                    const base = ud.start.clone();
                    g.position.copy(base.add(ud.dir.clone().multiplyScalar(pulse)));
                } else if(ud.start){
                    // pulse arrow along the direction it's pointing, then back
                    const base = ud.start.clone();
                    const drift = Math.sin(now*3 + ud.sideSeed) * 0.025;
                    g.position.copy(base.add(ud.dir.clone().multiplyScalar(drift)));
                }
                // scale with camera distance for readability
                const ref = ud.start ? ud.start : g.position;
                const dist = cam.position.distanceTo(ref);
                const s = Math.max(0.6, Math.min(1.8, 0.9 + (dist*0.18)));
                g.scale.setScalar(s);
            });
        }

        if(incompatibilityIndicator && incompatibilityIndicator.visible) {
            incompatibilityIndicator.rotation.y += 0.008;
            const now = Date.now() * 0.002;
            incompatibilityIndicator.position.y = incompatibilityIndicator.userData.basePosition.y + Math.sin(now) * 0.03;
            incompatibilityIndicator.position.x = incompatibilityIndicator.userData.basePosition.x + Math.sin(now * 0.6) * 0.01;
        }

        controls.update();

        // Update camera-dependent fan visibility materials (GPU fans: transparent when camera is below)
        if(fanVisibilityMats && fanVisibilityMats.length){
            fanVisibilityMats.forEach(mat=>{
                try{
                    const owner = mat.userData && mat.userData.owner;
                    if(!owner) return;
                    if(owner.updateMatrixWorld) owner.updateMatrixWorld(true);
                    const pos = owner.getWorldPosition(new THREE.Vector3());
                    const worldFront = new THREE.Vector3(0,0,1)
                        .applyQuaternion(owner.getWorldQuaternion(new THREE.Quaternion()))
                        .normalize();
                    const camDir = cam.position.clone().sub(pos).normalize();
                    const dot = worldFront.dot(camDir);
                    const mode = mat.userData.visibilityMode;
                    let shouldShow = false;
                    if(mode === 'bottom') {
                        shouldShow = cam.position.y < pos.y - 0.01;
                    } else if(mode === 'plane') {
                        shouldShow = Math.abs(dot) > 0.25;
                    } else if(mode === 'always') {
                        shouldShow = true;
                    }
                    if(shouldShow){
                        mat.transparent = true;
                        mat.opacity = 0.35;
                        mat.depthTest = false;
                    } else {
                        mat.transparent = false;
                        mat.opacity = 1.0;
                        mat.depthTest = true;
                    }
                }catch(e){}
            });
        }

        renderer.render(scene,cam);
    }

    // =====================================================
    // INIT
    // =================================================
    window.addEventListener('error', function(event) {
        console.error('Runtime error:', event.error || event.message, event.filename, event.lineno, event.colno);
        const ld = document.getElementById('nexus-loader');
        if(ld) {
            ld.style.opacity = '0';
            ld.style.pointerEvents = 'none';
            ld.querySelector('span')?.remove();
        }
    });
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        const ld = document.getElementById('nexus-loader');
        if(ld) {
            ld.style.opacity = '0';
            ld.style.pointerEvents = 'none';
            ld.querySelector('span')?.remove();
        }
    });

    async function bootstrapNexus3D() {
        try {
            await loadSavedPositions();
            await loadComponentDB();
            syncBuildFromPageSelectedParts();
            initEngine();
        } catch (e) {
            console.error('Initialization failed:', e);
            const ld = document.getElementById('nexus-loader');
            if(ld) {
                ld.style.opacity = '0';
                ld.style.pointerEvents = 'none';
                ld.querySelector('span')?.remove();
            }
        }
    }

    
    window.nexus3d_full = window.nexus3d_full || {};
    window.nexus3d_full.refresh = function() {
        syncBuildFromPageSelectedParts();
        try { if (typeof rebuildAll === 'function') rebuildAll(); } catch(e) {}
    };

if (document.readyState === 'complete' || document.readyState === 'interactive') {
        bootstrapNexus3D();
    } else {
        window.addEventListener('DOMContentLoaded', bootstrapNexus3D);
    }