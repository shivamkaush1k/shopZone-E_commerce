document.addEventListener("DOMContentLoaded", function () {
  const retryBtn = document.querySelector('.result-actions .btn.btn-primary');
  const supportBtn = document.querySelector('.result-actions .btn-outline-danger');

  if (retryBtn) {
    retryBtn.addEventListener("click", function () {
      retryBtn.classList.add("is-loading");
      retryBtn.setAttribute("aria-disabled", "true");
    });
  }

  if (supportBtn) {
    supportBtn.addEventListener("click", function () {
      supportBtn.classList.add("is-clicked");
    });
  }

  const errorCell = document.querySelector(".text-danger");
  if (errorCell) {
    errorCell.setAttribute("role", "alert");
  }
});