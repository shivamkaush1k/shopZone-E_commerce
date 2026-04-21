document.addEventListener("DOMContentLoaded", function () {
  const payloadNode = document.getElementById("razorpay-payload");
  if (!payloadNode) return;

  let payload = null;

  try {
    payload = JSON.parse(payloadNode.textContent);
  } catch (error) {
    console.error("Invalid Razorpay payload:", error);
    renderMessage("Payment Initialization Failed", "Unable to load payment details.");
    return;
  }

  if (!window.Razorpay) {
    renderMessage("Gateway Error", "Razorpay SDK failed to load. Please refresh and try again.");
    return;
  }

  const options = {
    key: payload.key,
    amount: payload.amount,
    currency: payload.currency || "INR",
    name: payload.name || "ShopZone",
    description: payload.description || "Order Payment",
    image: payload.image || undefined,
    order_id: payload.order_id,
    prefill: {
      name: payload.prefill?.name || "",
      email: payload.prefill?.email || "",
      contact: payload.prefill?.contact || ""
    },
    notes: payload.notes || {},
    theme: {
      color: payload.theme_color || "#0d6efd"
    },
    modal: {
      backdropclose: false,
      escape: false,
      handleback: true,
      ondismiss: function () {
        if (payload.cancel_url) {
          window.location.href = payload.cancel_url;
        } else if (payload.failure_url) {
          window.location.href = payload.failure_url;
        } else {
          renderMessage("Payment Cancelled", "You closed the payment window before completing payment.");
        }
      }
    },
    handler: function (response) {
      verifyPayment(response);
    }
  };

  const razorpay = new Razorpay(options);

  razorpay.on("payment.failed", function (response) {
    const error = response.error || {};

    if (payload.failure_url) {
      const params = new URLSearchParams({
        payment_id: payload.payment_id || "",
        code: error.code || "",
        description: error.description || "Payment failed",
        source: error.source || "",
        step: error.step || "",
        reason: error.reason || "",
        metadata_order_id: error.metadata?.order_id || payload.order_id || "",
        metadata_payment_id: error.metadata?.payment_id || ""
      });

      window.location.href = `${payload.failure_url}?${params.toString()}`;
    } else {
      renderMessage("Payment Failed", error.description || "Your payment could not be completed.");
    }
  });

  razorpay.open();

  function verifyPayment(response) {
    if (!payload.verify_url) {
      renderMessage("Verification Error", "Payment verification URL is missing.");
      return;
    }

    fetch(payload.verify_url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
        "X-Requested-With": "XMLHttpRequest"
      },
      body: JSON.stringify({
        payment_id: payload.payment_id,
        razorpay_payment_id: response.razorpay_payment_id,
        razorpay_order_id: response.razorpay_order_id,
        razorpay_signature: response.razorpay_signature
      })
    })
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok || !data.success) {
          throw new Error(data.error || data.message || "Payment verification failed.");
        }
        window.location.href = data.redirect_url || payload.success_url || "/";
      })
      .catch((error) => {
        console.error("Verification failed:", error);
        if (payload.failure_url) {
          const params = new URLSearchParams({
            payment_id: payload.payment_id || "",
            error_message: error.message || "Verification failed"
          });
          window.location.href = `${payload.failure_url}?${params.toString()}`;
        } else {
          renderMessage("Verification Failed", error.message || "Could not verify payment.");
        }
      });
  }

  function getCSRFToken() {
    const name = "csrftoken";
    const cookies = document.cookie ? document.cookie.split(";") : [];

    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + "=")) {
        return decodeURIComponent(cookie.substring(name.length + 1));
      }
    }

    const csrfInput = document.querySelector('[name="csrfmiddlewaretoken"]');
    return csrfInput ? csrfInput.value : "";
  }

  function renderMessage(title, text) {
    const titleNode = document.querySelector(".processing-title");
    const textNode = document.querySelector(".processing-text");
    const spinner = document.querySelector(".processing-spinner");

    if (titleNode) titleNode.textContent = title;
    if (textNode) textNode.textContent = text;
    if (spinner) spinner.style.display = "none";
  }
});