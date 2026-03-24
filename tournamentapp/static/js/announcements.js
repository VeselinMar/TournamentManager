document.addEventListener('DOMContentLoaded', function () {
  const popup = document.getElementById('announcementPopup');
  const closeBtn = document.getElementById('closeAnnouncement');

  if (closeBtn && popup) {
    closeBtn.addEventListener('click', () => {
      popup.style.display = 'none';
    });
  }
});