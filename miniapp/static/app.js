const tg = window.Telegram?.WebApp;

if (tg) {
    tg.ready();
    tg.expand();
}

const telegramUser = tg?.initDataUnsafe?.user || null;
const telegramInitData = tg?.initData || "";

const telegramNameElement = document.getElementById("telegramName");
const telegramUsernameElement = document.getElementById("telegramUsername");
const statusMessage = document.getElementById("statusMessage");

const profileForm = document.getElementById("profileForm");

const nameInput = document.getElementById("name");
const facultyInput = document.getElementById("faculty");
const courseInput = document.getElementById("course");
const goalInput = document.getElementById("goal");
const aboutInput = document.getElementById("about");
const interestsInput = document.getElementById("interests");

const profilePhotoInput = document.getElementById("profilePhotoInput");
const myPhotoPreview = document.getElementById("myPhotoPreview");
const myPhotoLetter = document.getElementById("myPhotoLetter");
const photoStatus = document.getElementById("photoStatus");

const tabButtons = document.querySelectorAll(".tab-button");

const profileTab = document.getElementById("profileTab");
const browseTab = document.getElementById("browseTab");
const matchesTab = document.getElementById("matchesTab");
const statsTab = document.getElementById("statsTab");

const goalFilterButtons = document.querySelectorAll(".goal-filter-chip");
const loadProfileButton = document.getElementById("loadProfileButton");
const browseCard = document.getElementById("browseCard");
const browseStatus = document.getElementById("browseStatus");

const browseAvatar = document.getElementById("browseAvatar");
const browseAvatarLetter = document.getElementById("browseAvatarLetter");
const browseName = document.getElementById("browseName");
const browseMeta = document.getElementById("browseMeta");
const browseAbout = document.getElementById("browseAbout");
const browseInterests = document.getElementById("browseInterests");

const backButton = document.getElementById("backButton");
const likeButton = document.getElementById("likeButton");
const skipButton = document.getElementById("skipButton");
const reportButton = document.getElementById("reportButton");
const blockButton = document.getElementById("blockButton");

const loadMatchesButton = document.getElementById("loadMatchesButton");
const matchesList = document.getElementById("matchesList");
const matchesStatus = document.getElementById("matchesStatus");

const loadStatsButton = document.getElementById("loadStatsButton");
const statsStatus = document.getElementById("statsStatus");

const profilesCount = document.getElementById("profilesCount");
const likesCount = document.getElementById("likesCount");
const skipsCount = document.getElementById("skipsCount");
const matchesCount = document.getElementById("matchesCount");
const reportsCount = document.getElementById("reportsCount");
const blocksCount = document.getElementById("blocksCount");

let currentBrowseProfile = null;
let selectedBrowseGoal = "";

const authErrorText = "Ошибка авторизации Telegram. Открой Mini App через кнопку меню в боте.";


function setStatus(message, type = "") {
    statusMessage.textContent = message;
    statusMessage.className = "status";

    if (type) {
        statusMessage.classList.add(type);
    }
}


function setBrowseStatus(message, type = "") {
    browseStatus.textContent = message;
    browseStatus.className = "status";

    if (type) {
        browseStatus.classList.add(type);
    }
}


function setMatchesStatus(message, type = "") {
    matchesStatus.textContent = message;
    matchesStatus.className = "status";

    if (type) {
        matchesStatus.classList.add(type);
    }
}


function setStatsStatus(message, type = "") {
    statsStatus.textContent = message;
    statsStatus.className = "status";

    if (type) {
        statsStatus.classList.add(type);
    }
}


function setPhotoStatus(message, type = "") {
    photoStatus.textContent = message;
    photoStatus.className = "photo-status";

    if (type === "success") {
        photoStatus.style.color = "#1f7a5c";
    } else if (type === "error") {
        photoStatus.style.color = "#b91c1c";
    } else {
        photoStatus.style.color = "#6b7c75";
    }
}


function getAuthHeaders() {
    return {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": telegramInitData
    };
}


function getTelegramAuthOnlyHeaders() {
    return {
        "X-Telegram-Init-Data": telegramInitData
    };
}


function escapeHtml(value) {
    return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function getFirstLetter(name) {
    if (!name) {
        return "Ф";
    }

    return String(name).trim().charAt(0).toUpperCase() || "Ф";
}


function renderPhoto(container, letterElement, photoUrl, fallbackLetter) {
    container.innerHTML = "";

    if (photoUrl) {
        const image = document.createElement("img");
        image.src = photoUrl;
        image.alt = "Фото профиля";

        image.onerror = () => {
            container.innerHTML = "";

            const span = document.createElement("span");
            span.textContent = fallbackLetter;

            container.appendChild(span);
        };

        container.appendChild(image);
        return;
    }

    const span = document.createElement("span");
    span.textContent = fallbackLetter;

    container.appendChild(span);

    if (letterElement) {
        letterElement.textContent = fallbackLetter;
    }
}


function setActiveGoalFilter(goal) {
    selectedBrowseGoal = goal;

    goalFilterButtons.forEach((button) => {
        const buttonGoal = button.dataset.goal || "";
        button.classList.toggle("active", buttonGoal === goal);
    });
}


async function fillTelegramUserInfo() {
    try {
        const response = await fetch("/api/me", {
            method: "GET",
            headers: getTelegramAuthOnlyHeaders()
        });

        if (!response.ok) {
            throw new Error("Не удалось получить пользователя");
        }

        const user = await response.json();

        const fullName = [user.first_name, user.last_name]
            .filter(Boolean)
            .join(" ");

        telegramNameElement.textContent = fullName || "Пользователь Telegram";

        const usernameText = user.username
            ? `@${user.username}`
            : "username не указан";

        const modeText = user.is_dev_auth
            ? "режим браузера / тестовый пользователь"
            : "Telegram Mini App";

        telegramUsernameElement.textContent = `${usernameText} · ID: ${user.id} · ${modeText}`;
    } catch (error) {
        telegramNameElement.textContent = "Ошибка";

        const initDataLength = telegramInitData ? telegramInitData.length : 0;

        telegramUsernameElement.textContent =
            `Не удалось определить пользователя. initData length: ${initDataLength}`;

        console.error(error);
    }
}


async function loadProfile() {
    try {
        const response = await fetch("/api/profile/me", {
            method: "GET",
            headers: getTelegramAuthOnlyHeaders()
        });

        if (response.status === 404) {
            setStatus("Анкета пока не создана. Заполни форму ниже.");
            renderPhoto(myPhotoPreview, myPhotoLetter, null, "Ф");
            return;
        }

        if (response.status === 401) {
            setStatus(authErrorText, "error");
            return;
        }

        if (!response.ok) {
            throw new Error("Не удалось загрузить анкету");
        }

        const profile = await response.json();

        nameInput.value = profile.name || "";
        facultyInput.value = profile.faculty || "";
        courseInput.value = profile.course || "";
        goalInput.value = profile.goal || "";
        aboutInput.value = profile.about || "";
        interestsInput.value = profile.interests || "";

        const fallbackLetter = getFirstLetter(profile.name);

        renderPhoto(
            myPhotoPreview,
            myPhotoLetter,
            profile.photo_url,
            fallbackLetter
        );

        setStatus("Анкета загружена.", "success");
    } catch (error) {
        setStatus("Ошибка загрузки анкеты.", "error");
        console.error(error);
    }
}


async function saveProfile(event) {
    event.preventDefault();

    const payload = {
        name: nameInput.value.trim(),
        faculty: facultyInput.value.trim(),
        course: courseInput.value,
        goal: goalInput.value,
        about: aboutInput.value.trim(),
        interests: interestsInput.value.trim(),
        photo_file_id: null
    };

    if (
        !payload.name ||
        !payload.faculty ||
        !payload.course ||
        !payload.goal ||
        !payload.about ||
        !payload.interests
    ) {
        setStatus("Заполни все поля.", "error");
        return;
    }

    try {
        const response = await fetch("/api/profile", {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify(payload)
        });

        if (response.status === 401) {
            setStatus(authErrorText, "error");
            return;
        }

        if (!response.ok) {
            throw new Error("Не удалось сохранить анкету");
        }

        setStatus("Анкета сохранена ✅", "success");

        await loadProfile();

        if (tg) {
            tg.HapticFeedback?.notificationOccurred("success");
        }
    } catch (error) {
        setStatus("Ошибка сохранения анкеты.", "error");

        if (tg) {
            tg.HapticFeedback?.notificationOccurred("error");
        }

        console.error(error);
    }
}


async function uploadProfilePhoto() {
    const file = profilePhotoInput.files?.[0];

    if (!file) {
        return;
    }

    if (!file.type.startsWith("image/")) {
        setPhotoStatus("Можно загрузить только изображение.", "error");
        return;
    }

    const maxSizeBytes = 5 * 1024 * 1024;

    if (file.size > maxSizeBytes) {
        setPhotoStatus("Фото слишком большое. Максимум 5 МБ.", "error");
        return;
    }

    const localPreviewUrl = URL.createObjectURL(file);
    renderPhoto(myPhotoPreview, myPhotoLetter, localPreviewUrl, getFirstLetter(nameInput.value));

    const formData = new FormData();
    formData.append("photo", file);

    setPhotoStatus("Загружаем фото...");

    try {
        const response = await fetch("/api/profile/photo", {
            method: "POST",
            headers: getTelegramAuthOnlyHeaders(),
            body: formData
        });

        if (response.status === 400) {
            setPhotoStatus("Сначала сохрани анкету, потом загрузи фото.", "error");
            return;
        }

        if (response.status === 401) {
            setPhotoStatus("Ошибка авторизации Telegram.", "error");
            return;
        }

        if (!response.ok) {
            throw new Error("Не удалось загрузить фото");
        }

        const data = await response.json();

        renderPhoto(
            myPhotoPreview,
            myPhotoLetter,
            data.photo_url,
            getFirstLetter(nameInput.value)
        );

        setPhotoStatus("Фото обновлено ✅", "success");

        if (tg) {
            tg.HapticFeedback?.notificationOccurred("success");
        }
    } catch (error) {
        setPhotoStatus("Ошибка загрузки фото.", "error");
        console.error(error);

        if (tg) {
            tg.HapticFeedback?.notificationOccurred("error");
        }
    } finally {
        URL.revokeObjectURL(localPreviewUrl);
    }
}


function switchTab(tabName) {
    tabButtons.forEach((button) => {
        button.classList.toggle("active", button.dataset.tab === tabName);
    });

    profileTab.classList.toggle("active", tabName === "profile");
    browseTab.classList.toggle("active", tabName === "browse");
    matchesTab.classList.toggle("active", tabName === "matches");
    statsTab.classList.toggle("active", tabName === "stats");

    if (tabName === "matches") {
        loadMatches();
    }

    if (tabName === "stats") {
        loadStats();
    }
}


function renderBrowseProfile(profile) {
    currentBrowseProfile = profile;

    if (!profile) {
        browseCard.classList.add("hidden");
        return;
    }

    browseName.textContent = profile.name;

    browseMeta.textContent =
        `${profile.faculty} · ${profile.course} курс · ${profile.goal}`;

    browseAbout.textContent = profile.about;
    browseInterests.textContent = profile.interests;

    renderPhoto(
        browseAvatar,
        browseAvatarLetter,
        profile.photo_url,
        getFirstLetter(profile.name)
    );

    browseCard.classList.remove("hidden");
}


async function loadNextBrowseProfile() {
    setBrowseStatus("Загрузка анкеты...");
    browseCard.classList.add("hidden");
    currentBrowseProfile = null;

    const query = selectedBrowseGoal
        ? `?goal=${encodeURIComponent(selectedBrowseGoal)}`
        : "";

    try {
        const response = await fetch(`/api/browse/next${query}`, {
            method: "GET",
            headers: getTelegramAuthOnlyHeaders()
        });

        if (response.status === 400) {
            setBrowseStatus("Сначала создай свою анкету во вкладке «Анкета».", "error");
            return;
        }

        if (response.status === 401) {
            setBrowseStatus(authErrorText, "error");
            return;
        }

        if (!response.ok) {
            throw new Error("Не удалось загрузить анкету");
        }

        const data = await response.json();

        if (!data.profile) {
            renderBrowseProfile(null);
            setBrowseStatus("Анкеты закончились. Попробуй позже или выбери другой фильтр.");
            return;
        }

        renderBrowseProfile(data.profile);
        setBrowseStatus("Анкета загружена.", "success");
    } catch (error) {
        setBrowseStatus("Ошибка загрузки анкеты.", "error");
        console.error(error);
    }
}


async function undoLastSkip() {
    setBrowseStatus("Возвращаем предыдущую анкету...");

    try {
        const response = await fetch("/api/profiles/undo-skip", {
            method: "POST",
            headers: getAuthHeaders()
        });

        if (response.status === 400) {
            setBrowseStatus("Сначала создай свою анкету во вкладке «Анкета».", "error");
            return;
        }

        if (response.status === 401) {
            setBrowseStatus(authErrorText, "error");
            return;
        }

        if (!response.ok) {
            throw new Error("Не удалось вернуться к предыдущей анкете");
        }

        const data = await response.json();

        if (!data.ok || !data.profile) {
            setBrowseStatus(data.message || "Нет предыдущей пропущенной анкеты.");
            return;
        }

        renderBrowseProfile(data.profile);
        setBrowseStatus("↩️ Вернулись к предыдущей анкете.", "success");

        if (tg) {
            tg.HapticFeedback?.notificationOccurred("success");
        }
    } catch (error) {
        setBrowseStatus("Ошибка возврата к предыдущей анкете.", "error");
        console.error(error);

        if (tg) {
            tg.HapticFeedback?.notificationOccurred("error");
        }
    }
}


async function sendBrowseAction(action) {
    if (!currentBrowseProfile) {
        setBrowseStatus("Сначала загрузи анкету.", "error");
        return;
    }

    try {
        const response = await fetch("/api/browse/action", {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({
                target_user_id: currentBrowseProfile.telegram_id,
                action: action
            })
        });

        if (response.status === 401) {
            setBrowseStatus(authErrorText, "error");
            return;
        }

        if (!response.ok) {
            throw new Error("Не удалось выполнить действие");
        }

        const data = await response.json();

        if (action === "like") {
            if (data.match) {
                setBrowseStatus(
                    "🎉 Мэтч! Контакт теперь доступен во вкладке «Мэтчи».",
                    "success"
                );

                loadMatches();

                if (tg) {
                    tg.HapticFeedback?.notificationOccurred("success");
                }
            } else {
                setBrowseStatus("❤️ Лайк сохранён.", "success");
            }
        }

        if (action === "skip") {
            setBrowseStatus("➡️ Анкета пропущена.", "success");
        }

        if (action === "report") {
            setBrowseStatus("⚠️ Жалоба сохранена. Анкета скрыта.", "success");
        }

        if (action === "block") {
            setBrowseStatus("🚫 Пользователь заблокирован.", "success");
            loadMatches();
        }

        await loadNextBrowseProfile();
    } catch (error) {
        setBrowseStatus("Ошибка действия.", "error");
        console.error(error);

        if (tg) {
            tg.HapticFeedback?.notificationOccurred("error");
        }
    }
}


async function unlikeProfile(targetUserId) {
    setMatchesStatus("Убираем лайк...");

    try {
        const response = await fetch("/api/profiles/unlike", {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({
                target_user_id: targetUserId
            })
        });

        if (response.status === 400) {
            setMatchesStatus("Сначала создай свою анкету.", "error");
            return;
        }

        if (response.status === 401) {
            setMatchesStatus(authErrorText, "error");
            return;
        }

        if (!response.ok) {
            throw new Error("Не удалось убрать лайк");
        }

        const data = await response.json();

        if (!data.ok) {
            setMatchesStatus(data.message || "Лайк уже был убран.");
            return;
        }

        setMatchesStatus("💔 Лайк убран. Мэтч удалён.", "success");

        await loadMatches();

        if (tg) {
            tg.HapticFeedback?.notificationOccurred("success");
        }
    } catch (error) {
        setMatchesStatus("Ошибка удаления лайка.", "error");
        console.error(error);

        if (tg) {
            tg.HapticFeedback?.notificationOccurred("error");
        }
    }
}


function renderMatches(matches) {
    matchesList.innerHTML = "";

    if (!matches.length) {
        matchesList.innerHTML = `
            <div class="match-card">
                <div class="match-avatar">♡</div>
                <div class="match-card-content">
                    <h3>Мэтчей пока нет</h3>
                    <p>Смотри анкеты и ставь лайки. Когда лайк будет взаимным, контакт появится здесь.</p>
                </div>
            </div>
        `;
        return;
    }

    matches.forEach((profile) => {
        const username = profile.username
            ? `@${escapeHtml(profile.username)}`
            : "username не указан";

        const card = document.createElement("div");
        card.className = "match-card";

        const avatar = document.createElement("div");
        avatar.className = "match-avatar";

        renderPhoto(
            avatar,
            null,
            profile.photo_url,
            getFirstLetter(profile.name)
        );

        const content = document.createElement("div");
        content.className = "match-card-content";

        content.innerHTML = `
            <h3>${escapeHtml(profile.name)}</h3>
            <p><b>Факультет / направление:</b> ${escapeHtml(profile.faculty)}</p>
            <p><b>Курс:</b> ${escapeHtml(profile.course)}</p>
            <p><b>Цель:</b> ${escapeHtml(profile.goal)}</p>
            <p><b>Интересы:</b> ${escapeHtml(profile.interests)}</p>
            <div class="match-contact">Контакт: ${username}</div>
            <button type="button" class="match-unlike-button" data-user-id="${profile.telegram_id}">
                💔 Убрать лайк
            </button>
        `;

        card.appendChild(avatar);
        card.appendChild(content);

        const unlikeButton = card.querySelector(".match-unlike-button");

        unlikeButton.addEventListener("click", () => {
            unlikeProfile(profile.telegram_id);
        });

        matchesList.appendChild(card);
    });
}


async function loadMatches() {
    setMatchesStatus("Загрузка мэтчей...");

    try {
        const response = await fetch("/api/matches", {
            method: "GET",
            headers: getTelegramAuthOnlyHeaders()
        });

        if (response.status === 400) {
            setMatchesStatus("Сначала создай свою анкету.", "error");
            return;
        }

        if (response.status === 401) {
            setMatchesStatus(authErrorText, "error");
            return;
        }

        if (!response.ok) {
            throw new Error("Не удалось загрузить мэтчи");
        }

        const data = await response.json();

        renderMatches(data.matches || []);
        setMatchesStatus("Мэтчи обновлены.", "success");
    } catch (error) {
        setMatchesStatus("Ошибка загрузки мэтчей.", "error");
        console.error(error);
    }
}


async function loadStats() {
    setStatsStatus("Загрузка статистики...");

    try {
        const response = await fetch("/api/stats", {
            method: "GET",
            headers: getTelegramAuthOnlyHeaders()
        });

        if (response.status === 401) {
            setStatsStatus(authErrorText, "error");
            return;
        }

        if (!response.ok) {
            throw new Error("Не удалось загрузить статистику");
        }

        const stats = await response.json();

        profilesCount.textContent = stats.profiles_count ?? 0;
        likesCount.textContent = stats.likes_count ?? 0;
        skipsCount.textContent = stats.skips_count ?? 0;
        matchesCount.textContent = stats.matches_count ?? 0;
        reportsCount.textContent = stats.reports_count ?? 0;
        blocksCount.textContent = stats.blocks_count ?? 0;

        setStatsStatus("Статистика обновлена.", "success");
    } catch (error) {
        setStatsStatus("Ошибка загрузки статистики.", "error");
        console.error(error);
    }
}


tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
        switchTab(button.dataset.tab);
    });
});

goalFilterButtons.forEach((button) => {
    button.addEventListener("click", () => {
        setActiveGoalFilter(button.dataset.goal || "");
    });
});

profileForm.addEventListener("submit", saveProfile);
profilePhotoInput.addEventListener("change", uploadProfilePhoto);

loadProfileButton.addEventListener("click", loadNextBrowseProfile);

backButton.addEventListener("click", undoLastSkip);
likeButton.addEventListener("click", () => sendBrowseAction("like"));
skipButton.addEventListener("click", () => sendBrowseAction("skip"));
reportButton.addEventListener("click", () => sendBrowseAction("report"));
blockButton.addEventListener("click", () => sendBrowseAction("block"));

loadMatchesButton.addEventListener("click", loadMatches);
loadStatsButton.addEventListener("click", loadStats);

setActiveGoalFilter("");
fillTelegramUserInfo();
loadProfile();