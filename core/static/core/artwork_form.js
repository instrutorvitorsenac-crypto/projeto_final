(() => {
  const promotionToggle = document.getElementById("id_promotion");
  const promotionPriceField = document.querySelector("[data-promotion-price-field]");
  const regularPrice = document.getElementById("id_price");
  const promotionPrice = document.getElementById("id_promotion_price");
  const feedback = document.querySelector("[data-promotion-price-feedback]");

  if (!promotionToggle || !promotionPriceField || !regularPrice || !promotionPrice || !feedback) {
    return;
  }

  const updatePromotionPrice = () => {
    const enabled = promotionToggle.checked;
    promotionPriceField.hidden = !enabled;
    promotionPrice.required = enabled;
    promotionPrice.setCustomValidity("");
    feedback.hidden = true;

    if (!enabled || !promotionPrice.value || !regularPrice.value) {
      return;
    }

    const promo = Number(promotionPrice.value);
    const regular = Number(regularPrice.value);
    if (Number.isFinite(promo) && Number.isFinite(regular) && promo >= regular) {
      const message = "O preço em promoção deve ser menor que o preço normal.";
      promotionPrice.setCustomValidity(message);
      feedback.textContent = message;
      feedback.hidden = false;
    }
  };

  promotionToggle.addEventListener("change", updatePromotionPrice);
  promotionPrice.addEventListener("input", updatePromotionPrice);
  regularPrice.addEventListener("input", updatePromotionPrice);
  updatePromotionPrice();
})();
