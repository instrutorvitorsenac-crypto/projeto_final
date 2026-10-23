from django import forms
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Artwork, Profile


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        files = data if isinstance(data, (list, tuple)) else [data]
        return [super().clean(upload, initial) for upload in files]


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
    images = MultipleFileField(
        label="Imagens da obra",
        required=False,
        widget=MultipleFileInput(
            attrs={
                "accept": "image/jpeg,image/png,image/webp,image/heic,image/heif",
            }
        ),
    )

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
            "promotion_price",
            "observations",
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
            "promotion_price": "Preço em Promoção (R$)",
            "observations": "Observações",
            "image_url": "Ou endereço da imagem",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "observations": forms.Textarea(attrs={"rows": 3}),
            "width": forms.NumberInput(attrs={"min": 1}),
            "height": forms.NumberInput(attrs={"min": 1}),
            "price": forms.NumberInput(attrs={"min": "0", "step": "0.01"}),
            "promotion_price": forms.NumberInput(
                attrs={"min": "0", "step": "0.01", "inputmode": "decimal"}
            ),
            "image_url": forms.URLInput(
                attrs={"placeholder": "https://exemplo.com/minha-obra.jpg"}
            ),
        }

    def clean_images(self):
        images = self.cleaned_data.get("images", [])
        valid_signatures = {
            "jpg": lambda header: header.startswith(b"\xff\xd8\xff"),
            "jpeg": lambda header: header.startswith(b"\xff\xd8\xff"),
            "png": lambda header: header.startswith(b"\x89PNG\r\n\x1a\n"),
            "webp": lambda header: (
                header[:4] == b"RIFF" and header[8:12] == b"WEBP"
            ),
            "heic": lambda header: (
                header[4:8] == b"ftyp"
                and header[8:12]
                in {
                    b"heic",
                    b"heix",
                    b"hevc",
                    b"hevx",
                    b"heif",
                    b"mif1",
                    b"msf1",
                }
            ),
            "heif": lambda header: (
                header[4:8] == b"ftyp"
                and header[8:12]
                in {
                    b"heic",
                    b"heix",
                    b"hevc",
                    b"hevx",
                    b"heif",
                    b"mif1",
                    b"msf1",
                }
            ),
        }
        allowed_content_types = {
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/heic",
            "image/heif",
            "image/heic-sequence",
            "image/heif-sequence",
        }

        for image in images:
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    "Cada imagem deve ter no máximo 10 MB."
                )
            extension = image.name.rsplit(".", 1)[-1].lower()
            image_header = image.read(16)
            image.seek(0)
            if not valid_signatures.get(extension, lambda header: False)(
                image_header
            ):
                raise forms.ValidationError(
                    f"O arquivo {image.name} não corresponde a uma imagem "
                    "JPG, PNG, WEBP, HEIC ou HEIF válida."
                )
            content_type = getattr(image, "content_type", "")
            if (
                content_type.startswith("image/")
                and content_type not in allowed_content_types
            ):
                raise forms.ValidationError(
                    "Envie imagens JPG, PNG, WEBP, HEIC ou HEIF."
                )
        return images

    def clean(self):
        cleaned_data = super().clean()
        regular_price = cleaned_data.get("price")
        promotion = cleaned_data.get("promotion")
        promotion_price = cleaned_data.get("promotion_price")

        if promotion:
            if promotion_price is None:
                self.add_error(
                    "promotion_price",
                    "Informe o preço em promoção para ativar a oferta.",
                )
            elif regular_price is not None and promotion_price >= regular_price:
                self.add_error(
                    "promotion_price",
                    "O preço em promoção deve ser menor que o preço normal.",
                )
        else:
            cleaned_data["promotion_price"] = None

        has_existing_image = bool(
            self.instance.pk
            and (
                self.instance.image
                or self.instance.images.exists()
                or self.instance.image_url
            )
        )
        if (
            not cleaned_data.get("images")
            and not cleaned_data.get("image_url")
            and not has_existing_image
            and not self.errors.get("images")
        ):
            self.add_error(
                "images",
                "Envie ao menos uma imagem ou informe o endereço de uma imagem.",
            )
        return cleaned_data
