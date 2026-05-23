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
const genderInput = document.getElementById("gender");
const ageInput = document.getElementById("age");
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
const likesTab = document.getElementById("likesTab");
const matchesTab = document.getElementById("matchesTab");
const statsTab = document.getElementById("statsTab");

const goalFilterButtons = document.querySelectorAll(".goal-filter-chip");
const genderFilterInput = document.getElementById("genderFilter");
const ageMinFilterInput = document.getElementById("ageMinFilter");
const ageMaxFilterInput = document.getElementById("ageMaxFilter");
const courseFilterInput = document.getElementById("courseFilter");
const resetFiltersButton = document.getElementById("resetFiltersButton");

const loadProfileButton = document.getElementById("loadProfileButton");
const browseCard = document.getElementById("browseCard");
const browseStatus = document.getElementById("browseStatus");

const browseAvatar = document.getElementById("browseAvatar");
const browseAvatarLetter = document.getElementById("browseAvatarLetter");
const browseName = document.getElementById("browseName");
const browseMeta = document.getElementById("browseMeta");
const browseAbout = document.getElementById("browseAbout");
const browseInterests = document.getElementById("browseInterests");

const loadNewLikesButton = document.getElementById("loadNewLikesButton");
const newLikesCard = document.getElementById("newLikesCard");
const newLikesStatus = document.getElementById("newLikesStatus");

const newLikesAvatar = document.getElementById("newLikesAvatar");
const newLikesAvatarLetter = document.getElementById("newLikesAvatarLetter");
const newLikesName = document.getElementById("newLikesName");
const newLikesMeta = document.getElementById("newLikesMeta");
const newLikesAbout = document.getElementById("newLikesAbout");
const newLikesInterests = document.getElementById("newLikesInterests");

const newLikesReportForm = document.getElementById("newLikesReportForm");
const newLikesReportReasonSelect = document.getElementById("newLikesReportReason");
const newLikesReportCommentInput = document.getElementById("newLikesReportComment");
const submitNewLikesReportButton = document.getElementById("submitNewLikesReportButton");
const cancelNewLikesReportButton = document.getElementById("cancelNewLikesReportButton");

const newLikesLikeButton = document.getElementById("newLikesLikeButton");
const newLikesSkipButton = document.getElementById("newLikesSkipButton");
const newLikesReportButton = document.getElementById("newLikesReportButton");
const newLikesBlockButton = document.getElementById("newLikesBlockButton");

const reportForm = document.getElementById("reportForm");
const reportReasonSelect = document.getElementById("reportReason");
const reportCommentInput = document.getElementById("reportComment");
const submitReportButton = document.getElementById("submitReportButton");
const cancelReportButton = document.getElementById("cancelReportButton");

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

const activeProfilesCount = document.getElementById("activeProfilesCount");
const temporaryBlockedProfilesCount = document.getElementById("temporaryBlockedProfilesCount");
const permanentlyBlockedProfilesCount = document.getElementById("permanentlyBlockedProfilesCount");
const newReportsCount = document.getElementById("newReportsCount");

let currentBrowseProfile = null;
let currentNewLikeProfile = null;
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


function setNewLikesStatus(message, type = "") {
    if (!newLikesStatus) {
        return;
    }

    newLikesStatus.textContent = message;
    newLikesStatus.className = "status";

    if (type) {
        newLikesStatus.classList.add(type);
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


function getAgeValue(input) {
    const value = Number(input.value);

    if (!Number.isInteger(value)) {
        return null;
    }

    if (value < 16 || value > 80) {
        return null;
    }

    return value;
}


function buildBrowseQuery() {
    const params = new URLSearchParams();

    if (selectedBrowseGoal) {
        params.set("goal", selectedBrowseGoal);
    }

    if (genderFilterInput?.value) {
        params.set("gender", genderFilterInput.value);
    }

    if (courseFilterInput?.value) {
        params.set("course", courseFilterInput.value);
    }

    if (ageMinFilterInput?.value) {
        params.set("age_min", ageMinFilterInput.value);
    }

    if (ageMaxFilterInput?.value) {
        params.set("age_max", ageMaxFilterInput.value);
    }

    const queryString = params.toString();

    return queryString ? `?${queryString}` : "";
}


function resetBrowseFilters() {
    setActiveGoalFilter("");

    if (genderFilterInput) {
        genderFilterInput.value = "";
    }

    if (ageMinFilterInput) {
        ageMinFilterInput.value = "";
    }

    if (ageMaxFilterInput) {
        ageMaxFilterInput.value = "";
    }

    if (courseFilterInput) {
        courseFilterInput.value = "";
    }

    setBrowseStatus("Фильтры сброшены.");
}


function openReportForm() {
    if (!currentBrowseProfile) {
        setBrowseStatus("Сначала загрузи анкету.", "error");
        return;
    }

    if (!reportForm) {
        setBrowseStatus("Форма жалобы не найдена. Обнови Mini App.", "error");
        return;
    }

    if (reportReasonSelect) {
        reportReasonSelect.value = "";
    }

    if (reportCommentInput) {
        reportCommentInput.value = "";
    }

    reportForm.classList.remove("hidden");
    setBrowseStatus("Опиши причину жалобы и отправь её модераторам.");
}


function closeReportForm() {
    if (!reportForm) {
        return;
    }

    reportForm.classList.add("hidden");

    if (reportReasonSelect) {
        reportReasonSelect.value = "";
    }

    if (reportCommentInput) {
        reportCommentInput.value = "";
    }
}


function buildReportReason() {
    const selectedReason = reportReasonSelect?.value?.trim() || "";
    const comment = reportCommentInput?.value?.trim() || "";

    if (!selectedReason && !comment) {
        return "";
    }

    if (selectedReason && comment) {
        return `${selectedReason}: ${comment}`;
    }

    return selectedReason || comment;
}


async function submitReport() {
    if (!currentBrowseProfile) {
        setBrowseStatus("Сначала загрузи анкету.", "error");
        return;
    }

    const reason = buildReportReason();

    if (!reason) {
        setBrowseStatus("Выбери причину жалобы или напиши комментарий.", "error");
        return;
    }

    await sendBrowseAction("report", reason);
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
        genderInput.value = profile.gender || "";
        ageInput.value = profile.age || "";
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

    const age = getAgeValue(ageInput);

    if (age === null) {
        setStatus("Укажи возраст числом от 16 до 80.", "error");
        return;
    }

    const payload = {
        name: nameInput.value.trim(),
        gender: genderInput.value,
        age: age,
        faculty: facultyInput.value.trim(),
        course: courseInput.value,
        goal: goalInput.value,
        about: aboutInput.value.trim(),
        interests: interestsInput.value.trim(),
        photo_file_id: null
    };

    if (
        !payload.name ||
        !payload.gender ||
        !payload.age ||
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




function closeNewLikesReportForm() {
    if (!newLikesReportForm) {
        return;
    }

    newLikesReportForm.classList.add("hidden");

    if (newLikesReportReasonSelect) {
        newLikesReportReasonSelect.value = "";
    }

    if (newLikesReportCommentInput) {
        newLikesReportCommentInput.value = "";
    }
}


function openNewLikesReportForm() {
    if (!currentNewLikeProfile) {
        setNewLikesStatus("Сначала загрузи новый лайк.", "error");
        return;
    }

    if (!newLikesReportForm) {
        setNewLikesStatus("Форма жалобы не найдена. Обнови Mini App.", "error");
        return;
    }

    if (newLikesReportReasonSelect) {
        newLikesReportReasonSelect.value = "";
    }

    if (newLikesReportCommentInput) {
        newLikesReportCommentInput.value = "";
    }

    newLikesReportForm.classList.remove("hidden");
    setNewLikesStatus("Опиши причину жалобы и отправь её модераторам.");
}


function buildNewLikesReportReason() {
    const selectedReason = newLikesReportReasonSelect?.value?.trim() || "";
    const comment = newLikesReportCommentInput?.value?.trim() || "";

    if (!selectedReason && !comment) {
        return "";
    }

    if (selectedReason && comment) {
        return `${selectedReason}: ${comment}`;
    }

    return selectedReason || comment;
}


async function submitNewLikesReport() {
    if (!currentNewLikeProfile) {
        setNewLikesStatus("Сначала загрузи новый лайк.", "error");
        return;
    }

    const reason = buildNewLikesReportReason();

    if (!reason) {
        setNewLikesStatus("Выбери причину жалобы или напиши комментарий.", "error");
        return;
    }

    await sendNewLikeAction("report", reason);
}


function renderNewLikeProfile(profile) {
    currentNewLikeProfile = profile;

    closeNewLikesReportForm();

    if (!newLikesCard) {
        return;
    }

    if (!profile) {
        newLikesCard.classList.add("hidden");
        return;
    }

    newLikesName.textContent = profile.name;

    const genderText = profile.gender || "пол не указан";
    const ageText = profile.age ? `${profile.age} лет` : "возраст не указан";

    newLikesMeta.textContent =
        `${genderText} · ${ageText} · ${profile.faculty} · ${profile.course} курс · ${profile.goal}`;

    newLikesAbout.textContent = profile.about;
    newLikesInterests.textContent = profile.interests;

    renderPhoto(
        newLikesAvatar,
        newLikesAvatarLetter,
        profile.photo_url,
        getFirstLetter(profile.name)
    );

    newLikesCard.classList.remove("hidden");
}


async function loadNextNewLikeProfile() {
    setNewLikesStatus("Загрузка новых лайков...");

    if (newLikesCard) {
        newLikesCard.classList.add("hidden");
    }

    currentNewLikeProfile = null;
    closeNewLikesReportForm();

    try {
        const response = await fetch("/api/likes/incoming", {
            method: "GET",
            headers: getTelegramAuthOnlyHeaders()
        });

        if (response.status === 400) {
            setNewLikesStatus("Сначала создай свою анкету во вкладке «Анкета».", "error");
            return;
        }

        if (response.status === 401) {
            setNewLikesStatus(authErrorText, "error");
            return;
        }

        if (!response.ok) {
            throw new Error("Не удалось загрузить новые лайки");
        }

        const data = await response.json();
        const likes = data.likes || [];

        if (!likes.length) {
            renderNewLikeProfile(null);
            setNewLikesStatus("Новых лайков пока нет. Когда кто-то лайкнет твою анкету, он появится здесь.");
            return;
        }

        renderNewLikeProfile(likes[0]);
        setNewLikesStatus(`Найдено новых лайков: ${likes.length}.`, "success");
    } catch (error) {
        setNewLikesStatus("Ошибка загрузки новых лайков.", "error");
        console.error(error);

        if (tg) {
            tg.HapticFeedback?.notificationOccurred("error");
        }
    }
}


async function sendNewLikeAction(action, reason = null) {
    if (!currentNewLikeProfile) {
        setNewLikesStatus("Сначала загрузи новый лайк.", "error");
        return;
    }

    const payload = {
        target_user_id: currentNewLikeProfile.telegram_id,
        action: action
    };

    if (action === "report") {
        payload.reason = reason;
    }

    try {
        const response = await fetch("/api/browse/action", {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify(payload)
        });

        if (response.status === 401) {
            setNewLikesStatus(authErrorText, "error");
            return;
        }

        if (!response.ok) {
            throw new Error("Не удалось выполнить действие");
        }

        const data = await response.json();

        if (action === "like") {
            if (data.match) {
                setNewLikesStatus(
                    "🎉 Мэтч! Контакт теперь доступен во вкладке «Мэтчи».",
                    "success"
                );

                loadMatches();

                if (tg) {
                    tg.HapticFeedback?.notificationOccurred("success");
                }
            } else {
                setNewLikesStatus("❤️ Лайк сохранён.", "success");
            }
        }

        if (action === "skip") {
            setNewLikesStatus("➡️ Анкета пропущена.", "success");
        }

        if (action === "report") {
            closeNewLikesReportForm();

            if (data.permanent_block_applied) {
                setNewLikesStatus(
                    "⚠️ Жалоба отправлена. Анкета заблокирована навсегда из-за повторных нарушений.",
                    "success"
                );
            } else if (data.temporary_block_applied) {
                setNewLikesStatus(
                    "⚠️ Жалоба отправлена. Анкета временно скрыта модерацией.",
                    "success"
                );
            } else {
                setNewLikesStatus("⚠️ Жалоба отправлена модераторам. Анкета скрыта.", "success");
            }
        }

        if (action === "block") {
            setNewLikesStatus("🚫 Пользователь заблокирован.", "success");
            loadMatches();
        }

        await loadNextNewLikeProfile();
    } catch (error) {
        setNewLikesStatus("Ошибка действия.", "error");
        console.error(error);

        if (tg) {
            tg.HapticFeedback?.notificationOccurred("error");
        }
    }
}


function switchTab(tabName) {
    tabButtons.forEach((button) => {
        button.classList.toggle("active", button.dataset.tab === tabName);
    });

    profileTab.classList.toggle("active", tabName === "profile");
    browseTab.classList.toggle("active", tabName === "browse");
    likesTab?.classList.toggle("active", tabName === "likes");
    matchesTab.classList.toggle("active", tabName === "matches");
    statsTab.classList.toggle("active", tabName === "stats");

    if (tabName === "likes") {
        loadNextNewLikeProfile();
    }

    if (tabName === "matches") {
        loadMatches();
    }

    if (tabName === "stats") {
        loadStats();
    }
}


function renderBrowseProfile(profile) {
    currentBrowseProfile = profile;

    closeReportForm();

    if (!profile) {
        browseCard.classList.add("hidden");
        return;
    }

    browseName.textContent = profile.name;

    const genderText = profile.gender || "пол не указан";
    const ageText = profile.age ? `${profile.age} лет` : "возраст не указан";

    browseMeta.textContent =
        `${genderText} · ${ageText} · ${profile.faculty} · ${profile.course} курс · ${profile.goal}`;

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
    closeReportForm();

    const query = buildBrowseQuery();

    try {
        const response = await fetch(`/api/browse/next${query}`, {
            method: "GET",
            headers: getTelegramAuthOnlyHeaders()
        });

        if (response.status === 400) {
            setBrowseStatus("Проверь фильтры или сначала создай свою анкету во вкладке «Анкета».", "error");
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
            setBrowseStatus("Анкеты закончились. Попробуй позже или измени фильтры.");
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


async function sendBrowseAction(action, reason = null) {
    if (!currentBrowseProfile) {
        setBrowseStatus("Сначала загрузи анкету.", "error");
        return;
    }

    const payload = {
        target_user_id: currentBrowseProfile.telegram_id,
        action: action
    };

    if (action === "report") {
        payload.reason = reason;
    }

    try {
        const response = await fetch("/api/browse/action", {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify(payload)
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
            closeReportForm();

            if (data.permanent_block_applied) {
                setBrowseStatus(
                    "⚠️ Жалоба отправлена. Анкета заблокирована навсегда из-за повторных нарушений.",
                    "success"
                );
            } else if (data.temporary_block_applied) {
                setBrowseStatus(
                    "⚠️ Жалоба отправлена. Анкета временно скрыта модерацией.",
                    "success"
                );
            } else {
                setBrowseStatus("⚠️ Жалоба отправлена модераторам. Анкета скрыта.", "success");
            }
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

        const gender = profile.gender || "—";
        const age = profile.age || "—";

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
            <p><b>Пол:</b> ${escapeHtml(gender)}</p>
            <p><b>Возраст:</b> ${escapeHtml(age)}</p>
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

        if (activeProfilesCount) {
            activeProfilesCount.textContent = stats.active_profiles_count ?? 0;
        }

        if (temporaryBlockedProfilesCount) {
            temporaryBlockedProfilesCount.textContent = stats.temporary_blocked_profiles_count ?? 0;
        }

        if (permanentlyBlockedProfilesCount) {
            permanentlyBlockedProfilesCount.textContent = stats.permanently_blocked_profiles_count ?? 0;
        }

        if (newReportsCount) {
            newReportsCount.textContent = stats.new_reports_count ?? 0;
        }

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

if (resetFiltersButton) {
    resetFiltersButton.addEventListener("click", resetBrowseFilters);
}

if (cancelReportButton) {
    cancelReportButton.addEventListener("click", closeReportForm);
}

if (submitReportButton) {
    submitReportButton.addEventListener("click", submitReport);
}

if (loadNewLikesButton) {
    loadNewLikesButton.addEventListener("click", loadNextNewLikeProfile);
}

if (cancelNewLikesReportButton) {
    cancelNewLikesReportButton.addEventListener("click", closeNewLikesReportForm);
}

if (submitNewLikesReportButton) {
    submitNewLikesReportButton.addEventListener("click", submitNewLikesReport);
}

profileForm.addEventListener("submit", saveProfile);
profilePhotoInput.addEventListener("change", uploadProfilePhoto);

loadProfileButton.addEventListener("click", loadNextBrowseProfile);

backButton.addEventListener("click", undoLastSkip);
likeButton.addEventListener("click", () => sendBrowseAction("like"));
skipButton.addEventListener("click", () => sendBrowseAction("skip"));
reportButton.addEventListener("click", openReportForm);
blockButton.addEventListener("click", () => sendBrowseAction("block"));

if (newLikesLikeButton) {
    newLikesLikeButton.addEventListener("click", () => sendNewLikeAction("like"));
}

if (newLikesSkipButton) {
    newLikesSkipButton.addEventListener("click", () => sendNewLikeAction("skip"));
}

if (newLikesReportButton) {
    newLikesReportButton.addEventListener("click", openNewLikesReportForm);
}

if (newLikesBlockButton) {
    newLikesBlockButton.addEventListener("click", () => sendNewLikeAction("block"));
}

loadMatchesButton.addEventListener("click", loadMatches);
loadStatsButton.addEventListener("click", loadStats);

setActiveGoalFilter("");
fillTelegramUserInfo();
loadProfile();