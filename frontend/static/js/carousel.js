/**
 * carousel.js — Swiper.js initialization for the advertisement carousel.
 */
document.addEventListener('DOMContentLoaded', function () {
  if (typeof Swiper === 'undefined') return;

  new Swiper('.ad-swiper', {
    loop: true,
    autoplay: {
      delay: 4000,
      disableOnInteraction: false,
      pauseOnMouseEnter: true,
    },
    speed: 800,
    effect: 'fade',
    fadeEffect: { crossFade: true },
    pagination: {
      el: '.swiper-pagination',
      clickable: true,
    },
    keyboard: { enabled: true },
    a11y: {
      prevSlideMessage: 'Previous advertisement',
      nextSlideMessage: 'Next advertisement',
    },
  });
});
