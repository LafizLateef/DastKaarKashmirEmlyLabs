async function loadInsights() {

    const list = document.getElementById("aiInsights");

    list.innerHTML = "<li>Loading AI insights...</li>";

    try {

        const response = await fetch("/market-insights");

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        console.log(data);

        list.innerHTML = "";

        if (!data.insights || !Array.isArray(data.insights)) {
            list.innerHTML = "<li>No AI insights available.</li>";
            return;
        }

        data.insights.forEach(item => {

            const badge =
                item.trend === "up"
                    ? "badge-verified"
                    : "badge-pending";

            const arrow =
                item.trend === "up"
                    ? "↑"
                    : "↓";

            const li = document.createElement("li");
            li.append(document.createTextNode(item.title + " "));

            const span = document.createElement("span");
            span.className = `badge ${badge}`;
            span.textContent = `${arrow} ${item.percentage}%`;

            li.append(span);
            list.append(li);
        });

    } catch (err) {

        console.error(err);

        list.innerHTML = "<li>Unable to load AI insights.</li>";
    }
}

loadInsights();

document
    .getElementById("refreshInsights")
    .onclick = loadInsights;