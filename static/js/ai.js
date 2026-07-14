// ===============================
// DASTKAAR AI DASHBOARD
// ===============================

document.addEventListener("DOMContentLoaded", () => {

    loadAI();

    const askBtn = document.getElementById("askAI");

    if (askBtn) {
        askBtn.addEventListener("click", askAI);
    }

});


// ===============================
// LOAD DASHBOARD
// ===============================

async function loadAI() {

    try {

        const response = await fetch("/ai-dashboard");

        if (!response.ok) {
            throw new Error("Failed to load AI dashboard.");
        }

        const data = await response.json();

        console.log("AI Dashboard:", data);

        renderBuyers(data.buyers || []);

        renderDemand(data.demand || {});

        renderProducts(data.products || []);

        renderQuality(data.quality || {});

        renderSuggestions(data.suggestions || []);

    }

    catch (err) {

        console.error(err);

    }

}


// ===============================
// BUYERS
// ===============================

function renderBuyers(buyers) {

    const div = document.getElementById("buyerList");

    div.innerHTML = "";

    buyers.forEach(b => {

        div.innerHTML += `

        <div class="ai-list-item">

            <div class="ai-list-item-body">

                <div class="ai-list-item-title">
                    ${b.name}
                </div>

                <div class="ai-list-item-sub">
                    ${b.country} · ${b.type}
                </div>

            </div>

            <span class="badge badge-verified">
                ${b.match}% Match
            </span>

        </div>

        `;

    });

}



// ===============================
// DEMAND CHART
// ===============================

function renderDemand(demand) {

    const chart = document.getElementById("demandChart");

    const labels = document.getElementById("demandLabels");

    chart.innerHTML = "";

    labels.innerHTML = "";

    let values = demand.values || [];

    let months = demand.months || [];

    // Fix invalid AI output

    if (values.length !== 6) {

        console.warn("Invalid demand values from AI. Using defaults.");

        values = [45, 58, 63, 72, 81, 93];

    }

    values.forEach(v => {

        v = Number(v);

        if (isNaN(v)) v = 50;

        if (v < 5) v = 5;

        if (v > 100) v = 100;

        chart.innerHTML += `

        <div
            class="mini-bar"
            style="height:${v}%">
        </div>

        `;

    });

    if (months.length !== 6) {

        months = ["Feb", "Mar", "Apr", "May", "Jun", "Jul"];

    }

    months.forEach(m => {

        labels.innerHTML += `<span>${m}</span>`;

    });

}



// ===============================
// PRODUCTS
// ===============================

function renderProducts(products) {

    const div = document.getElementById("productList");

    div.innerHTML = "";

    products.forEach(p => {

        div.innerHTML += `

        <div class="ai-list-item">

            <div class="ai-list-item-body">

                <div class="ai-list-item-title">
                    ${p.name}
                </div>

                <div class="ai-list-item-sub">
                    ${p.category} · ${p.price}
                </div>

            </div>

            <span class="badge badge-verified">
                ${p.match}% Match
            </span>

        </div>

        `;

    });

}



// ===============================
// QUALITY SCORE
// ===============================

function renderQuality(q) {

    document.getElementById("overallScore").textContent =
        q.overall ?? "--";

    document.getElementById("craftValue").textContent =
        (q.craftsmanship ?? 0) + "%";

    document.getElementById("materialValue").textContent =
        (q.material ?? 0) + "%";

    document.getElementById("listingValue").textContent =
        (q.listing ?? 0) + "%";

    document.getElementById("craftProgress").style.width =
        (q.craftsmanship ?? 0) + "%";

    document.getElementById("materialProgress").style.width =
        (q.material ?? 0) + "%";

    document.getElementById("listingProgress").style.width =
        (q.listing ?? 0) + "%";

}



// ===============================
// SMART SUGGESTIONS
// ===============================

function renderSuggestions(list) {

    const div = document.getElementById("suggestions");

    div.innerHTML = "";

    list.forEach(item => {

        div.innerHTML += `

        <div class="ai-list-item">

            <div class="ai-list-item-body">

                <div class="ai-list-item-title">

                    ${item}

                </div>

            </div>

        </div>

        `;

    });

}



// ===============================
// AI CHAT
// ===============================

async function askAI() {

    const input = document.getElementById("aiQuestion");

    const responseBox = document.getElementById("aiResponse");

    if (!input.value.trim()) return;

    responseBox.hidden = false;

    responseBox.innerHTML = "Thinking...";

    // Requires a Flask /ai-chat endpoint
    try {

        const res = await fetch("/ai-chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                question: input.value

            })

        });

        const data = await res.json();

        responseBox.textContent = data.answer;

    }

    catch {

        responseBox.textContent =
            "AI Assistant is unavailable.";

    }

}
// ============================
// AI TRANSLATION
// ============================

const translateBtn = document.getElementById("translateBtn");

if (translateBtn) {

    translateBtn.addEventListener("click", translateNow);

}

async function translateNow() {

    const text = document.getElementById("translateText").value.trim();

    const language = document.getElementById("translateLanguage").value;

    const output = document.getElementById("translatedText");

    if (!text) {

        alert("Please enter text.");

        return;

    }

    output.style.display = "block";

    output.innerHTML = "Translating...";

    try {

        const response = await fetch("/translate", {

            method: "POST",

            headers: {

                "Content-Type": "application/json"

            },

            body: JSON.stringify({

                text: text,

                language: language

            })

        });

        const data = await response.json();

        output.innerHTML = "";

        const heading = document.createElement("strong");
        heading.textContent = "Translated Text";

        const hr = document.createElement("hr");

        const body = document.createElement("div");
        body.textContent = data.translated;
        body.style.margin = "8px 0";

        const status = document.createElement("small");
        status.textContent = `Status: ${data.status}`;

        output.append(heading, hr, body, status);

    }

    catch (err) {

        output.innerHTML = "Translation failed.";

    }

}