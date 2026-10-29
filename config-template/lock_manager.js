(function() {
  let idleTime = 0;
  let timeoutMinutes = 15;
  let warningSeconds = 60;
  let warningShown = false;
  let warningDiv = null;

  // 1. Fetch user profile config
  fetch('/auth_user')
    .then(r => r.json())
    .then(data => {
      if (data && data.idleTimeoutMinutes !== undefined) {
        timeoutMinutes = parseInt(data.idleTimeoutMinutes, 10);
      }
    })
    .catch(() => {});

  function doLock() {
    window.location.href = '/auth_logout';
  }

  // 2. Activity Tracker & Idle Timer
  function resetActivity() {
    idleTime = 0;
    if (warningShown) {
      dismissWarning();
    }
  }

  ['mousemove', 'mousedown', 'keydown', 'wheel', 'touchstart', 'pointerdown'].forEach(evt => {
    window.addEventListener(evt, resetActivity, { passive: true });
  });

  // Hotkey: Ctrl + Alt + L
  window.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.altKey && (e.key === 'l' || e.key === 'L')) {
      e.preventDefault();
      doLock();
    }
  });

  // Warning Toast
  function showWarning(remainingSeconds) {
    if (!warningDiv) {
      warningDiv = document.createElement('div');
      warningDiv.id = 'webtop-idle-warning';
      Object.assign(warningDiv.style, {
        position: 'fixed',
        bottom: '60px',
        right: '24px',
        zIndex: '9999999',
        background: 'rgba(25, 25, 25, 0.92)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        border: '1px solid rgba(255, 185, 0, 0.6)',
        borderRadius: '8px',
        color: '#ffffff',
        padding: '14px 20px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        fontSize: '13px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        transition: 'opacity 0.3s ease',
        opacity: '0'
      });
      document.body.appendChild(warningDiv);
    }
    warningDiv.innerHTML = `
      <span style="font-size: 18px;">⏳</span>
      <div>
        <div style="font-weight: 600; color: #ffb900;">Aviso de Inatividade</div>
        <div style="color: #d0d0d0; margin-top: 2px;">Sua sessão será bloqueada em <b id="webtop-sec-left">${remainingSeconds}</b>s. Mova o mouse para continuar.</div>
      </div>
    `;
    setTimeout(() => { if (warningDiv) warningDiv.style.opacity = '1'; }, 50);
    warningShown = true;
  }

  function dismissWarning() {
    if (warningDiv) {
      warningDiv.style.opacity = '0';
      setTimeout(() => {
        if (warningDiv && warningDiv.parentNode) {
          warningDiv.parentNode.removeChild(warningDiv);
          warningDiv = null;
        }
      }, 300);
    }
    warningShown = false;
  }

  // Timer Tick every 1 second
  setInterval(() => {
    if (timeoutMinutes <= 0) return; // Disabled
    idleTime++;

    const totalSeconds = timeoutMinutes * 60;
    const remaining = totalSeconds - idleTime;

    if (remaining <= warningSeconds && remaining > 0) {
      showWarning(remaining);
      const secSpan = document.getElementById('webtop-sec-left');
      if (secSpan) secSpan.textContent = remaining;
    } else if (remaining <= 0) {
      doLock();
    }
  }, 1000);

  // 3. Poll for external lock command (from Start Menu / xflock4)
  setInterval(() => {
    fetch('/auth_lock_status')
      .then(r => r.json())
      .then(d => {
        if (d && d.locked) {
          doLock();
        }
      })
      .catch(() => {});
  }, 1500);
})();
