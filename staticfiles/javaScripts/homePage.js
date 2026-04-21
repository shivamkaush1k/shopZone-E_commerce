/* =========================================================
   SHOPZONE HOMEPAGE JS
   Handles: Navbar, Hero interactions, Newsletter, Product actions,
   Scroll reveals, Smooth scrolling, Toasts
   ========================================================= */

(() => {
  "use strict";

  // DOM selectors
  const qs = (selector, scope = document) => scope.querySelector(selector);
  const qsa = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));

  const ui = {
    mobileMenuBtn: qs('.navbar__mobile-menu-btn'),
    navLinks: qs('.navbar__links'),
    dropdowns: qsa('.navbar__dropdown'),
    newsletterForm: qs('.newsletter-form'),
    addToCartBtns: qsa('.btn-add-cart'),
    actionBtns: qsa('.action-btn'),
    heroButtons: qsa('.hero-buttons .btn'),
    cartBadges: qsa('.navbar__cart-count'),
    revealElements: qsa('.feature-card, .category-card, .product-card, .newsletter-card, .section-header, .stat-item'),
  };

  const state = {
    cartCount: parseInt(localStorage.getItem('shopzone_cart_count') || '0'),
    mobileMenuOpen: false,
  };

  function init() {
    bindMobileMenu();
    bindDropdowns();
    bindNewsletter();
    bindProductActions();
    bindSmoothScroll();
    initScrollReveals();
    updateCartBadges();
    bindImageErrors();
  }

  // Mobile menu toggle
  function bindMobileMenu() {
    if (!ui.mobileMenuBtn || !ui.navLinks) return;

    ui.mobileMenuBtn.addEventListener('click', toggleMobileMenu);
    
    // Close on outside click
    document.addEventListener('click', (e) => {
      if (state.mobileMenuOpen && !e.target.closest('.navbar')) {
        closeMobileMenu();
      }
    });

    // Close on escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && state.mobileMenuOpen) {
        closeMobileMenu();
      }
    });

    window.addEventListener('resize', () => {
      if (window.innerWidth > 860) closeMobileMenu();
    });
  }

  function toggleMobileMenu() {
    state.mobileMenuOpen = !state.mobileMenuOpen;
    ui.navLinks.classList.toggle('active', state.mobileMenuOpen);
    ui.mobileMenuBtn.setAttribute('aria-expanded', state.mobileMenuOpen);
    ui.mobileMenuBtn.classList.toggle('is-active', state.mobileMenuOpen);
    document.body.style.overflow = state.mobileMenuOpen ? 'hidden' : '';
  }

  function closeMobileMenu() {
    state.mobileMenuOpen = false;
    ui.navLinks?.classList.remove('active');
    ui.mobileMenuBtn?.setAttribute('aria-expanded', 'false');
    ui.mobileMenuBtn?.classList.remove('is-active');
    document.body.style.overflow = '';
  }

  // Dropdown menus
  function bindDropdowns() {
    ui.dropdowns.forEach(dropdown => {
      const btn = qs('.navbar__dropdown-btn', dropdown);
      const menu = qs('.navbar__dropdown-menu', dropdown);

      if (!btn || !menu) return;

      // Mouse hover (desktop)
      dropdown.addEventListener('mouseenter', () => {
        if (window.innerWidth > 860) {
          dropdown.classList.add('is-open');
        }
      });

      dropdown.addEventListener('mouseleave', () => {
        if (window.innerWidth > 860) {
          dropdown.classList.remove('is-open');
        }
      });

      // Click (mobile)
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (window.innerWidth <= 860) {
          dropdown.classList.toggle('is-open');
        }
      });
    });
  }

  // Newsletter form
  function bindNewsletter() {
    if (!ui.newsletterForm) return;

    ui.newsletterForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const formData = new FormData(ui.newsletterForm);
      const submitBtn = qs('button', ui.newsletterForm);
      const originalText = submitBtn.innerHTML;

      submitBtn.disabled = true;
      submitBtn.innerHTML = 'Subscribing...';

      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1200));
        
        showToast('✅ Thanks for subscribing!', 'success');
        ui.newsletterForm.reset();
      } catch (error) {
        showToast('❌ Something went wrong. Try again.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    });
  }

  // Product actions
  function bindProductActions() {
    // Add to cart
    ui.addToCartBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        
        state.cartCount++;
        localStorage.setItem('shopzone_cart_count', state.cartCount);
        updateCartBadges();
        
        // Visual feedback
        const originalText = btn.innerHTML;
        btn.innerHTML = '✅ Added!';
        btn.classList.add('added');
        
        setTimeout(() => {
          btn.innerHTML = originalText;
          btn.classList.remove('added');
        }, 1200);

        showToast('🛒 Item added to cart!');
      });
    });

    // Quick actions (wishlist, quick view)
    ui.actionBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const title = btn.getAttribute('title') || 'Action completed';
        showToast(title);
      });
    });
  }

  function updateCartBadges() {
    ui.cartBadges.forEach(badge => {
      badge.textContent = state.cartCount;
      badge.style.display = state.cartCount > 0 ? 'flex' : 'none';
    });
  }

  // Smooth scrolling for anchor links
  function bindSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
          const navbarHeight = 80;
          const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - navbarHeight;
          
          window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
          });
          
          closeMobileMenu();
        }
      });
    });
  }

  // Scroll reveal animations
  function initScrollReveals() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
          entry.target.style.animationDelay = `${index * 100}ms`;
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    });

    ui.revealElements.forEach(el => observer.observe(el));
  }

  // Image error handling
  function bindImageErrors() {
    document.querySelectorAll('img').forEach(img => {
      img.addEventListener('error', function() {
        if (!this.dataset.fallback) {
          this.src = `https://via.placeholder.com/400x400/f8fafc/64748b?text=No+Image`;
          this.dataset.fallback = 'true';
        }
      });
    });
  }

  // Toast notifications
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.innerHTML = `
      <span>${message}</span>
      <button class="toast__close" aria-label="Close">&times;</button>
    `;
    
    toast.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #0f172a;
      color: white;
      padding: 1rem 1.5rem;
      border-radius: 12px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.15);
      z-index: 10000;
      opacity: 0;
      transform: translateX(100%);
      transition: all 0.3s ease;
      max-width: 350px;
      font-size: 0.95rem;
    `;

    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateX(0)';
    });

    // Close button
    qs('.toast__close', toast)?.addEventListener('click', () => {
      toast.remove();
    });

    // Auto remove
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // Hero button animations
  function initHeroInteractions() {
    ui.heroButtons?.forEach((btn, index) => {
      btn.addEventListener('mouseenter', () => {
        btn.style.transform = 'translateY(-2px)';
      });
      
      btn.addEventListener('mouseleave', () => {
        btn.style.transform = 'translateY(0)';
      });
    });
  }

  // Initialize everything
  document.addEventListener('DOMContentLoaded', () => {
    init();
    initHeroInteractions();
  });

  // Handle page visibility changes
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      closeMobileMenu();
    }
  });

})();