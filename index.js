 document.addEventListener('DOMContentLoaded', () => {
 
  /* ---------------------------------------------------------------------
     1. HEADER — muda de aparência ao rolar a página
  --------------------------------------------------------------------- */
  const header = document.getElementById('site-header');
 
  function updateHeaderOnScroll() {
    if (!header) return;
    header.classList.toggle('is-scrolled', window.scrollY > 12);
  }
 
  updateHeaderOnScroll();
  window.addEventListener('scroll', updateHeaderOnScroll, { passive: true });
 
 
  /* ---------------------------------------------------------------------
     2. MENU MOBILE — abre/fecha o painel de navegação (hambúrguer)
  --------------------------------------------------------------------- */
  const menuToggle = document.getElementById('menu-toggle');
  const primaryNav = document.getElementById('primary-nav');
 
  if (menuToggle && primaryNav) {
    menuToggle.addEventListener('click', () => {
      const isOpen = primaryNav.classList.toggle('is-open');
      menuToggle.setAttribute('aria-expanded', String(isOpen));
      menuToggle.setAttribute('aria-label', isOpen ? 'Fechar menu' : 'Abrir menu');
    });
  }
 
 
  /* ---------------------------------------------------------------------
     3. ACCORDION DO MENU — "Quem Somos" e "Perguntas Frequentes" (+ / ×)
        Abrir um fecha o outro automaticamente.
  --------------------------------------------------------------------- */
  const navQuestions = document.querySelectorAll('[data-menu-toggle]');
 
  navQuestions.forEach((btn) => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('aria-controls');
      const targetPane = document.getElementById(targetId);
      const willOpen = !btn.getAttribute('aria-expanded') || btn.getAttribute('aria-expanded') === 'false';
 
      // Fecha todos os outros itens do accordion
      navQuestions.forEach((otherBtn) => {
        if (otherBtn === btn) return;
        otherBtn.setAttribute('aria-expanded', 'false');
        const otherPaneId = otherBtn.getAttribute('aria-controls');
        const otherPane = document.getElementById(otherPaneId);
        if (otherPane) otherPane.classList.remove('is-open');
      });
 
      // Alterna o item clicado
      btn.setAttribute('aria-expanded', String(willOpen));
      if (targetPane) targetPane.classList.toggle('is-open', willOpen);
    });
  });
 
  // Fecha o accordion do menu ao clicar fora dele (apenas em telas maiores,
  // onde o painel flutua sobre o conteúdo)
  document.addEventListener('click', (event) => {
    const clickedInsideNav = event.target.closest('.nav-accordion-item');
    if (clickedInsideNav) return;
 
    navQuestions.forEach((btn) => {
      btn.setAttribute('aria-expanded', 'false');
      const paneId = btn.getAttribute('aria-controls');
      const pane = document.getElementById(paneId);
      if (pane) pane.classList.remove('is-open');
    });
  });
 
 
  /* ---------------------------------------------------------------------
     4. FAQ — cada pergunta abre/fecha de forma independente
  --------------------------------------------------------------------- */
  const faqButtons = document.querySelectorAll('[data-faq-toggle]');
 
  faqButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const item = btn.closest('.faq-item');
      if (!item) return;
      const isOpen = item.classList.toggle('is-open');
      btn.setAttribute('aria-expanded', String(isOpen));
    });
  });
 
 
  /* ---------------------------------------------------------------------
     5. CARROSSEL — avança automaticamente, com setas, dots e swipe
  --------------------------------------------------------------------- */
  const slider = document.getElementById('hero-slider');
 
  if (slider) {
    const slides = Array.from(slider.querySelectorAll('.hero-slide'));
    const dots = Array.from(document.querySelectorAll('.hero-dots .dot'));
    const prevBtn = document.querySelector('[data-hero-prev]');
    const nextBtn = document.querySelector('[data-hero-next]');
 
    let current = slides.findIndex((s) => s.classList.contains('active'));
    if (current < 0) current = 0;
 
    const SLIDE_DURATION = 3500; // ms — deve bater com a animação do .progress-bar no CSS
    let autoplayTimer = null;
 
    function goToSlide(index) {
      if (!slides.length) return;
      const nextIndex = (index + slides.length) % slides.length;
 
      slides[current]?.classList.remove('active');
      slides[current]?.setAttribute('aria-hidden', 'true');
      dots[current]?.classList.remove('active');
 
      current = nextIndex;
 
      slides[current]?.classList.add('active');
      slides[current]?.setAttribute('aria-hidden', 'false');
      dots[current]?.classList.add('active');
 
      restartAutoplay();
    }
 
    function nextSlide() {
      goToSlide(current + 1);
    }
 
    function prevSlide() {
      goToSlide(current - 1);
    }
 
    function restartAutoplay() {
      if (autoplayTimer) clearInterval(autoplayTimer);
      if (slides.length > 1) {
        autoplayTimer = setInterval(nextSlide, SLIDE_DURATION);
      }
    }
 
    nextBtn?.addEventListener('click', () => goToSlide(current + 1));
    prevBtn?.addEventListener('click', () => goToSlide(current - 1));
 
    dots.forEach((dot, i) => {
      dot.addEventListener('click', () => goToSlide(i));
    });
 
    // Pausa o autoplay quando o rato está sobre o carrossel
    const heroSection = document.getElementById('top');
    heroSection?.addEventListener('mouseenter', () => {
      if (autoplayTimer) clearInterval(autoplayTimer);
    });
    heroSection?.addEventListener('mouseleave', restartAutoplay);
 
    // Suporte a gesto de arrastar (swipe) em ecrãs táteis
    let touchStartX = 0;
    let touchEndX = 0;
 
    slider.addEventListener('touchstart', (e) => {
      touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });
 
    slider.addEventListener('touchend', (e) => {
      touchEndX = e.changedTouches[0].screenX;
      const delta = touchEndX - touchStartX;
      const SWIPE_THRESHOLD = 40;
 
      if (delta > SWIPE_THRESHOLD) {
        prevSlide();
      } else if (delta < -SWIPE_THRESHOLD) {
        nextSlide();
      }
    }, { passive: true });
 
    // Pausa quando a aba não está visível, para poupar recursos
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        if (autoplayTimer) clearInterval(autoplayTimer);
      } else {
        restartAutoplay();
      }
    });
 
    restartAutoplay();
  }
 
 
  /* ---------------------------------------------------------------------
     6. ESTATÍSTICAS — contador animado quando a secção entra em ecrã
  --------------------------------------------------------------------- */
  const statNumbers = document.querySelectorAll('.stat-number[data-target]');
 
  function animateCount(el) {
    const target = parseFloat(el.getAttribute('data-target'));
    if (Number.isNaN(target)) return;
 
    const duration = 1400;
    const startTime = performance.now();
    const isInteger = Number.isInteger(target);
 
    function tick(now) {
      const progress = Math.min((now - startTime) / duration, 1);
      // easeOutExpo — desacelera suavemente perto do fim
      const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      const value = target * eased;
 
      el.textContent = isInteger ? Math.round(value) : value.toFixed(1);
 
      if (progress < 1) {
        requestAnimationFrame(tick);
      } else {
        el.textContent = isInteger ? target : target.toFixed(1);
      }
    }
 
    requestAnimationFrame(tick);
  }
 
  if (statNumbers.length && 'IntersectionObserver' in window) {
    const statsObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateCount(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });
 
    statNumbers.forEach((el) => statsObserver.observe(el));
  } else {
    // Sem suporte a IntersectionObserver: mostra o valor final direto
    statNumbers.forEach((el) => {
      const target = el.getAttribute('data-target');
      if (target) el.textContent = target;
    });
  }
 
 
  /* ---------------------------------------------------------------------
     7. REVEAL ON SCROLL — elementos surgem suavemente ao entrar em vista
  --------------------------------------------------------------------- */
  const revealTargets = document.querySelectorAll('[data-reveal], [data-reveal-group]');
 
  if (revealTargets.length && 'IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -60px 0px' });
 
    revealTargets.forEach((el) => revealObserver.observe(el));
  } else {
    revealTargets.forEach((el) => el.classList.add('is-visible'));
  }
 
  // Marca automaticamente as secções e cartões principais para animação de entrada,
  // sem exigir que o HTML declare manualmente cada atributo data-reveal.
  document.querySelectorAll('.section-heading').forEach((el) => el.setAttribute('data-reveal', ''));
  document.querySelectorAll('.service-grid, .notice-list, .faq-list, .stats-grid').forEach((el) => el.setAttribute('data-reveal-group', ''));
  document.querySelectorAll('.split-layout').forEach((el) => el.setAttribute('data-reveal', ''));
 
  // Reobserva os elementos recém-marcados (caso o passo acima rode depois da observação inicial)
  if ('IntersectionObserver' in window) {
    const lateTargets = document.querySelectorAll('[data-reveal]:not(.is-visible), [data-reveal-group]:not(.is-visible)');
    const lateObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -60px 0px' });
    lateTargets.forEach((el) => lateObserver.observe(el));
  }
 
 
  /* ---------------------------------------------------------------------
     8. BOTÃO VOLTAR AO TOPO — aparece após rolar, com scroll suave
  --------------------------------------------------------------------- */
  const backToTop = document.createElement('button');
  backToTop.type = 'button';
  backToTop.className = 'back-to-top';
  backToTop.setAttribute('aria-label', 'Voltar ao topo da página');
  backToTop.innerHTML = '&uarr;';
  document.body.appendChild(backToTop);
 
  function updateBackToTop() {
    backToTop.classList.toggle('is-visible', window.scrollY > 480);
  }
 
  updateBackToTop();
  window.addEventListener('scroll', updateBackToTop, { passive: true });
 
  backToTop.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
 
 
  /* ---------------------------------------------------------------------
     9. FECHAR MENU MOBILE ao clicar num link interno (âncora)
  --------------------------------------------------------------------- */
  document.querySelectorAll('a[href^="#"]').forEach((link) => {
    link.addEventListener('click', () => {
      if (primaryNav && primaryNav.classList.contains('is-open')) {
        primaryNav.classList.remove('is-open');
        menuToggle?.setAttribute('aria-expanded', 'false');
      }
    });
  });
 
});