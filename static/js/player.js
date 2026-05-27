/* ═══════════════════════════════════════════════
   SafePlace — Persistent Audio Player
   ═══════════════════════════════════════════════ */
(function () {
  'use strict';

  var audio = document.getElementById('sp-audio');
  if (!audio) return;

  /* ── Desktop elements ── */
  var playerFooter   = document.getElementById('sp-player');
  var titleEl        = document.getElementById('player-title');
  var hostEl         = document.getElementById('player-host');
  var coverEl        = document.getElementById('player-cover');
  var playPauseBtn   = document.getElementById('play-pause-btn');
  var playIcon       = document.getElementById('play-icon');
  var progressBar    = document.getElementById('progress-bar');
  var progressFill   = document.getElementById('progress-fill');
  var currentTimeEl  = document.getElementById('current-time');
  var totalTimeEl    = document.getElementById('total-time');

  /* ── Mobile elements ── */
  var mobilePlayer        = document.getElementById('sp-mobile-player');
  var mobTitle            = document.getElementById('sp-mob-title');
  var mobPlayBtn          = document.getElementById('sp-mob-play-btn');
  var mobPlayIcon         = document.getElementById('sp-mob-play-icon');
  var mobCover            = document.getElementById('sp-mob-cover');
  var mobileProgressEl    = document.getElementById('sp-mobile-progress');
  var mobileProgressFill  = document.getElementById('sp-mobile-progress-fill');
  var mobCloseBtn         = document.getElementById('sp-mob-close-btn');

  /* ── Helpers ── */
  function fmt(s) {
    if (!isFinite(s)) return '0:00';
    var m = Math.floor(s / 60);
    var sec = Math.floor(s % 60);
    return m + ':' + (sec < 10 ? '0' : '') + sec;
  }

  function setPlayIcons(playing) {
    var icon = playing ? 'pause' : 'play_arrow';
    if (playIcon)    playIcon.textContent    = icon;
    if (mobPlayIcon) mobPlayIcon.textContent = icon;
  }

  function updateCover(color) {
    var c = color || '#00261b';
    var gradient = 'linear-gradient(135deg,' + c + ',#416900)';
    var inner = '<span class="material-symbols-outlined" style="color:#fff;font-size:22px;font-variation-settings:\'FILL\' 1">headphones</span>';
    if (coverEl) {
      coverEl.style.background = gradient;
      coverEl.innerHTML = inner;
    }
    if (mobCover) {
      mobCover.style.background = gradient;
      mobCover.innerHTML = '<span class="material-symbols-outlined text-white" style="font-size:17px;font-variation-settings:\'FILL\' 1">headphones</span>';
    }
  }

  function showPlayers() {
    /* Desktop player is hidden by default via CSS (hidden lg:block) but starts
       as hidden because there's nothing playing. Show it. */
    if (playerFooter) {
      playerFooter.style.display = 'block';
    }
    if (mobilePlayer) {
      mobilePlayer.classList.add('sp-player-visible');
    }
  }

  function hideMobilePlayer() {
    if (mobilePlayer) mobilePlayer.classList.remove('sp-player-visible');
  }

  /* ── Load and play ── */
  function loadAndPlay(data) {
    if (!data || !data.audioUrl) return;

    audio.src = data.audioUrl;
    audio.load();

    var playPromise = audio.play();
    if (playPromise !== undefined) {
      playPromise.catch(function () {
        /* autoplay blocked — user still sees the player and can press play */
      });
    }

    if (titleEl) titleEl.textContent = data.title || 'The SafePlace by K';
    if (hostEl)  hostEl.textContent  = data.host  || '';
    if (mobTitle) mobTitle.textContent = data.title || 'The SafePlace by K';
    updateCover(data.color);
    showPlayers();
    setPlayIcons(true);
  }

  /* ── Listen for sp:play events (fired by main.js / page scripts) ── */
  document.addEventListener('sp:play', function (e) {
    loadAndPlay(e.detail || {});
  });

  /* ── Desktop play/pause ── */
  if (playPauseBtn) {
    playPauseBtn.addEventListener('click', function () {
      if (audio.paused) { audio.play().catch(function(){}); }
      else              { audio.pause(); }
    });
  }

  /* ── Mobile play/pause ── */
  if (mobPlayBtn) {
    mobPlayBtn.addEventListener('click', function () {
      if (audio.paused) { audio.play().catch(function(){}); }
      else              { audio.pause(); }
    });
  }

  /* ── Mobile close ── */
  if (mobCloseBtn) {
    mobCloseBtn.addEventListener('click', function () {
      audio.pause();
      audio.src = '';
      hideMobilePlayer();
    });
  }

  /* ── Audio events → UI sync ── */
  audio.addEventListener('play',  function () { setPlayIcons(true);  });
  audio.addEventListener('pause', function () { setPlayIcons(false); });
  audio.addEventListener('ended', function () { setPlayIcons(false); });

  audio.addEventListener('timeupdate', function () {
    if (!audio.duration) return;
    var pct = (audio.currentTime / audio.duration) * 100;
    if (progressFill)      progressFill.style.width      = pct + '%';
    if (mobileProgressFill) mobileProgressFill.style.width = pct + '%';
    if (currentTimeEl)     currentTimeEl.textContent     = fmt(audio.currentTime);
  });

  audio.addEventListener('loadedmetadata', function () {
    if (totalTimeEl) totalTimeEl.textContent = fmt(audio.duration);
  });

  /* ── Seek on desktop progress bar ── */
  if (progressBar) {
    progressBar.addEventListener('click', function (e) {
      if (!audio.duration) return;
      var rect = progressBar.getBoundingClientRect();
      audio.currentTime = ((e.clientX - rect.left) / rect.width) * audio.duration;
    });
  }

  /* ── Seek on mobile progress bar ── */
  if (mobileProgressEl) {
    mobileProgressEl.addEventListener('click', function (e) {
      if (!audio.duration) return;
      var rect = mobileProgressEl.getBoundingClientRect();
      audio.currentTime = ((e.clientX - rect.left) / rect.width) * audio.duration;
    });
  }

  /* ── Volume bar (desktop) ── */
  var volumeFill = document.getElementById('volume-fill');
  var volumeBar  = document.getElementById('volume-bar');
  if (volumeBar && volumeFill) {
    volumeBar.addEventListener('click', function (e) {
      var rect = volumeFill.parentElement.getBoundingClientRect();
      var vol = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      audio.volume = vol;
      volumeFill.style.width = (vol * 100) + '%';
    });
  }

})();
