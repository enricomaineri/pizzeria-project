document.addEventListener("DOMContentLoaded", () => {
  const chatbotMessages = document.getElementById("chatbotMessages");
  const chatbotQuickActions = document.getElementById("chatbotQuickActions");
  const chatbotInput = document.getElementById("chatbotInput");
  const chatbotSendBtn = document.getElementById("chatbotSendBtn");
  const chatbotStatus = document.getElementById("chatbotStatus");

  if (!chatbotMessages || !chatbotQuickActions || !chatbotInput || !chatbotSendBtn || !chatbotStatus) {
    console.error("Elementi chatbot non trovati nel DOM");
    return;
  }

  const state = {
    step: "loading",
    categories: [],
    products: [],
    selectedCategory: null,
    selectedProduct: null,
    cart: [],
    fulfillmentType: null,
    address: "",
    slotLabel: "",
    customerName: "",
    phone: "",
  };

  function euro(value) {
    return `€${Number(value).toFixed(2)}`;
  }

  function addMessage(text, type = "bot") {
    const message = document.createElement("div");
    message.className = `chatbot-message ${type}`;
    message.innerHTML = text;
    chatbotMessages.appendChild(message);
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
  }

  function clearQuickActions() {
    chatbotQuickActions.innerHTML = "";
  }

  function setQuickActions(actions) {
    chatbotQuickActions.innerHTML = "";

    actions.forEach((action) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chatbot-chip";
      btn.textContent = action.label;
      btn.addEventListener("click", action.onClick);
      chatbotQuickActions.appendChild(btn);
    });
  }

  function resetInput(placeholder = "Scrivi qui il tuo indirizzo oppure una nota") {
    chatbotInput.value = "";
    chatbotInput.placeholder = placeholder;
  }

  function getCategoryProducts(category) {
    if (!category) return [];
    if (Array.isArray(category.items)) return category.items;
    if (Array.isArray(category.products)) return category.products;
    return [];
  }

  function isProductAvailable(product) {
    return product?.is_available !== false;
  }

  function getAvailableCategories() {
    return state.categories.filter((category) =>
      getCategoryProducts(category).some(isProductAvailable)
    );
  }

  function getProductsByCategorySlug(slug) {
    const category = state.categories.find((c) => c.slug === slug);
    return category ? getCategoryProducts(category) : [];
  }

  function getCartTotal() {
    return state.cart.reduce((sum, item) => sum + item.quantity * item.unit_price, 0);
  }

  function renderCartSummary() {
    if (!state.cart.length) return "Carrello vuoto.";

    const rows = state.cart
      .map(
        (item) =>
          `- ${item.product_name} x${item.quantity} (${euro(item.unit_price)} cad.)`
      )
      .join("<br>");

    return `
      <div class="chatbot-summary">
        <strong>Carrello attuale</strong><br>
        ${rows}<br><br>
        <strong>Totale:</strong> ${euro(getCartTotal())}
      </div>
    `;
  }

  function startOrderFlow() {
    state.step = "choose_category";
    addMessage("Perfetto, iniziamo. Scegli una categoria del menu.");

    const categories = getAvailableCategories();

    if (!categories.length) {
      addMessage("Non trovo categorie con prodotti disponibili nel menu.");
      setQuickActions([{ label: "Riprova", onClick: resetChatbot }]);
      return;
    }

    setQuickActions(
      categories.map((category) => ({
        label: category.name,
        onClick: () => chooseCategory(category.slug),
      }))
    );
  }

  function chooseCategory(categorySlug) {
    state.selectedCategory = categorySlug;

    const category = state.categories.find((c) => c.slug === categorySlug);
    addMessage(category?.name || categorySlug, "user");

    const products = getProductsByCategorySlug(categorySlug).filter(isProductAvailable);

    if (!products.length) {
      addMessage("In questa categoria non ci sono prodotti disponibili. Scegline un'altra.");
      return startOrderFlow();
    }

    state.step = "choose_product";
    addMessage("Ora scegli un prodotto.");

    setQuickActions(
      products.slice(0, 8).map((product) => ({
        label: `${product.name} · ${euro(product.price)}`,
        onClick: () => chooseProduct(product),
      }))
    );
  }

  function chooseProduct(product) {
    state.selectedProduct = product;
    addMessage(product.name, "user");
    addMessage(`Quante unità di <strong>${product.name}</strong> vuoi ordinare? Scegli una quantità.`);

    state.step = "choose_quantity";

    setQuickActions([
      { label: "1", onClick: () => setQuantity(1) },
      { label: "2", onClick: () => setQuantity(2) },
      { label: "3", onClick: () => setQuantity(3) },
      { label: "4", onClick: () => setQuantity(4) },
    ]);
  }

  function setQuantity(quantity) {
    addMessage(String(quantity), "user");

    const product = state.selectedProduct;
    if (!product) {
      addMessage("Non riesco a capire quale prodotto stai ordinando. Ripartiamo.");
      return resetChatbot();
    }

    const existing = state.cart.find((item) => item.product_id === product.id);

    if (existing) {
      existing.quantity += quantity;
    } else {
      state.cart.push({
        product_id: product.id,
        product_name: product.name,
        quantity,
        unit_price: product.price,
      });
    }

    addMessage(`Aggiunto <strong>${product.name}</strong> x${quantity} al carrello.`);
    addMessage(renderCartSummary());

    state.selectedProduct = null;
    askAddMore();
  }

  function askAddMore() {
    state.step = "ask_add_more";
    addMessage("Vuoi aggiungere altri prodotti?");
    setQuickActions([
      { label: "Sì, aggiungi ancora", onClick: askWhichCategoryAgain },
      { label: "No, continua", onClick: chooseFulfillmentType },
    ]);
  }

  function askWhichCategoryAgain() {
    addMessage("Sì, aggiungi ancora", "user");
    addMessage("Perfetto. Scegli una categoria per continuare.");
    state.step = "choose_category";

    const categories = getAvailableCategories();

    setQuickActions(
      categories.map((category) => ({
        label: category.name,
        onClick: () => chooseCategory(category.slug),
      }))
    );
  }

  function chooseFulfillmentType() {
    addMessage("No, continua", "user");
    addMessage("Preferisci consegna o ritiro?");
    state.step = "choose_fulfillment";

    setQuickActions([
      { label: "🚚 Consegna", onClick: () => setFulfillmentType("delivery") },
      { label: "🏠 Ritiro", onClick: () => setFulfillmentType("pickup") },
    ]);
  }

  function setFulfillmentType(type) {
    state.fulfillmentType = type;
    addMessage(type === "delivery" ? "Consegna" : "Ritiro", "user");

    if (type === "delivery") {
      state.step = "enter_address";
      clearQuickActions();
      resetInput("Inserisci il tuo indirizzo completo");
      addMessage("Perfetto. Inserisci il tuo indirizzo completo.");
      return;
    }

    state.address = "";
    loadSlots();
  }

  async function loadSlots() {
    state.step = "loading_slots";
    clearQuickActions();
    chatbotStatus.textContent = "Caricamento slot...";

    try {
      const response = await fetch(`/api/slots?fulfillment_type=${state.fulfillmentType}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      const availableSlots = (data.slots || []).filter((slot) => slot.available);

      chatbotStatus.textContent = "Menu collegato";

      if (!availableSlots.length) {
        addMessage("Al momento non ci sono slot disponibili. Riprova più tardi.");
        setQuickActions([{ label: "Nuovo ordine", onClick: resetChatbot }]);
        state.step = "done";
        return;
      }

      addMessage("Ecco gli slot disponibili. Scegli un orario.");
      state.step = "choose_slot";

      setQuickActions(
        availableSlots.map((slot) => ({
          label: slot.label,
          onClick: () => chooseSlot(slot.label),
        }))
      );
    } catch (error) {
      chatbotStatus.textContent = "Errore slot";
      addMessage("Non riesco a leggere gli slot disponibili dal backend.");
      console.error("Errore slot:", error);
    }
  }

  async function chooseSlot(slotLabel) {
    state.slotLabel = slotLabel;
    addMessage(slotLabel, "user");
    addMessage("Controllo la disponibilità effettiva dello slot selezionato...");

    state.step = "checking_slot";
    clearQuickActions();

    try {
      const response = await fetch("/api/orders/check-slot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          fulfillment_type: state.fulfillmentType,
          slot_label: slotLabel,
        }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();

      if (data.available) {
        showFinalSummary();
        return;
      }

      addMessage("Questo slot non è più disponibile.");

      if (data.alternatives && data.alternatives.length) {
        addMessage("Ti propongo alcuni orari alternativi.");
        state.step = "choose_alternative_slot";

        setQuickActions(
          data.alternatives.map((slot) => ({
            label: slot,
            onClick: () => chooseSlot(slot),
          }))
        );
      } else {
        addMessage("Non ci sono slot alternativi disponibili in questo momento.");
        setQuickActions([{ label: "Nuovo ordine", onClick: resetChatbot }]);
        state.step = "done";
      }
    } catch (error) {
      addMessage("Errore durante il controllo dello slot.");
      console.error("Errore check slot:", error);
    }
  }

  function showFinalSummary() {
    state.step = "summary";

    const rows = state.cart
      .map(
        (item) =>
          `- ${item.product_name} x${item.quantity} = ${euro(item.quantity * item.unit_price)}`
      )
      .join("<br>");

    addMessage(`
      <div class="chatbot-summary">
        <strong>Riepilogo finale</strong><br><br>
        ${rows}<br><br>
        <strong>Totale:</strong> ${euro(getCartTotal())}<br>
        <strong>Modalità:</strong> ${state.fulfillmentType === "delivery" ? "Consegna" : "Ritiro"}<br>
        ${state.fulfillmentType === "delivery" ? `<strong>Indirizzo:</strong> ${state.address}<br>` : ""}
        <strong>Slot:</strong> ${state.slotLabel}
      </div>
    `);

    addMessage("Confermi l’ordine?");
    setQuickActions([
      { label: "✅ Conferma ordine", onClick: askCustomerInfo },
      { label: "❌ Annulla", onClick: resetChatbot },
    ]);
  }

  function askCustomerInfo() {
    addMessage("✅ Conferma ordine", "user");
    addMessage("Perfetto. Inserisci il tuo nome.");
    clearQuickActions();
    resetInput("Inserisci il tuo nome");
    state.step = "enter_name";
  }

  function askPhone() {
    addMessage("Perfetto. Ora inserisci il tuo numero di telefono.");
    resetInput("Inserisci il tuo numero di telefono");
    state.step = "enter_phone";
  }

  async function submitOrder() {
    state.step = "submitting";
    addMessage("Sto salvando il tuo ordine nel database...");
    clearQuickActions();

    try {
      const payload = {
        customer_name: state.customerName,
        phone: state.phone,
        address: state.fulfillmentType === "delivery" ? state.address : null,
        fulfillment_type: state.fulfillmentType,
        slot_label: state.slotLabel,
        items: state.cart.map((item) => ({
          product_id: item.product_id,
          quantity: item.quantity,
        })),
      };

      const response = await fetch("/api/orders", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const err = await response.text();
        throw new Error(err || `HTTP ${response.status}`);
      }

      const data = await response.json();

      addMessage(`
        <div class="chatbot-summary">
          <strong>Ordine ricevuto</strong><br>
          ID ordine: ${data.order_id}<br>
          Stato: ${data.status}<br>
          Totale: ${euro(data.total_price)}<br>
          Slot: ${data.slot_label}
        </div>
      `);

      addMessage("Grazie! Il tuo ordine è stato registrato correttamente.");
      setQuickActions([
        { label: "Nuovo ordine", onClick: resetChatbot },
        { label: "Vai al menu", onClick: () => (window.location.href = "/menu") },
      ]);
      state.step = "done";
    } catch (error) {
      addMessage("Non sono riuscito a salvare l’ordine. Controlla backend e database.");
      console.error("Errore salvataggio ordine:", error);
      setQuickActions([{ label: "Riprova", onClick: submitOrder }]);
    }
  }

  function resetStateValues() {
    state.step = "loading";
    state.selectedCategory = null;
    state.selectedProduct = null;
    state.cart = [];
    state.fulfillmentType = null;
    state.address = "";
    state.slotLabel = "";
    state.customerName = "";
    state.phone = "";
  }

  function resetChatbot() {
    chatbotMessages.innerHTML = "";
    chatbotQuickActions.innerHTML = "";
    resetInput("Scrivi qui il tuo indirizzo oppure una nota");
    resetStateValues();
    initChatbot(true);
  }

  async function initChatbot(fromReset = false) {
    try {
      chatbotStatus.textContent = "Caricamento menu...";

      if (!fromReset) {
        addMessage("Ciao, sono l’Assistente Vesuvio.");
      }

      addMessage("Sto caricando il menu reale dal database...");

      const response = await fetch("/api/menu");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();

      state.categories = Array.isArray(data.categories) ? data.categories : [];
      state.products = state.categories.flatMap((category) => getCategoryProducts(category));

      chatbotStatus.textContent = "Menu collegato";
      addMessage("Perfetto, il menu è pronto.");
      addMessage("Premi qui sotto per iniziare l’ordine.");

      state.step = "ready";
      setQuickActions([{ label: "🍕 Ordina ora", onClick: startOrderFlow }]);
    } catch (error) {
      chatbotStatus.textContent = "Errore API";
      addMessage("Non riesco a leggere il menu dal backend.");
      console.error("Errore chatbot init:", error);
    }
  }

  chatbotSendBtn.addEventListener("click", () => {
    const value = chatbotInput.value.trim();
    if (!value) return;

    if (state.step === "enter_address") {
      state.address = value;
      addMessage(value, "user");
      resetInput();
      loadSlots();
      return;
    }

    if (state.step === "enter_name") {
      state.customerName = value;
      addMessage(value, "user");
      chatbotInput.value = "";
      askPhone();
      return;
    }

    if (state.step === "enter_phone") {
      state.phone = value;
      addMessage(value, "user");
      chatbotInput.value = "";
      submitOrder();
      return;
    }

    addMessage(value, "user");
    chatbotInput.value = "";
    addMessage("In questo chatbot usa soprattutto i pulsanti rapidi, così il flow segue esattamente il percorso previsto.");
  });

  chatbotInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      chatbotSendBtn.click();
    }
  });

  initChatbot();
});