const TRACKING_ENDPOINT = 'https://example.com/track';

function sendTrackingEvent(eventName, metadata = {}) {
  if (!TRACKING_ENDPOINT || TRACKING_ENDPOINT === 'https://example.com/track') {
    console.warn('[tracking] Tracking endpoint is not configured. Set TRACKING_ENDPOINT to your backend URL.');
    return;
  }

  const payload = {
    event: eventName,
    page: window.location.pathname,
    timestamp: new Date().toISOString(),
    ...metadata,
  };

  const body = JSON.stringify(payload);

  if (navigator.sendBeacon) {
    navigator.sendBeacon(TRACKING_ENDPOINT, body);
    return;
  }

  fetch(TRACKING_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body,
    keepalive: true,
  }).catch((error) => {
    console.error('[tracking] Failed to send event', error);
  });
}

function initAmmTracking() {
  const downloadLink = document.querySelector('a[download]');
  if (downloadLink) {
    downloadLink.addEventListener('click', () => {
      sendTrackingEvent('amm_working_paper_download');
    });
  }

  sendTrackingEvent('amm_page_view');
}

document.addEventListener('DOMContentLoaded', initAmmTracking);
