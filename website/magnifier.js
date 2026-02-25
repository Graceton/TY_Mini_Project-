/**
 * Optivox Magnifier Module
 * Provides accessible screen magnification functionality
 * with adjustable zoom levels via keyboard shortcuts
 */

(function() {
  'use strict';

  // Configuration
  const config = {
    defaultZoom: 2,
    minZoom: 1.5,
    maxZoom: 5,
    zoomStep: 0.5,
    magnifierSize: 200
  };

  // DOM Elements
  const magnifier = document.getElementById('magnifier');
  const magnifierContent = document.getElementById('magnifierContent');
  
  // State
  let zoomLevel = config.defaultZoom;
  let contentCloned = false;

  /**
   * Clones the page content once for magnification
   */
  function clonePageContent() {
    if (contentCloned) return;
    
    // Clone entire document for magnification
    const bodyClone = document.body.cloneNode(true);
    
    // Remove magnifier elements from clone to avoid recursion
    const elementsToRemove = ['#magnifier', '#zoomTip', '#zoomIndicator'];
    elementsToRemove.forEach(selector => {
      const element = bodyClone.querySelector(selector);
      if (element) element.remove();
    });
    
    // Clear and set content
    magnifierContent.innerHTML = '';
    magnifierContent.appendChild(bodyClone);
    
    // Apply zoom transformation
    magnifierContent.style.transform = `scale(${zoomLevel})`;
    
    contentCloned = true;
  }

  /**
   * Updates the magnifier position based on cursor position
   * @param {number} x - Cursor X coordinate
   * @param {number} y - Cursor Y coordinate
   */
  function updateMagnifierPosition(x, y) {
    // Calculate offset to center the magnified area on cursor
    const offsetX = -(x * zoomLevel - config.magnifierSize / 2);
    const offsetY = -(y * zoomLevel - config.magnifierSize / 2);
    magnifierContent.style.left = `${offsetX}px`;
    magnifierContent.style.top = `${offsetY}px`;
  }

  /**
   * Handles mouse movement to position and update magnifier
   */
  function handleMouseMove(e) {
    const x = e.clientX;
    const y = e.clientY;
    
    // Clone content on first mouse move
    clonePageContent();
    
    // Show and position magnifier circle
    magnifier.style.display = 'block';
    magnifier.style.left = `${x - config.magnifierSize / 2}px`;
    magnifier.style.top = `${y - config.magnifierSize / 2}px`;
    
    // Update magnified content position
    updateMagnifierPosition(x, y);
  }

  /**
   * Handles keyboard shortcuts for zoom control
   */
  function handleKeyDown(e) {
    if (e.ctrlKey || e.metaKey) {
      if (e.key === '+' || e.key === '=') {
        e.preventDefault();
        zoomLevel = Math.min(zoomLevel + config.zoomStep, config.maxZoom);
        magnifierContent.style.transform = `scale(${zoomLevel})`;
        showZoomLevel();
      } else if (e.key === '-' || e.key === '_') {
        e.preventDefault();
        zoomLevel = Math.max(zoomLevel - config.zoomStep, config.minZoom);
        magnifierContent.style.transform = `scale(${zoomLevel})`;
        showZoomLevel();
      }
    }
  }

  /**
   * Displays zoom level indicator
   */
  function showZoomLevel() {
    let indicator = document.getElementById('zoomIndicator');
    
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.id = 'zoomIndicator';
      indicator.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0, 0, 0, 0.95);
        color: #00ffcc;
        padding: 20px 40px;
        border-radius: 15px;
        font-size: 26px;
        font-weight: 700;
        z-index: 999999;
        transition: opacity 0.3s;
        border: 2px solid #00ffcc;
        box-shadow: 0 0 30px rgba(0, 255, 204, 0.5);
      `;
      document.body.appendChild(indicator);
    }
    
    indicator.textContent = `🔍 Magnifier: ${zoomLevel.toFixed(1)}x`;
    indicator.style.opacity = '1';
    
    // Auto-hide after delay
    clearTimeout(indicator.timeout);
    indicator.timeout = setTimeout(() => {
      indicator.style.opacity = '0';
    }, 1200);
  }

  /**
   * Shows initial tip about keyboard shortcuts
   */
  function showInitialTip() {
    const zoomTip = document.createElement('div');
    zoomTip.id = 'zoomTip';
    zoomTip.innerHTML = '💡 <strong>Tip:</strong> Use Ctrl + <strong>+</strong> or <strong>–</strong> to adjust magnifier zoom';
    document.body.appendChild(zoomTip);
    
    setTimeout(() => zoomTip.style.opacity = 1, 600);
    setTimeout(() => zoomTip.style.opacity = 0, 6000);
  }

  /**
   * Initialize magnifier functionality
   */
  function init() {
    // Check if required elements exist
    if (!magnifier || !magnifierContent) {
      console.error('Magnifier elements not found in DOM');
      return;
    }

    // Attach event listeners
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('keydown', handleKeyDown);
    
    // Show initial tip
    showInitialTip();
    
    console.log('Optivox Magnifier initialized successfully');
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();

// === Accessibility Controls ===
document.addEventListener('DOMContentLoaded', () => {
  const contrastBtn = document.getElementById('contrastBtn');
  const fontBtn = document.getElementById('fontBtn');
  const motionBtn = document.getElementById('motionBtn');
  const root = document.documentElement;

  // restore saved states (from localStorage)
  if (localStorage.getItem('highContrast') === 'true')
    document.body.classList.add('a11y-high-contrast');
  if (localStorage.getItem('largeFont') === 'true')
    document.body.classList.add('a11y-large-font');
  if (localStorage.getItem('reducedMotion') === 'true')
    root.style.setProperty('--reduced', '1');

  // toggle High Contrast
  contrastBtn?.addEventListener('click', () => {
    document.body.classList.toggle('a11y-high-contrast');
    const active = document.body.classList.contains('a11y-high-contrast');
    contrastBtn.setAttribute('aria-pressed', active);
    localStorage.setItem('highContrast', active);
  });

  // toggle Large Font
  fontBtn?.addEventListener('click', () => {
    document.body.classList.toggle('a11y-large-font');
    const active = document.body.classList.contains('a11y-large-font');
    fontBtn.setAttribute('aria-pressed', active);
    localStorage.setItem('largeFont', active);
  });

  // toggle Reduced Motion
  motionBtn?.addEventListener('click', () => {
    const reduced = root.style.getPropertyValue('--reduced') === '1';
    root.style.setProperty('--reduced', reduced ? '0' : '1');
    motionBtn.setAttribute('aria-pressed', !reduced);
    localStorage.setItem('reducedMotion', (!reduced).toString());
  });
});

