document.addEventListener("DOMContentLoaded", function () {
  const filterForm = document.querySelector(".payment-history-filters-form");
  const statusSelect = document.getElementById("status");
  const methodSelect = document.getElementById("method");
  const table = document.querySelector(".payment-history-table");

  if (filterForm) {
    [statusSelect, methodSelect].forEach((select) => {
      if (!select) return;
      select.addEventListener("change", function () {
        filterForm.submit();
      });
    });
  }

  if (table && !document.getElementById("paymentSearch")) {
    const wrapper = document.querySelector(".payment-history-table-card");
    if (wrapper) {
      const searchInput = document.createElement("input");
      searchInput.type = "search";
      searchInput.id = "paymentSearch";
      searchInput.className = "filter-select";
      searchInput.placeholder = "Search transaction, order, amount...";
      searchInput.style.marginBottom = "1rem";

      wrapper.insertBefore(searchInput, wrapper.firstChild);

      searchInput.addEventListener("input", function () {
        const query = searchInput.value.toLowerCase().trim();
        const rows = table.querySelectorAll("tbody tr");

        rows.forEach((row) => {
          const text = row.textContent.toLowerCase();
          row.style.display = text.includes(query) ? "" : "none";
        });
      });
    }
  }
});