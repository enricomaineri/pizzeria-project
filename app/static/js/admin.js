// ── Calendario custom ──────────────────────────────────
(function () {
  const grid       = document.getElementById('cal-grid');
  const monthLabel = document.getElementById('cal-month-label');
  const prevBtn    = document.getElementById('cal-prev');
  const nextBtn    = document.getElementById('cal-next');
  const dateInput  = document.getElementById('date-input');

  if (!grid) return;

  const MONTHS_IT = ['Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno',
                     'Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'];

  const serverDate = dateInput ? dateInput.value : null;
  let selected = serverDate ? new Date(serverDate + 'T12:00:00') : new Date();
  selected.setHours(12, 0, 0, 0);

  let viewYear  = selected.getFullYear();
  let viewMonth = selected.getMonth();

  const today = new Date();
  today.setHours(12, 0, 0, 0);

  function isSameDay(a, b) {
    return a.getFullYear() === b.getFullYear() &&
           a.getMonth()   === b.getMonth()    &&
           a.getDate()    === b.getDate();
  }

  function renderCalendar() {
    const toRemove = grid.querySelectorAll('.day');
    toRemove.forEach(el => el.remove());

    monthLabel.textContent = MONTHS_IT[viewMonth] + ' ' + viewYear;

    const firstDay = new Date(viewYear, viewMonth, 1);
    let startDow = firstDay.getDay() - 1;
    if (startDow < 0) startDow = 6;

    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
    const daysInPrev  = new Date(viewYear, viewMonth, 0).getDate();

    for (let i = startDow - 1; i >= 0; i--) {
      const d = document.createElement('div');
      d.className = 'day other-month';
      d.textContent = daysInPrev - i;
      grid.appendChild(d);
    }

    for (let d = 1; d <= daysInMonth; d++) {
      const dt = new Date(viewYear, viewMonth, d, 12);
      const el = document.createElement('div');
      el.className = 'day';
      el.textContent = d;

      if (isSameDay(dt, today))    el.classList.add('today');
      if (isSameDay(dt, selected)) el.classList.add('selected');

      if (dt > today) {
        el.classList.add('other-month');
      } else {
        el.addEventListener('click', () => {
          const y   = dt.getFullYear();
          const m   = String(dt.getMonth() + 1).padStart(2, '0');
          const day = String(dt.getDate()).padStart(2, '0');
          window.location.href = '/admin/storico?data=' + y + '-' + m + '-' + day;
        });
      }

      grid.appendChild(el);
    }

    const total     = startDow + daysInMonth;
    const remaining = total % 7 === 0 ? 0 : 7 - (total % 7);
    for (let i = 1; i <= remaining; i++) {
      const el = document.createElement('div');
      el.className = 'day other-month';
      el.textContent = i;
      grid.appendChild(el);
    }
  }

  prevBtn.addEventListener('click', () => {
    viewMonth--;
    if (viewMonth < 0) { viewMonth = 11; viewYear--; }
    renderCalendar();
  });

  nextBtn.addEventListener('click', () => {
    viewMonth++;
    if (viewMonth > 11) { viewMonth = 0; viewYear++; }
    renderCalendar();
  });

  renderCalendar();
})();

// ── Aggiornamento live ──────────────────────────────────
(function () {
  const isOrdersPage = window.location.pathname === '/admin';
  if (!isOrdersPage) return;

  const REFRESH_MS = 10000;
  const liveBar  = document.querySelector('.live-bar');
  const liveText = document.getElementById('live-status-text');

  let intervalId  = null;
  let countdownId = null;
  let secondsLeft = REFRESH_MS / 1000;

  function updateLabel(paused = false) {
    if (!liveText) return;
    liveText.textContent = paused
      ? 'LIVE in pausa · tab non attiva'
      : `LIVE · aggiornamento tra ${secondsLeft}s`;
  }

  function startCountdown() {
    stopCountdown();
    secondsLeft = REFRESH_MS / 1000;
    updateLabel(false);
    countdownId = setInterval(() => {
      secondsLeft--;
      if (secondsLeft <= 0) secondsLeft = REFRESH_MS / 1000;
      updateLabel(false);
    }, 1000);
  }

  function stopCountdown() {
    if (countdownId) { clearInterval(countdownId); countdownId = null; }
  }

  function startRefresh() {
    if (intervalId) return;
    if (liveBar) liveBar.classList.remove('paused');
    startCountdown();
    intervalId = setInterval(() => {
      if (!document.hidden) window.location.reload();
    }, REFRESH_MS);
  }

  function stopRefresh() {
    if (intervalId) { clearInterval(intervalId); intervalId = null; }
    stopCountdown();
    if (liveBar) liveBar.classList.add('paused');
    updateLabel(true);
  }

  document.addEventListener('visibilitychange', () => {
    document.hidden ? stopRefresh() : startRefresh();
  });

  startRefresh();
})();

// ── Tab Telefono: carrello interattivo ──────────────────
(function () {
  if (!document.getElementById('tel-form')) return;

  const cart = {};

  window.changeQty = function (pid, delta) {
    const input = document.getElementById('qty-' + pid);
    if (!input) return;
    let v = parseInt(input.value) || 0;
    v = Math.max(0, Math.min(20, v + delta));
    input.value = v;
    syncCart();
  };

  window.syncCart = function () {
    document.querySelectorAll('.qty-input').forEach(input => {
      const pid   = parseInt(input.dataset.pid);
      const qty   = parseInt(input.value) || 0;
      const price = parseFloat(input.dataset.price);
      const name  = input.dataset.name;
      const row   = document.getElementById('row-' + pid);
      if (qty > 0) {
        cart[pid] = { name, price, qty };
        if (row) row.classList.add('in-cart');
      } else {
        delete cart[pid];
        if (row) row.classList.remove('in-cart');
      }
    });
    renderCart();
  };

  function renderCart() {
    const linesEl   = document.getElementById('cart-lines');
    const totalEl   = document.getElementById('cart-total');
    const submitBtn = document.getElementById('submit-btn');

    const keys = Object.keys(cart);
    if (keys.length === 0) {
      linesEl.innerHTML = '<span class="cart-empty">Nessun prodotto aggiunto</span>';
      totalEl.textContent = '€0.00';
      if (submitBtn) submitBtn.disabled = true;
      return;
    }

    let html = '';
    let total = 0;
    keys.forEach(pid => {
      const { name, price, qty } = cart[pid];
      const line = price * qty;
      total += line;
      html += `<div class="cart-line">
        <span class="cart-line-name">${name} ×${qty}</span>
        <span class="cart-line-price">€${line.toFixed(2)}</span>
      </div>`;
    });
    linesEl.innerHTML = html;
    totalEl.textContent = '€' + total.toFixed(2);
    if (submitBtn) submitBtn.disabled = false;
  }

  window.toggleAddress = function () {
    const sel = document.getElementById('fulfillment-type');
    const grp = document.getElementById('address-group');
    const inp = document.getElementById('address-input');
    if (!sel || !grp) return;
    const isDelivery = sel.value === 'delivery';
    grp.style.display = isDelivery ? '' : 'none';
    if (inp) inp.required = isDelivery;
  };

  window.resetForm = function () {
    document.querySelectorAll('.qty-input').forEach(i => { i.value = 0; });
    document.querySelectorAll('.tel-product-row').forEach(r => r.classList.remove('in-cart'));
    Object.keys(cart).forEach(k => delete cart[k]);
    renderCart();
  };

  toggleAddress();
})();
