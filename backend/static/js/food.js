(function () {
  const dietPrefEl = document.getElementById("dietPref");
  const scheduleEl = document.getElementById("schedule");
  const promptEl   = document.getElementById("prompt");
  const btnGen     = document.getElementById("btnGenerate");
  const btnClear   = document.getElementById("btnClear");
  const resultEl   = document.getElementById("result");

  function setLoading(isLoading) {
    if (isLoading) {
      resultEl.classList.add("muted");
      resultEl.textContent = "Se generează recomandarea…";
    } else {
      resultEl.classList.remove("muted");
    }
  }

  btnClear?.addEventListener("click", () => {
    dietPrefEl.value = "";
    scheduleEl.value = "";
    promptEl.value = "";
    resultEl.classList.add("muted");
    resultEl.textContent = "Nimic generat încă.";
  });

  btnGen?.addEventListener("click", async () => {
    const payload = {
      diet_pref: (dietPrefEl.value || "").trim(),
      schedule:  (scheduleEl.value || "").trim(),
      prompt:    (promptEl.value   || "").trim(),
    };

    setLoading(true);
    try {
      const res = await fetch("/api/food/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok || data.error) {
        resultEl.classList.add("muted");
        resultEl.textContent = "Eroare: " + (data.error || res.statusText);
        return;
      }

      resultEl.textContent = data.content || "(fără conținut)";
      resultEl.classList.remove("muted");
    } catch (err) {
      console.error(err);
      resultEl.classList.add("muted");
      resultEl.textContent = "Eroare la generare.";
    } finally {
      setLoading(false);
    }
  });
})();
