/**
 * three-hero.js — Lightweight Three.js hero scene for Viraamam cafe.
 * Lazy-loaded, respects prefers-reduced-motion.
 */
(function initHero() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const canvas = document.getElementById('hero-canvas');
  if (!canvas) return;

  // Dynamically load Three.js
  const script = document.createElement('script');
  script.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js';
  script.onload = setupScene;
  document.head.appendChild(script);

  function setupScene() {
    const W = canvas.clientWidth, H = canvas.clientHeight;
    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, W / H, 0.1, 100);
    camera.position.z = 5;

    // ── Coffee Cup ─────────────────────────────────
    const cupGroup = new THREE.Group();

    // Body (cylinder)
    const bodyGeo = new THREE.CylinderGeometry(0.55, 0.45, 0.9, 32);
    const bodyMat = new THREE.MeshPhongMaterial({
      color: 0x3C2A21, shininess: 80,
      specular: new THREE.Color(0xD4622A),
    });
    const body = new THREE.Mesh(bodyGeo, bodyMat);
    cupGroup.add(body);

    // Rim
    const rimGeo = new THREE.TorusGeometry(0.55, 0.04, 12, 40);
    const rimMat = new THREE.MeshPhongMaterial({ color: 0x6b4c3b });
    const rim = new THREE.Mesh(rimGeo, rimMat);
    rim.position.y = 0.45;
    cupGroup.add(rim);

    // Handle (torus section)
    const handleGeo = new THREE.TorusGeometry(0.28, 0.06, 8, 20, Math.PI);
    const handleMat = new THREE.MeshPhongMaterial({ color: 0x4e3728 });
    const handle = new THREE.Mesh(handleGeo, handleMat);
    handle.rotation.y = Math.PI / 2;
    handle.position.set(0.6, 0, 0);
    cupGroup.add(handle);

    // Saucer
    const saucerGeo = new THREE.CylinderGeometry(0.85, 0.75, 0.1, 32);
    const saucer = new THREE.Mesh(saucerGeo, bodyMat);
    saucer.position.y = -0.55;
    cupGroup.add(saucer);

    // Coffee surface
    const coffeeGeo = new THREE.CircleGeometry(0.53, 32);
    const coffeeMat = new THREE.MeshPhongMaterial({ color: 0x1a0f0a });
    const coffee = new THREE.Mesh(coffeeGeo, coffeeMat);
    coffee.rotation.x = -Math.PI / 2;
    coffee.position.y = 0.46;
    cupGroup.add(coffee);

    scene.add(cupGroup);

    // ── Steam Particles ──────────────────────────
    const steamGeo = new THREE.BufferGeometry();
    const STEAM_COUNT = 60;
    const positions = new Float32Array(STEAM_COUNT * 3);
    const speeds = [];
    for (let i = 0; i < STEAM_COUNT; i++) {
      positions[i * 3]     = (Math.random() - 0.5) * 0.6;
      positions[i * 3 + 1] = 0.5 + Math.random() * 1.5;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 0.4;
      speeds.push(0.003 + Math.random() * 0.005);
    }
    steamGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const steamMat = new THREE.PointsMaterial({
      color: 0xF5EBDD, size: 0.05, transparent: true, opacity: 0.4,
    });
    const steam = new THREE.Points(steamGeo, steamMat);
    scene.add(steam);

    // ── Floating Beans ───────────────────────────
    const beans = [];
    for (let i = 0; i < 12; i++) {
      const bGeo = new THREE.SphereGeometry(0.06, 8, 8);
      const bMat = new THREE.MeshPhongMaterial({ color: 0x4e3728 });
      const b = new THREE.Mesh(bGeo, bMat);
      b.position.set(
        (Math.random() - 0.5) * 8,
        (Math.random() - 0.5) * 5,
        (Math.random() - 0.5) * 3 - 1,
      );
      b.userData = { speed: 0.002 + Math.random() * 0.003, offset: Math.random() * Math.PI * 2 };
      scene.add(b);
      beans.push(b);
    }

    // ── Lighting ─────────────────────────────────
    const ambient = new THREE.AmbientLight(0xffffff, 0.4);
    scene.add(ambient);
    const key = new THREE.DirectionalLight(0xffe0c0, 1.2);
    key.position.set(3, 4, 3);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0xD4622A, 0.6);
    fill.position.set(-3, -1, 2);
    scene.add(fill);

    // ── Mouse Parallax ───────────────────────────
    let mouseX = 0, mouseY = 0;
    document.addEventListener('mousemove', (e) => {
      mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
      mouseY = -(e.clientY / window.innerHeight - 0.5) * 2;
    });

    // ── Resize ───────────────────────────────────
    window.addEventListener('resize', () => {
      const w = canvas.clientWidth, h = canvas.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    });

    // ── Animate ──────────────────────────────────
    let t = 0;
    function animate() {
      requestAnimationFrame(animate);
      t += 0.01;

      // Rotate cup
      cupGroup.rotation.y += 0.005;
      cupGroup.rotation.x += (mouseY * 0.15 - cupGroup.rotation.x) * 0.05;
      cupGroup.position.y = Math.sin(t * 0.6) * 0.05;

      // Parallax
      camera.position.x += (mouseX * 0.5 - camera.position.x) * 0.04;
      camera.position.y += (mouseY * 0.3 - camera.position.y) * 0.04;

      // Animate steam
      const pos = steamGeo.attributes.position.array;
      for (let i = 0; i < STEAM_COUNT; i++) {
        pos[i * 3 + 1] += speeds[i];
        pos[i * 3]     += Math.sin(t + i) * 0.001;
        if (pos[i * 3 + 1] > 2.5) {
          pos[i * 3 + 1] = 0.5;
          pos[i * 3]     = (Math.random() - 0.5) * 0.6;
        }
      }
      steamGeo.attributes.position.needsUpdate = true;

      // Float beans
      beans.forEach(b => {
        b.position.y += Math.sin(t + b.userData.offset) * b.userData.speed;
        b.rotation.x += 0.01;
        b.rotation.z += 0.008;
      });

      renderer.render(scene, camera);
    }
    animate();
  }
})();
