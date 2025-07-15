document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ match_edit.js loaded");

  const matchId = document.getElementById("match-wrapper")?.dataset.matchId;

  function setupPlayerForm(formId, listId) {
    const form = document.getElementById(formId);
    const list = document.getElementById(listId);

    if (!form || !list) {
      console.warn(`⛔ Form or list not found: ${formId}, ${listId}`);
      return;
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();

      const teamName = form.dataset.teamId;
      const formData = new FormData(form);
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

      fetch(`/teams/${teamId}/add-player/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken
        },
        body: formData
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            const placeholder = list.querySelector('.text-muted');
            if (placeholder) placeholder.remove();

            const li = document.createElement("li");
            li.className = "list-group-item d-flex justify-content-between align-items-center";
            li.innerHTML = `
              ${data.player.name}
              <div class="btn-group btn-group-sm" role="group">
                <button class="btn btn-success assign-event" data-player-id="${data.player.id}" data-team="${teamName}" data-type="goal">⚽</button>
                <button class="btn btn-warning assign-event" data-player-id="${data.player.id}" data-team="${teamName}" data-type="yellow_card">🟨</button>
                <button class="btn btn-danger assign-event" data-player-id="${data.player.id}" data-team="${teamName}" data-type="red_card">🟥</button>
                <button class="btn btn-secondary assign-event" data-player-id="${data.player.id}" data-team="${teamName}" data-type="own_goal">❗</button>
              </div>
            `;
            list.appendChild(li);
            attachAssignEventListeners(li);
            form.reset();
          } else {
            alert(data.error || "Failed to add player.");
          }
        })
        .catch(err => {
          console.error("❌ Error adding player:", err);
          alert("Something went wrong.");
        });
    });
  }

  function attachAssignEventListeners(scope = document) {
    scope.querySelectorAll(".assign-event").forEach(button => {
      button.addEventListener("click", function () {
        const playerId = this.dataset.playerId;
        const team = this.dataset.team;
        const eventType = this.dataset.type;

        const MatchWrapper = document.getElementById("match-wrapper");
        const matchId = MatchWrapper ? MatchWrapper.dataset.matchId : null;

        if (!matchId) {
          console.error("❌ No match ID found");
          return alert("Match ID is missing.");
        }
        
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        fetch(`/matches/${matchId}/add-event/`, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrfToken,
            "Content-Type": "application/x-www-form-urlencoded"
          },
          body: new URLSearchParams({
            player_id: playerId,
            team: team,
            event_type: eventType,
            minute: new Date().getMinutes()
          })
        })
          .then(res => res.json())
          .then(data => {
            if (data.success) {
              alert(`✅ ${eventType.replace("_", " ")} assigned to ${data.player_name}`);
            } else {
              alert(data.error || "❌ Failed to assign event.");
            }
          })
          .catch(err => {
            console.error("❌ Error assigning event:", err);
            alert("❌ Something went wrong.");
          });
      });
    });
  }

  setupPlayerForm("home-player-form", "home-player-list");
  setupPlayerForm("away-player-form", "away-player-list");
  attachAssignEventListeners();
});
