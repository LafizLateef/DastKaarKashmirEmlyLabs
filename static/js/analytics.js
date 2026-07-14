async function loadAnalytics() {

    try {

        const res = await fetch("/market-analytics");

        if (!res.ok) {
            throw new Error(`Server returned ${res.status}`);
        }

        const data = await res.json();
        console.log(data);

        const analytics = data.exportAnalysis;

        renderCountries(analytics.countries);
        renderProducts(analytics.products);
        renderPrice(analytics.price);
        renderDemand(analytics.months, analytics.demand);
        renderTips(analytics.tips);
        renderSummary(analytics);
        renderBuyers(analytics.buyers);

    } catch (err) {

        console.error(err);

    }

}

loadAnalytics();


function renderCountries(countries) {

    const container = document.getElementById("countryList");

    if (!container) return;

    let html = "";

    countries.forEach(c => {

        html += `
        <div class="country-row">
            <div class="country-row-top">
                <span>${c.country}</span>
                <span>${c.score}%</span>
            </div>

            <div class="progress">
                <div class="progress-bar" style="width:${c.score}%"></div>
            </div>
        </div>
        `;

    });

    container.innerHTML = html;

}


function renderProducts(products) {

    const container = document.getElementById("productList");

    if (!container) return;

    let html = "";

    products.forEach(product => {

        html += `<p>🔥 ${product}</p>`;

    });

    container.innerHTML = html;

}


function renderPrice(price) {

    const el = document.getElementById("priceRange");

    if (!el) return;

    el.textContent = `$${price.min} - $${price.max}`;

}


function renderDemand(months, demand) {

    const chart = document.getElementById("marketChart");
    const labels = document.getElementById("monthLabels");

    if (!chart || !labels) return;

    chart.innerHTML = "";

    demand.forEach(value => {

        chart.innerHTML += `
        <div class="mini-bar" style="height:${value}%"></div>
        `;

    });

    labels.innerHTML = months
        .map(month => `<span>${month}</span>`)
        .join("");

}


function renderTips(tips) {

    const container = document.getElementById("tipsList");

    if (!container) return;

    let html = "";

    tips.forEach(tip => {

        html += `<li>${tip}</li>`;

    });

    container.innerHTML = html;

}


function renderSummary(data) {

    const topMarket = document.getElementById("topMarket");
    const bestMonth = document.getElementById("bestMonth");
    const marketTrend = document.getElementById("marketTrend");
    const summary = document.getElementById("marketSummary");

    if (topMarket)
        topMarket.textContent = data.topMarket;

    if (bestMonth)
        bestMonth.textContent = data.bestMonth;

    if (marketTrend)
        marketTrend.textContent = data.marketTrend;

    if (summary)
        summary.textContent = data.summary;

}

function renderBuyers(buyers){

    const div=document.getElementById("buyerList");

    if(!div) return;

    div.innerHTML="";

    buyers.forEach(b=>{

        div.innerHTML += `
        <div class="ai-list-item">

            <div class="ai-list-item-body">
                <div class="ai-list-item-title">
                    ${b.name}
                </div>

                <div class="ai-list-item-sub">
                    ${b.country}
                </div>
            </div>

            <span class="badge badge-ai">
                ${b.match}% Match
            </span>

        </div>
        `;

    });

}