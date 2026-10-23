from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PasswordComplexityValidator:
    def validate(self, password, user=None):
        errors = []
        if not any(character.isupper() for character in password):
            errors.append(_("A senha deve conter pelo menos uma letra maiúscula."))
        if not any(character.islower() for character in password):
            errors.append(_("A senha deve conter pelo menos uma letra minúscula."))
        if not any(character.isdigit() for character in password):
            errors.append(_("A senha deve conter pelo menos um número."))
        if not any(not character.isalnum() for character in password):
            errors.append(
                _("A senha deve conter pelo menos um caractere especial.")
            )
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "A senha deve conter letras maiúsculas e minúsculas, um número "
            "e um caractere especial."
        )
