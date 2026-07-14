function initBoard(boardEl) {
    const reorderUrl = boardEl.dataset.reorderUrl;
    let dragged = null;

    boardEl.querySelectorAll(".board-card[draggable='true']").forEach((card) => {
        card.addEventListener("dragstart", () => {
            dragged = card;
            card.classList.add("dragging");
        });
        card.addEventListener("dragend", () => {
            card.classList.remove("dragging");
            dragged = null;
        });
    });

    boardEl.querySelectorAll(".board-column").forEach((column) => {
        column.addEventListener("dragover", (e) => {
            e.preventDefault();
            if (!dragged) return;
            column.classList.add("drop-target");
            const after = [...column.querySelectorAll(".board-card:not(.dragging)")].find(
                (card) => e.clientY <= card.getBoundingClientRect().top + card.offsetHeight / 2
            );
            if (after) {
                column.insertBefore(dragged, after);
            } else {
                column.appendChild(dragged);
            }
        });
        column.addEventListener("dragleave", (e) => {
            if (!column.contains(e.relatedTarget)) column.classList.remove("drop-target");
        });
        column.addEventListener("drop", (e) => {
            e.preventDefault();
            column.classList.remove("drop-target");
            const order = [...column.querySelectorAll(".board-card")].map((c) => c.dataset.id);
            fetch(reorderUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: column.dataset.status, order }),
            });
        });
    });
}

document.querySelectorAll(".board[data-reorder-url]").forEach(initBoard);
