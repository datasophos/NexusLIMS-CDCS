(function () {
  var history = [];
  var historyPos = -1;
  var timer = null;
  var progressRaf = null;
  var progressStart = null;
  var mouseIdleTimer = null;
  var bgPatterns = ['nx-bg-0', 'nx-bg-1', 'nx-bg-2'];
  var bgIndex = bgPatterns.length - 1;  /* rotateBg() on first slide wraps to 0 */

  var bgEl    = document.getElementById('nx-gallery-bg');
  var imgEl   = document.getElementById('nx-gallery-img');
  var titleEl = document.getElementById('nx-gallery-title');
  var descEl  = document.getElementById('nx-gallery-desc');
  var descTextEl = document.getElementById('nx-gallery-desc-text');
  var featuredEl = document.getElementById('nx-gallery-featured');
  var expEl   = document.getElementById('nx-gallery-experimenter');
  var instEl  = document.getElementById('nx-gallery-instrument');
  var dateEl  = document.getElementById('nx-gallery-date');
  var linkEl  = document.getElementById('nx-gallery-link');
  var prevBtn = document.getElementById('nx-prev');
  var nextBtn = document.getElementById('nx-next');
  var fsBtn   = document.getElementById('nx-fullscreen-btn');
  var progressEl = document.getElementById('nx-progress-bar');
  var instSep = document.getElementById('nx-gallery-inst-sep');
  var dateSep = document.getElementById('nx-gallery-date-sep');

  function setMeta(slide) {
    titleEl.textContent = slide.title || '';
    titleEl.title       = slide.title || '';
    descTextEl.textContent = slide.description || '';
    descEl.title        = slide.description || '';
    descEl.style.display = slide.description ? '' : 'none';
    featuredEl.hidden   = !slide.featured;
    expEl.textContent   = slide.experimenter || '';
    instEl.textContent  = slide.instrument || '';
    dateEl.textContent  = slide.month_year || '';
    linkEl.href         = slide.record_url || '#';
    instSep.style.display = slide.instrument ? '' : 'none';
    dateSep.style.display = slide.month_year ? '' : 'none';
  }

  function rotateBg() {
    bgEl.classList.remove(bgPatterns[bgIndex]);
    bgIndex = (bgIndex + 1) % bgPatterns.length;
    bgEl.classList.add(bgPatterns[bgIndex]);
  }

  function applySlide(slide) {
    imgEl.style.opacity = '0';
    rotateBg();
    setTimeout(function () {
      imgEl.src = slide.preview_url;
      imgEl.style.opacity = '1';
    }, 200);
    setMeta(slide);
    startProgress();
  }

  function startProgress() {
    cancelAnimationFrame(progressRaf);
    progressEl.style.transition = 'none';
    progressEl.style.width = '0%';
    progressStart = performance.now();
    function tick(now) {
      var elapsed = now - progressStart;
      var pct = Math.min(100, (elapsed / ROTATION_INTERVAL) * 100);
      progressEl.style.width = pct + '%';
      if (pct < 100) {
        progressRaf = requestAnimationFrame(tick);
      }
    }
    progressRaf = requestAnimationFrame(tick);
  }

  function scheduleNext() {
    clearTimeout(timer);
    timer = setTimeout(function () { goNext(true); }, ROTATION_INTERVAL);
  }

  function goNext(fetch) {
    clearTimeout(timer);
    if (!fetch && historyPos < history.length - 1) {
      historyPos++;
      applySlide(history[historyPos]);
      scheduleNext();
      return;
    }
    window.fetch(GALLERY_API_URL)
      .then(function (r) { return r.json(); })
      .then(function (slide) {
        if (slide.error) { scheduleNext(); return; }
        history = history.slice(0, historyPos + 1);
        if (history.length >= 10) history.shift();
        history.push(slide);
        historyPos = history.length - 1;
        applySlide(slide);
        scheduleNext();
      })
      .catch(function () { scheduleNext(); });
  }

  function goPrev() {
    if (historyPos <= 0) return;
    historyPos--;
    applySlide(history[historyPos]);
    clearTimeout(timer);
    scheduleNext();
  }

  prevBtn.addEventListener('click', goPrev);
  nextBtn.addEventListener('click', function () { goNext(false); });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowLeft')  goPrev();
    if (e.key === 'ArrowRight') goNext(false);
    if (e.key === 'f' || e.key === 'F') toggleFullscreen();
  });

  function showArrows() {
    prevBtn.classList.add('nx-visible');
    nextBtn.classList.add('nx-visible');
    if (!document.fullscreenElement) fsBtn.classList.add('nx-visible');
    document.body.style.cursor = '';
    clearTimeout(mouseIdleTimer);
    mouseIdleTimer = setTimeout(function () {
      prevBtn.classList.remove('nx-visible');
      nextBtn.classList.remove('nx-visible');
      fsBtn.classList.remove('nx-visible');
      document.body.style.cursor = 'none';
    }, 2000);
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  }

  document.addEventListener('fullscreenchange', function () {
    if (document.fullscreenElement) {
      fsBtn.classList.remove('nx-visible');
      fsBtn.setAttribute('aria-label', 'Exit full screen');
      fsBtn.setAttribute('title', 'Exit full screen');
    } else {
      fsBtn.setAttribute('aria-label', 'Make gallery full screen');
      fsBtn.setAttribute('title', 'Make gallery full screen');
    }
  });

  fsBtn.addEventListener('click', toggleFullscreen);

  document.addEventListener('mousemove', showArrows);
  document.addEventListener('mouseleave', function () {
    prevBtn.classList.remove('nx-visible');
    nextBtn.classList.remove('nx-visible');
  });

  // Load first slide
  goNext(true);
})();
