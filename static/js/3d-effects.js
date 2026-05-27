/* ═══════════════════════════════════════════════
   SafePlace — 3D & Visual Effects
   ═══════════════════════════════════════════════ */
(function () {
  'use strict';

  var isMobile = window.matchMedia('(pointer: coarse)').matches;

  /* ─────────────────────────────────────────────
     1. 3D Mouse-tilt on cards
  ───────────────────────────────────────────── */
  function initTilt(selector) {
    if (isMobile) return; /* skip on touch devices */
    document.querySelectorAll(selector).forEach(function (card) {
      var MAX = 7;

      /* Add glare overlay */
      if (!card.querySelector('.glare-overlay')) {
        var glare = document.createElement('div');
        glare.className = 'glare-overlay';
        card.appendChild(glare);
      }
      card.classList.add('tilt-card');

      card.addEventListener('mousemove', function (e) {
        var rect = card.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var y = e.clientY - rect.top;
        var cx = rect.width / 2;
        var cy = rect.height / 2;
        var rotX = ((y - cy) / cy) * -MAX;
        var rotY = ((x - cx) / cx) * MAX;

        card.style.transition = 'none';
        card.style.transform =
          'perspective(900px) rotateX(' + rotX.toFixed(2) + 'deg) rotateY(' + rotY.toFixed(2) + 'deg) translateZ(6px)';

        /* Glare position */
        var glareEl = card.querySelector('.glare-overlay');
        if (glareEl) {
          var mx = ((x / rect.width)  * 100).toFixed(1);
          var my = ((y / rect.height) * 100).toFixed(1);
          glareEl.style.setProperty('--mx', mx + '%');
          glareEl.style.setProperty('--my', my + '%');
        }
      });

      card.addEventListener('mouseleave', function () {
        card.style.transition = 'transform 0.55s cubic-bezier(0.34,1.56,0.64,1)';
        card.style.transform = '';
      });
    });
  }

  /* ─────────────────────────────────────────────
     2. Particle canvas on bento cards
  ───────────────────────────────────────────── */
  function initBentoParticles() {
    document.querySelectorAll('.bento-particle-canvas').forEach(function (canvas) {
      var ctx = canvas.getContext('2d');
      if (!ctx) return;
      var W, H, particles = [];

      function resize() {
        W = canvas.width  = canvas.offsetWidth  || canvas.parentElement.offsetWidth;
        H = canvas.height = canvas.offsetHeight || canvas.parentElement.offsetHeight;
      }
      resize();

      for (var i = 0; i < 22; i++) {
        particles.push({
          x: Math.random() * W,
          y: Math.random() * H,
          r: Math.random() * 2.2 + 0.4,
          vx: (Math.random() - 0.5) * 0.38,
          vy: (Math.random() - 0.5) * 0.38,
          alpha: Math.random() * 0.55 + 0.2
        });
      }

      var raf;
      function draw() {
        ctx.clearRect(0, 0, W, H);
        for (var j = 0; j < particles.length; j++) {
          var p = particles[j];
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(159,247,0,' + p.alpha + ')';
          ctx.fill();
          p.x += p.vx;
          p.y += p.vy;
          if (p.x < 0) p.x = W;
          if (p.x > W) p.x = 0;
          if (p.y < 0) p.y = H;
          if (p.y > H) p.y = 0;
        }
        raf = requestAnimationFrame(draw);
      }
      draw();

      window.addEventListener('resize', resize);
    });
  }

  /* ─────────────────────────────────────────────
     3. Neon glow on play buttons
  ───────────────────────────────────────────── */
  function initPlayGlow() {
    document.querySelectorAll('.ep-play-fab, .play-fab, .play-fab-vid').forEach(function (btn) {
      btn.classList.add('neon-play');
    });
  }

  /* ─────────────────────────────────────────────
     4. Magnetic micro-move on CTAs
  ───────────────────────────────────────────── */
  function initMagnetic(selector) {
    if (isMobile) return;
    document.querySelectorAll(selector).forEach(function (btn) {
      btn.classList.add('magnetic-btn');
      btn.addEventListener('mousemove', function (e) {
        var rect = btn.getBoundingClientRect();
        var dx = e.clientX - (rect.left + rect.width / 2);
        var dy = e.clientY - (rect.top  + rect.height / 2);
        btn.style.transform = 'translate(' + (dx * 0.14) + 'px,' + (dy * 0.14) + 'px) scale(1.04)';
      });
      btn.addEventListener('mouseleave', function () {
        btn.style.transform = '';
      });
    });
  }

  /* ─────────────────────────────────────────────
     5. Holographic shimmer on cards
  ───────────────────────────────────────────── */
  function initHolo(selector) {
    document.querySelectorAll(selector).forEach(function (card) {
      card.classList.add('holo-card');
    });
  }

  /* ─────────────────────────────────────────────
     6. Card entry stagger animation (on load)
  ───────────────────────────────────────────── */
  function initCardEntry() {
    var cards = document.querySelectorAll(
      '.ep-card, .ep-card-new, .vid-card, .vid-card-wrap, .bento-card'
    );
    cards.forEach(function (card, i) {
      card.style.animationDelay = (i * 0.07) + 's';
      card.classList.add('card-enter');
    });
  }

  /* ─────────────────────────────────────────────
     7. Hero section scroll parallax
  ───────────────────────────────────────────── */
  function initParallax() {
    if (isMobile) return;
    var heroInner = document.querySelector('.sp-section [data-parallax]');
    if (!heroInner) return;
    window.addEventListener('scroll', function () {
      heroInner.style.transform = 'translateY(' + (window.scrollY * 0.25) + 'px)';
    }, { passive: true });
  }

  /* ─────────────────────────────────────────────
     8. Depth class on episode/video cards
  ───────────────────────────────────────────── */
  function initDepth() {
    document.querySelectorAll('.ep-card-new, .vid-card-wrap').forEach(function (card) {
      card.classList.add('depth-card');
    });
  }

  /* ─────────────────────────────────────────────
     Init
  ───────────────────────────────────────────── */
  document.addEventListener('DOMContentLoaded', function () {
    initTilt('.ep-card, .ep-card-new, .vid-card, .vid-card-wrap, .bento-card');
    initBentoParticles();
    initPlayGlow();
    initMagnetic('.btn-lime, .btn-glass, .play-fab, .ep-play-fab, .play-fab-vid');
    initHolo('.ep-card, .ep-card-new, .vid-card');
    initCardEntry();
    initParallax();
    initDepth();
  });

})();
