from django import forms
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Artwork, Profile


class RegistrationForm(forms.Form):
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Senha",
        min_length=8,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password_confirmation = forms.CharField(
        label="Confirme a senha",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Este e-mail já possui uma conta. Entre na sua conta."
            )
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmation = cleaned_data.get("password_confirmation")
        if password and confirmation and password != confirmation:
            self.add_error("password_confirmation", "As senhas não coincidem.")
        elif password:
            try:
                validate_password(password)
            except ValidationError as error:
                self.add_error("password", error)
        return cleaned_data


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            "role",
            "name",
            "age",
            "city",
            "state",
            "country",
            "contact",
            "education",
            "education_place",
            "styles",
        )
        labels = {
            "role": "Quero participar como",
            "name": "Nome",
            "age": "Idade",
            "city": "Cidade",
            "state": "Estado",
            "country": "País",
            "contact": "Contato",
            "education": "Tenho formação em arte",
            "education_place": "Instituição de ensino",
            "styles": "Estilos e técnicas (separados por vírgula)",
        }
        widgets = {
            "role": forms.Select(),
            "age": forms.NumberInput(attrs={"min": 1, "max": 120}),
            "education": forms.CheckboxInput(),
            "styles": forms.TextInput(
                attrs={"placeholder": "Abstrato, Acrílica, Aquarela"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("role") != Profile.Role.ARTIST:
            cleaned_data["education"] = False
            cleaned_data["education_place"] = ""
            cleaned_data["styles"] = ""
        elif cleaned_data.get("education") and not cleaned_data.get(
            "education_place", ""
        ).strip():
            self.add_error(
                "education_place",
                "Informe a instituição onde estudou.",
            )
        return cleaned_data


class ArtworkForm(forms.ModelForm):
    class Meta:
        model = Artwork
        fields = (
            "title",
            "series",
            "description",
            "material",
            "technique",
            "style",
            "width",
            "height",
            "price",
            "promotion",
            "observations",
            "image",
            "image_url",
        )
        labels = {
            "title": "Título da obra",
            "series": "Série",
            "description": "Descrição",
            "material": "Material",
            "technique": "Técnica",
            "style": "Estilo",
            "width": "Largura (cm)",
            "height": "Altura (cm)",
            "price": "Preço (R$)",
            "promotion": "Incluir em Promoções",
            "observations": "Observações",
            "image": "Imagem da obra",
            "image_url": "Ou endereço da imagem",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "observations": forms.Textarea(attrs={"rows": 3}),
            "width": forms.NumberInput(attrs={"min": 1}),
            "height": forms.NumberInput(attrs={"min": 1}),
            "price": forms.NumberInput(attrs={"min": "0", "step": "0.01"}),
            "image": forms.ClearableFileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp,image/gif"}
            ),
            "image_url": forms.URLInput(
                attrs={"placeholder": "https://exemplo.com/minha-obra.jpg"}
            ),
        }

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if not image:
            return image
        if image.size > 5 * 1024 * 1024:
            raise forms.ValidationError("A imagem deve ter no máximo 5 MB.")
        image_header = image.read(12)
        image.seek(0)
        extension = image.name.rsplit(".", 1)[-1].lower()
        valid_signature = {
            "jpg": image_header.startswith(b"\xff\xd8\xff"),
            "jpeg": image_header.startswith(b"\xff\xd8\xff"),
            "png": image_header.startswith(b"\x89PNG\r\n\x1a\n"),
            "gif": image_header.startswith((b"GIF87a", b"GIF89a")),
            "webp": image_header[:4] == b"RIFF" and image_header[8:12] == b"WEBP",
        }.get(extension, False)
        if not valid_signature:
            raise forms.ValidationError(
                "O conteúdo do arquivo não corresponde a uma imagem válida."
            )
        content_type = getattr(image, "content_type", "")
        if content_type and content_type not in {
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/gif",
        }:
            raise forms.ValidationError(
                "Envie uma imagem JPG, PNG, WEBP ou GIF."
            )
        return image

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("image") and not cleaned_data.get("image_url"):
            self.add_error(
                "image",
                "Envie uma imagem ou informe o endereço de uma imagem.",
            )
        return cleaned_data
