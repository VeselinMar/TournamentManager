// Edit match modal
const editModal   = document.getElementById('editMatchModal');
const editForm    = document.getElementById('editMatchForm');
const editTime    = document.getElementById('editStartTime');
const editField   = document.getElementById('editField');
const editCancel  = document.getElementById('editMatchCancel');

document.querySelectorAll('.btn-match-edit').forEach(btn => {
  btn.addEventListener('click', () => {
    const matchId  = btn.dataset.matchId;
    const matchName = btn.dataset.matchName;
    const baseUrl  = editForm.dataset.baseUrl;
    editForm.action = baseUrl.replace('0', matchId);
    editTime.value  = btn.dataset.startTime;
    editField.value = btn.dataset.fieldId;
    document.getElementById('editPropagate').checked = false;
    document.getElementById('editMatchTitle').textContent = matchName;
    editModal.classList.add('open');
  });
});

editCancel.addEventListener('click', () => editModal.classList.remove('open'));
editModal.querySelector('.confirm-backdrop').addEventListener('click', () =>
  editModal.classList.remove('open')
);

// Delete match modal
const deleteModal   = document.getElementById('deleteMatchModal');
const deleteForm    = document.getElementById('deleteMatchForm');
const deleteMessage = document.getElementById('deleteMatchMessage');
const deleteCancel  = document.getElementById('deleteMatchCancel');

document.querySelectorAll('.btn-match-delete').forEach(btn => {
  btn.addEventListener('click', () => {
    const matchId   = btn.dataset.matchId;
    const matchName = btn.dataset.matchName;
    const baseUrl   = deleteForm.dataset.baseUrl;
    deleteForm.action = baseUrl.replace('0', matchId);
    deleteMessage.textContent = `Delete "${matchName}"? This cannot be undone.`;
    deleteModal.classList.add('open');
  });
});

deleteCancel.addEventListener('click', () => deleteModal.classList.remove('open'));
deleteModal.querySelector('.confirm-backdrop').addEventListener('click', () =>
  deleteModal.classList.remove('open')
);