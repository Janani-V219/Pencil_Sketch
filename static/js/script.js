/**
 * PencilSketch AI - Interactive Frontend Controller
 * Handles image upload, drag-and-drop, OpenCV processing, interactive split comparison slider,
 * style switcher, real-time parameters, and export downloads.
 */

document.addEventListener('DOMContentLoaded', () => {
  // --- Application State ---
  const state = {
    currentFileId: null,
    currentFilename: null,
    currentSketchFilename: null,
    currentStyle: 'graphite',
    intensity: 50,
    darkness: 50,
    detail: 50,
    viewMode: 'slider', // 'slider' | 'side-by-side'
    isProcessing: false,
    sliderPosPct: 50,
  };

  // --- Style Display Names ---
  const styleNames = {
    graphite: 'Realistic Graphite',
    soft: 'Soft Pencil',
    dark: 'Dark Pencil',
    charcoal: 'Charcoal Wash',
    detailed: 'Detailed Sketch',
  };

  // --- DOM Elements ---
  const html = document.documentElement;
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const uploadSection = document.getElementById('uploadSection');
  const studioSection = document.getElementById('studioSection');
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const browseBtn = document.getElementById('browseBtn');
  const presetsGrid = document.getElementById('presetsGrid');

  // Viewer elements
  const comparisonContainer = document.getElementById('comparisonContainer');
  const sketchClipWrapper = document.getElementById('sketchClipWrapper');
  const sliderHandle = document.getElementById('sliderHandle');
  const originalImg = document.getElementById('originalImg');
  const sketchImg = document.getElementById('sketchImg');
  const sideBySideContainer = document.getElementById('sideBySideContainer');
  const sideOriginalImg = document.getElementById('sideOriginalImg');
  const sideSketchImg = document.getElementById('sideSketchImg');
  const processingOverlay = document.getElementById('processingOverlay');
  const processingStepText = document.getElementById('processingStepText');
  const activeStyleBadge = document.getElementById('activeStyleBadge');
  const latencyBadge = document.getElementById('latencyBadge');

  // Controls
  const modeSliderBtn = document.getElementById('modeSliderBtn');
  const modeSideBtn = document.getElementById('modeSideBtn');
  const zoomModalBtn = document.getElementById('zoomModalBtn');
  const styleCards = document.querySelectorAll('.style-card');
  const intensitySlider = document.getElementById('intensitySlider');
  const darknessSlider = document.getElementById('darknessSlider');
  const detailSlider = document.getElementById('detailSlider');
  const intensityVal = document.getElementById('intensityVal');
  const darknessVal = document.getElementById('darknessVal');
  const detailVal = document.getElementById('detailVal');
  const resetSlidersBtn = document.getElementById('resetSlidersBtn');
  const reprocessBtn = document.getElementById('reprocessBtn');
  const resetBtn = document.getElementById('resetBtn');
  const downloadSketchBtn = document.getElementById('downloadSketchBtn');
  const downloadComparisonBtn = document.getElementById('downloadComparisonBtn');

  // Lightbox
  const lightboxModal = document.getElementById('lightboxModal');
  const lightboxBackdrop = document.getElementById('lightboxBackdrop');
  const lightboxClose = document.getElementById('lightboxClose');
  const lightboxImg = document.getElementById('lightboxImg');
  const lightboxCaptionStyle = document.getElementById('lightboxCaptionStyle');
  const lightboxDownloadBtn = document.getElementById('lightboxDownloadBtn');
  const toastContainer = document.getElementById('toastContainer');

  // =========================================================================
  // 1. Theme Management (Light / Dark mode)
  // =========================================================================
  function initTheme() {
    const savedTheme = localStorage.getItem('pencilsketch_theme');
    if (savedTheme) {
      html.setAttribute('data-theme', savedTheme);
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      html.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    }
  }

  themeToggleBtn.addEventListener('click', () => {
    const current = html.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('pencilsketch_theme', next);
    showToast(`Switched to ${next} theme`, 'info');
  });

  initTheme();

  // =========================================================================
  // 2. Toast Notifications
  // =========================================================================
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '⚠️';

    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  // =========================================================================
  // 3. Drag and Drop & File Upload Handling
  // =========================================================================
  browseBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  dropZone.addEventListener('click', () => {
    fileInput.click();
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add('drag-over');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove('drag-over');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  });

  function handleFileUpload(file) {
    // Validate type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      showToast('Please select a valid image file (JPG, PNG, WEBP).', 'error');
      return;
    }

    // Validate size (16MB)
    if (file.size > 16 * 1024 * 1024) {
      showToast('File size exceeds 16MB limit.', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('image', file);

    setProcessingState(true, 'Uploading & validating photo...');

    fetch('/upload', {
      method: 'POST',
      body: formData,
    })
      .then(res => res.json())
      .then(data => {
        if (!data.success) {
          throw new Error(data.error || 'Upload failed');
        }
        onUploadSuccess(data.file_id, data.filename, data.original_url);
      })
      .catch(err => {
        setProcessingState(false);
        showToast(err.message, 'error');
      });
  }

  // =========================================================================
  // 4. Sample Presets Click Handler
  // =========================================================================
  presetsGrid.addEventListener('click', (e) => {
    const card = e.target.closest('.preset-card');
    if (!card) return;

    const presetId = card.getAttribute('data-preset');
    if (!presetId) return;

    setProcessingState(true, `Loading sample preset: ${presetId}...`);

    const formData = new FormData();
    formData.append('preset_id', presetId);

    fetch('/upload', {
      method: 'POST',
      body: formData,
    })
      .then(res => res.json())
      .then(data => {
        if (!data.success) {
          throw new Error(data.error || 'Preset failed to load');
        }
        onUploadSuccess(data.file_id, data.filename, data.original_url);
      })
      .catch(err => {
        setProcessingState(false);
        showToast(err.message, 'error');
      });
  });

  function onUploadSuccess(fileId, filename, originalUrl) {
    state.currentFileId = fileId;
    state.currentFilename = filename;
    state.isProcessing = false; // Reset processing flag after upload completes

    // Load original image into DOM
    originalImg.src = originalUrl;
    sideOriginalImg.src = originalUrl;

    // Switch view
    uploadSection.style.display = 'none';
    studioSection.style.display = 'block';

    // Synchronize widths when image loads
    originalImg.onload = () => {
      syncImageDimensions();
    };

    // Trigger initial sketch generation
    requestSketchProcess();
  }

  function syncImageDimensions() {
    // Ensure the sketch image overlay matches original container width & height
    const rect = originalImg.getBoundingClientRect();
    if (rect.width > 0) {
      sketchImg.style.width = `${rect.width}px`;
      sketchImg.style.height = `${rect.height}px`;
    }
  }

  window.addEventListener('resize', () => {
    if (state.currentFileId) {
      syncImageDimensions();
    }
  });

  // =========================================================================
  // 5. Sketch Generation Engine (POST /process)
  // =========================================================================
  function requestSketchProcess() {
    if (!state.currentFileId || state.isProcessing) return;

    setProcessingState(true, 'Synthesizing pencil strokes...');

    const payload = {
      file_id: state.currentFileId,
      style: state.currentStyle,
      intensity: state.intensity,
      darkness: state.darkness,
      detail: state.detail,
    };

    const startTime = performance.now();

    fetch('/process', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
      .then(res => res.json())
      .then(data => {
        if (!data.success) {
          throw new Error(data.error || 'Sketch processing failed');
        }

        state.currentSketchFilename = data.filename;
        const sketchUrl = `${data.sketch_url}?t=${Date.now()}`;

        // Set listeners before updating src
        sketchImg.onload = () => {
          syncImageDimensions();
          setProcessingState(false);
        };
        sketchImg.onerror = () => {
          setProcessingState(false);
          showToast('Image display error, please retry.', 'error');
        };

        // Update image sources
        sketchImg.src = sketchUrl;
        sideSketchImg.src = sketchUrl;
        lightboxImg.src = sketchUrl;

        // Fallback safety timeout if image is already cached or load event is delayed
        setTimeout(() => {
          if (state.isProcessing) {
            syncImageDimensions();
            setProcessingState(false);
          }
        }, 1200);

        // Update badges
        activeStyleBadge.textContent = styleNames[state.currentStyle] || 'Custom Sketch';
        latencyBadge.textContent = `⚡ ${data.processing_time_ms}ms`;
        lightboxCaptionStyle.textContent = `${styleNames[state.currentStyle]} Sketch (${data.processing_time_ms}ms)`;

        showToast(`Created ${styleNames[state.currentStyle]} sketch!`, 'success');
      })
      .catch(err => {
        setProcessingState(false);
        showToast(err.message, 'error');
      });
  }

  function setProcessingState(processing, stepText = '') {
    state.isProcessing = processing;
    if (processing) {
      processingOverlay.style.display = 'flex';
      processingStepText.textContent = stepText;
    } else {
      processingOverlay.style.display = 'none';
    }
  }

  // =========================================================================
  // 6. Interactive Before / After Split Slider
  // =========================================================================
  let isDraggingSlider = false;

  function updateSliderPosition(clientX) {
    const rect = comparisonContainer.getBoundingClientRect();
    let offsetX = clientX - rect.left;
    let pct = (offsetX / rect.width) * 100;

    // Clamp between 2% and 98%
    pct = Math.max(2, Math.min(98, pct));
    state.sliderPosPct = pct;

    sketchClipWrapper.style.width = `${pct}%`;
    sliderHandle.style.left = `${pct}%`;
  }

  // Mouse events
  comparisonContainer.addEventListener('mousedown', (e) => {
    isDraggingSlider = true;
    sliderHandle.classList.add('dragging');
    updateSliderPosition(e.clientX);
  });

  window.addEventListener('mousemove', (e) => {
    if (!isDraggingSlider) return;
    updateSliderPosition(e.clientX);
  });

  window.addEventListener('mouseup', () => {
    if (isDraggingSlider) {
      isDraggingSlider = false;
      sliderHandle.classList.remove('dragging');
    }
  });

  // Touch events for mobile & tablet
  comparisonContainer.addEventListener('touchstart', (e) => {
    if (e.touches.length === 1) {
      isDraggingSlider = true;
      sliderHandle.classList.add('dragging');
      updateSliderPosition(e.touches[0].clientX);
    }
  }, { passive: true });

  window.addEventListener('touchmove', (e) => {
    if (!isDraggingSlider || e.touches.length === 0) return;
    updateSliderPosition(e.touches[0].clientX);
  }, { passive: true });

  window.addEventListener('touchend', () => {
    if (isDraggingSlider) {
      isDraggingSlider = false;
      sliderHandle.classList.remove('dragging');
    }
  });

  // =========================================================================
  // 7. View Mode Switcher (Split Slider vs Side-by-Side)
  // =========================================================================
  modeSliderBtn.addEventListener('click', () => {
    state.viewMode = 'slider';
    modeSliderBtn.classList.add('active');
    modeSideBtn.classList.remove('active');
    comparisonContainer.style.display = 'block';
    sideBySideContainer.style.display = 'none';
    syncImageDimensions();
  });

  modeSideBtn.addEventListener('click', () => {
    state.viewMode = 'side-by-side';
    modeSideBtn.classList.add('active');
    modeSliderBtn.classList.remove('active');
    comparisonContainer.style.display = 'none';
    sideBySideContainer.style.display = 'grid';
  });

  // =========================================================================
  // 8. Style Cards Selection
  // =========================================================================
  styleCards.forEach(card => {
    card.addEventListener('click', () => {
      const selectedStyle = card.getAttribute('data-style');
      if (selectedStyle === state.currentStyle) return;

      styleCards.forEach(c => c.classList.remove('active'));
      card.classList.add('active');

      const radio = card.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;

      state.currentStyle = selectedStyle;
      requestSketchProcess();
    });
  });

  // =========================================================================
  // 9. Fine-Tuning Parameter Sliders
  // =========================================================================
  intensitySlider.addEventListener('input', (e) => {
    state.intensity = parseInt(e.target.value);
    intensityVal.textContent = state.intensity;
  });

  darknessSlider.addEventListener('input', (e) => {
    state.darkness = parseInt(e.target.value);
    darknessVal.textContent = state.darkness;
  });

  detailSlider.addEventListener('input', (e) => {
    state.detail = parseInt(e.target.value);
    detailVal.textContent = state.detail;
  });

  // Apply button
  reprocessBtn.addEventListener('click', () => {
    requestSketchProcess();
  });

  // Reset Sliders button
  resetSlidersBtn.addEventListener('click', () => {
    state.intensity = 50;
    state.darkness = 50;
    state.detail = 50;
    intensitySlider.value = 50;
    darknessSlider.value = 50;
    detailSlider.value = 50;
    intensityVal.textContent = '50';
    darknessVal.textContent = '50';
    detailVal.textContent = '50';
    requestSketchProcess();
  });

  // =========================================================================
  // 10. Downloads & Reset
  // =========================================================================
  downloadSketchBtn.addEventListener('click', () => {
    if (!state.currentSketchFilename) {
      showToast('No sketch available to download.', 'error');
      return;
    }
    const downloadUrl = `/download?filename=${encodeURIComponent(state.currentSketchFilename)}&mode=sketch`;
    window.location.href = downloadUrl;
    showToast('Downloading high-resolution sketch PNG...', 'success');
  });

  downloadComparisonBtn.addEventListener('click', () => {
    if (!state.currentSketchFilename) {
      showToast('No sketch available to generate comparison.', 'error');
      return;
    }
    const downloadUrl = `/download?filename=${encodeURIComponent(state.currentSketchFilename)}&mode=comparison`;
    window.location.href = downloadUrl;
    showToast('Generating side-by-side comparison graphic...', 'success');
  });

  resetBtn.addEventListener('click', () => {
    state.currentFileId = null;
    state.currentFilename = null;
    state.currentSketchFilename = null;
    fileInput.value = '';
    studioSection.style.display = 'none';
    uploadSection.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // =========================================================================
  // 11. Lightbox Modal
  // =========================================================================
  zoomModalBtn.addEventListener('click', () => {
    if (!sketchImg.src) return;
    lightboxModal.style.display = 'flex';
  });

  function closeLightbox() {
    lightboxModal.style.display = 'none';
  }

  lightboxClose.addEventListener('click', closeLightbox);
  lightboxBackdrop.addEventListener('click', closeLightbox);

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && lightboxModal.style.display === 'flex') {
      closeLightbox();
    }
  });

  lightboxDownloadBtn.addEventListener('click', () => {
    downloadSketchBtn.click();
  });
});
