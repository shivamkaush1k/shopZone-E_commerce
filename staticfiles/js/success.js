document.addEventListener("DOMContentLoaded", function () {
  const actionButtons = document.querySelectorAll(".result-actions .btn");
  const codeElement = document.querySelector(".result-details-table code");

  actionButtons.forEach((button) => {
    button.addEventListener("click", function () {
      button.classList.add("is-clicked");
    });
  });

  if (codeElement) {
    codeElement.style.cursor = "pointer";
    codeElement.title = "Click to copy transaction ID";

    codeElement.addEventListener("click", async function () {
      const text = codeElement.textContent.trim();

      try {
        await navigator.clipboard.writeText(text);
        const original = codeElement.textContent;
        codeElement.textContent = "Copied!";
        setTimeout(() => {
          codeElement.textContent = original;
        }, 1200);
      } catch (error) {
        console.error("Copy failed:", error);
      }
    });
  }
});