(function () {
  const tableWrap = document.getElementById("tableWrap");
  const reloadBtn = document.getElementById("reload");
  const maxInput = document.getElementById("maxResults");

  function fmtDateTime(iso) {
    if (!iso) return "-";
    // dacă e doar data (YYYY-MM-DD), o afișăm ca atare
    if (iso.length <= 10 && /^\d{4}-\d{2}-\d{2}$/.test(iso)) return iso;
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  }

  async function loadEvents() {
    const max = Number(maxInput?.value || 20);
    tableWrap.innerHTML = `<div class="spinner muted">Se încarcă…</div>`;
    try {
      const res = await fetch(`/events?max_results=${max}`);
      const data = await res.json();

      if (data.adapter_error) {
        tableWrap.innerHTML = `<p style="color:#b00020">Adapter error: ${data.adapter_error}</p>`;
        return;
      }

      const events = Array.isArray(data.events) ? data.events : [];
      if (!events.length) {
        tableWrap.innerHTML = `<p class="muted">Nu există evenimente de afișat.</p>`;
        return;
      }

      const rows = events
        .map((e) => {
          const summary = e.summary || "No Title";
          const startDate = e.start_date || "";
          const endDate = e.end_date || "";
          const start = fmtDateTime(e.start);
          const end = fmtDateTime(e.end);
          const location = e.location || "";

          return `
            <tr>
              <td data-label="Titlu"><span class="badge">${summary}</span></td>
              <td data-label="Start (data)">${startDate}</td>
              <td data-label="End (data)">${endDate}</td>
              <td data-label="Start (exact)">${start}</td>
              <td data-label="End (exact)">${end}</td>
              <td data-label="Locație"><span class="loc" title="${location}">${location || "-"}</span></td>
            </tr>
          `;
        })
        .join("");

      tableWrap.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Titlu</th>
              <th>Start (data)</th>
              <th>End (data)</th>
              <th>Start (exact)</th>
              <th>End (exact)</th>
              <th>Locație</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      `;
    } catch (err) {
      console.error(err);
      tableWrap.innerHTML = `<p style="color:#b00020">Eroare la încărcarea evenimentelor.</p>`;
    }
  }

  reloadBtn?.addEventListener("click", loadEvents);
  // load la deschiderea paginii
  loadEvents();
})();
