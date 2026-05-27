/* ═══════════════════════════════════════════════
   SafePlace — Main JS (interactions globales)
   ═══════════════════════════════════════════════ */
(function () {
  'use strict';

  /* ─────────────────────────────────────────────
     1. js-play-btn → fire sp:play event
     Tous les boutons avec class="js-play-btn"
     data-audio-url, data-title, data-host, data-color
  ───────────────────────────────────────────── */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.js-play-btn');
    if (!btn) return;
    var audioUrl = btn.dataset.audioUrl;
    if (!audioUrl) return;
    e.preventDefault();
    document.dispatchEvent(new CustomEvent('sp:play', {
      detail: {
        audioUrl: audioUrl,
        title:    btn.dataset.title || 'The SafePlace by K',
        host:     btn.dataset.host  || '',
        color:    btn.dataset.color || '#00261b'
      }
    }));
    /* Ripple visuel sur le bouton */
    addRipple(btn, e);
  });

  /* ─────────────────────────────────────────────
     2. Ripple effect helper
  ───────────────────────────────────────────── */
  function addRipple(el, e) {
    var rect = el.getBoundingClientRect();
    var ripple = document.createElement('span');
    ripple.className = 'ripple-effect';
    ripple.style.left = (e.clientX - rect.left) + 'px';
    ripple.style.top  = (e.clientY - rect.top)  + 'px';
    el.style.position = 'relative';
    el.style.overflow = 'hidden';
    el.appendChild(ripple);
    setTimeout(function () { ripple.remove(); }, 600);
  }

  /* ─────────────────────────────────────────────
     3. Scroll reveal (.sp-reveal)
  ───────────────────────────────────────────── */
  if ('IntersectionObserver' in window) {
    var revealObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          revealObs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });

    document.querySelectorAll('.sp-reveal').forEach(function (el) {
      revealObs.observe(el);
    });
  } else {
    /* Fallback : tout visible d'emblée */
    document.querySelectorAll('.sp-reveal').forEach(function (el) {
      el.classList.add('is-visible');
    });
  }

  /* ─────────────────────────────────────────────
     4. Stagger lists
  ───────────────────────────────────────────── */
  if ('IntersectionObserver' in window) {
    var staggerObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.querySelectorAll('.stagger-item').forEach(function (item, i) {
            setTimeout(function () { item.classList.add('visible'); }, i * 90);
          });
          staggerObs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.05 });

    document.querySelectorAll('.stagger-list').forEach(function (list) {
      staggerObs.observe(list);
    });
  }

  /* ─────────────────────────────────────────────
     5. Cover gradient auto-coloring
  ───────────────────────────────────────────── */
  document.querySelectorAll('[data-cover-color]').forEach(function (el) {
    var color = el.dataset.coverColor;
    if (color && !el.dataset.videoUrl && !el.style.background) {
      el.style.background = 'linear-gradient(135deg,' + color + ',#416900)';
    }
  });

  /* ─────────────────────────────────────────────
     6. Share panels (cards list pages)
  ───────────────────────────────────────────── */
  document.addEventListener('click', function (e) {
    var toggle = e.target.closest('.js-share-toggle');
    if (toggle) {
      e.stopPropagation();
      var panel = toggle.parentElement.querySelector('.share-panel');
      if (!panel) return;
      var wasOpen = panel.classList.contains('open');
      document.querySelectorAll('.share-panel').forEach(function (p) { p.classList.remove('open'); });
      if (!wasOpen) panel.classList.add('open');
      return;
    }
    /* Close all on outside click */
    document.querySelectorAll('.share-panel').forEach(function (p) { p.classList.remove('open'); });
  });

  /* ─────────────────────────────────────────────
     7. Copy-link buttons
  ───────────────────────────────────────────── */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.js-copy-link');
    if (!btn) return;
    var url = btn.dataset.url || location.href;
    if (url && url.startsWith('/')) url = location.origin + url;
    navigator.clipboard.writeText(url).then(function () {
      var orig = btn.innerHTML;
      btn.innerHTML = '<span class="material-symbols-outlined" style="font-size:17px;color:#416900">check</span> Copié !';
      var panel = btn.closest('.share-panel');
      if (panel) panel.classList.remove('open');
      setTimeout(function () { btn.innerHTML = orig; }, 2200);
    }).catch(function () {
      /* Fallback for older browsers */
      var ta = document.createElement('textarea');
      ta.value = url;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      ta.remove();
    });
  });

  /* ─────────────────────────────────────────────
     8. Reminder button (home hero)
  ───────────────────────────────────────────── */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.js-reminder-btn');
    if (!btn) return;
    var title = btn.dataset.title || 'ce live';
    showToast('🔔 Rappel activé pour « ' + title + ' »');
  });

  function showToast(msg) {
    var toast = document.getElementById('sp-reminder-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'sp-reminder-toast';
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(function () { toast.classList.remove('show'); }, 3200);
  }

  /* ─────────────────────────────────────────────
     9. Detail page — share button wiring
  ───────────────────────────────────────────── */
  var detailShareBtn   = document.getElementById('detail-share-btn');
  var detailSharePanel = document.getElementById('detail-share-panel');
  var detailCopyLink   = document.getElementById('detail-copy-link');
  var detailWaLink     = document.getElementById('detail-wa-link');
  var detailEmailLink  = document.getElementById('detail-email-link');

  if (detailShareBtn && detailSharePanel) {
    detailShareBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      detailSharePanel.classList.toggle('open');
    });
    if (detailCopyLink) {
      detailCopyLink.addEventListener('click', function () {
        navigator.clipboard.writeText(location.href).then(function () {
          var orig = detailCopyLink.innerHTML;
          detailCopyLink.innerHTML = '<span class="material-symbols-outlined" style="font-size:18px;color:#416900">check</span> Copié !';
          detailSharePanel.classList.remove('open');
          setTimeout(function () { detailCopyLink.innerHTML = orig; }, 2200);
        });
      });
    }
    if (detailWaLink) {
      detailWaLink.href = 'https://wa.me/?text=' + encodeURIComponent(document.title + ' ' + location.href);
    }
    if (detailEmailLink) {
      detailEmailLink.href = 'mailto:?subject=' + encodeURIComponent(document.title) + '&body=' + encodeURIComponent(location.href);
    }
  }

  /* Legacy .js-share-btn (podcast_detail cover) */
  var legacyShareBtn = document.querySelector('.js-share-btn');
  if (legacyShareBtn && detailSharePanel) {
    legacyShareBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      detailSharePanel.classList.toggle('open');
    });
  }

  /* ─────────────────────────────────────────────
     10. Simple search (header input)
     Filtre les cartes visibles sur la page
  ───────────────────────────────────────────── */
  var searchInput = document.querySelector('input[placeholder="Rechercher..."]');
  if (searchInput) {
    searchInput.addEventListener('input', function () {
      var q = searchInput.value.toLowerCase().trim();
      var cards = document.querySelectorAll('.ep-card, .ep-card-new, .vid-card, .vid-card-wrap');
      cards.forEach(function (card) {
        var text = card.textContent.toLowerCase();
        card.style.display = (!q || text.includes(q)) ? '' : 'none';
      });
    });
  }

})();
