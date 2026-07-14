console.log("Dastkaar Kashmir Loaded");

// Page-load progress bar (gives multi-page navigation a "transition" feel)
(function () {
    var bar = document.getElementById("page-progress");
    if (!bar) return;

    var prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function finishBar() {
        bar.style.width = "100%";
        setTimeout(function () {
            bar.classList.remove("loading");
            setTimeout(function () {
                bar.style.width = "0";
            }, 300);
        }, 150);
    }

    if (prefersReducedMotion) {
        // Skip the animated bar entirely; just avoid layout jank.
    } else {
        bar.classList.add("loading");
        bar.style.width = "40%";
        window.addEventListener("load", finishBar);
        // In case the load event already fired before this ran.
        if (document.readyState === "complete") finishBar();

        document.querySelectorAll("a[href]").forEach(function (link) {
            var url = link.getAttribute("href");
            var isInternal = url && !url.startsWith("#") && !url.startsWith("http") && !url.startsWith("mailto:");
            var opensNewTab = link.target === "_blank";

            if (isInternal && !opensNewTab) {
                link.addEventListener("click", function () {
                    bar.classList.add("loading");
                    bar.style.width = "80%";
                });
            }
        });
    }
})();

// Show/Hide password toggle
document.querySelectorAll(".toggle-password").forEach(function (button) {
    button.addEventListener("click", function () {
        var input = document.getElementById(button.dataset.target);
        if (!input) return;
        var isVisible = input.type === "text";
        input.type = isVisible ? "password" : "text";
        button.classList.toggle("is-visible", !isVisible);
        button.setAttribute("aria-label", isVisible ? "Show password" : "Hide password");
    });
});

// Tabs
document.querySelectorAll(".tab-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
        var tabs = btn.closest(".tabs");
        var panelGroup = tabs ? tabs.parentElement : document;

        panelGroup.querySelectorAll(".tab-btn").forEach(function (b) {
            b.classList.remove("active");
        });
        panelGroup.querySelectorAll(".tab-panel").forEach(function (p) {
            p.classList.remove("active");
        });

        btn.classList.add("active");
        var panel = document.getElementById("tab-" + btn.dataset.tab);
        if (panel) panel.classList.add("active");
    });
});

// Modals
document.querySelectorAll("[data-modal-open]").forEach(function (btn) {
    btn.addEventListener("click", function () {
        var modal = document.getElementById(btn.dataset.modalOpen);
        if (modal) modal.classList.add("open");
    });
});

document.querySelectorAll("[data-modal-close]").forEach(function (btn) {
    btn.addEventListener("click", function () {
        var modal = btn.closest(".modal-overlay");
        if (modal) modal.classList.remove("open");
    });
});

document.querySelectorAll(".modal-overlay").forEach(function (overlay) {
    overlay.addEventListener("click", function (e) {
        if (e.target === overlay) overlay.classList.remove("open");
    });
});

document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        document.querySelectorAll(".modal-overlay.open").forEach(function (m) {
            m.classList.remove("open");
        });
    }
});

// Chat: conversation switching
document.querySelectorAll(".chat-list-item").forEach(function (item) {
    item.addEventListener("click", function () {
        document.querySelectorAll(".chat-list-item").forEach(function (i) {
            i.classList.remove("active");
        });
        item.classList.add("active");
    });
});

// Chat: translate toggle
document.querySelectorAll(".translate-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
        var messages = document.querySelector(".chat-messages");
        if (messages) messages.classList.toggle("translate-on");
        btn.classList.toggle("active");
    });
});

// Selectable groups (theme, language, etc.)
document.querySelectorAll(".select-group").forEach(function (group) {
    group.querySelectorAll(".selectable").forEach(function (item) {
        item.addEventListener("click", function () {
            group.querySelectorAll(".selectable").forEach(function (i) {
                i.classList.remove("selected");
            });
            item.classList.add("selected");
        });
    });
});

// Mobile sidebar drawer
(function () {
    var toggle = document.getElementById("sidebar-toggle");
    var sidebar = document.querySelector(".sidebar");
    var overlay = document.getElementById("sidebar-overlay");
    if (!toggle || !sidebar || !overlay) return;

    function closeSidebar() {
        sidebar.classList.remove("open");
        overlay.classList.remove("open");
    }

    toggle.addEventListener("click", function () {
        sidebar.classList.add("open");
        overlay.classList.add("open");
    });

    overlay.addEventListener("click", closeSidebar);

    sidebar.querySelectorAll(".sidebar-link").forEach(function (link) {
        link.addEventListener("click", closeSidebar);
    });

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closeSidebar();
    });
})();