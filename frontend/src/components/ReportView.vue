<template>
  <div class="report-view" ref="containerRef">
    <iframe ref="iframeRef" :src="reportUrl" frameborder="0" class="report-iframe" @load="patchReportStyles"></iframe>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import apiClient from '../api/axios';

const props = defineProps({
  runId: String,
});

const iframeRef = ref(null);
const containerRef = ref(null);

const reportUrl = computed(() => {
  // Construct the full URL to the report endpoint
  return `${apiClient.defaults.baseURL}/runs/${props.runId}/report`;
});

// Resize iframe to match content height
const resizeIframe = () => {
  try {
    const iframe = iframeRef.value;
    if (!iframe || !iframe.contentDocument) return;

    const iframeDoc = iframe.contentDocument;
    const body = iframeDoc.body;
    const html = iframeDoc.documentElement;

    // Get the full content height
    const height = Math.max(
      body.scrollHeight,
      body.offsetHeight,
      html.clientHeight,
      html.scrollHeight,
      html.offsetHeight
    );

    // Set iframe height to content height
    iframe.style.height = height + 'px';
  } catch (e) {
    console.error('Failed to resize iframe:', e);
  }
};

// Patch the report iframe with updated styles
const patchReportStyles = () => {
  try {
    const iframe = iframeRef.value;
    if (!iframe || !iframe.contentDocument) return;

    const iframeDoc = iframe.contentDocument;
    const head = iframeDoc.head;

    // Check if already patched
    const existingPatch = iframeDoc.getElementById('myquant-patch-styles');
    if (existingPatch) {
      console.log('Report already patched, skipping');
      return;
    }

    // Create style element with updated table and UI styles
    const styleEl = iframeDoc.createElement('style');
    styleEl.id = 'myquant-patch-styles';
    styleEl.textContent = `
      /* Enhanced Table Styles for Dark Mode */
      body:not(.dark-mode) table {
        background-color: white !important;
        color: #2c3e50 !important;
      }

      body.dark-mode table {
        background-color: #242830 !important;
        color: #e4e6eb !important;
      }

      body:not(.dark-mode) table th {
        background-color: #f8fafc !important;
        color: #64748b !important;
      }

      body.dark-mode table th {
        background-color: #2d3139 !important;
        color: #94a3b8 !important;
      }

      body:not(.dark-mode) table td {
        background-color: white !important;
        color: #2c3e50 !important;
        border-bottom: 1px solid #e2e8f0;
      }

      body.dark-mode table td {
        background-color: #242830 !important;
        color: #e4e6eb !important;
        border-bottom: 1px solid #3d4451;
      }

      body:not(.dark-mode) table tbody tr:nth-child(even) td {
        background-color: #f8fafc !important;
      }

      body.dark-mode table tbody tr:nth-child(even) td {
        background-color: #2d3139 !important;
      }

      body:not(.dark-mode) table tbody tr:hover td {
        background-color: #f1f5f9 !important;
      }

      body.dark-mode table tbody tr:hover td {
        background-color: #353945 !important;
      }

      /* Ensure consistent font colors in tables */
      body.dark-mode table td,
      body.dark-mode table th,
      body.dark-mode table span,
      body.dark-mode table div {
        color: inherit;
      }

      /* Keep colored values visible */
      body.dark-mode .positive {
        color: #ef4444 !important;
      }

      body.dark-mode .negative {
        color: #10b981 !important;
      }

      /* Fix any inline styles that might override */
      body.dark-mode table td[style*="background"],
      body.dark-mode table th[style*="background"] {
        background-color: inherit !important;
      }

      /* Hide theme toggle button visually but keep it functional */
      .theme-toggle {
        position: absolute !important;
        left: -9999px !important;
        opacity: 0 !important;
        pointer-events: none !important;
      }

      /* Remove all scrollbars from iframe content */
      html, body {
        overflow: hidden !important;
        height: auto !important;
        margin: 0 !important;
        padding: 0 !important;
      }

      /* Ensure container doesn't create scrollbars */
      .container {
        overflow: visible !important;
        max-width: 100% !important;
      }

      /* Limit code snapshot height */
      .snapshots-container pre {
        max-height: 500px !important;
        overflow: auto !important;
      }

      /* Code block scrollbar for light mode */
      body:not(.dark-mode) .snapshots-container pre::-webkit-scrollbar {
        width: 8px;
        height: 8px;
      }

      body:not(.dark-mode) .snapshots-container pre::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 4px;
      }

      body:not(.dark-mode) .snapshots-container pre::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 4px;
      }

      body:not(.dark-mode) .snapshots-container pre::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
      }

      /* Code block scrollbar for dark mode */
      body.dark-mode .snapshots-container pre::-webkit-scrollbar {
        width: 8px;
        height: 8px;
      }

      body.dark-mode .snapshots-container pre::-webkit-scrollbar-track {
        background: #2d3139;
        border-radius: 4px;
      }

      body.dark-mode .snapshots-container pre::-webkit-scrollbar-thumb {
        background: #4a5568;
        border-radius: 4px;
      }

      body.dark-mode .snapshots-container pre::-webkit-scrollbar-thumb:hover {
        background: #718096;
      }

      /* Code block background colors */
      body:not(.dark-mode) .snapshots-container pre.hljs {
        background: #f8fafc !important;
      }

      body.dark-mode .snapshots-container pre.hljs {
        background: #1e1e1e !important;
      }

      /* Chart Container Styling - Match Monitoring Page */
      .chart-container,
      .chart-container-placeholder {
        background-color: var(--table-header-bg);
        border-radius: 6px;
      }

      /* Light mode chart backgrounds */
      body:not(.dark-mode) .chart-container,
      body:not(.dark-mode) .chart-container-placeholder {
        background-color: #f8fafc !important;
      }

      /* Dark mode chart backgrounds */
      body.dark-mode .chart-container,
      body.dark-mode .chart-container-placeholder {
        background-color: #2d3139 !important;
      }

      /* Fix ECharts background by injecting into canvas parent */
      body:not(.dark-mode) #equity-chart,
      body:not(.dark-mode) #intraday-chart {
        background-color: #f8fafc !important;
        border-radius: 6px;
      }

      body.dark-mode #equity-chart,
      body.dark-mode #intraday-chart {
        background-color: #2d3139 !important;
        border-radius: 6px;
      }
    `;

    // Append to head (will be last, highest priority)
    head.appendChild(styleEl);
    console.log('Patch styles applied to report iframe');

    // Patch the title to remove "QTrader" prefix
    patchReportTitle(iframeDoc);

    // Wait a bit for iframe content to fully load, then sync theme
    setTimeout(() => {
      syncThemeToIframe();
    }, 200);

    // Resize iframe to fit content
    resizeIframe();

    // Watch for content changes and resize
    const resizeObserver = new ResizeObserver(() => {
      resizeIframe();
    });
    resizeObserver.observe(iframeDoc.body);

    // Store observer for cleanup
    iframe._resizeObserver = resizeObserver;
  } catch (e) {
    console.error('Failed to patch report styles:', e);
  }
};

// Patch the report title to remove "QTrader" prefix
const patchReportTitle = (iframeDoc) => {
  try {
    const titleElement = iframeDoc.getElementById('main-title');
    if (titleElement) {
      const currentTitle = titleElement.textContent;
      // Remove "QTrader " prefix if it exists
      if (currentTitle.startsWith('QTrader ')) {
        const newTitle = currentTitle.replace(/^QTrader\s+/, '');
        titleElement.textContent = newTitle;
      }
    }

    // Also update document title
    const docTitle = iframeDoc.title;
    if (docTitle.startsWith('QTrader - ')) {
      iframeDoc.title = docTitle.replace(/^QTrader - /, '');
    }
  } catch (e) {
    console.error('Failed to patch report title:', e);
  }
};

// Force Chrome/Edge to redraw scrollbars
const forceScrollbarRedraw = (iframe) => {
  try {
    const iframeWin = iframe.contentWindow;
    const iframeDoc = iframe.contentDocument;
    const iframeHtml = iframeDoc.documentElement;

    // Save current scroll position
    const scrollTop = iframeHtml.scrollTop || iframeDoc.body.scrollTop;
    const scrollLeft = iframeHtml.scrollLeft || iframeDoc.body.scrollLeft;

    // Method 1: Toggle overflow
    iframeHtml.style.overflow = 'hidden';
    iframeDoc.body.style.overflow = 'hidden';

    // Force immediate reflow
    void iframeHtml.offsetHeight;

    // Restore overflow
    iframeHtml.style.overflow = '';
    iframeDoc.body.style.overflow = '';

    // Method 2: Tiny iframe resize to force complete repaint
    const currentWidth = iframe.style.width;
    iframe.style.width = 'calc(100% - 1px)';

    // Force immediate reflow
    void iframe.offsetHeight;

    iframe.style.width = currentWidth || '100%';

    // Method 3: Trigger resize event (forces scrollbar recalculation)
    setTimeout(() => {
      if (iframeWin) {
        iframeWin.dispatchEvent(new Event('resize'));
      }

      // Restore scroll position
      if (scrollTop > 0 || scrollLeft > 0) {
        iframeHtml.scrollTop = scrollTop;
        iframeHtml.scrollLeft = scrollLeft;
      }
    }, 10);
  } catch (e) {
    console.error('Failed to force scrollbar redraw:', e);
  }
};

// Patch code highlighting theme based on dark mode
const patchCodeHighlighting = (iframeDoc) => {
  try {
    const isDarkMode = document.body.classList.contains('dark-mode');
    const lightThemeLink = iframeDoc.getElementById('hljs-light-theme');
    const darkThemeLink = iframeDoc.getElementById('hljs-dark-theme');

    if (lightThemeLink && darkThemeLink) {
      if (isDarkMode) {
        lightThemeLink.disabled = true;
        darkThemeLink.disabled = false;
      } else {
        lightThemeLink.disabled = false;
        darkThemeLink.disabled = true;
      }
    }
  } catch (e) {
    console.error('Failed to patch code highlighting:', e);
  }
};

// Trigger iframe's internal theme toggle button
const triggerIframeThemeToggle = (iframeDoc) => {
  try {
    // Find and click the theme toggle button inside iframe
    const themeToggleBtn = iframeDoc.querySelector('.theme-toggle');
    if (themeToggleBtn) {
      themeToggleBtn.click();
      console.log('Clicked iframe theme toggle button');
    } else {
      console.warn('Theme toggle button not found in iframe');
    }
  } catch (e) {
    console.error('Failed to trigger iframe theme toggle:', e);
  }
};

// Sync theme from parent body to iframe
const syncThemeToIframe = () => {
  try {
    const iframe = iframeRef.value;
    if (!iframe || !iframe.contentDocument) return;

    const iframeBody = iframe.contentDocument.body;
    const parentBody = document.body;

    const isDarkMode = parentBody.classList.contains('dark-mode');
    const iframeHasDarkMode = iframeBody.classList.contains('dark-mode');

    // Only trigger if there's a change
    if (isDarkMode !== iframeHasDarkMode) {
      console.log(`Theme mismatch detected. Parent: ${isDarkMode ? 'dark' : 'light'}, Iframe: ${iframeHasDarkMode ? 'dark' : 'light'}`);
      // Trigger the iframe's internal theme toggle button
      triggerIframeThemeToggle(iframe.contentDocument);
    }
  } catch (e) {
    console.error('Failed to sync theme to iframe:', e);
  }
};

// Watch for theme changes in parent document
const themeObserver = new MutationObserver(() => {
  syncThemeToIframe();
});

onMounted(() => {
  // Observe theme changes on parent body
  themeObserver.observe(document.body, {
    attributes: true,
    attributeFilter: ['class']
  });
});

onBeforeUnmount(() => {
  themeObserver.disconnect();
});
</script>

<style scoped>
.report-view {
  width: 100%;
  height: 100%;
  overflow: auto;
}

.report-iframe {
  width: 100%;
  height: 100%;
  border: none;
}
</style>