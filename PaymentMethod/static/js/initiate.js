document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("paymentForm");
  if (!form) return;

  const methodOptions = [...document.querySelectorAll(".payment-method-option")];
  const paymentRadios = [...form.querySelectorAll('input[name="payment_method"]')];
  const savedToggle = document.getElementById("useSavedPayment");
  const savedList = document.getElementById("savedPaymentsList");
  const savedSelect = form.querySelector('[name="saved_payment"]');
  const submitBtn = form.querySelector('button[type="submit"]');
  const savedRadio = form.querySelector('input[name="payment_method"][value="saved"]');

  function updateSelectedMethodUI() {
    methodOptions.forEach((option) => {
      const radio = option.querySelector('input[type="radio"]');
      option.classList.toggle("is-selected", !!radio?.checked);
    });
  }

  function toggleSavedPayments(enabled) {
    if (!savedList) return;

    savedList.classList.toggle("is-hidden", !enabled);

    if (savedToggle) {
      savedToggle.setAttribute("aria-expanded", String(enabled));
    }

    if (enabled) {
      paymentRadios.forEach((radio) => {
        if (radio.value !== "saved") {
          radio.checked = false;
          radio.disabled = true;
        }
      });

      if (savedRadio) {
        savedRadio.disabled = false;
        savedRadio.checked = true;
      }

      if (savedSelect) {
        savedSelect.disabled = false;
        savedSelect.required = true;
      }
    } else {
      paymentRadios.forEach((radio) => {
        radio.disabled = false;
      });

      if (savedRadio) {
        savedRadio.checked = false;
      }

      if (savedSelect) {
        savedSelect.disabled = true;
        savedSelect.required = false;
        savedSelect.value = "";
      }
    }

    updateSelectedMethodUI();
  }

  paymentRadios.forEach((radio) => {
    radio.addEventListener("change", function () {
      if (radio.value !== "saved" && savedToggle?.checked) {
        savedToggle.checked = false;
        toggleSavedPayments(false);
      }
      updateSelectedMethodUI();
    });
  });

  methodOptions.forEach((option) => {
    option.setAttribute("tabindex", "0");

    option.addEventListener("click", function (event) {
      const radio = option.querySelector('input[type="radio"]');
      if (!radio || radio.disabled) return;

      if (event.target.tagName !== "INPUT" && event.target.tagName !== "LABEL") {
        radio.checked = true;
        radio.dispatchEvent(new Event("change", { bubbles: true }));
      }
    });

    option.addEventListener("keydown", function (event) {
      const radio = option.querySelector('input[type="radio"]');
      if (!radio || radio.disabled) return;

      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        radio.checked = true;
        radio.dispatchEvent(new Event("change", { bubbles: true }));
      }
    });
  });

  if (savedToggle) {
    savedToggle.addEventListener("change", function () {
      toggleSavedPayments(savedToggle.checked);
    });

    toggleSavedPayments(savedToggle.checked);
  }

  form.addEventListener("submit", function (event) {
    const usingSaved = !!savedToggle?.checked;
    const selectedRadio = form.querySelector('input[name="payment_method"]:checked');

    if (usingSaved) {
      if (!savedRadio) {
        event.preventDefault();
        alert("Saved payment option is not available.");
        return;
      }

      if (savedSelect && !savedSelect.value) {
        event.preventDefault();
        savedSelect.focus();
        alert("Please select a saved payment method.");
        return;
      }
    } else {
      if (!selectedRadio) {
        event.preventDefault();
        paymentRadios[0]?.focus();
        alert("Please select a payment method.");
        return;
      }
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.dataset.originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = "Processing...";
      submitBtn.classList.add("is-loading");
    }
  });

  updateSelectedMethodUI();
});