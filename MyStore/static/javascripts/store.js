/* ===========================
   MyStore App - Complete JavaScript
   Cart, Checkout, Product Pages
   =========================== */

document.addEventListener('DOMContentLoaded', function() {
    initMyStore();
});

function initMyStore() {
    initQuantityControls();
    initCartUpdates();
    initProductImageGallery();
    initAddToCart();
    initWishlistButtons();
    initFilterSort();
    initCheckoutValidation();
}

// ===========================
// Quantity Controls
// ===========================

function initQuantityControls() {
    // Quantity buttons in product detail
    const qtyInputs = document.querySelectorAll('.quantity-input input[type="number"]');
    
    qtyInputs.forEach(input => {
        // Prevent manual entry beyond max
        input.addEventListener('input', function() {
            const max = parseInt(this.getAttribute('max'));
            const min = parseInt(this.getAttribute('min')) || 1;
            let value = parseInt(this.value);
            
            if (value > max) {
                this.value = max;
                showAlert(`Maximum quantity is ${max}`, 'warning');
            }
            if (value < min) {
                this.value = min;
            }
        });
    });
}

// Increase quantity
window.increaseQty = function(max) {
    const input = document.getElementById('quantity');
    let value = parseInt(input.value);
    
    if (value < max) {
        input.value = value + 1;
    } else {
        showAlert(`Maximum available quantity is ${max}`, 'warning');
    }
}

// Decrease quantity
window.decreaseQty = function() {
    const input = document.getElementById('quantity');
    let value = parseInt(input.value);
    
    if (value > 1) {
        input.value = value - 1;
    }
}

// ===========================
// Cart Updates (AJAX)
// ===========================

function initCartUpdates() {
    // Update quantity in cart
    const quantityInputs = document.querySelectorAll('.cart-table .quantity-input input');
    
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            const itemId = this.getAttribute('data-item-id');
            const newQuantity = parseInt(this.value);
            
            if (newQuantity < 1) {
                this.value = 1;
                return;
            }
            
            updateCartItem(itemId, newQuantity);
        });
    });
    
    // Remove from cart confirmation
    const removeButtons = document.querySelectorAll('.btn-remove');
    removeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Remove this item from cart?')) {
                e.preventDefault();
            }
        });
    });
}

function updateCartItem(itemId, quantity) {
    // Show loading state
    showLoadingOverlay();
    
    fetch(`/cart/update/${itemId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ quantity: quantity })
    })
    .then(response => response.json())
    .then(data => {
        hideLoadingOverlay();
        
        if (data.success) {
            // Update cart total display
            updateCartTotals(data.cart_total, data.item_total);
            showAlert('Cart updated successfully', 'success');
        } else {
            showAlert(data.message || 'Error updating cart', 'error');
            // Revert to previous value
            location.reload();
        }
    })
    .catch(error => {
        hideLoadingOverlay();
        console.error('Error:', error);
        showAlert('An error occurred', 'error');
    });
}

function updateCartTotals(cartTotal, itemTotal) {
    // Update cart total
    const cartTotalElement = document.querySelector('.cart-summary h3');
    if (cartTotalElement) {
        cartTotalElement.textContent = `Cart Total: ₹${cartTotal}`;
    }
    
    // Update item total in table if provided
    if (itemTotal) {
        // Find and update specific item total
        // Implementation depends on your HTML structure
    }
    
    // Update header cart count
    updateCartCount();
}

// ===========================
// Product Image Gallery
// ===========================

function initProductImageGallery() {
    const thumbnails = document.querySelectorAll('.thumbnail');
    
    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', function() {
            // Remove active class from all thumbnails
            thumbnails.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked thumbnail
            this.classList.add('active');
        });
    });
}

// Change main image
window.changeImage = function(src) {
    const mainImage = document.getElementById('mainImage');
    if (mainImage) {
        // Fade out effect
        mainImage.style.opacity = '0';
        
        setTimeout(() => {
            mainImage.src = src;
            mainImage.style.opacity = '1';
        }, 200);
    }
}

// ===========================
// Add to Cart
// ===========================

function initAddToCart() {
    // Quick add to cart from product list
    const addToCartButtons = document.querySelectorAll('.add-to-cart');
    
    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            quickAddToCart(productId, this);
        });
    });
    
    // Add to cart form submission
    const cartForms = document.querySelectorAll('.cart-form');
    cartForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const productId = this.action.split('/').slice(-2,-1)[0];
            
            addToCartWithQuantity(productId, formData);
        });
    });
}

function quickAddToCart(productId, button) {
    const originalText = button.innerHTML;
    
    // Show loading state
    button.disabled = true;
    button.innerHTML = `
        <svg class="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="10" stroke-width="4" opacity="0.25"></circle>
            <path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" opacity="0.75"></path>
        </svg>
        Adding...
    `;
    
    fetch(`/cart/add/${productId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Product added to cart!', 'success');
            button.innerHTML = '✓ Added';
            button.style.backgroundColor = 'var(--success-color)';
            
            // Update cart count
            updateCartCount();
            
            // Reset button after 2 seconds
            setTimeout(() => {
                button.innerHTML = originalText;
                button.disabled = false;
                button.style.backgroundColor = '';
            }, 2000);
        } else {
            showAlert(data.message || 'Error adding to cart', 'error');
            button.innerHTML = originalText;
            button.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred', 'error');
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

function addToCartWithQuantity(productId, formData) {
    showLoadingOverlay();
    
    fetch(`/cart/add/${productId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoadingOverlay();
        
        if (data.success) {
            showAlert('Product added to cart!', 'success');
            updateCartCount();
            
            // Redirect to cart after 1 second
            setTimeout(() => {
                window.location.href = '/cart/';
            }, 1000);
        } else {
            showAlert(data.message || 'Error adding to cart', 'error');
        }
    })
    .catch(error => {
        hideLoadingOverlay();
        console.error('Error:', error);
        showAlert('An error occurred', 'error');
    });
}

// ===========================
// Wishlist
// ===========================

function initWishlistButtons() {
    // Already handled by global wishlist function
}

window.addToWishlist = function(productId) {
    fetch(`/wishlist/add/${productId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Added to wishlist!', 'success');
            
            // Update wishlist button UI
            const wishlistBtn = document.querySelector('.btn-wishlist');
            if (wishlistBtn) {
                wishlistBtn.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M8 1.314C12.438-3.248 23.534 4.735 8 15-7.534 4.736 3.562-3.248 8 1.314z"/>
                    </svg>
                    Added to Wishlist
                `;
                wishlistBtn.style.backgroundColor = 'var(--primary-color)';
                wishlistBtn.style.color = 'white';
            }
        } else if (data.message === 'already_exists') {
            showAlert('Already in wishlist', 'info');
        } else {
            showAlert(data.message || 'Error adding to wishlist', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred', 'error');
    });
}

// ===========================
// Filter & Sort
// ===========================

function initFilterSort() {
    // Category filter
    const categoryFilter = document.querySelector('select[onchange*="category"]');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', function() {
            // Already handled by inline onchange
        });
    }
    
    // Sort filter with AJAX
    const sortFilter = document.querySelector('.filter-select:not([onchange*="category"])');
    if (sortFilter) {
        sortFilter.addEventListener('change', function() {
            const sortValue = this.value;
            if (sortValue) {
                // Redirect with sort parameter
                const url = new URL(window.location.href);
                url.searchParams.set('sort', sortValue.split('=')[1]);
                window.location.href = url.toString();
            }
        });
    }
}

// ===========================
// Checkout Validation
// ===========================

function initCheckoutValidation() {
    const checkoutForm = document.querySelector('.shipping-form form');
    
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validate all fields
            const fullName = this.querySelector('[name="full_name"]').value.trim();
            const address = this.querySelector('[name="address"]').value.trim();
            const phone = this.querySelector('[name="phone"]').value.trim();
            
            if (!fullName) {
                showAlert('Please enter your full name', 'error');
                return;
            }
            
            if (!address) {
                showAlert('Please enter your address', 'error');
                return;
            }
            
            if (!phone) {
                showAlert('Please enter your phone number', 'error');
                return;
            }
            
            // Validate phone number format
            const phoneRegex = /^[0-9]{10}$/;
            if (!phoneRegex.test(phone.replace(/\D/g, ''))) {
                showAlert('Please enter a valid 10-digit phone number', 'error');
                return;
            }
            
            // Show confirmation
            if (confirm('Proceed with this order?')) {
                // Show loading
                showLoadingOverlay('Processing your order...');
                this.submit();
            }
        });
    }
}

// ===========================
// Cart Count Update
// ===========================

function updateCartCount() {
    fetch('/cart/count/')
        .then(response => response.json())
        .then(data => {
            const cartCount = document.querySelector('.cart-count');
            if (cartCount && data.count !== undefined) {
                cartCount.textContent = data.count;
                
                // Animate count
                cartCount.style.transform = 'scale(1.5)';
                setTimeout(() => {
                    cartCount.style.transform = 'scale(1)';
                }, 300);
            }
        })
        .catch(error => console.error('Error updating cart count:', error));
}

// ===========================
// Loading Overlay
// ===========================

function showLoadingOverlay(message = 'Loading...') {
    let overlay = document.getElementById('loadingOverlay');
    
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        `;
        
        overlay.innerHTML = `
            <div style="
                background: white;
                padding: 2rem;
                border-radius: 12px;
                text-align: center;
                min-width: 200px;
            ">
                <div class="spinner" style="
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid var(--primary-color);
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 1rem;
                "></div>
                <p style="margin: 0; color: var(--text-primary); font-weight: 600;">${message}</p>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Add keyframe animation
        if (!document.getElementById('spinnerStyle')) {
            const style = document.createElement('style');
            style.id = 'spinnerStyle';
            style.textContent = `
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        }
    }
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

// ===========================
// Alert System (reuse from myaccount.js)
// ===========================

function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.messages') || createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        ${getAlertIcon(type)}
        <span>${message}</span>
        <button class="alert-close">&times;</button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Add close functionality
    alert.querySelector('.alert-close').addEventListener('click', function() {
        fadeOut(alert);
    });
    
    // Auto dismiss
    setTimeout(() => {
        fadeOut(alert);
    }, 5000);
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.className = 'messages';
    container.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        max-width: 400px;
    `;
    document.body.appendChild(container);
    return container;
}

function getAlertIcon(type) {
    const icons = {
        success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;"><polyline points="20 6 9 17 4 12"></polyline></svg>',
        error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
        warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
        info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
    };
    return icons[type] || icons.info;
}

function fadeOut(element) {
    element.style.transition = 'opacity 0.3s ease';
    element.style.opacity = '0';
    setTimeout(() => {
        element.remove();
    }, 300);
}

// ===========================
// Utility Functions
// ===========================

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Export for global use
window.MyStore = {
    updateCartItem,
    addToWishlist,
    changeImage,
    increaseQty,
    decreaseQty,
    showAlert,
    updateCartCount
};
