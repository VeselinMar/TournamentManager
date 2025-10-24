document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ match_edit.js loaded");

  const wrapper = document.getElementById("match-wrapper");
  const tournamentId = wrapper.dataset.tournamentId;
  const matchId = wrapper.dataset.matchId;

  const scoreDisplay = wrapper.querySelector("h2:nth-child(2)");
  const eventLog = document.querySelector("#match-events-log ul");

  function getCSRFToken() {
    return document.querySelector("[name=csrfmiddlewaretoken]")?.value;
  }

  function updateScore(home, away) {
    if (scoreDisplay) scoreDisplay.textContent = `${home} - ${away}`;
  }

  function appendEventToLog(event) {
    const li = document.createElement("li");
    li.className =
      "list-group-item d-flex justify-content-between align-items-center";
    li.dataset.eventId = event.id;

    let text = `${event.timestamp} - ${event.player_name} `;
    switch (event.event_type) {
      case "goal":
        text += "scored a goal ⚽";
        break;
      case "yellow_card":
        text += "received a yellow card 🟨";
        break;
      case "red_card":
        text += "received a red card 🟥";
        break;
      case "own_goal":
        text += "scored an own goal ❗";
        break;
      default:
        text += `did ${event.event_type}`;
    }

    li.innerHTML = `<span>${text}</span>
                    <button class="btn btn-sm btn-danger delete-event-btn">Delete</button>`;
    eventLog.appendChild(li);
  }

  // -------------------------
  // Player form handler
  // -------------------------
  function setupPlayerForm(formId, listId, teamSide) {
    const form = document.getElementById(formId);
    const list = document.getElementById(listId);
    if (!form || !list) return;

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      const teamId = form.dataset.teamId;
      const csrfToken = getCSRFToken();
      const formData = new FormData(form);

      fetch(`/tournament/${tournamentId}/teams/${teamId}/add-player/`, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        body: formData,
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            const placeholder = list.querySelector(".text-muted");
            if (placeholder) placeholder.remove();

            const li = document.createElement("li");
            li.className =
              "list-group-item d-flex justify-content-between align-items-center";
            li.innerHTML = `
              ${data.player.name}
              <div class="btn-group btn-group-sm" role="group">
                <button class="btn btn-success assign-event" data-player-id="${data.player.id}" data-team="${teamSide}" data-team-id="${teamId}" data-type="goal">⚽</button>
                <button class="btn btn-warning assign-event" data-player-id="${data.player.id}" data-team="${teamSide}" data-team-id="${teamId}" data-type="yellow_card">🟨</button>
                <button class="btn btn-danger assign-event" data-player-id="${data.player.id}" data-team="${teamSide}" data-team-id="${teamId}" data-type="red_card">🟥</button>
                <button class="btn btn-secondary assign-event" data-player-id="${data.player.id}" data-team="${teamSide}" data-team-id="${teamId}" data-type="own_goal">❗</button>
              </div>
            `;
            list.appendChild(li);
            form.reset();
          } else {
            alert(data.error || "Failed to add player.");
          }
        })
        .catch((err) => console.error("❌ Error adding player:", err));
    });
  }

  // -------------------------
  // Event delegation
  // -------------------------
  document.addEventListener("click", function (e) {
    const target = e.target;

    // Assign event
    if (target.classList.contains("assign-event")) {
      const playerId = target.dataset.playerId;
      const team = target.dataset.team;
      const teamId = target.dataset.teamId;
      const eventType = target.dataset.type;

      fetch(`/tournament/${tournamentId}/matches/${matchId}/add-event/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCSRFToken(),
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
          player_id: playerId,
          team: team,
          team_id: teamId,
          event_type: eventType,
        }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            appendEventToLog(data.event);
            updateScore(data.home_score, data.away_score);
          } else {
            alert(data.error || "Failed to assign event.");
          }
        })
        .catch((err) => console.error("❌ Error assigning event:", err));
    }

    // Delete event
    if (target.classList.contains("delete-event-btn")) {
      const li = target.closest("li");
      const eventId = li.dataset.eventId;

      fetch(`/tournament/${tournamentId}/matches/delete-event/${eventId}/`, {
        method: "DELETE",
        headers: { "X-CSRFToken": getCSRFToken() },
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.success) {
            li.remove();
            updateScore(data.home_score, data.away_score);
          } else {
            alert(data.error || "Could not delete event.");
          }
        })
        .catch((err) => console.error("❌ Error deleting event:", err));
    }
  });

  // Init forms
  setupPlayerForm("home-player-form", "home-player-list", "home");
  setupPlayerForm("away-player-form", "away-player-list", "away");
});
