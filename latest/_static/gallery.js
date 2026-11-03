/* Enhance the screenshot gallery; without JavaScript all figures remain visible. */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.cdcs-carousel').forEach((carousel) => {
    const slides = Array.from(carousel.querySelectorAll('figure'));
    if (slides.length < 2) return;
    carousel.setAttribute('role', 'region');
    carousel.setAttribute('aria-label', 'NexusLIMS CDCS screenshot gallery');

    let current = 0;
    const makeButton = (label, icon) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.setAttribute('aria-label', label);
      button.title = label;
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox', '0 0 24 24');
      svg.setAttribute('aria-hidden', 'true');
      svg.setAttribute('focusable', 'false');
      svg.classList.add('cdcs-control-icon');
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', {
        previous: 'M15 5l-7 7 7 7',
        next: 'M9 5l7 7-7 7',
        close: 'M6 6l12 12M18 6L6 18',
      }[icon]);
      svg.append(path);
      button.append(svg);
      return button;
    };
    const controls = document.createElement('div');
    controls.className = 'cdcs-carousel-controls';
    const previous = makeButton('Previous screenshot', 'previous');
    const position = document.createElement('span');
    position.setAttribute('aria-live', 'polite');
    position.setAttribute('aria-atomic', 'true');
    const next = makeButton('Next screenshot', 'next');
    controls.append(previous, position, next);
    carousel.append(controls);

    // A normal image link remains available when dialog support is absent.
    const lightbox = document.createElement('dialog');
    lightbox.className = 'cdcs-lightbox';
    lightbox.setAttribute('aria-label', 'Full-page screenshot gallery');
    const close = makeButton('Close full-page gallery', 'close');
    close.className = 'cdcs-lightbox-close';
    const image = document.createElement('img');
    const caption = document.createElement('div');
    caption.className = 'cdcs-lightbox-caption';
    caption.setAttribute('aria-live', 'polite');
    caption.setAttribute('aria-atomic', 'true');
    const lightboxControls = document.createElement('div');
    lightboxControls.className = 'cdcs-carousel-controls';
    const lightboxPrevious = makeButton('Previous screenshot', 'previous');
    const lightboxPosition = document.createElement('span');
    const lightboxNext = makeButton('Next screenshot', 'next');
    lightboxControls.append(lightboxPrevious, lightboxPosition, lightboxNext);
    lightbox.append(close, image, caption, lightboxControls);
    document.body.append(lightbox);

    const show = (index) => {
      current = (index + slides.length) % slides.length;
      slides.forEach((slide, i) => { slide.hidden = i !== current; });
      position.textContent = `${current + 1} of ${slides.length}`;
      const source = slides[current].querySelector('img');
      const link = slides[current].querySelector('a.image-reference');
      image.src = link ? link.href : source.src;
      image.alt = source.alt;
      caption.replaceChildren(...Array.from(slides[current].querySelector('figcaption').childNodes, node => node.cloneNode(true)));
      caption.querySelectorAll('.headerlink').forEach(node => node.remove());
      lightboxPosition.textContent = position.textContent;
    };
    const open = (event) => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || typeof lightbox.showModal !== 'function') return;
      event.preventDefault();
      lightbox.showModal();
      close.focus();
    };
    slides.forEach((slide) => slide.querySelector('a.image-reference').addEventListener('click', open));
    previous.addEventListener('click', () => show(current - 1));
    next.addEventListener('click', () => show(current + 1));
    lightboxPrevious.addEventListener('click', () => show(current - 1));
    lightboxNext.addEventListener('click', () => show(current + 1));
    close.addEventListener('click', () => lightbox.close());
    lightbox.addEventListener('close', () => slides[current].querySelector('a.image-reference').focus());
    const navigate = (event) => {
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault();
        show(current + (event.key === 'ArrowRight' ? 1 : -1));
      }
    };
    carousel.addEventListener('keydown', navigate);
    lightbox.addEventListener('keydown', navigate);
    show(0);
  });
});
