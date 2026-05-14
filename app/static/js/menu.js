// ── Helpers ──────────────────────────────────────────────
function slugToId(slug) {
  return `section-${slug}`;
}

function euro(value) {
  return `€${Number(value).toFixed(2)}`;
}

function createBadge(label, type) {
  return `<span class="pill ${type}">${label}</span>`;
}

// ── Render anchors ────────────────────────────────────────
function renderAnchors(categories) {
  const menuAnchorLinks  = document.getElementById('menuAnchorLinks');
  const menuSidebarLinks = document.getElementById('menuSidebarLinks');

  if (!categories.length) {
    menuAnchorLinks.innerHTML  = `<span class="anchor-placeholder">Nessuna categoria disponibile</span>`;
    menuSidebarLinks.innerHTML = `<p>Nessuna categoria disponibile</p>`;
    return;
  }

  const links = categories
    .map(cat => `<a href="#${slugToId(cat.slug)}">${cat.name}</a>`)
    .join('');

  menuAnchorLinks.innerHTML  = links;
  menuSidebarLinks.innerHTML = links;
}

// ── Render menu ───────────────────────────────────────────
function renderMenu(categories) {
  const menuDynamicContent = document.getElementById('menuDynamicContent');
  const menuStatusTitle    = document.getElementById('menuStatusTitle');
  const menuStatusText     = document.getElementById('menuStatusText');

  if (!categories.length) {
    menuStatusTitle.textContent = 'Nessun prodotto disponibile';
    menuStatusText.textContent  = 'Il database è raggiungibile, ma al momento il menu è vuoto.';
    menuDynamicContent.innerHTML = '';
    renderAnchors([]);
    return;
  }

  menuStatusTitle.textContent = 'Menu caricato correttamente';
  menuStatusText.textContent  = 'Questi contenuti arrivano direttamente dal database del progetto.';
  renderAnchors(categories);

  menuDynamicContent.innerHTML = categories.map(category => {
    const items = category.items || [];

    const itemsHtml = items.length
      ? `<div class="menu-items-grid">
          ${items.map(item => {
            const badgeHtml = [
              item.is_vegetarian ? createBadge('Veg',  'veg')  : '',
              item.is_spicy      ? createBadge('Hot',  'spicy') : '',
              item.is_featured   ? createBadge('Chef', 'chef')  : '',
            ].join('');

            return `
              <article class="dish-card ${item.is_featured ? 'featured-dish' : ''}">
                <div class="dish-top">
                  <h3>${item.name}</h3>
                  <span>${euro(item.price)}</span>
                </div>
                <p>${item.description || ''}</p>
                ${badgeHtml ? `<div class="dish-tags">${badgeHtml}</div>` : ''}
              </article>`;
          }).join('')}
        </div>`
      : `<p class="empty-menu-note">Nessun prodotto disponibile in questa categoria.</p>`;

    return `
      <section class="menu-section" id="${slugToId(category.slug)}">
        <div class="menu-section-head">
          <p class="eyebrow">Categoria</p>
          <h2>${category.name}</h2>
          <p>Prodotti letti dinamicamente dal database tramite API.</p>
        </div>
        ${itemsHtml}
      </section>`;
  }).join('');
}

// ── Fetch & load ──────────────────────────────────────────
async function loadMenu() {
  const menuDynamicContent = document.getElementById('menuDynamicContent');
  const menuStatusTitle    = document.getElementById('menuStatusTitle');
  const menuStatusText     = document.getElementById('menuStatusText');
  const menuAnchorLinks    = document.getElementById('menuAnchorLinks');
  const menuSidebarLinks   = document.getElementById('menuSidebarLinks');

  try {
    const response = await fetch('/api/menu');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    renderMenu(data.categories || []);
  } catch (error) {
    menuStatusTitle.textContent = 'Errore nel caricamento';
    menuStatusText.textContent  = 'Non sono riuscito a leggere il menu dal backend.';
    menuAnchorLinks.innerHTML   = `<span class="anchor-placeholder">API non disponibile</span>`;
    menuSidebarLinks.innerHTML  = `<p>API non disponibile</p>`;
    menuDynamicContent.innerHTML = `
      <section class="menu-section">
        <div class="menu-section-head">
          <p class="eyebrow">Errore</p>
          <h2>Il menu non è disponibile</h2>
          <p>Controlla che il server sia avviato, che il database esista e che /api/menu risponda correttamente.</p>
        </div>
      </section>`;
    console.error('Errore caricamento menu:', error);
  }
}

document.addEventListener('DOMContentLoaded', loadMenu);
