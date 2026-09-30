let gameState = {
    balance: 1250, luck: 1.0, luckBoost: 0, cashback: 0, isTurbo: false, sortAsc: true,
    selectedInput: null, selectedOutput: null, cart: {}, 
    isAuthorized: false, username: "Игрок", rank: "PLAYER [ 1 ]", isAdmin: false,
    
    marketItems: [
        { id: 101, name: 'Куб #047', price: 10, rarity: 'common', icon: '📦' },
        { id: 102, name: 'Куб #156', price: 25, rarity: 'common', icon: '📦' },
        { id: 103, name: 'Куб #024', price: 84, rarity: 'rare', icon: '🔷' },
        { id: 104, name: 'Куб #118', price: 120, rarity: 'rare', icon: '🔷' },
        { id: 105, name: 'Куб #083', price: 250, rarity: 'epic', icon: '🔥' },
        { id: 106, name: 'Куб #031', price: 500, rarity: 'ultra', icon: '👑' },
        { id: 107, name: 'Кубик Льда', price: 750, rarity: 'epic', icon: '🧊' },
        { id: 108, name: 'Облачный Куб', price: 1100, rarity: 'ultra', icon: '☁️' }
    ],
    inventory: []
};

const tg = window.Telegram?.WebApp;

// Адрес бэкенда. Локально (ПК или телефон в одной сети) идём на сам сервер,
// с Netlify — в облако. Впиши сюда свой логин PythonAnywhere.
const CLOUD_API = "https://burnbox-me3b.onrender.com";
const API_BASE = (location.hostname === "localhost" || location.hostname === "127.0.0.1" ||
  /^192\.168\.|^10\.|^172\.(1[6-9]|2\d|3[01])\./.test(location.hostname))
  ? location.origin
  : CLOUD_API;
const balanceEl = document.getElementById('balance-amount');
const invGrid = document.getElementById('inventory-grid');
const targetGrid = document.getElementById('target-grid');
const inputSlot = document.getElementById('input-skin-display');
const outputSlot = document.getElementById('output-skin-display');
const chanceText = document.getElementById('chance-text');
const chanceSubText = document.getElementById('chance-sub-text');
const wheelScale = document.getElementById('wheel-scale');
const arrowEl = document.getElementById('wheel-arrow'); 
const spinBtn = document.getElementById('spin-button');
const turboBtn = document.getElementById('turbo-toggle');
const searchInput = document.getElementById('search-input');
const priceFrom = document.getElementById('price-from');
const priceTo = document.getElementById('price-to');
const sortPriceBtn = document.getElementById('sort-price-btn');
const sortIco = document.getElementById('sort-ico');
const targetCount = document.getElementById('target-count');
const searchClear = document.getElementById('search-clear');
const infoBlock = document.getElementById('wheel-info-block');
const mainInventoryGrid = document.getElementById('main-inventory-grid');
const mainMarketGrid = document.getElementById('main-market-grid');
const cartConfirmBtn = document.getElementById('cart-confirm-btn');
const screenAuth = document.getElementById('screen-auth');
const gameWrapper = document.getElementById('game-wrapper');
const authUsernameInput = document.getElementById('auth-username');
const authPasswordInput = document.getElementById('auth-password');
const authSubmitBtn = document.getElementById('auth-submit-btn');
const authRegBtn = document.getElementById('auth-reg-btn');
const authTgBtn = document.getElementById('auth-tg-btn');
const authStatusMsg = document.getElementById('auth-status-msg');
const invPaneTitle = document.getElementById('inv-pane-title');
const profileNickname = document.getElementById('profile-nickname');
const nicknameInput = document.getElementById('nickname-input');
const editNicknameBtn = document.getElementById('edit-nickname-btn');
const saveNicknameBtn = document.getElementById('save-nickname-btn');
const nicknameDisplayMode = document.getElementById('nickname-display-mode');
const nicknameEditMode = document.getElementById('nickname-edit-mode');
const avatarUpload = document.getElementById('avatar-upload');
const profileAvatar = document.getElementById('profile-avatar');
const profileStatItems = document.getElementById('profile-stat-items');
const profileStatValue = document.getElementById('profile-stat-value');
const cashbackBox = document.getElementById('cashback-box');
const cashbackValue = document.getElementById('cashback-value');
const cashbackBtn = document.getElementById('cashback-btn');
const profileRankDisplay = document.getElementById('profile-rank-display');
const adminPanelBtn = document.getElementById('admin-panel-btn');
const topupBox = document.getElementById('topup-box');
const topupRange = document.getElementById('topup-range');
const topupAmount = document.getElementById('topup-amount');
const topupMaxLbl = document.getElementById('topup-max');

const CHANCE_CAP = 80;

// Кешбек начисляется от цены исходного скина за каждый апгрейд.
// 0.001 = 0.1%: скин за 500 $B даёт 0.5 $B. Копится в 4 знака, чтобы 0.025 не терялось.
const CASHBACK_RATE = 0.001;

function roundCashback(n) { return Math.round((n + Number.EPSILON) * 10000) / 10000; }
const logoutBtn = document.getElementById('logout-btn');
const logoutModal = document.getElementById('logout-modal');
const logoutConfirmYes = document.getElementById('logout-confirm-yes');
const logoutConfirmNo = document.getElementById('logout-confirm-no');

const avatarCropModal = document.getElementById('avatar-crop-modal');
const avatarCropImg = document.getElementById('avatar-crop-img');
const avatarCropPreview = document.getElementById('avatar-crop-preview');
const avatarCropZoom = document.getElementById('avatar-crop-zoom');
const avatarCropConfirm = document.getElementById('avatar-crop-confirm');
const avatarCropCancel = document.getElementById('avatar-crop-cancel');
const CROP_PREVIEW_SIZE = 240;
const CROP_OUTPUT_SIZE = 256;
let cropImage = null;
let cropZoom = 1;
let cropPanX = 0;
let cropPanY = 0;
let cropBaseScale = 1;
let isCropDragging = false;
let cropDragStart = null;

let currentRotation = 0; 
let banTimerInterval = null;

function init() {
    const urlParams = new URLSearchParams(window.location.search);
    const regUser = urlParams.get('reg_user');
    const regPass = urlParams.get('reg_pass');
    
    if (regUser && regPass) {
        if (authUsernameInput) authUsernameInput.value = regUser;
        if (authPasswordInput) authPasswordInput.value = regPass;
        if (authStatusMsg) { authStatusMsg.textContent = "Синхронизация..."; authStatusMsg.style.color = "#00ccff"; }
        if (authSubmitBtn) authSubmitBtn.click();
        window.history.replaceState({}, document.title, window.location.pathname);
    } else if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const user = tg.initDataUnsafe.user.first_name || "Игрок";
        checkTgAuth(user);
    } else {
        autoLogin();
    }
    setupEventListeners();
}

function getSavedSession() {
    try {
        const raw = localStorage.getItem('burnbox_session');
        if (!raw) return null;
        const parsed = JSON.parse(raw);
        return (parsed && parsed.user) ? parsed : null;
    } catch (e) { return null; }
}

function saveSession(user, pass) {
    try { localStorage.setItem('burnbox_session', JSON.stringify({ user: user, pass: pass })); } catch (e) { console.error("Не удалось сохранить сессию", e); }
}

function clearSession() {
    try { localStorage.removeItem('burnbox_session'); } catch (e) { console.error(e); }
}

async function autoLogin() {
    const session = getSavedSession();
    if (!session) return false;
    try {
        let data;
        if (session.pass) {
            const response = await fetch(API_BASE + '/login', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: session.user, password: session.pass })
            });
            data = await response.json();
            if (response.status === 403) { showBanScreen(data.ban_until, data.ban_reason); return true; }
            if (response.ok && data.status === "success") {
                bypassAuth(session.user, data.rank, data.balance, data.luck, data.inventory, data.cashback);
                return true;
            }
        } else {
            const response = await fetch(API_BASE + '/get_rank', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: session.user })
            });
            data = await response.json();
            if (response.status === 403) { showBanScreen(data.ban_until, data.ban_reason); return true; }
            if (response.ok && data.status === "success") {
                bypassAuth(session.user, data.rank, data.balance, data.luck, data.inventory, data.cashback);
                return true;
            }
        }
    } catch (e) { console.error("Автовход не удался", e); }
    clearSession();
    return false;
}

// 🛡 ЖЕЛЕЗОБЕТОННАЯ ФУНКЦИЯ БАНА
function showBanScreen(banUntil, reason) {
    if (screenAuth) screenAuth.style.display = 'none';
    if (gameWrapper) gameWrapper.style.display = 'none';
    
    const banScreen = document.getElementById('ban-screen');
    const banReason = document.getElementById('ban-reason');
    const banTimer = document.getElementById('ban-timer');
    
    // Если HTML бана не найден - рисуем черный экран принудительно
    if (!banScreen) {
        document.body.innerHTML = `<div style="background:#0b0c10;color:#ff3333;height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;">
            <h1 style="font-size:40px;">BAN</h1>
            <p style="color:#fff;margin-top:10px;">Причина: ${reason}</p>
        </div>`;
        return;
    }
    
    banScreen.style.display = 'flex';
    if(banReason) banReason.textContent = reason;
    if (banTimerInterval) clearInterval(banTimerInterval);
    
    banTimerInterval = setInterval(() => {
        const now = Math.floor(Date.now() / 1000);
        const diff = banUntil - now;
        if (diff <= 0) {
            clearInterval(banTimerInterval);
            location.reload(); 
        } else {
            const minutes = Math.floor(diff / 60);
            const seconds = diff % 60;
            if(banTimer) banTimer.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
        }
    }, 1000);
}

async function checkTgAuth(username) {
    try {
        const response = await fetch(API_BASE + '/get_rank', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username })
        });
        const data = await response.json();
        if (response.status === 403) { showBanScreen(data.ban_until, data.ban_reason); return; }
        if (response.ok && data.status === "success") {
            saveSession(username, '');
            bypassAuth(username, data.rank, data.balance, data.luck, data.inventory, data.cashback);
        }
    } catch (e) { console.error(e); }
}

async function saveProgressToServer() {
    if (!gameState.isAuthorized) return;
    const invIds = gameState.inventory.map(i => i.baseId || i.id);
    try {
        await fetch(API_BASE + '/update_progress', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: gameState.username, balance: gameState.balance, cashback: roundCashback(gameState.cashback || 0), inventory: invIds })
        });
    } catch (e) { console.error(e); }
}

async function fetchActualRank(username) {
    try {
        const response = await fetch(API_BASE + '/get_rank', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username })
        });
        const data = await response.json();
        
        if (response.status === 403) { showBanScreen(data.ban_until, data.ban_reason); return; }
        
        if (response.ok && data.status === "success") {
            gameState.rank = data.rank; gameState.balance = data.balance; gameState.luck = data.luck;
            gameState.cashback = roundCashback(data.cashback || 0);
            if (data.inventory && data.inventory.length > 0) {
                gameState.inventory = [];
                data.inventory.forEach(baseId => {
                    const template = gameState.marketItems.find(m => m.id === baseId);
                    if (template) gameState.inventory.push({ ...template, id: Math.random(), baseId: template.id });
                });
            }
            updateProfileUI(); renderBalance(); renderLeftPane(); renderFullScreens(); updateProfileStats();
        }
    } catch (e) { console.error("Ошибка синхронизации", e); }
}

function bypassAuth(name, rank = "PLAYER [ 1 ]", balance = 1250, luck = 1.0, inventoryIds = [], cashback = 0) {
    if (screenAuth) screenAuth.style.display = 'none';
    if (gameWrapper) gameWrapper.style.display = 'flex';
    gameState.isAuthorized = true; gameState.username = name; gameState.rank = rank;
    gameState.balance = balance; gameState.luck = luck; gameState.cashback = roundCashback(cashback || 0);
    
    if (inventoryIds && inventoryIds.length > 0) {
        gameState.inventory = [];
        inventoryIds.forEach(id => {
            const template = gameState.marketItems.find(m => m.id === id);
            if (template) gameState.inventory.push({ ...template, id: Math.random(), baseId: template.id });
        });
    }
    updateProfileUI(); renderBalance(); renderLeftPane(); renderFullScreens(); updateProfileStats();
}

function updateProfileUI() {
    if (invPaneTitle) invPaneTitle.textContent = `📦 Инвентарь: ${gameState.username}`;
    if (profileNickname) profileNickname.textContent = gameState.username;
    if (nicknameInput) nicknameInput.value = gameState.username;
    if (profileRankDisplay) profileRankDisplay.textContent = gameState.rank;
    try {
        const savedAvatar = localStorage.getItem('burnbox_avatar_' + (gameState.username || 'guest'));
        if (savedAvatar && profileAvatar) profileAvatar.src = savedAvatar;
    } catch (err) { console.error("Не удалось загрузить аватар", err); }
    const adminRanks = ["HELPER", "MODERATOR", "ADMIN", "OWNER"];
    gameState.isAdmin = adminRanks.some(r => gameState.rank.toUpperCase().includes(r));
    if (adminPanelBtn) adminPanelBtn.style.display = gameState.isAdmin ? 'block' : 'none';
    if (topupBox) topupBox.style.display = gameState.isAdmin ? 'flex' : 'none';
    syncTopupRange();
    updateCashbackUI();
}

function updateProfileStats() {
    if (!profileStatItems || !profileStatValue) return;
    profileStatItems.textContent = gameState.inventory.length;
    profileStatValue.textContent = `${gameState.inventory.reduce((sum, item) => sum + item.price, 0).toLocaleString()} $B`;
}

function updateCashbackUI() {
    if (!cashbackValue || !cashbackBtn || !cashbackBox) return;
    const amount = gameState.cashback || 0;
    cashbackValue.textContent = `${amount.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 4 })} $B`;
    const ready = amount >= 0.01;
    cashbackBtn.disabled = !ready;
    cashbackBtn.textContent = ready ? 'Забрать кешбек' : 'Кешбек ещё не начислен';
    cashbackBox.classList.toggle('ready', ready);
}

function collectCashback() {
    const amount = roundCashback(gameState.cashback || 0);
    if (amount < 0.01) { updateCashbackUI(); return; }
    gameState.balance = Math.round((gameState.balance + Math.floor(amount * 100) / 100) * 100) / 100;
    gameState.cashback = 0;
    updateBalanceText();
    updateCashbackUI();
    saveProgressToServer();
}

function updateBalanceText() { if (balanceEl) balanceEl.textContent = `${gameState.balance.toLocaleString()} $BURN`; }

function renderBalance() { updateBalanceText(); syncTopupRange(); }

function topupNiceStep(max) {
    if (!(max > 0)) return 1;
    const raw = max / 100;
    const pow = Math.pow(10, Math.floor(Math.log10(raw)));
    const n = raw / pow;
    const mult = n >= 5 ? 5 : n >= 2 ? 2 : 1;
    return Math.max(1, Math.round(mult * pow));
}

function topupBudget() {
    const skin = gameState.selectedInput?.price || 0;
    const target = gameState.selectedOutput?.price || 0;
    if (skin <= 0 || target <= 0) return 0;
    if ((skin / target) * 100 >= CHANCE_CAP) return 0;
    const need = (CHANCE_CAP / 100) * target - skin;
    if (need <= 0) return 0;
    return round2(Math.min(need, gameState.balance || 0));
}

function round2(n) { return Math.round(n * 100) / 100; }

function topupIsAvailable() {
    if (!(gameState.selectedInput && gameState.selectedOutput)) return false;
    return (gameState.selectedInput.price || 0) > 0 && (gameState.selectedOutput.price || 0) > 0;
}

function topupApplyRange() {
    if (!topupRange) return;
    const max = topupBudget();
    topupRange.step = 0.01;
    topupRange.max = max;
    const staked = parseFloat(topupRange.value) || 0;
    if (staked > max) topupRange.value = max;
    if ((gameState.luckBoost || 0) > max) gameState.luckBoost = max;
    if (topupMaxLbl) topupMaxLbl.textContent = max.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function refreshTopupState() {
    if (!topupRange) return;
    const enabled = topupIsAvailable();
    topupRange.disabled = !enabled;
    if (topupBox) topupBox.classList.toggle('off', !enabled);
    if (!enabled) { topupRange.style.setProperty('--fill', '0%'); }
    return enabled;
}

function syncTopupRange() {
    if (!topupRange) return;
    topupApplyRange();
    refreshTopupState();
    updateTopupVisual();
}

function updateTopupVisual() {
    if (!topupRange) return;
    const v = parseFloat(topupRange.value) || 0;
    const max = parseFloat(topupRange.max) || 0;
    topupRange.style.setProperty('--fill', max > 0 ? `${(v / max) * 100}%` : '0%');
    if (topupAmount) topupAmount.textContent = `+${(gameState.luckBoost || 0).toLocaleString()} $B`;
}

function clampCropPan() {
    if (!cropImage) return;
    const dispW = cropImage.naturalWidth * cropBaseScale * cropZoom;
    const dispH = cropImage.naturalHeight * cropBaseScale * cropZoom;
    const maxX = Math.max(0, (dispW - CROP_PREVIEW_SIZE) / 2);
    const maxY = Math.max(0, (dispH - CROP_PREVIEW_SIZE) / 2);
    cropPanX = Math.max(-maxX, Math.min(maxX, cropPanX));
    cropPanY = Math.max(-maxY, Math.min(maxY, cropPanY));
}

function updateCropPreview() {
    if (!cropImage) return;
    clampCropPan();
    const dispW = cropImage.naturalWidth * cropBaseScale * cropZoom;
    const dispH = cropImage.naturalHeight * cropBaseScale * cropZoom;
    avatarCropImg.style.width = dispW + 'px';
    avatarCropImg.style.height = dispH + 'px';
    avatarCropImg.style.left = (CROP_PREVIEW_SIZE / 2 - dispW / 2 + cropPanX) + 'px';
    avatarCropImg.style.top = (CROP_PREVIEW_SIZE / 2 - dispH / 2 + cropPanY) + 'px';
}

function openCropModal(img) {
    cropImage = img;
    cropZoom = 1;
    cropPanX = 0;
    cropPanY = 0;
    cropBaseScale = CROP_PREVIEW_SIZE / Math.min(img.naturalWidth, img.naturalHeight);
    if (avatarCropZoom) avatarCropZoom.value = 1;
    if (avatarCropImg) avatarCropImg.src = img.src;
    updateCropPreview();
    if (avatarCropModal) avatarCropModal.style.display = 'flex';
}

function closeCropModal() {
    if (avatarCropModal) avatarCropModal.style.display = 'none';
    cropImage = null;
}

function confirmCropAndSave() {
    if (!cropImage) return;
    const canvas = document.createElement('canvas');
    canvas.width = CROP_OUTPUT_SIZE;
    canvas.height = CROP_OUTPUT_SIZE;
    const ctx = canvas.getContext('2d');
    const scale = cropBaseScale * cropZoom;
    const dispW = cropImage.naturalWidth * scale;
    const dispH = cropImage.naturalHeight * scale;
    const imgLeft = CROP_PREVIEW_SIZE / 2 - dispW / 2 + cropPanX;
    const imgTop = CROP_PREVIEW_SIZE / 2 - dispH / 2 + cropPanY;
    let srcX = -imgLeft / scale;
    let srcY = -imgTop / scale;
    srcX = Math.max(0, srcX);
    srcY = Math.max(0, srcY);
    const srcW = Math.min(CROP_PREVIEW_SIZE / scale, cropImage.naturalWidth - srcX);
    const srcH = Math.min(CROP_PREVIEW_SIZE / scale, cropImage.naturalHeight - srcY);
    if (srcW > 0 && srcH > 0) ctx.drawImage(cropImage, srcX, srcY, srcW, srcH, 0, 0, CROP_OUTPUT_SIZE, CROP_OUTPUT_SIZE);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
    profileAvatar.src = dataUrl;
    try { localStorage.setItem('burnbox_avatar_' + (gameState.username || 'guest'), dataUrl); } catch (err) { console.error("Не удалось сохранить аватар", err); }
    closeCropModal();
}

window.switchMainScreen = function(screenId, clickedBtnId) {
    if (!gameState.isAuthorized) return;
    if (screenId === 'screen-profile') fetchActualRank(gameState.username);
    document.querySelectorAll('.app-screen').forEach(screen => screen.style.display = 'none');
    const targetScreen = document.getElementById(screenId);
    if (targetScreen) targetScreen.style.display = 'flex';
    document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
    const targetBtn = document.getElementById(clickedBtnId);
    if (targetBtn) targetBtn.classList.add('active');
    renderLeftPane(); renderFullScreens();
};

function renderFullScreens() {
    if (!mainInventoryGrid || !mainMarketGrid) return;
    mainInventoryGrid.innerHTML = '';
    if (gameState.inventory.length === 0) mainInventoryGrid.innerHTML = '<div style="grid-column: 1/-1; color: rgba(255,255,255,0.2); text-align:center; padding-top:40px;">Инвентарь пуст</div>';
    
    gameState.inventory.forEach(item => {
        const card = document.createElement('div'); card.className = 'cube-card';
        card.innerHTML = `<span class="rarity-badge ${item.rarity}">${item.rarity}</span><div class="cube-img-placeholder">${item.icon}</div><div class="cube-name">${item.name}</div><div class="cube-price">${item.price} $B</div>`;
        mainInventoryGrid.appendChild(card);
    });

    mainMarketGrid.innerHTML = '';
    gameState.marketItems.forEach(item => {
        const card = document.createElement('div');
        const qty = gameState.cart[item.id] || 0;
        let controlsHTML = '';
        if (qty > 0) {
            card.className = 'cube-card selected';
            controlsHTML = `<div class="cart-controls" onclick="event.stopPropagation()"><button class="cart-btn" onclick="updateMarketCart(${item.id}, -1)">-</button><span class="cart-qty">${qty}</span><button class="cart-btn" onclick="updateMarketCart(${item.id}, 1)">+</button></div>`;
        } else {
            card.className = 'cube-card'; card.onclick = () => updateMarketCart(item.id, 1);
        }
        card.innerHTML = `<span class="rarity-badge ${item.rarity}">${item.rarity}</span><div class="cube-img-placeholder">${item.icon}</div><div class="cube-name">${item.name}</div><div class="cube-price">${item.price} $B</div>${controlsHTML}`;
        mainMarketGrid.appendChild(card);
    });
    updateCartButtonUI();
}

window.updateMarketCart = function(id, change) {
    let current = gameState.cart[id] || 0;
    let newQty = current + change;
    if (newQty <= 0) delete gameState.cart[id]; else gameState.cart[id] = newQty;
    renderFullScreens();
};

function updateCartButtonUI() {
    if (!cartConfirmBtn) return;
    const totalItems = Object.values(gameState.cart).reduce((a, b) => a + b, 0);
    if (totalItems > 0) { cartConfirmBtn.style.display = 'block'; cartConfirmBtn.textContent = `Купить (${totalItems})`; } 
    else { cartConfirmBtn.style.display = 'none'; }
}

function renderLeftPane() {
    if (!invGrid) return;
    invGrid.innerHTML = '';
    if (gameState.inventory.length === 0) { invGrid.innerHTML = '<div style="grid-column: 1/-1; color: rgba(255,255,255,0.15); text-align:center; padding-top:20px;">Инвентарь пуст</div>'; return; }
    gameState.inventory.forEach(item => {
        const card = document.createElement('div');
        card.onclick = () => selectFileInput(item);
        card.className = `cube-card ${gameState.selectedInput?.id === item.id ? 'selected' : ''}`;
        card.innerHTML = `<span class="rarity-badge ${item.rarity}">${item.rarity}</span><div class="cube-img-placeholder">${item.icon}</div><div class="cube-name">${item.name}</div><div class="cube-price">${item.price} $B</div>`;
        invGrid.appendChild(card);
    });
}

function renderRightPane() {
    if (!targetGrid) return;
    targetGrid.innerHTML = '';
    let filtered = gameState.marketItems.filter(item => item.name.toLowerCase().includes(searchInput?.value.toLowerCase() || "") && item.price >= (parseFloat(priceFrom?.value) || 0) && item.price <= (parseFloat(priceTo?.value) || Infinity));
    filtered.sort((a, b) => gameState.sortAsc ? a.price - b.price : b.price - a.price);

    if (targetCount) targetCount.textContent = filtered.length;

    if (filtered.length === 0) {
        targetGrid.innerHTML = '<div class="empty-grid">Ничего не найдено 🔍</div>';
        return;
    }

    filtered.forEach(item => {
        const isLocked = gameState.selectedInput && item.price <= gameState.selectedInput.price;
        const card = document.createElement('div');
        card.className = `cube-card ${gameState.selectedOutput?.id === item.id ? 'selected' : ''} ${isLocked ? 'locked' : ''}`;
        card.innerHTML = `<span class="rarity-badge ${item.rarity}">${item.rarity}</span><div class="cube-img-placeholder">${item.icon}</div><div class="cube-name">${item.name}</div><div class="cube-price">${item.price} $B</div>`;
        if (!isLocked) card.onclick = () => selectFileOutput(item);
        targetGrid.appendChild(card);
    });
}

function selectFileInput(item) {
    gameState.selectedInput = item;
    inputSlot.innerHTML = `<div class="cube-img-placeholder">${item.icon}</div><div style="font-size:10px;font-weight:700;">${item.price} $B</div>`;
    inputSlot.classList.add('active-slot');
    if (gameState.selectedOutput && gameState.selectedOutput.price <= item.price) { gameState.selectedOutput = null; outputSlot.innerHTML = '<div class="empty-placeholder">?</div>'; outputSlot.classList.remove('active-slot'); }
    calculateChance(); renderLeftPane(); renderRightPane(); 
}

function selectFileOutput(item) {
    if (gameState.selectedInput && item.price <= gameState.selectedInput.price) return;
    gameState.selectedOutput = item;
    outputSlot.innerHTML = `<div class="cube-img-placeholder">${item.icon}</div><div style="font-size:10px;font-weight:700;">${item.price} $B</div>`;
    outputSlot.classList.add('active-slot');
    calculateChance(); renderRightPane();
}

function getStakeAmount(pendingBoost = 0) {
    return Math.max(0, (gameState.luckBoost || 0) + pendingBoost);
}

function getStakeChance(pendingBoost = 0) {
    const target = gameState.selectedOutput?.price || 0;
    const skin = gameState.selectedInput?.price || 0;
    if (target <= 0 || skin <= 0) return 0;
    const base = (skin / target) * 100;
    if (base >= CHANCE_CAP) return base;
    return Math.min(((skin + getStakeAmount(pendingBoost)) / target) * 100, CHANCE_CAP);
}

function getBaseChance() {
    const target = gameState.selectedOutput?.price || 0;
    const skin = gameState.selectedInput?.price || 0;
    if (target <= 0 || skin <= 0) return 0;
    return (skin / target) * 100;
}

function getEffectiveChance(pendingBoost = 0) {
    return getStakeChance(pendingBoost);
}

function calculateChance(pendingBoost = 0, instant = false) {
    syncTopupRange();
    if (!gameState.selectedInput || !gameState.selectedOutput) { updateWheelUI(0, instant); return; }
    updateWheelUI(getEffectiveChance(pendingBoost), instant);
}

const WHEEL_SVG_R = 43;
let wheelArcEl = null;
let arcAnimId = null;
let lastArcValue = 0;

function buildWheelSvg() {
    if (!wheelScale || wheelArcEl) return;
    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', '0 0 100 100');
    svg.style.width = '100%';
    svg.style.height = '100%';
    const base = document.createElementNS(svgNS, 'circle');
    base.setAttribute('cx', '50'); base.setAttribute('cy', '50');
    base.setAttribute('r', String(WHEEL_SVG_R));
    base.setAttribute('fill', '#1c1f24');
    base.setAttribute('stroke', 'rgba(255,255,255,0.05)');
    base.setAttribute('stroke-width', '1');
    const arc = document.createElementNS(svgNS, 'path');
    arc.setAttribute('fill', 'none');
    arc.setAttribute('stroke', '#ff4d00');
    arc.setAttribute('stroke-width', '11');
    arc.setAttribute('stroke-linecap', 'round');
    arc.setAttribute('d', '');
    svg.appendChild(base);
    svg.appendChild(arc);
    wheelScale.innerHTML = '';
    wheelScale.appendChild(svg);
    wheelArcEl = arc;
}

function setWheelArcRaw(chance) {
    if (!wheelArcEl) return;
    const f = Math.max(0, Math.min(1, chance / 100));
    const R = WHEEL_SVG_R, CX = 50, CY = 50;
    const toXY = (deg) => {
        const rad = deg * Math.PI / 180;
        return [(CX + R * Math.cos(rad)).toFixed(3), (CY + R * Math.sin(rad)).toFixed(3)];
    };
    if (f >= 1) {
        const [x1, y1] = toXY(90);
        const [x2, y2] = toXY(270);
        wheelArcEl.setAttribute('d', `M ${x1} ${y1} A ${R} ${R} 0 1 1 ${x2} ${y2} A ${R} ${R} 0 1 1 ${x1} ${y1}`);
        return;
    }
    const startDeg = 90 - f * 180;
    const [sx, sy] = toXY(startDeg);
    const [ex, ey] = toXY(startDeg + f * 360);
    const large = f > 0.5 ? 1 : 0;
    wheelArcEl.setAttribute('d', `M ${sx} ${sy} A ${R} ${R} 0 ${large} 1 ${ex} ${ey}`);
}

function renderWheelArc(targetChance) {
    buildWheelSvg();
    if (!wheelArcEl) return;
    if (arcAnimId) { cancelAnimationFrame(arcAnimId); arcAnimId = null; }
    const from = lastArcValue;
    const to = Math.max(0, Math.min(100, targetChance));
    const startTime = performance.now();
    const DURATION = 450;
    const step = (now) => {
        const t = Math.min(1, (now - startTime) / DURATION);
        const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
        const val = from + (to - from) * eased;
        lastArcValue = val;
        setWheelArcRaw(val);
        if (t < 1) { arcAnimId = requestAnimationFrame(step); }
        else { lastArcValue = to; arcAnimId = null; }
    };
    arcAnimId = requestAnimationFrame(step);
}

function updateWheelUI(chance, instant = false) {
    if (!chanceText || !wheelScale || !spinBtn || !infoBlock) return;
    chanceText.style.color = "#ffffff";
    if (chanceSubText) chanceSubText.style.display = 'block';

    if (!gameState.selectedInput || !gameState.selectedOutput) {
        if (instant) { if (arcAnimId) { cancelAnimationFrame(arcAnimId); arcAnimId = null; } lastArcValue = 0; buildWheelSvg(); setWheelArcRaw(0); }
        else renderWheelArc(0);
        spinBtn.disabled = true; spinBtn.textContent = gameState.selectedInput ? 'Выберите цель' : 'Выберите скины';
        chanceText.textContent = '--'; chanceText.style.color = "rgba(255,255,255,0.3)";
        if (chanceSubText) chanceSubText.style.display = 'none'; return;
    }
    spinBtn.disabled = false; spinBtn.textContent = 'Апгрейд';
    chanceText.textContent = `${chance.toFixed(2)}%`;
    if (instant) { if (arcAnimId) { cancelAnimationFrame(arcAnimId); arcAnimId = null; } lastArcValue = chance; setWheelArcRaw(chance); }
    else renderWheelArc(chance);
}

function startUpgrade() {
    if (!gameState.selectedInput || !gameState.selectedOutput) return;
    spinBtn.disabled = true; spinBtn.textContent = 'Крутим...';
    const baseChance = (gameState.selectedInput.price / gameState.selectedOutput.price) * 100;
    const rollChance = getStakeChance();
    const isWin = Math.random() * 100 <= rollChance;

    const stake = Math.min(gameState.luckBoost || 0, gameState.balance || 0);
    if (stake > 0) {
        gameState.balance = Math.max(0, Math.round((gameState.balance - stake) * 100) / 100);
        updateBalanceText();
    }

    const earned = roundCashback((gameState.selectedInput.price || 0) * CASHBACK_RATE);
    if (earned > 0) {
        gameState.cashback = roundCashback((gameState.cashback || 0) + earned);
        updateCashbackUI();
    }
    

    if (gameState.isTurbo) { resolveResult(isWin); } 
    else {
        if (arrowEl) { arrowEl.style.transition = "none"; currentRotation = 0; arrowEl.style.transform = `rotate(0deg)`; }
        setTimeout(() => {
            const startOrange = (50 - (baseChance / 2)), endOrange = (50 + (baseChance / 2));
            let finalAngle = isWin ? startOrange + (Math.random() * (endOrange - startOrange)) : Math.random() * 100;
            if (!isWin && finalAngle >= startOrange && finalAngle <= endOrange) finalAngle = (endOrange + Math.random() * (100 - (endOrange - startOrange))) % 100;
            currentRotation = (5 * 360) + (finalAngle * 3.6);
            if (arrowEl) { arrowEl.style.transition = "transform 4s cubic-bezier(0.17, 0.67, 0.12, 0.99)"; arrowEl.style.transform = `rotate(${currentRotation}deg)`; }
            setTimeout(() => { resolveResult(isWin); }, 4100); 
        }, 50);
    }
}

function resolveResult(isWin) {
    if (arrowEl) arrowEl.style.transition = "none";
    if (chanceSubText) chanceSubText.style.display = 'none';
    if (chanceText) { chanceText.textContent = isWin ? "УСПЕХ" : "НЕУДАЧА"; chanceText.style.color = isWin ? "#00ff66" : "#ff3333"; }

    gameState.luckBoost = 0;

    gameState.inventory = gameState.inventory.filter(i => i.id !== gameState.selectedInput.id);
    if (isWin) gameState.inventory.push({ ...gameState.selectedOutput, id: Math.random(), baseId: gameState.selectedOutput.baseId || gameState.selectedOutput.id });

    gameState.selectedInput = null; gameState.selectedOutput = null;
    inputSlot.innerHTML = '<div class="empty-placeholder">+</div>'; outputSlot.innerHTML = '<div class="empty-placeholder">?</div>';
    inputSlot.classList.remove('active-slot'); outputSlot.classList.remove('active-slot');
    
    renderLeftPane(); renderRightPane(); renderFullScreens(); updateProfileStats();
    syncTopupRange();
    saveProgressToServer(); 
    
    spinBtn.disabled = false; spinBtn.textContent = 'Апгрейд';
    setTimeout(() => { calculateChance(); }, 2000);
}

function setupEventListeners() {
    if (authSubmitBtn) {
        authSubmitBtn.onclick = async () => {
            const user = authUsernameInput.value.trim();
            const pass = authPasswordInput.value.trim();
            try {
                const response = await fetch(API_BASE + '/login', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: user, password: pass })
                });
                const data = await response.json();
                
                if (response.status === 403) { showBanScreen(data.ban_until, data.ban_reason); return; }
                
                if (response.ok && data.status === "success") {
                    saveSession(user, pass);
                    authStatusMsg.textContent = "Вход выполнен!"; authStatusMsg.style.color = "#00ff66";
                    setTimeout(() => bypassAuth(user, data.rank, data.balance, data.luck, data.inventory, data.cashback), 800);
                } else {
                    authStatusMsg.textContent = data.message || "Ошибка входа"; authStatusMsg.style.color = "#ff3333";
                }
            } catch (e) { authStatusMsg.textContent = "Ошибка сервера!"; }
        };
    }

    if (authRegBtn) {
        authRegBtn.onclick = async () => {
            const user = authUsernameInput.value.trim(); const pass = authPasswordInput.value.trim();
            try {
                const response = await fetch(API_BASE + '/register', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: user, password: pass })
                });
                const data = await response.json();
                if (response.ok && data.status === "success") {
                    authStatusMsg.textContent = "Аккаунт создан! Теперь нажмите 'Войти'."; authStatusMsg.style.color = "#00ccff";
                } else { authStatusMsg.textContent = data.message || "Ошибка!"; authStatusMsg.style.color = "#ff3333"; }
            } catch (error) { authStatusMsg.textContent = "Ошибка сервера!"; }
        };
    }

    if (authTgBtn) authTgBtn.onclick = () => { window.open("https://t.me/burningmarket_bot", "_blank"); };
    if (editNicknameBtn) editNicknameBtn.onclick = () => { nicknameDisplayMode.style.display = 'none'; nicknameEditMode.style.display = 'flex'; nicknameInput.focus(); };
    if (saveNicknameBtn) saveNicknameBtn.onclick = () => { const newName = nicknameInput.value.trim(); if (newName) { gameState.username = newName; updateProfileUI(); } nicknameEditMode.style.display = 'none'; nicknameDisplayMode.style.display = 'flex'; };
    if (avatarUpload && profileAvatar) avatarUpload.onchange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (event) => {
            const img = new Image();
            img.onload = () => openCropModal(img);
            img.src = event.target.result;
        };
        reader.readAsDataURL(file);
        avatarUpload.value = '';
    };
    if (avatarCropPreview) {
        avatarCropPreview.addEventListener('pointerdown', (e) => {
            isCropDragging = true;
            cropDragStart = { x: e.clientX - cropPanX, y: e.clientY - cropPanY };
            avatarCropPreview.setPointerCapture(e.pointerId);
        });
        avatarCropPreview.addEventListener('pointermove', (e) => {
            if (!isCropDragging) return;
            cropPanX = e.clientX - cropDragStart.x;
            cropPanY = e.clientY - cropDragStart.y;
            updateCropPreview();
        });
        avatarCropPreview.addEventListener('pointerup', () => { isCropDragging = false; });
        avatarCropPreview.addEventListener('pointercancel', () => { isCropDragging = false; });
    }
    if (avatarCropZoom) avatarCropZoom.oninput = () => { cropZoom = parseFloat(avatarCropZoom.value) || 1; updateCropPreview(); };
    if (avatarCropCancel) avatarCropCancel.onclick = closeCropModal;
    if (avatarCropConfirm) avatarCropConfirm.onclick = confirmCropAndSave;
    if (adminPanelBtn) adminPanelBtn.onclick = () => { window.open("https://t.me/burning_market_admin_panel_bot", "_blank"); };
    if (logoutBtn) logoutBtn.onclick = () => { if (logoutModal) logoutModal.style.display = 'flex'; };
    if (logoutConfirmNo) logoutConfirmNo.onclick = () => { if (logoutModal) logoutModal.style.display = 'none'; };
    if (logoutConfirmYes) { logoutConfirmYes.onclick = () => { if (logoutModal) logoutModal.style.display = 'none'; clearSession(); gameState.isAuthorized = false; gameWrapper.style.display = 'none'; screenAuth.style.display = 'flex'; }; }

    if (spinBtn) spinBtn.onclick = startUpgrade;
    if (turboBtn) { turboBtn.onclick = () => { gameState.isTurbo = !gameState.isTurbo; turboBtn.textContent = `⚡ Быстрая прокрутка: ${gameState.isTurbo ? 'ВКЛ' : 'ВЫКЛ'}`; turboBtn.classList.toggle('active', gameState.isTurbo); }; }

    if (cashbackBtn) cashbackBtn.onclick = collectCashback;
    if (searchInput) searchInput.oninput = renderRightPane; if (priceFrom) priceFrom.oninput = renderRightPane; if (priceTo) priceTo.oninput = renderRightPane;
    if (searchInput) searchInput.oninput = () => { if (searchClear) searchClear.classList.toggle('visible', !!searchInput.value); renderRightPane(); };
    if (searchClear) searchClear.onclick = () => { if (searchInput) { searchInput.value = ''; searchInput.focus(); } searchClear.classList.remove('visible'); renderRightPane(); };
    if (sortPriceBtn) sortPriceBtn.onclick = () => { gameState.sortAsc = !gameState.sortAsc; if (sortIco) sortIco.textContent = gameState.sortAsc ? '⬇' : '⬆'; sortPriceBtn.classList.toggle('active', !gameState.sortAsc); renderRightPane(); };

    if (topupRange) {
        topupRange.oninput = () => {
            const v = parseFloat(topupRange.value) || 0;
            gameState.luckBoost = v;
            updateTopupVisual();
            calculateChance(true);
        };
        topupRange.onchange = () => {
            if ((gameState.luckBoost || 0) > 0 && topupBox) {
                topupBox.classList.remove('flash');
                void topupBox.offsetWidth;
                topupBox.classList.add('flash');
            }
            syncTopupRange();
        };
        updateTopupVisual();
    }

    if (document.getElementById('btn-x2')) document.getElementById('btn-x2').onclick = () => autoSelectTargetByChance(50);
    if (document.getElementById('btn-x4')) document.getElementById('btn-x4').onclick = () => autoSelectTargetByChance(25);
    if (document.getElementById('btn-30')) document.getElementById('btn-30').onclick = () => autoSelectTargetByChance(30);
    if (document.getElementById('btn-75')) document.getElementById('btn-75').onclick = () => autoSelectTargetByChance(75);

    const modal = document.getElementById('buy-modal');
    if (cartConfirmBtn) {
        cartConfirmBtn.onclick = () => {
            let totalCost = 0; for (let id in gameState.cart) totalCost += gameState.marketItems.find(i => i.id == id).price * gameState.cart[id];
            document.getElementById('modal-total-price').textContent = `${totalCost} $B`;
            if (modal) modal.style.display = 'flex';
        };
    }
    if (document.getElementById('modal-no')) document.getElementById('modal-no').onclick = () => { if (modal) modal.style.display = 'none'; };
    if (document.getElementById('modal-yes')) {
        document.getElementById('modal-yes').onclick = () => {
            let totalCost = 0; for (let id in gameState.cart) totalCost += gameState.marketItems.find(i => i.id == id).price * gameState.cart[id];
            if (gameState.balance >= totalCost) {
                gameState.balance -= totalCost;
                for (let id in gameState.cart) {
                    let item = gameState.marketItems.find(i => i.id == id);
                    for (let i = 0; i < gameState.cart[id]; i++) gameState.inventory.push({ ...item, id: Math.random(), baseId: item.id });
                }
                gameState.cart = {}; if (modal) modal.style.display = 'none';
                renderBalance(); renderLeftPane(); renderFullScreens(); updateProfileStats();
                saveProgressToServer(); 
            } else { alert('Недостаточно средств на балансе!'); if (modal) modal.style.display = 'none'; }
        };
    }
}

function autoSelectTargetByChance(targetChance) {
    if (!gameState.selectedInput) return alert('Сначала выберите исходный скин!');
    const idealPrice = (gameState.selectedInput.price / targetChance) * 100;
    const validItems = gameState.marketItems.filter(item => item.price > gameState.selectedInput.price);
    if (validItems.length === 0) return alert('Нет подходящих скинов для апгрейда!');
    selectFileOutput(validItems.reduce((prev, curr) => (Math.abs(curr.price - idealPrice) < Math.abs(prev.price - idealPrice)) ? curr : prev));
}

window.onload = init;