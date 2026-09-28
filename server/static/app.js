// AutoCroqui3D - Frontend Application Logic & Three.js Viewport

let currentSpec = null;
let currentThreeData = null;
let threeScene, threeCamera, threeRenderer, threeControls;
let modelGroup = null;
let isWireframe = false;

document.addEventListener('DOMContentLoaded', () => {
  initDOM();
  initThreeJS();
});

function initDOM() {
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const fileBadge = document.getElementById('fileSelectedBadge');
  const uploadForm = document.getElementById('uploadForm');
  const apiKeyInput = document.getElementById('apiKey');
  const toggleApiKey = document.getElementById('toggleApiKey');

  // Load saved API key from localStorage if present
  const savedKey = localStorage.getItem('croqui3d_gemini_key');
  if (savedKey) {
    apiKeyInput.value = savedKey;
  }

  toggleApiKey.addEventListener('click', () => {
    apiKeyInput.type = apiKeyInput.type === 'password' ? 'text' : 'password';
  });

  apiKeyInput.addEventListener('change', () => {
    if (apiKeyInput.value.trim()) {
      localStorage.setItem('croqui3d_gemini_key', apiKeyInput.value.trim());
    }
  });

  // Drop zone events
  dropZone.addEventListener('click', () => fileInput.click());
  
  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove('dragover');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      updateFileBadge();
    }
  });

  fileInput.addEventListener('change', updateFileBadge);

  function updateFileBadge() {
    if (fileInput.files && fileInput.files[0]) {
      fileBadge.textContent = `Arquivo: ${fileInput.files[0].name} (${(fileInput.files[0].size / 1024).toFixed(1)} KB)`;
      fileBadge.classList.remove('hidden');
    }
  }

  // Upload Form Submit
  uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!fileInput.files || !fileInput.files[0]) {
      showAlert('Por favor, selecione um croqui (PDF, imagem, etc.) para analisar.', 'warning');
      return;
    }

    const btn = document.getElementById('btnAnalyze');
    const spinner = btn.querySelector('.spinner');
    const btnText = btn.querySelector('.btn-text');
    btn.disabled = true;
    spinner.classList.remove('hidden');
    btnText.textContent = 'Interpretando Cotas & Vistas...';

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('notes', document.getElementById('studentNotes').value);
    formData.append('api_key', apiKeyInput.value);
    formData.append('model_name', document.getElementById('aiModel').value);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      if (!data.success) {
        throw new Error(data.detail || 'Erro ao processar croqui.');
      }

      currentSpec = data.spec;
      currentThreeData = data.threejs_data;

      // Populate UI
      document.getElementById('blueprintPreview').src = data.preview_image;
      document.getElementById('partTitleTag').textContent = currentSpec.metadata.title;
      document.getElementById('ilogicCodeDisplay').textContent = data.ilogic_script;

      populateParameters(currentSpec);
      render3DModel(currentThreeData);

      document.getElementById('resultsWorkspace').classList.remove('hidden');
      showAlert(`✓ ${data.summary}`, 'success');

      // Scroll smoothly to workspace
      document.getElementById('resultsWorkspace').scrollIntoView({ behavior: 'smooth' });

    } catch (err) {
      showAlert(`Falha: ${err.message}`, 'error');
    } finally {
      btn.disabled = false;
      spinner.classList.add('hidden');
      btnText.textContent = '⚡ Interpretar & Modelar';
    }
  });

  // Tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      document.getElementById(targetId).classList.add('active');
    });
  });

  // Update Parameters
  document.getElementById('btnUpdateModel').addEventListener('click', async () => {
    if (!currentSpec) return;

    currentSpec.base_feature.length = parseFloat(document.getElementById('paramBaseLength').value);
    currentSpec.base_feature.width = parseFloat(document.getElementById('paramBaseWidth').value);
    currentSpec.base_feature.extrude_depth = parseFloat(document.getElementById('paramBaseHeight').value);

    try {
      const res = await fetch('/api/update_model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentSpec)
      });
      const data = await res.json();
      if (data.success) {
        currentSpec = data.spec;
        currentThreeData = data.threejs_data;
        document.getElementById('ilogicCodeDisplay').textContent = data.ilogic_script;
        render3DModel(currentThreeData);
        showAlert('Modelo 3D e script iLogic atualizados com sucesso!', 'success');
      }
    } catch (err) {
      showAlert(`Erro ao atualizar: ${err.message}`, 'error');
    }
  });

  // Action Buttons
  document.getElementById('btnSendToInventor').addEventListener('click', async () => {
    if (!currentSpec) return;
    showAlert('Conectando ao Autodesk Inventor na máquina local...', 'info');
    try {
      const res = await fetch('/api/model_inventor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentSpec)
      });
      const data = await res.json();
      if (data.success) {
        showAlert(`🎉 ${data.message}`, 'success');
      } else {
        showAlert(`Aviso Inventor: ${data.error}. Você pode usar o script iLogic abaixo diretamente no Inventor!`, 'warning');
      }
    } catch (err) {
      showAlert(`Erro de comunicação: ${err.message}`, 'error');
    }
  });

  document.getElementById('btnCopyIlogic').addEventListener('click', () => {
    const code = document.getElementById('ilogicCodeDisplay').textContent;
    if (code) {
      navigator.clipboard.writeText(code);
      showAlert('✓ Código iLogic copiado para a Área de Transferência!', 'success');
    }
  });

  document.getElementById('btnDownloadIlogic').addEventListener('click', () => {
    if (!currentSpec) return;
    downloadFile('/api/download_ilogic', `${currentSpec.metadata.title}_iLogic.iLogicVb`);
  });

  document.getElementById('btnDownloadObj').addEventListener('click', () => {
    if (!currentSpec) return;
    downloadFile('/api/download_obj', `${currentSpec.metadata.title}.obj`);
  });

  // Viewport helper buttons
  document.getElementById('btnToggleWireframe').addEventListener('click', () => {
    isWireframe = !isWireframe;
    if (modelGroup) {
      modelGroup.traverse(child => {
        if (child.isMesh && child.material) {
          child.material.wireframe = isWireframe;
        }
      });
    }
  });

  document.getElementById('btnResetCamera').addEventListener('click', resetCamera);

  // Modal events
  const modal = document.getElementById('helpModal');
  document.getElementById('btnOpenHelp').addEventListener('click', () => modal.classList.remove('hidden'));
  document.getElementById('btnCloseModal').addEventListener('click', () => modal.classList.add('hidden'));
  window.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.add('hidden');
  });
}

function populateParameters(spec) {
  const base = spec.base_feature;
  document.getElementById('paramBaseLength').value = base.length;
  document.getElementById('paramBaseWidth').value = base.width;
  document.getElementById('paramBaseHeight').value = base.extrude_depth;

  // Cuts
  const cutsContainer = document.getElementById('cutsContainer');
  cutsContainer.innerHTML = '';
  if (!spec.cuts || spec.cuts.length === 0) {
    cutsContainer.innerHTML = '<span class="text-muted">Nenhum rebaixo detectado.</span>';
  } else {
    spec.cuts.forEach((cut, i) => {
      const card = document.createElement('div');
      card.className = 'feature-item-card';
      card.innerHTML = `
        <strong>${cut.name || `Corte #${i+1}`}</strong>
        <span>Dim: ${cut.length}x${cut.width} mm</span>
        <span>Profundidade: ${cut.depth} mm</span>
        <span>Posição: (${cut.pos_x}, ${cut.pos_y})</span>
      `;
      cutsContainer.appendChild(card);
    });
  }

  // Holes
  const holesContainer = document.getElementById('holesContainer');
  holesContainer.innerHTML = '';
  if (!spec.holes || spec.holes.length === 0) {
    holesContainer.innerHTML = '<span class="text-muted">Nenhum furo detectado.</span>';
  } else {
    spec.holes.forEach((hole, i) => {
      const card = document.createElement('div');
      card.className = 'feature-item-card';
      card.innerHTML = `
        <strong>${hole.name || `Furo #${i+1}`}</strong>
        <span>Ø ${hole.diameter} mm</span>
        <span>Posição: (${hole.pos_x}, ${hole.pos_y})</span>
        <span>${hole.through_all ? 'Passante' : `Prof: ${hole.depth} mm`}</span>
      `;
      holesContainer.appendChild(card);
    });
  }
}

function initThreeJS() {
  const container = document.getElementById('threeViewport');
  if (!container) return;

  const width = container.clientWidth || 600;
  const height = container.clientHeight || 400;

  threeScene = new THREE.Scene();
  threeScene.background = new THREE.Color(0x0a0f18);

  threeCamera = new THREE.PerspectiveCamera(45, width / height, 0.1, 2000);
  threeRenderer = new THREE.WebGLRenderer({ antialias: true });
  threeRenderer.setSize(width, height);
  threeRenderer.setPixelRatio(window.devicePixelRatio);
  threeRenderer.shadowMap.enabled = true;
  container.appendChild(threeRenderer.domElement);

  threeControls = new THREE.OrbitControls(threeCamera, threeRenderer.domElement);
  threeControls.enableDamping = true;
  threeControls.dampingFactor = 0.05;

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
  threeScene.add(ambientLight);

  const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
  dirLight1.position.set(100, 200, 150);
  threeScene.add(dirLight1);

  const dirLight2 = new THREE.DirectionalLight(0x90b0e0, 0.4);
  dirLight2.position.set(-100, -100, -150);
  threeScene.add(dirLight2);

  // Ground Grid
  const gridHelper = new THREE.GridHelper(300, 30, 0x22354d, 0x152233);
  gridHelper.position.y = 0;
  threeScene.add(gridHelper);

  const axesHelper = new THREE.AxesHelper(40);
  threeScene.add(axesHelper);

  resetCamera();

  // Resize handler
  window.addEventListener('resize', () => {
    if (!container) return;
    const w = container.clientWidth;
    const h = container.clientHeight;
    threeCamera.aspect = w / h;
    threeCamera.updateProjectionMatrix();
    threeRenderer.setSize(w, h);
  });

  // Animation Loop
  function animate() {
    requestAnimationFrame(animate);
    threeControls.update();
    threeRenderer.render(threeScene, threeCamera);
  }
  animate();
}

function render3DModel(threeData) {
  if (!threeScene || !threeData) return;

  if (modelGroup) {
    threeScene.remove(modelGroup);
  }

  modelGroup = new THREE.Group();
  const baseInfo = threeData.base_mesh;
  const dims = baseInfo.dimensions;

  // Base Solid Mesh
  let baseGeo;
  if (baseInfo.type === 'cylinder') {
    baseGeo = new THREE.CylinderGeometry(dims.radius, dims.radius, dims.height, 32);
  } else {
    baseGeo = new THREE.BoxGeometry(dims.length, dims.height, dims.width);
  }

  const baseMat = new THREE.MeshStandardMaterial({
    color: 0x3b82f6,
    metalness: 0.35,
    roughness: 0.45,
    wireframe: isWireframe
  });

  const baseMesh = new THREE.Mesh(baseGeo, baseMat);
  baseMesh.position.set(baseInfo.position.x, baseInfo.position.y, baseInfo.position.z);
  baseMesh.castShadow = true;
  baseMesh.receiveShadow = true;

  // Add edge outlines for CAD aesthetic
  const edgesGeo = new THREE.EdgesGeometry(baseGeo);
  const edgesMat = new THREE.LineBasicMaterial({ color: 0x93c5fd, linewidth: 2 });
  const edges = new THREE.LineSegments(edgesGeo, edgesMat);
  baseMesh.add(edges);

  modelGroup.add(baseMesh);

  // Render Cuts (Visualized in semi-transparent red cavities)
  if (threeData.cuts) {
    threeData.cuts.forEach(cut => {
      const cutGeo = new THREE.BoxGeometry(cut.dimensions.length, cut.dimensions.height, cut.dimensions.width);
      const cutMat = new THREE.MeshStandardMaterial({
        color: 0xef4444,
        transparent: true,
        opacity: 0.5,
        wireframe: isWireframe
      });
      const cutMesh = new THREE.Mesh(cutGeo, cutMat);
      cutMesh.position.set(cut.position.x, cut.position.y, cut.position.z);
      modelGroup.add(cutMesh);
    });
  }

  // Render Holes (Dark transparent cylindrical cavity markers)
  if (threeData.holes) {
    threeData.holes.forEach(hole => {
      const holeGeo = new THREE.CylinderGeometry(hole.radius, hole.radius, hole.height + 1, 24);
      const holeMat = new THREE.MeshStandardMaterial({
        color: 0x0f172a,
        metalness: 0.8,
        wireframe: isWireframe
      });
      const holeMesh = new THREE.Mesh(holeGeo, holeMat);
      holeMesh.position.set(hole.position.x, hole.position.y, hole.position.z);
      modelGroup.add(holeMesh);
    });
  }

  threeScene.add(modelGroup);

  // Adjust camera to fit part bounds nicely
  const maxDim = Math.max(dims.length, dims.width, dims.height);
  threeCamera.position.set(maxDim * 1.5, maxDim * 1.2, maxDim * 1.8);
  threeControls.target.set(0, dims.height / 2.0, 0);
  threeControls.update();
}

function resetCamera() {
  threeCamera.position.set(120, 100, 160);
  threeControls.target.set(0, 15, 0);
  threeControls.update();
}

function showAlert(text, type = 'info') {
  const alert = document.getElementById('statusAlert');
  const textEl = document.getElementById('statusText');
  const iconEl = document.getElementById('statusIcon');
  alert.className = `alert alert-${type}`;
  textEl.textContent = text;
  iconEl.textContent = type === 'success' ? '✓' : type === 'warning' ? '⚠️' : type === 'error' ? '❌' : 'ℹ️';
  alert.classList.remove('hidden');
}

async function downloadFile(endpoint, filename) {
  if (!currentSpec) return;
  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(currentSpec)
    });
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch (err) {
    showAlert(`Erro no download: ${err.message}`, 'error');
  }
}
