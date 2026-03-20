const finishBtn  = document.getElementById('finishBtn');
const reopenBtn  = document.getElementById('reopenBtn');
const resetBtn   = document.getElementById('resetBtn');
const modal      = document.getElementById('confirmModal');
const message    = document.getElementById('confirmMessage');
const confirmYes = document.getElementById('confirmYes');
const confirmNo  = document.getElementById('confirmNo');
const toggleForm = document.getElementById('toggleStatusForm');
const resetForm  = document.getElementById('resetForm');

let activeForm = null;

function showModal(msg, form) {
  message.textContent = msg;
  activeForm = form;
  modal.classList.add('open');
}

function hideModal() {
  modal.classList.remove('open');
  activeForm = null;
}

if (finishBtn) {
  finishBtn.addEventListener('click', () =>
    showModal(
      'Are you sure you want to finish this tournament? The Score buttons will be hidden.',
      toggleForm
    )
  );
}

if (reopenBtn) {
  reopenBtn.addEventListener('click', () =>
    showModal(
      'Reopen this tournament? Score buttons will become available again.',
      toggleForm
    )
  );
}

if (resetBtn) {
  resetBtn.addEventListener('click', () =>
    showModal(
      'Reset the entire schedule? All matches, results and events will be permanently deleted. This cannot be undone.',
      resetForm
    )
  );
}

confirmYes.addEventListener('click', () => {
  const form = activeForm;
  hideModal();
  if (form) form.submit();
});confirmNo.addEventListener('click', hideModal);
modal.querySelector('.confirm-backdrop').addEventListener('click', hideModal);
document.addEventListener('keydown', e => { if (e.key === 'Escape') hideModal(); });