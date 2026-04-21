document.addEventListener("DOMContentLoaded", function () {
  const printButtons = document.querySelectorAll("[data-print-receipt]");

  printButtons.forEach((button) => {
    button.addEventListener("click", function () {
      window.print();
    });
  });
});