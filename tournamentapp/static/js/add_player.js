
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("team-detail-player-form");
  if (!form) return;

  const tournamentId = document.querySelector(".team-detail-container").dataset.tournamentId;
  const teamId = form.dataset.teamId;

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    const formData = new FormData(form);
    const csrf = document.querySelector("[name=csrfmiddlewaretoken]").value;

    fetch(`/tournament/${tournamentId}/teams/${teamId}/add-player/`, {
      method: "POST",
      headers: { "X-CSRFToken": csrf },
      body: formData,
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          let playerList = document.querySelector(".team-detail-right .list-vertical-gap");

          if (!playerList) {
            const empty = document.querySelector(".team-detail-right p");
            if (empty) empty.remove();

            playerList = document.createElement("ul");
            playerList.className = "list-vertical-gap";
            form.insertAdjacentElement("beforebegin", playerList);
          }

          const li = document.createElement("li");
          li.className = "card card-player";
          li.innerHTML = `<div class="d-flex justify-content-between align-items-center">
            <span>${data.player.name} — 0 goals</span>
          </div>`;
          playerList.appendChild(li);
          form.reset();
        } else {
          alert(data.error || "Failed to add player.");
        }
      })
      .catch((err) => console.error("❌ Error adding player:", err));
  });
});

const tournamentId = document.querySelector(".team-detail-container").dataset.tournamentId;

document.querySelector(".team-detail-right").addEventListener("keydown", function (e) {
  if (e.key === "Enter" && e.target.classList.contains("player-name-edit")) {
    e.preventDefault();
    e.target.blur();
  }
});

document.querySelector(".team-detail-right").addEventListener("focusout", function (e) {
  if (!e.target.classList.contains("player-name-edit")) return;

  const el = e.target;
  const playerId = el.dataset.playerId;
  const original = el.dataset.original;
  const name = el.textContent.trim();

  if (name === original) return;

  fetch(`/tournament/${tournamentId}/players/${playerId}/rename/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams({ name }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        el.dataset.original = data.name;
      } else {
        alert(data.error || "Failed to rename player.");
        el.textContent = original; // revert
      }
    })
    .catch(() => {
      el.textContent = original; // revert on network error
    });
});