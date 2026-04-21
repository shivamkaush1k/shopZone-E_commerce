/* ============================================
   HOMEPAGE JAVASCRIPT - homePage.js
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize homepage features
    initHeroAnimation();
    initCategoryCards();
    initProductHover();
    initNewsletterForm();
    
});

/* ============================================
   HERO ANIMATION
   ============================================ */

function initHeroAnimation() {
    const heroText = document.querySelector('.hero-text');
    
    if (heroText) {
        // Fade in animation
        setTimeout(() => {
            heroText.style.opacity = '1';
            heroText.style.transform = 'translateY(0)';
        }, 100);
    }
    
    // Parallax effect on hero
    const hero = document.querySelector('.hero-section');
    if (hero) {
        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;
            hero.style.transform = `translateY(${scrolled * 0.5}px)`;
        });
    }
}

/* ============================================
   CATEGORY CARDS
   ============================================ */

function initCategoryCards() {
    const categoryCards = document.querySelectorAll('.category-card');
    
    categoryCards.forEach((card, index) => {
        // Stagger animation on load
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 * index);
        
        // Add hover effect
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05) translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1) translateY(0)';
        });
    });
}

/* ============================================
   PRODUCT HOVER EFFECTS
   ============================================ */

function initProductHover() {
    const productCards = document.querySelectorAll('.product-card');
    
    productCards.forEach(card => {
        const actions = card.querySelector('.product-actions');
        
        if (actions) {
            card.addEventListener('mouseenter', function() {
                actions.style.opacity = '1';
                actions.style.transform = 'translateX(0)';
            });
            
            card.addEventListener('mouseleave', function() {
                actions.style.opacity = '0';
                actions.style.transform = 'translateX(10px)';
            });
        }
    });
}

/* ============================================
   NEWSLETTER FORM
   ============================================ */

function initNewsletterForm() {
    const newsletterForm = document.querySelector('.newsletter-form');
    
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const emailInput = this.querySelector('input[type="email"]');
            const email = emailInput.value;
            
            if (email && isValidEmail(email)) {
                // Simulate subscription
                showSuccessMessage('Thank you for subscribing!');
                emailInput.value = '';
            } else {
                showErrorMessage('Please enter a valid email address');
            }
        });
    }
}

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function showSuccessMessage(message) {
    if (window.ShopZone && window.ShopZone.showSuccessMessage) {
        window.ShopZone.showSuccessMessage(message);
    }
}

function showErrorMessage(message) {
    if (window.ShopZone && window.ShopZone.showErrorMessage) {
        window.ShopZone.showErrorMessage(message);
    }
}

/* ============================================
   SMOOTH SCROLL TO FEATURED PRODUCTS
   ============================================ */

const exploreBtn = document.querySelector('a[href="#featured-products"]');
if (exploreBtn) {
    exploreBtn.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector('#featured-products');
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
}
