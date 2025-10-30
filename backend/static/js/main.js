document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("loadBtn");
  const eventsDiv = document.getElementById("events");

  if (btn) {
    btn.addEventListener("click", async () => {
      eventsDiv.innerHTML = "<p>Se încarcă...</p>";
      try {
        const res = await fetch("/api/calendar/month-split");
        const data = await res.json();

        let html = "";

        html += "<h3>Evenimente din luna curentă</h3>";
        if (data.past_current_month && data.past_current_month.length > 0) {
          data.past_current_month.forEach(ev => {
            html += `
              <div class="event">
                <b>${ev.summary}</b><br>
                ${ev.start_date} → ${ev.end_date}<br>
                <small>${ev.location || "Fără locație"}</small>
              </div>
            `;
          });
        } else html += "<p>Niciun eveniment trecut.</p>";

        html += "<h3>Evenimente viitoare</h3>";
        if (data.future_next_month && data.future_next_month.length > 0) {
          data.future_next_month.forEach(ev => {
            html += `
              <div class="event future">
                <b>${ev.summary}</b><br>
                ${ev.start_date} → ${ev.end_date}<br>
                <small>${ev.location || "Fără locație"}</small>
              </div>
            `;
          });
        } else html += "<p>Niciun eveniment viitor.</p>";

        eventsDiv.innerHTML = html;
      } catch (err) {
        console.error(err);
        eventsDiv.innerHTML = "<p style='color:red'>Eroare la încărcare!</p>";
      }
    });
  }
});
