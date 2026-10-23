(() => {
  const carousel = document.querySelector("[data-featured-carousel]");
  const slides = carousel
    ? Array.from(carousel.querySelectorAll("[data-carousel-slide]"))
    : [];
  const previous = document.querySelector("[data-carousel-previous]");
  const next = document.querySelector("[data-carousel-next]");
  const position = document.querySelector("[data-carousel-position]");

  if (!carousel || slides.length === 0 || !previous || !next || !position) {
    return;
  }

  let current = 0;
  let touchStartX = null;
  const showSlide = (index) => {
    current = (index + slides.length) % slides.length;
    slides.forEach((slide, slideIndex) => {
      slide.hidden = slideIndex !== current;
      slide.classList.toggle("is-active", slideIndex === current);
    });
    position.textContent = `${current + 1} / ${slides.length}`;
  };

  previous.addEventListener("click", () => showSlide(current - 1));
  next.addEventListener("click", () => showSlide(current + 1));
  carousel.addEventListener("touchstart", (event) => {
    touchStartX = event.changedTouches[0].clientX;
  }, { passive: true });
  carousel.addEventListener("touchend", (event) => {
    if (touchStartX === null) {
      return;
    }
    const distance = event.changedTouches[0].clientX - touchStartX;
    if (Math.abs(distance) > 45) {
      showSlide(current + (distance < 0 ? 1 : -1));
    }
    touchStartX = null;
  }, { passive: true });
  showSlide(current);
})();
