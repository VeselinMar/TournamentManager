const finishBtn  = document.getElementById('finishBtn');
const reopenBtn  = document.getElementById('reopenBtn');
const modal      = document.getElementById('confirmModal');
const message    = document.getElementById('confirmMessage');
const confirmYes = document.getElementById('confirmYes');
const confirmNo  = document.getElementById('confirmNo');
const form       = document.getElementById('toggleStatusForm');

function showModal(msg) {
  message.textContent = msg;
  modal.classList.add('open');
}

function hideModal() {
  modal.classList.remove('open');
}

if (finishBtn) {
  finishBtn.addEventListener('click', () =>
    showModal('Are you sure you want to finish this tournament? The Score buttons will be hidden.')
  );
}

if (reopenBtn) {
  reopenBtn.addEventListener('click', () =>
    showModal('Reopen this tournament? Score buttons will become available again.')
  );
}

confirmYes.addEventListener('click', () => { hideModal(); form.submit(); });
confirmNo.addEventListener('click', hideModal);
modal.querySelector('.confirm-backdrop').addEventListener('click', hideModal);
document.addEventListener('keydown', e => { if (e.key === 'Escape') hideModal(); });