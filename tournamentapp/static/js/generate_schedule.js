document.addEventListener("DOMContentLoaded", function () {
    const checkbox = document.getElementById('id_has_halves');
    const halvesFields = document.getElementById('halves-fields');
    const singleFields = document.getElementById('single-game-fields');

    function toggle() {
        if (checkbox.checked) {
            halvesFields.style.display = 'block';
            singleFields.style.display = 'none';
        } else {
            halvesFields.style.display = 'none';
            singleFields.style.display = 'block';
        }
    }

    if (checkbox) {
        checkbox.addEventListener('change', toggle);
        toggle();
    }
});