(function () {
  const goalEl = document.getElementById("goal");
  const expEl = document.getElementById("experience");
  const eqEl = document.getElementById("equipment");
  const injEl = document.getElementById("injuries");
  const promptEl = document.getElementById("prompt");
  const btnGen = document.getElementById("btnGenerate");
  const btnClear = document.getElementById("btnClear");
  const resultEl = document.getElementById("result");
  const badgeEl = document.getElementById("badge");

  function setLoading(isLoading) {
    if (isLoading) {
      resultEl.classList.add("muted");
      resultEl.textContent = "Se generează planul…";
      badgeEl.textContent = "";
    } else {
      resultEl.classList.remove("muted");
    }
  }

  btnClear?.addEventListener("click", () => {
    goalEl.value = "";
    expEl.value = "";
    eqEl.value = "";
    injEl.value = "";
    promptEl.value = "";
    resultEl.classList.add("muted");
    resultEl.textContent = "Nimic generat încă.";
    badgeEl.textContent = "";
  });

  btnGen?.addEventListener("click", async () => {
    const payload = {
      goal: (goalEl.value || "").trim(),
      experience: (expEl.value || "").trim(),
      equipment: (eqEl.value || "").trim(),
      injuries: (injEl.value || "").trim(),
      prompt: (promptEl.value || "").trim(),
    };

    setLoading(true);
    try {
      const res = await fetch("/api/fitness/generate", {
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
      badgeEl.textContent = data.used_calendar ? "Calendar folosit: da" : "Calendar folosit: nu";
    } catch (err) {
      console.error(err);
      resultEl.classList.add("muted");
      resultEl.textContent = "Eroare la generare.";
    } finally {
      setLoading(false);
    }
  });
})();
