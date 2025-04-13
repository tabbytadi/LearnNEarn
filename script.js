document.addEventListener('DOMContentLoaded', function () {
  const scrollElements = document.querySelectorAll(
    ".scroll-animate, .scroll-animate-side, .scroll-animate-leftside, .scroll-fade, .scroll-scale-fade"
  );

  const elementInView = (el, percentageScroll = 100) => {
    const elementTop = el.getBoundingClientRect().top;
    return (
      elementTop <=
      (window.innerHeight || document.documentElement.clientHeight) *
      (percentageScroll / 100)
    );
  };

  const elementRevealProgress = (el) => {
    const elementTop = el.getBoundingClientRect().top;
    const elementHeight = el.offsetHeight;
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight;

    const revealStart = viewportHeight - elementTop;
    const progress = Math.min(1, Math.max(0, revealStart / elementHeight));
    return progress;
  };

  const handleScrollAnimation = () => {
    scrollElements.forEach((el) => {
      if (elementInView(el, 100)) {
        el.classList.add("in-view");

        if (el.classList.contains("scroll-fade")) {
          const progress = elementRevealProgress(el) * 100;
          el.style.setProperty("--reveal-progress", `${100 - progress}%`);
        }
      } else {
        el.classList.remove("in-view");
      }
    });
  };

  window.addEventListener("scroll", handleScrollAnimation);
  handleScrollAnimation();



  // Current year update
  const yearElement = document.getElementById('current-year');
  if (yearElement) {
    yearElement.textContent = new Date().getFullYear();
  } else {
    console.error('Element with id "current-year" not found');
  }

  // Mobile menu functionality
  const mobileMenuButton = document.querySelector('.mobile-menu-button');
  const navLinks = document.querySelector('.nav-links');

  if (mobileMenuButton && navLinks) {
    // Toggle menu
    mobileMenuButton.addEventListener('click', function (e) {
      e.stopPropagation();
      navLinks.classList.toggle('active');
    });

    // Close menu when clicking outside
    document.addEventListener('click', function (e) {
      if (!navLinks.contains(e.target) && !mobileMenuButton.contains(e.target)) {
        navLinks.classList.remove('active');
      }
    });

    // Smooth scroll for mobile links
    navLinks.querySelectorAll('a').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
        navLinks.classList.remove('active');
      });
    });
  } else {
    console.error('Mobile menu elements not found');
  }

  // Smooth scroll for all navigation links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const targetId = this.getAttribute('href');
      const targetElement = document.querySelector(targetId);

      if (targetElement) {
        const headerHeight = document.querySelector('header').offsetHeight;
        const targetPosition = targetElement.offsetTop - headerHeight;

        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });
      }
    });
  });

  // Scroll-to-top button functionality
  const scrollTopButton = document.querySelector('.scroll-top');
  let lastScrollTop = 0;

  if (scrollTopButton) {
    window.addEventListener('scroll', () => {
      const currentScroll = window.scrollY;

      if (currentScroll < lastScrollTop && currentScroll > 200) {
        scrollTopButton.classList.add('active');
      } else {
        scrollTopButton.classList.remove('active');
      }

      lastScrollTop = currentScroll;
    });

    scrollTopButton.addEventListener('click', (e) => {
      e.preventDefault();
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  }

  // Header scroll effects
  const header = document.querySelector('header');
  let lastScrollHeader = 0;

  if (header) {
    window.addEventListener('scroll', () => {
      const currentScroll = window.scrollY;

      // Blur effect management
      if (currentScroll > 0) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }

      // Visibility management
      if (currentScroll > lastScrollHeader && currentScroll > 100) {
        // Scrolling down past 100px
        header.classList.add('hidden');
      } else {
        // Scrolling up
        header.classList.remove('hidden');
      }

      lastScrollHeader = currentScroll;
    });
  }
});