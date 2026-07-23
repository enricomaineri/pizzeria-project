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
    menuStatusText.textContent  = 'Il menu è momentaneamente vuoto, torna a trovarci più tardi.';
    menuDynamicContent.innerHTML = '';
    renderAnchors([]);
    return;
  }

  menuStatusTitle.textContent = 'Ecco il menu di oggi';
  menuStatusText.textContent  = 'Sfoglia le categorie qui sotto e scegli quello che preferisci.';
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
          <p>Scegli tra le nostre proposte.</p>
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
    menuStatusTitle.textContent = 'Qualcosa non ha funzionato';
    menuStatusText.textContent  = 'Non riusciamo a mostrare il menu in questo momento.';
    menuAnchorLinks.innerHTML   = `<span class="anchor-placeholder">Menu non disponibile</span>`;
    menuSidebarLinks.innerHTML  = `<p>Menu non disponibile</p>`;
    menuDynamicContent.innerHTML = `
      <section class="menu-section">
        <div class="menu-section-head">
          <p class="eyebrow">Ci scusiamo</p>
          <h2>Il menu non è disponibile al momento</h2>
          <p>Riprova tra qualche minuto oppure chiamaci al +39 0123 456789: saremo felici di aiutarti.</p>
        </div>
      </section>`;
    console.error('Errore caricamento menu:', error);
  }
}

document.addEventListener('DOMContentLoaded', loadMenu);
