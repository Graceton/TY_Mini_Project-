/**
 * Optivox Magnifier Module
 * Provides robust magnification and accessibility features.
 */

(function() {
  'use strict';

  // Configuration
  const config = {
    defaultZoom: 2,
    minZoom: 1.2,
    maxZoom: 4,
    zoomStep: 0.2,
    magnifierSize: 220 // Matches CSS --magnifier-size
  };

  // DOM Elements
  const magnifier = document.getElementById('magnifier');
  const magnifierContent = document.getElementById('magnifierContent');
  
  // State
  let zoomLevel = parseFloat(localStorage.getItem('optivox_zoom')) || config.defaultZoom;
  let contentCloned = false;
  let isMagnifying = false;
  let lastX = 0;
  let lastY = 0;

  /**
   * Clones the page content accurately
   */
  function clonePageContent() {
    if (contentCloned) return;
    
    // We clone the body but need to handle some specific cleaning
    const bodyClone = document.body.cloneNode(true);
    
    // Remove scripts and assistive elements from clone to prevent issues
    const selectorsToRemove = [
      'script', 
      '#magnifier', 
      '#zoomIndicator', 
      '#zoomTip', 
      '.skip-link',
      'iframe'
    ];
    
    selectorsToRemove.forEach(selector => {
      bodyClone.querySelectorAll(selector).forEach(el => el.remove());
    });

    // Ensure cloned IDs don't conflict (optional but safer)
    bodyClone.querySelectorAll('[id]').forEach(el => el.removeAttribute('id'));
    
    magnifierContent.innerHTML = '';
    magnifierContent.appendChild(bodyClone);
    
    contentCloned = true;
    updateZoom();
  }

  function updateZoom() {
    if (magnifierContent) {
      magnifierContent.style.transform = `scale(${zoomLevel})`;
      localStorage.setItem('optivox_zoom', zoomLevel);
    }
  }

  /**
   * Precise position calculation including scroll offsets
   */
  function updatePosition(x, y) {
    if (!magnifier || !magnifierContent) return;

    const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
    const scrollY = window.pageYOffset || document.documentElement.scrollTop;

    // Position the magnifier circle (viewport coordinates)
    magnifier.style.left = `${x - config.magnifierSize / 2}px`;
    magnifier.style.top = `${y - config.magnifierSize / 2}px`;

    // Position the content inside (absolute page coordinates)
    const centerX = (x + scrollX) * zoomLevel;
    const centerY = (y + scrollY) * zoomLevel;
    
    const offsetX = config.magnifierSize / 2 - centerX;
    const offsetY = config.magnifierSize / 2 - centerY;

    magnifierContent.style.left = `${offsetX}px`;
    magnifierContent.style.top = `${offsetY}px`;
  }

  function handleMouseMove(e) {
    if (!isMagnifying) {
      magnifier.style.display = 'block';
      clonePageContent();
      isMagnifying = true;
    }
    
    lastX = e.clientX;
    lastY = e.clientY;
    updatePosition(lastX, lastY);
  }

  function handleScroll() {
    if (isMagnifying) {
      updatePosition(lastX, lastY);
    }
  }

  function handleKeyDown(e) {
    // Ctrl + / - for Zoom
    if (e.ctrlKey || e.metaKey) {
      if (e.key === '+' || e.key === '=') {
        e.preventDefault();
        zoomLevel = Math.min(zoomLevel + config.zoomStep, config.maxZoom);
        updateZoom();
        updatePosition(lastX, lastY);
        showIndicator(`Zoom: ${zoomLevel.toFixed(1)}x`);
      } else if (e.key === '-' || e.key === '_') {
        e.preventDefault();
        zoomLevel = Math.max(zoomLevel - config.zoomStep, config.minZoom);
        updateZoom();
        updatePosition(lastX, lastY);
        showIndicator(`Zoom: ${zoomLevel.toFixed(1)}x`);
      }
    }
    
    // Escape to hide tip
    if (e.key === 'Escape') {
      const tip = document.getElementById('zoomTip');
      if (tip) tip.style.opacity = '0';
    }
  }

  function showIndicator(text) {
    let indicator = document.getElementById('zoomIndicator');
    if (!indicator) return;
    
    indicator.textContent = text;
    indicator.style.opacity = '1';
    
    clearTimeout(indicator.timeout);
    indicator.timeout = setTimeout(() => {
      indicator.style.opacity = '0';
    }, 1500);
  }

  function init() {
    if (!magnifier || !magnifierContent) return;

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('scroll', handleScroll, { passive: true });
    document.addEventListener('keydown', handleKeyDown);

    // Initial tip
    setTimeout(() => {
      const tip = document.getElementById('zoomTip');
      if (tip) tip.style.opacity = '1';
    }, 1000);
    
    // Auto-hide tip
    setTimeout(() => {
      const tip = document.getElementById('zoomTip');
      if (tip) tip.style.opacity = '0';
    }, 8000);
  }

  // A11y Controls logic
  function initA11y() {
    const LS_KEY = 'optivox_a11y_prefs';
    let prefs = JSON.parse(localStorage.getItem(LS_KEY) || '{"contrast":false,"font":false}');

    const apply = () => {
      document.body.classList.toggle('a11y-high-contrast', prefs.contrast);
      document.body.classList.toggle('a11y-large-font', prefs.font);
      
      const cBtn = document.getElementById('contrastBtn');
      const fBtn = document.getElementById('fontBtn');
      if (cBtn) cBtn.setAttribute('aria-pressed', prefs.contrast);
      if (fBtn) fBtn.setAttribute('aria-pressed', prefs.font);
      
      localStorage.setItem(LS_KEY, JSON.stringify(prefs));
      
      // Re-clone if a11y changes to reflect styles in magnifier
      contentCloned = false;
      if (isMagnifying) clonePageContent();
    };

    document.getElementById('contrastBtn')?.addEventListener('click', () => {
      prefs.contrast = !prefs.contrast;
      apply();
    });

    document.getElementById('fontBtn')?.addEventListener('click', () => {
      prefs.font = !prefs.font;
      apply();
    });

    apply();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { init(); initA11y(); });
  } else {
    init();
    initA11y();
  }

})();
