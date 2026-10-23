(() => {
  const password = document.querySelector(
    "#id_password, #id_new_password1"
  );
  const checklist = document.querySelector("[data-password-checklist]");

  if (!password || !checklist) {
    return;
  }

  const checks = {
    length: (value) => value.length >= 8,
    upper: (value) => /\p{Lu}/u.test(value),
    lower: (value) => /\p{Ll}/u.test(value),
    number: (value) => /\p{N}/u.test(value),
    special: (value) => /[^\p{L}\p{N}]/u.test(value),
  };

  const updateChecklist = () => {
    checklist.querySelectorAll("[data-rule]").forEach((item) => {
      const rule = item.dataset.rule;
      const valid = checks[rule]?.(password.value) ?? false;
      item.classList.toggle("is-valid", valid);
      item.setAttribute("aria-checked", String(valid));
    });
  };

  password.addEventListener("input", updateChecklist);
  updateChecklist();
})();
