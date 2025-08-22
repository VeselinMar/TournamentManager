document.addEventListener('DOMContentLoaded', () => {
  // Edit button
  document.querySelectorAll('.btn-edit').forEach(button => {
    button.addEventListener('click', e => {
      const li = e.target.closest('li');
      const fieldId = li.dataset.fieldId;
      const tournamentId = li.dataset.tournamentId
      const nameSpan = li.querySelector('.field-name');
      const oldName = nameSpan.textContent.trim();

      nameSpan.innerHTML = `
        <input type="text" class="form-control form-control-sm field-edit-input" value="${oldName}">
        <button class="btn btn-sm btn-success btn-save">💾</button>
        <button class="btn btn-sm btn-secondary btn-cancel">✖</button>
      `;

      // Save
      nameSpan.querySelector('.btn-save').addEventListener('click', () => {
        const newName = nameSpan.querySelector('.field-edit-input').value.trim();
        if (!newName) return alert("Field name cannot be empty.");

        fetch(`/tournament/${tournamentId}/fields/${fieldId}/edit/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
          },
          body: JSON.stringify({ name: newName })
        })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            nameSpan.textContent = data.name;
          } else {
            alert(data.error || "❌ Failed to update name.");
            nameSpan.textContent = oldName;
          }
        });
      });

      // Cancel
      nameSpan.querySelector('.btn-cancel').addEventListener('click', () => {
        nameSpan.textContent = oldName;
      });
    });
  });

  // Delete button
  document.querySelectorAll('.btn-delete').forEach(button => {
    button.addEventListener('click', () => {
      if (!confirm("Are you sure you want to delete this field?")) return;

      const li = button.closest('li');
      const fieldId = li.dataset.fieldId;
      const tournamentId = li.dataset.tournamentId;

      fetch(`/tournament/${tournamentId}/fields/${fieldId}/delete/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken')
        }
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          li.remove();
        } else {
          alert(data.error || "❌ Could not delete field.");
        }
      });
    });
  });

  // CSRF helper
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      for (let cookie of document.cookie.split(';')) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});
