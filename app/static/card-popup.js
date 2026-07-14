(function () {
    var popup = document.getElementById('card-popup');
    if (!popup) return;

    document.querySelectorAll('.board-card').forEach(function (card) {
        var tpl = card.querySelector('template.card-full');
        if (!tpl) return;

        function open() {
            popup.innerHTML = '';
            popup.appendChild(tpl.content.cloneNode(true));
            var closeBtn = popup.querySelector('.popup-close');
            if (closeBtn) closeBtn.addEventListener('click', function () { popup.close(); });
            popup.showModal();
        }

        card.addEventListener('click', function (e) {
            if (e.target.closest('a, button, form')) return;
            open();
        });
        card.addEventListener('keydown', function (e) {
            if (e.target !== card) return;
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                open();
            }
        });
    });

    popup.addEventListener('click', function (e) {
        if (e.target === popup) popup.close();
    });
})();
