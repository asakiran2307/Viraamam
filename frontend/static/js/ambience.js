/**
 * ambience.js — Lightbox and GSAP scroll-reveal for the Ambience gallery page.
 */
document.addEventListener('DOMContentLoaded', () => {
  initGallery();
  initGsapReveal();
});

// ── Gallery Lightbox ──────────────────────────────────────────────────────
let galleryPhotos = [];
let currentIndex = 0;

function initGallery() {
  const items = document.querySelectorAll('.gallery-item');
  if (!items.length) return;

  galleryPhotos = Array.from(items).map(el => ({
    src: el.querySelector('img')?.src,
    title: el.dataset.title || '',
    caption: el.dataset.caption || '',
  }));

  const lightbox = document.getElementById('lightbox');
  const lbImg    = document.getElementById('lb-img');
  const lbCap    = document.getElementById('lb-caption');
  const lbClose  = document.getElementById('lb-close');
  const lbPrev   = document.getElementById('lb-prev');
  const lbNext   = document.getElementById('lb-next');

  items.forEach((item, idx) => {
    item.addEventListener('click', () => openLightbox(idx));
  });

  function openLightbox(idx) {
    currentIndex = idx;
    showPhoto(idx);
    lightbox?.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeLightbox() {
    lightbox?.classList.remove('open');
    document.body.style.overflow = '';
  }

  function showPhoto(idx) {
    const photo = galleryPhotos[idx];
    if (lbImg && photo) {
      lbImg.src = photo.src;
      lbImg.alt = photo.title;
    }
    if (lbCap) lbCap.textContent = [photo.title, photo.caption].filter(Boolean).join(' — ');
  }

  lbClose?.addEventListener('click', closeLightbox);
  lightbox?.addEventListener('click', (e) => { if (e.target === lightbox) closeLightbox(); });

  lbPrev?.addEventListener('click', () => {
    currentIndex = (currentIndex - 1 + galleryPhotos.length) % galleryPhotos.length;
    showPhoto(currentIndex);
  });

  lbNext?.addEventListener('click', () => {
    currentIndex = (currentIndex + 1) % galleryPhotos.length;
    showPhoto(currentIndex);
  });

  // Keyboard navigation
  document.addEventListener('keydown', (e) => {
    if (!lightbox?.classList.contains('open')) return;
    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowLeft')  { currentIndex = (currentIndex - 1 + galleryPhotos.length) % galleryPhotos.length; showPhoto(currentIndex); }
    if (e.key === 'ArrowRight') { currentIndex = (currentIndex + 1) % galleryPhotos.length; showPhoto(currentIndex); }
  });
}

// ── GSAP Scroll Reveal ────────────────────────────────────────────────────
function initGsapReveal() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
    // Load GSAP dynamically
    loadScript('https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js', () => {
      loadScript('https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js', applyReveal);
    });
    return;
  }
  applyReveal();
}

function applyReveal() {
  if (typeof gsap === 'undefined') return;
  gsap.registerPlugin(ScrollTrigger);

  gsap.utils.toArray('.gallery-item').forEach((el, i) => {
    gsap.from(el, {
      opacity: 0,
      y: 40,
      duration: 0.6,
      delay: (i % 3) * 0.1,
      scrollTrigger: {
        trigger: el,
        start: 'top 88%',
        toggleActions: 'play none none none',
      },
    });
  });

  gsap.from('.ambience-hero-content', {
    opacity: 0, y: 30, duration: 0.8, ease: 'power2.out',
  });
}

function loadScript(src, cb) {
  const s = document.createElement('script');
  s.src = src;
  s.onload = cb;
  document.head.appendChild(s);
}
