/* ═══════════════════════════════════════════════════════════════════════════════
   Echo — Dashboard Application Logic
   Auth guard, view routing, interactive audio waveform visualizer with cursor/gyro
   reactivity, profile management, emergency contact pairing, and WebSocket telemetry.
   ═══════════════════════════════════════════════════════════════════════════════ */

// ── Auth Guard ─────────────────────────────────────────────────────────────────

const TOKEN = localStorage.getItem('echo_token');
const USER = JSON.parse(localStorage.getItem('echo_user') || '{}');

if (!TOKEN) {
  window.location.href = '/';
}

function authHeaders() {
  return { 'Authorization': `Bearer ${TOKEN}`, 'Content-Type': 'application/json' };
}

function logout() {
  localStorage.removeItem('echo_token');
  localStorage.removeItem('echo_user');
  window.location.href = '/';
}

// ── View Router ────────────────────────────────────────────────────────────────

const views = ['home', 'meter', 'profile', 'contacts', 'integrations'];
let currentView = 'home';

function switchView(viewName) {
  if (!views.includes(viewName)) return;
  currentView = viewName;

  // Update nav
  document.querySelectorAll('.nav-item[data-view]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.view === viewName);
  });

  // Show/hide views
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  const target = document.getElementById('view' + viewName.charAt(0).toUpperCase() + viewName.slice(1));
  if (target) {
    target.classList.add('active');
    // Re-trigger animation
    target.style.animation = 'none';
    target.offsetHeight; // force reflow
    target.style.animation = '';
  }

  // Initialize view-specific logic
  if (viewName === 'profile') loadProfile();
  if (viewName === 'contacts') loadContacts();
  if (viewName === 'meter') initMeterCanvas();
}

// ── WebSocket Telemetry ────────────────────────────────────────────────────────

let ws = null;
let wsReconnectTimer = null;
let latestPacket = null;

function connectWebSocket() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${location.host}/ws/telemetry?token=${TOKEN}`);

  ws.onopen = () => {
    document.getElementById('connectionStatus').textContent = 'LIVE STREAM';
    document.getElementById('pulseDot').classList.remove('disconnected');
  };

  ws.onmessage = (event) => {
    try {
      latestPacket = JSON.parse(event.data);
      if (latestPacket.event === 'CONTACT_VERIFIED') {
        loadContacts();
      }
      handleTelemetryPacket(latestPacket);
    } catch (e) { /* ignore parse errors */ }
  };

  ws.onclose = () => {
    document.getElementById('connectionStatus').textContent = 'Reconnecting...';
    document.getElementById('pulseDot').classList.add('disconnected');
    wsReconnectTimer = setTimeout(connectWebSocket, 2000);
  };

  ws.onerror = () => { ws.close(); };
}

// ── Telemetry Packet Handler ───────────────────────────────────────────────────

function handleTelemetryPacket(p) {
  // Update uptime
  if (p.chunk_index) {
    const secs = Math.floor(p.chunk_index * 0.975);
    const h = String(Math.floor(secs / 3600)).padStart(2, '0');
    const m = String(Math.floor((secs % 3600) / 60)).padStart(2, '0');
    const s = String(secs % 60).padStart(2, '0');
    document.getElementById('systemUptime').textContent = `${h}:${m}:${s}`;
  }

  // Feed waveform data
  waveformData.push(p.mic_rms || 0);
  if (waveformData.length > waveformMaxPoints) waveformData.shift();

  // Sync mic toggle UI state
  if (typeof p.mic_enabled === 'boolean') {
    const cb = el('micCheckbox');
    const lbl = el('micLabel');
    if (cb) cb.checked = p.mic_enabled;
    if (lbl) lbl.textContent = p.mic_enabled ? 'Listening' : 'Paused';
  }

  // Home view stats
  const el = (id) => document.getElementById(id);
  if (el('homeMicRms')) el('homeMicRms').textContent = (p.mic_rms || 0).toFixed(4);
  if (el('homeTopClass')) el('homeTopClass').textContent = (p.top_prediction?.class_name || 'Silence').substring(0, 18);
  if (el('homeConfidence')) el('homeConfidence').textContent = ((p.top_prediction?.confidence || 0) * 100).toFixed(1) + '%';
  if (el('homeAlertState')) {
    el('homeAlertState').textContent = p.alert_state || 'NORMAL';
    el('homeAlertState').style.color = p.alert_state === 'CRITICAL' ? '#e74c3c' : p.alert_state === 'WARNING' ? '#f39c12' : '#27ae60';
  }
  if (el('homeChunks')) el('homeChunks').textContent = p.chunk_index || 0;
  if (el('homeSuppressed')) el('homeSuppressed').textContent = p.firewall?.suppressed_total || 0;
  if (el('homeThreats')) el('homeThreats').textContent = p.firewall?.confirmed_total || 0;

  // Buffer slots
  if (p.temporal_buffer) {
    const slots = document.querySelectorAll('#homeBufferSlots .buffer-slot');
    p.temporal_buffer.forEach((item, i) => {
      if (slots[i]) {
        slots[i].textContent = item.class_name ? item.class_name.substring(0, 8) : (i + 1);
        slots[i].className = 'buffer-slot';
        if (item.is_suppressed) slots[i].classList.add('suppressed');
        else if (item.is_target) slots[i].classList.add('hazard');
        else if (item.confidence > 0.5) slots[i].classList.add('active');
      }
    });
  }

  // Gate badge
  const gateBadge = el('homeGateBadge');
  if (gateBadge) {
    gateBadge.textContent = `Gate: ${p.alert_state || 'CLEAR'}`;
    gateBadge.className = 'buffer-gate-badge';
    if (p.alert_state === 'CRITICAL') gateBadge.classList.add('critical');
    else if (p.alert_state === 'WARNING') gateBadge.classList.add('warning');
  }

  // Hazard banner
  const banner = el('homeHazardBanner');
  if (banner) {
    if (p.active_hazard && p.alert_state !== 'NORMAL') {
      banner.style.display = 'flex';
      el('hazardTitle').textContent = p.active_hazard.tier || 'HAZARD';
      el('hazardDetail').textContent = `${p.active_hazard.class_name} — ${((p.active_hazard.max_confidence || 0) * 100).toFixed(0)}% confidence`;
    } else {
      banner.style.display = 'none';
    }
  }

  // Meter view stats
  if (el('meterDbfs')) el('meterDbfs').textContent = (p.mic_dbfs || -Infinity).toFixed(1) + ' dB';
  if (el('meterSpkRms')) el('meterSpkRms').textContent = (p.spk_rms || 0).toFixed(4);
  if (el('meterXCorr')) el('meterXCorr').textContent = (p.firewall?.cross_correlation || 0).toFixed(3);
  if (el('meterFirewall')) {
    const suppressed = p.firewall?.is_suppressed;
    el('meterFirewall').textContent = suppressed ? 'SUPPRESSED' : 'CLEAR';
    el('meterFirewall').style.color = suppressed ? '#e74c3c' : '#27ae60';
  }

  // Integrations view
  if (el('intSuppressed')) el('intSuppressed').textContent = p.firewall?.suppressed_total || 0;
  if (el('intConfirmed')) el('intConfirmed').textContent = p.firewall?.confirmed_total || 0;

  // Telegram state
  const tg = p.agent_state?.telegram;
  if (tg) {
    if (el('tgBotMode')) el('tgBotMode').textContent = tg.mock_mode ? 'MOCK' : 'LIVE';
    if (el('tgVerifiedCount')) el('tgVerifiedCount').textContent = (tg.configured_chats || []).length;
    if (el('tgActiveAlert')) {
      el('tgActiveAlert').textContent = tg.active_alert ? `${tg.active_alert.hazard_type} (${tg.active_alert.status})` : 'None';
    }
  }
}

// ── Interactive Audio Waveform Visualizer ───────────────────────────────────────

const waveformData = [];
const waveformMaxPoints = 128;
let cursorX = -1, cursorY = -1;
let gyroX = 0, gyroY = 0;
let animFrameId = null;

function initWaveformCanvas() {
  const canvas = document.getElementById('waveformCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }
  resize();
  window.addEventListener('resize', resize);

  // Cursor tracking
  canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    cursorX = e.clientX - rect.left;
    cursorY = e.clientY - rect.top;
  });
  canvas.addEventListener('mouseleave', () => { cursorX = -1; cursorY = -1; });

  // Gyroscope support
  if (window.DeviceOrientationEvent) {
    window.addEventListener('deviceorientation', (e) => {
      gyroX = (e.gamma || 0) / 90; // -1 to 1
      gyroY = (e.beta || 0) / 180;  // -1 to 1
    });
  }

  function draw() {
    const w = canvas.width / window.devicePixelRatio;
    const h = canvas.height / window.devicePixelRatio;

    // Clear with warm background
    ctx.fillStyle = '#ddd7cd';
    ctx.fillRect(0, 0, w, h);

    const barCount = waveformData.length || 1;
    const barWidth = w / waveformMaxPoints;
    const centerY = h / 2 + gyroY * 30; // Gyro shifts baseline

    // Draw waveform bars
    for (let i = 0; i < waveformData.length; i++) {
      const amplitude = Math.min(waveformData[i] * 800, h * 0.45);
      const x = i * barWidth + barWidth / 2;

      // Cursor repulsion effect
      let distortion = 0;
      if (cursorX > 0) {
        const dist = Math.abs(x - cursorX);
        if (dist < 80) {
          distortion = (1 - dist / 80) * 25 * (cursorY < centerY ? -1 : 1);
        }
      }

      // Gyro-based horizontal offset
      const gyroOffset = gyroX * 15;

      const barH = Math.max(amplitude + distortion, 2);
      const bx = x + gyroOffset;

      // Color gradient based on amplitude
      const intensity = Math.min(amplitude / (h * 0.3), 1);
      const r = Math.floor(78 + intensity * 177);  // teal -> coral
      const g = Math.floor(205 - intensity * 140);
      const b = Math.floor(196 - intensity * 130);

      ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.8)`;
      ctx.beginPath();
      ctx.roundRect(bx - barWidth * 0.35, centerY - barH, barWidth * 0.7, barH * 2, 4);
      ctx.fill();

      // Subtle glow for high amplitude
      if (intensity > 0.5) {
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.15)`;
        ctx.beginPath();
        ctx.roundRect(bx - barWidth * 0.5, centerY - barH * 1.2, barWidth, barH * 2.4, 6);
        ctx.fill();
      }
    }

    // Center line
    ctx.strokeStyle = 'rgba(44, 62, 80, 0.08)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(w, centerY);
    ctx.stroke();

    // Cursor crosshair glow
    if (cursorX > 0 && cursorY > 0) {
      const grad = ctx.createRadialGradient(cursorX, cursorY, 0, cursorX, cursorY, 60);
      grad.addColorStop(0, 'rgba(78, 205, 196, 0.15)');
      grad.addColorStop(1, 'rgba(78, 205, 196, 0)');
      ctx.fillStyle = grad;
      ctx.fillRect(cursorX - 60, cursorY - 60, 120, 120);
    }

    animFrameId = requestAnimationFrame(draw);
  }

  draw();
}

// Meter canvas (full-screen variant)
function initMeterCanvas() {
  const canvas = document.getElementById('meterCanvas');
  if (!canvas || canvas._initialized) return;
  canvas._initialized = true;
  const ctx = canvas.getContext('2d');

  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }
  resize();
  window.addEventListener('resize', resize);

  let mCursorX = -1, mCursorY = -1;
  canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    mCursorX = e.clientX - rect.left;
    mCursorY = e.clientY - rect.top;
  });
  canvas.addEventListener('mouseleave', () => { mCursorX = -1; mCursorY = -1; });

  function drawMeter() {
    const w = canvas.width / window.devicePixelRatio;
    const h = canvas.height / window.devicePixelRatio;

    ctx.fillStyle = '#ddd7cd';
    ctx.fillRect(0, 0, w, h);

    const barWidth = w / waveformMaxPoints;
    const centerY = h / 2 + gyroY * 50;

    for (let i = 0; i < waveformData.length; i++) {
      const amplitude = Math.min(waveformData[i] * 1200, h * 0.48);
      const x = i * barWidth + barWidth / 2;

      let distortion = 0;
      if (mCursorX > 0) {
        const dist = Math.abs(x - mCursorX);
        if (dist < 120) {
          distortion = (1 - dist / 120) * 40 * (mCursorY < centerY ? -1 : 1);
        }
      }

      const barH = Math.max(amplitude + distortion, 3);
      const bx = x + gyroX * 25;
      const intensity = Math.min(amplitude / (h * 0.25), 1);

      const r = Math.floor(78 + intensity * 177);
      const g = Math.floor(205 - intensity * 140);
      const b = Math.floor(196 - intensity * 130);

      ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.85)`;
      ctx.beginPath();
      ctx.roundRect(bx - barWidth * 0.4, centerY - barH, barWidth * 0.8, barH * 2, 5);
      ctx.fill();

      if (intensity > 0.4) {
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.1)`;
        ctx.beginPath();
        ctx.roundRect(bx - barWidth * 0.6, centerY - barH * 1.3, barWidth * 1.2, barH * 2.6, 8);
        ctx.fill();
      }
    }

    ctx.strokeStyle = 'rgba(44, 62, 80, 0.06)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(w, centerY);
    ctx.stroke();

    if (mCursorX > 0) {
      const grad = ctx.createRadialGradient(mCursorX, mCursorY, 0, mCursorX, mCursorY, 90);
      grad.addColorStop(0, 'rgba(78, 205, 196, 0.12)');
      grad.addColorStop(1, 'rgba(78, 205, 196, 0)');
      ctx.fillStyle = grad;
      ctx.fillRect(mCursorX - 90, mCursorY - 90, 180, 180);
    }

    requestAnimationFrame(drawMeter);
  }
  drawMeter();
}

// ── Profile Management ─────────────────────────────────────────────────────────

async function loadProfile() {
  try {
    const res = await fetch('/api/auth/me', { headers: authHeaders() });
    const data = await res.json();
    if (data.user) {
      document.getElementById('profileDisplayName').value = data.user.display_name || '';
      document.getElementById('profileEmail').value = data.user.email || '';
      document.getElementById('profileLocation').value = data.settings?.location || '';
      document.getElementById('prefNotifications').checked = data.settings?.notifications_enabled !== false;
    }
  } catch (e) { /* ignore */ }
}

async function saveProfile() {
  const msg = document.getElementById('profileMessage');
  try {
    const res = await fetch('/api/profile', {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify({
        display_name: document.getElementById('profileDisplayName').value,
        email: document.getElementById('profileEmail').value,
        location: document.getElementById('profileLocation').value,
      }),
    });
    if (res.ok) {
      msg.textContent = 'Profile updated successfully!';
      msg.className = 'form-message success';
    } else {
      const d = await res.json();
      msg.textContent = d.detail || 'Update failed';
      msg.className = 'form-message error';
    }
  } catch (e) {
    msg.textContent = 'Network error';
    msg.className = 'form-message error';
  }
  setTimeout(() => { msg.className = 'form-message'; }, 3000);
}

async function changePassword() {
  const msg = document.getElementById('passwordMessage');
  const oldPw = document.getElementById('profileOldPassword').value;
  const newPw = document.getElementById('profileNewPassword').value;
  if (!oldPw || !newPw) { msg.textContent = 'Both fields required'; msg.className = 'form-message error'; return; }

  try {
    const res = await fetch('/api/profile/password', {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify({ old_password: oldPw, new_password: newPw }),
    });
    if (res.ok) {
      msg.textContent = 'Password changed!';
      msg.className = 'form-message success';
      document.getElementById('profileOldPassword').value = '';
      document.getElementById('profileNewPassword').value = '';
    } else {
      const d = await res.json();
      msg.textContent = d.detail || 'Failed';
      msg.className = 'form-message error';
    }
  } catch (e) {
    msg.textContent = 'Network error';
    msg.className = 'form-message error';
  }
  setTimeout(() => { msg.className = 'form-message'; }, 3000);
}

// ── Emergency Contacts ─────────────────────────────────────────────────────────

async function loadContacts() {
  try {
    const res = await fetch('/api/contacts', { headers: authHeaders() });
    const data = await res.json();
    renderContacts(data.contacts || []);

    // Update home view contact count
    const verified = (data.contacts || []).filter(c => c.status === 'VERIFIED').length;
    const el = document.getElementById('homeContacts');
    if (el) el.textContent = verified;
  } catch (e) { /* ignore */ }
}

function renderContacts(contacts) {
  const container = document.getElementById('contactsList');
  if (!contacts.length) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📱</div>
        <p>No emergency contacts configured yet.</p>
        <p class="empty-hint">Add a contact and share their unique Telegram pairing link.</p>
      </div>`;
    return;
  }

  container.innerHTML = contacts.map(c => `
    <div class="clay-card contact-card" data-id="${c.id}">
      <div class="contact-left">
        <div class="contact-avatar">${c.status === 'VERIFIED' ? '✅' : '⏳'}</div>
        <div class="contact-info">
          <div class="contact-name">${escapeHtml(c.contact_name)}</div>
          <div class="contact-status ${c.status.toLowerCase()}">${c.status}${c.telegram_username ? ' — @' + escapeHtml(c.telegram_username) : ''}</div>
        </div>
      </div>
      <div class="contact-right">
        ${c.status === 'PENDING' ? `<button class="btn-clay btn-copy-link" onclick="copyLink('${c.deep_link}')">📋 Copy Link</button>` : ''}
        <button class="btn-clay btn-delete-contact" onclick="deleteContact(${c.id})">🗑️</button>
      </div>
    </div>
  `).join('');
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function copyLink(link) {
  navigator.clipboard.writeText(link).then(() => {
    // Brief visual feedback could be added here
  });
}

async function deleteContact(id) {
  try {
    await fetch(`/api/contacts/${id}`, { method: 'DELETE', headers: authHeaders() });
    loadContacts();
  } catch (e) { /* ignore */ }
}

function showAddContactModal() {
  document.getElementById('addContactModal').style.display = 'flex';
  document.getElementById('newContactName').value = '';
  document.getElementById('newContactName').focus();
}

function hideAddContactModal() {
  document.getElementById('addContactModal').style.display = 'none';
}

async function confirmAddContact() {
  const name = document.getElementById('newContactName').value.trim();
  if (!name) return;

  try {
    const res = await fetch('/api/contacts', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ contact_name: name }),
    });
    const data = await res.json();
    hideAddContactModal();

    if (data.contact) {
      // Show pairing link modal
      document.getElementById('pairingContactName').textContent = name;
      document.getElementById('pairingLinkInput').value = data.contact.deep_link;
      document.getElementById('pairingLinkModal').style.display = 'flex';
      loadContacts();
    }
  } catch (e) { /* ignore */ }
}

function hidePairingModal() {
  document.getElementById('pairingLinkModal').style.display = 'none';
}

// ── Mic Toggle ─────────────────────────────────────────────────────────────────

async function toggleMic(e) {
  if (e && e.target && e.target.id === 'micToggle') {
    return; // Prevent double firing from label container
  }
  try {
    const res = await fetch('/api/system/toggle-mic', { method: 'POST', headers: authHeaders() });
    const data = await res.json();
    const label = document.getElementById('micLabel');
    const checkbox = document.getElementById('micCheckbox');
    if (label) label.textContent = data.mic_enabled ? 'Listening' : 'Paused';
    if (checkbox) checkbox.checked = data.mic_enabled;
  } catch (err) { /* ignore */ }
}

// ── Event Listeners ────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Set user info
  if (USER.display_name || USER.username) {
    const name = USER.display_name || USER.username;
    document.getElementById('homeUserName').textContent = name;
    document.getElementById('avatarInitial').textContent = name.charAt(0).toUpperCase();
  }

  // Sidebar navigation
  document.querySelectorAll('.nav-item[data-view]').forEach(btn => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
  });

  // Logout
  document.getElementById('btnLogout').addEventListener('click', logout);

  // Avatar -> profile
  document.getElementById('btnUserAvatar').addEventListener('click', () => switchView('profile'));

  // Mic toggle on checkbox change
  const micCheckbox = document.getElementById('micCheckbox');
  if (micCheckbox) {
    micCheckbox.addEventListener('change', toggleMic);
  }

  // Profile save
  document.getElementById('btnSaveProfile').addEventListener('click', saveProfile);
  document.getElementById('btnChangePassword').addEventListener('click', changePassword);

  // Contacts
  document.getElementById('btnAddContact').addEventListener('click', showAddContactModal);
  document.getElementById('btnCancelModal').addEventListener('click', hideAddContactModal);
  document.getElementById('btnConfirmContact').addEventListener('click', confirmAddContact);
  document.getElementById('btnClosePairing').addEventListener('click', hidePairingModal);
  document.getElementById('btnCopyLink').addEventListener('click', () => {
    const input = document.getElementById('pairingLinkInput');
    navigator.clipboard.writeText(input.value);
  });

  // Alert cancel
  document.getElementById('btnCancelAlert').addEventListener('click', async () => {
    await fetch('/api/cancel-alert', { method: 'POST' });
  });

  // Test buttons
  document.getElementById('btnTestHazard').addEventListener('click', async () => {
    await fetch('/api/test-sound?mode=ambient_hazard', { method: 'POST' });
  });
  document.getElementById('btnTestMedia').addEventListener('click', async () => {
    await fetch('/api/test-sound?mode=media_suppress', { method: 'POST' });
  });
  document.getElementById('btnTestTelegram').addEventListener('click', async () => {
    await fetch('/api/trigger-telegram?hazard=Fire+alarm', { method: 'POST' });
  });

  // Initialize waveform
  initWaveformCanvas();

  // Connect WebSocket
  connectWebSocket();

  // Load initial contacts count
  loadContacts();

  // Sync high-precision browser GPS location
  syncBrowserLocation();

  // Manual GPS Sync Button
  const btnGps = document.getElementById('btnDetectGps');
  if (btnGps) {
    btnGps.addEventListener('click', () => {
      document.getElementById('locationStatusText').textContent = "Acquiring GPS...";
      syncBrowserLocation(true);
    });
  }
});

function syncBrowserLocation(isManualClick = false) {
  if (!navigator.geolocation) {
    const locText = document.getElementById('locationStatusText');
    if (locText) locText.textContent = "GPS Unavailable";
    return;
  }

  function pushLocation(pos) {
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;
    const locText = document.getElementById('locationStatusText');
    if (locText) {
      locText.textContent = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
      locText.style.color = "var(--accent-emerald)";
    }

    fetch('/api/location/update', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ latitude: lat, longitude: lon }),
    }).then(res => res.json()).then(data => {
      console.log("[Location Sync] Live coordinates updated:", data);
    }).catch(() => {});
  }

  const options = { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 };
  navigator.geolocation.getCurrentPosition(pushLocation, (err) => {
    console.warn("[Location Sync] getCurrentPosition warning:", err.message);
    const locText = document.getElementById('locationStatusText');
    if (locText && !locText.textContent.includes(",")) {
      locText.textContent = "Permission Needed";
      locText.style.color = "var(--accent-amber)";
    }
  }, options);

  navigator.geolocation.watchPosition(pushLocation, () => {}, options);
}
