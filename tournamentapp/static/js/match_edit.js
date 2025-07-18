document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ match_edit.js loaded");

  const matchWrapper = document.getElementById("match-wrapper");
  const matchId = matchWrapper?.dataset.matchId;
  const tournamentId = matchWrapper?.dataset.tournamentId;

  const scoreDisplay = document.querySelector('#match-wrapper h2:nth-child(2)');
  const eventLog = document.getElementById('match-events-log')?.querySelector('ul');

  function updateScore(homeScore, awayScore) {
    if (scoreDisplay) {
      scoreDisplay.textContent = `${homeScore} - ${awayScore}`;
    }
  }

  function appendEventToLog(event) {
    if (!eventLog) return;

    const li = document.createElement('li');
    li.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
    li.dataset.eventId = event.id;

    let text = `${event.timestamp} - ${event.player_name} `;
    switch (event.event_type) {
      case 'goal': text += 'scored a goal ⚽'; break;
      case 'yellow_card': text += 'received a yellow card 🟨'; break;
      case 'red_card': text += 'received a red card 🟥'; break;
      case 'own_goal': text += 'scored an own goal ❗'; break;
      default: text += `did ${event.event_type}`;
    }

    li.innerHTML = `<span>${text}</span><button class="btn btn-sm btn-danger delete-event-btn">Delete</button>`;
    eventLog.appendChild(li);
  }

  function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
  }

  function setupPlayerForm(formId, listId) {
    const form = document.getElementById(formId);
    const list = document.getElementById(listId);

    if (!form || !list) {
      console.warn(`⛔ Form or list not found: ${formId}, ${listId}`);
      return;
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();

      const teamId = form.dataset.teamId;
      const formData = new FormData(form);
      const csrfToken = getCSRFToken();

      fetch(`/tournament/${tournamentId}/teams/${teamId}/add-player/`, {
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
                <button class="btn btn-success assign-event" data-player-id="${data.player.id}" data-team="${data.team}" data-type="goal">⚽</button>
                <button class="btn btn-warning assign-event" data-player-id="${data.player.id}" data-team="${data.team}" data-type="yellow_card">🟨</button>
                <button class="btn btn-danger assign-event" data-player-id="${data.player.id}" data-team="${data.team}" data-type="red_card">🟥</button>
                <button class="btn btn-secondary assign-event" data-player-id="${data.player.id}" data-team="${data.team}" data-type="own_goal">❗</button>
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

        if (!matchId || !tournamentId) {
          console.error("❌ Match or Tournament ID missing");
          return alert("Match or Tournament ID is missing.");
        }

        const csrfToken = getCSRFToken();

        fetch(`/tournament/${tournamentId}/matches/${matchId}/add-event/`, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrfToken,
            "Content-Type": "application/x-www-form-urlencoded"
          },
          body: new URLSearchParams({
            player_id: playerId,
            team: team,
            event_type: eventType
          })
        })
          .then(res => res.json())
          .then(data => {
            if (data.success) {
              appendEventToLog(data.event);
              updateScore(data.home_score, data.away_score);
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

  if (eventLog) {
    eventLog.addEventListener('click', function (e) {
      if (!e.target.classList.contains('delete-event-btn')) return;

      const li = e.target.closest('li');
      const eventId = li.dataset.eventId;

      if (!tournamentId) {
        console.error("❌ Tournament ID missing");
        return alert("Tournament ID is missing.");
      }

      fetch(`/tournament/${tournamentId}/matches/delete-event/${eventId}/`, {
        method: 'DELETE',
        headers: {
          'X-CSRFToken': getCSRFToken(),
        },
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            li.remove();
            updateScore(data.home_score, data.away_score);
          } else {
            alert(data.error || "❌ Could not delete event.");
          }
        })
        .catch(err => {
          console.error("❌ Error deleting event:", err);
          alert("❌ Something went wrong.");
        });
    });
  }

  setupPlayerForm("home-player-form", "home-player-list");
  setupPlayerForm("away-player-form", "away-player-list");
  attachAssignEventListeners();
});
