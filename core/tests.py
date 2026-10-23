import tempfile
from urllib.parse import urlparse

from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    Artwork,
    ArtworkImage,
    ArtworkInterest,
    ArtworkLike,
    ArtistFollow,
    Profile,
)


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"]
)
class GalleryViewsTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username="client@example.com",
            email="client@example.com",
            password="StrongPassword123!",
        )
        self.client_profile = Profile.objects.create(
            user=self.client_user,
            role=Profile.Role.CLIENT,
            name="Cliente Exemplo",
            age=29,
            city="São Paulo",
            state="SP",
            country="Brasil",
            contact="cliente@example.com",
        )
        self.artist_user = User.objects.create_user(
            username="artist@example.com",
            email="artist@example.com",
            password="StrongPassword123!",
        )
        self.artist_profile = Profile.objects.create(
            user=self.artist_user,
            role=Profile.Role.ARTIST,
            name="Artista Exemplo",
            age=34,
            city="Salvador",
            state="BA",
            country="Brasil",
            contact="+55 71 99999-0000",
            styles="Óleo, Figurativo",
        )
        self.artwork = Artwork.objects.create(
            artist=self.artist_profile,
            title="Luz de verão",
            material="Tela",
            technique="Óleo",
            style="Figurativo",
            width=60,
            height=80,
            price="750.00",
            image_url="https://example.com/art.jpg",
        )

    def test_registered_user_is_sent_to_profile_setup(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "novo@example.com",
                "password": "StrongPassword123!",
                "password_confirmation": "StrongPassword123!",
            },
        )
        self.assertRedirects(response, reverse("profile_setup"))
        self.assertTrue(User.objects.filter(email="novo@example.com").exists())
        self.assertTrue("_auth_user_id" in self.client.session)

    def test_registration_rejects_password_without_displayed_requirements(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "senha-fraca@example.com",
                "password": "onlylowercase",
                "password_confirmation": "onlylowercase",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No mínimo 8 caracteres")
        self.assertContains(response, "letra maiúscula")
        self.assertFalse(User.objects.filter(email="senha-fraca@example.com").exists())

    def test_auth_pages_render(self):
        self.assertContains(self.client.get(reverse("login")), "Entrar na ArtGallery")
        self.assertContains(self.client.get(reverse("register")), "Criar sua conta")
        self.assertContains(
            self.client.get(reverse("login")), "Esqueci minha senha"
        )

    def test_incomplete_profile_can_view_home_but_dashboard_needs_setup(self):
        incomplete_user = User.objects.create_user(
            username="incomplete@example.com",
            email="incomplete@example.com",
            password="StrongPassword123!",
        )
        self.client.force_login(incomplete_user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        restricted = self.client.get(reverse("dashboard"))
        self.assertRedirects(
            restricted, f"{reverse('profile_setup')}"
        )

    def test_seed_gallery_is_visible_on_homepage(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Janela azul")
        self.assertContains(response, "Lia Monteiro")
        self.assertContains(response, "/static/core/styles.css")
        self.assertEqual(len(response.context["featured"]), 4)
        self.assertEqual(
            sum(work.promotion for work in response.context["featured"]), 2
        )
        self.assertEqual(
            sum(not work.promotion for work in response.context["featured"]), 2
        )

    def test_anonymous_users_are_redirected_from_restricted_pages(self):
        for url in (
            reverse("artworks"),
            reverse("artists"),
            reverse("dashboard"),
            reverse("artwork_detail", args=[self.artwork.pk]),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response, f"{reverse('login')}?next={url}"
                )

    def test_login_returns_to_requested_restricted_page(self):
        response = self.client.post(
            f"{reverse('login')}?next={reverse('artworks')}",
            {"username": "client@example.com", "password": "StrongPassword123!"},
        )
        self.assertRedirects(response, reverse("artworks"))

    def test_password_reset_sends_email_and_accepts_token(self):
        with self.settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
        ):
            response = self.client.post(
                reverse("password_reset"), {"email": self.client_user.email}
            )
            self.assertRedirects(response, reverse("password_reset_done"))
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn(
                "conta/senha/redefinir/",
                mail.outbox[0].body,
            )
            reset_url = next(
                line
                for line in mail.outbox[0].body.splitlines()
                if line.startswith("http://")
            )
            confirm = self.client.get(urlparse(reset_url).path)
            self.assertEqual(confirm.status_code, 302)
            set_password_url = confirm["Location"]
            form = self.client.get(set_password_url)
            self.assertEqual(form.status_code, 200)
            changed = self.client.post(
                set_password_url,
                {
                    "new_password1": "NewPassword123!",
                    "new_password2": "NewPassword123!",
                },
            )
            self.assertRedirects(changed, reverse("password_reset_complete"))
            self.client_user.refresh_from_db()
            self.assertTrue(self.client_user.check_password("NewPassword123!"))

    def test_client_can_like_follow_and_register_interest(self):
        self.client.force_login(self.client_user)
        self.client.post(
            reverse("toggle_like", args=[self.artwork.pk]),
            {"next": reverse("artwork_detail", args=[self.artwork.pk])},
        )
        self.client.post(
            reverse("toggle_follow", args=[self.artist_profile.pk]),
            {"next": reverse("artists")},
        )
        response = self.client.post(
            reverse("register_interest", args=[self.artwork.pk]),
            {
                "next": (
                    f"{reverse('artwork_detail', args=[self.artwork.pk])}"
                    "?interest=registered"
                )
            },
        )
        self.assertRedirects(
            response,
            f"{reverse('artwork_detail', args=[self.artwork.pk])}"
            "?interest=registered",
        )
        self.assertTrue(
            ArtworkLike.objects.filter(
                profile=self.client_profile, artwork=self.artwork
            ).exists()
        )
        self.assertTrue(
            ArtistFollow.objects.filter(
                follower=self.client_profile, artist=self.artist_profile
            ).exists()
        )
        self.assertTrue(
            ArtworkInterest.objects.filter(
                profile=self.client_profile, artwork=self.artwork
            ).exists()
        )
        detail = self.client.get(
            reverse("artwork_detail", args=[self.artwork.pk])
        )
        self.assertContains(detail, "artist@example.com")
        self.assertContains(detail, "+55 71 99999-0000")
        self.assertContains(detail, "data-contact-dialog")
        self.assertContains(
            self.client.get(
                reverse("artwork_detail", args=[self.artwork.pk]),
                {"interest": "registered"},
            ),
            "data-open-on-load",
        )
        dashboard = self.client.get(reverse("dashboard"))
        self.assertContains(dashboard, "Luz de verão")
        self.assertContains(dashboard, "Artista Exemplo")

    def test_artist_can_publish_an_uploaded_image(self):
        self.client.force_login(self.artist_user)
        image = SimpleUploadedFile(
            "obra.png",
            b"\x89PNG\r\n\x1a\nfake image bytes",
            content_type="image/png",
        )
        second_image = SimpleUploadedFile(
            "obra-secundaria.webp",
            b"RIFF\x04\x00\x00\x00WEBPfake image",
            content_type="image/webp",
        )
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse("artwork_create"),
                    {
                        "title": "Novo trabalho",
                        "series": "",
                        "description": "Estudo de cores",
                        "material": "Papel",
                        "technique": "Aquarela",
                        "style": "Abstrato",
                        "width": 30,
                        "height": 40,
                        "price": "320.00",
                        "promotion": "on",
                        "promotion_price": "280.00",
                        "observations": "",
                        "images": [image, second_image],
                        "image_url": "",
                    },
                )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(
            Artwork.objects.filter(
                artist=self.artist_profile, title="Novo trabalho", promotion=True
            ).exists()
        )
        self.assertEqual(
            ArtworkImage.objects.filter(artwork__title="Novo trabalho").count(),
            2,
        )

    def test_artist_can_upload_heif_image(self):
        self.client.force_login(self.artist_user)
        heif_image = SimpleUploadedFile(
            "obra.heif",
            b"\x00\x00\x00\x18ftypheif" + b"\x00" * 8,
            content_type="image/heif",
        )
        response = self.client.post(
            reverse("artwork_create"),
            {
                "title": "Obra HEIF",
                "series": "",
                "description": "",
                "material": "Papel",
                "technique": "Digital",
                "style": "Abstrato",
                "width": 30,
                "height": 40,
                "price": "320.00",
                "observations": "",
                "images": [heif_image],
                "image_url": "",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(
            ArtworkImage.objects.filter(artwork__title="Obra HEIF").count(), 1
        )

    def test_followed_artworks_appear_in_logged_in_home_feed(self):
        self.client.force_login(self.client_user)
        ArtistFollow.objects.create(
            follower=self.client_profile, artist=self.artist_profile
        )
        recent_work = Artwork.objects.create(
            artist=self.artist_profile,
            title="Obra recém-publicada",
            material="Papel",
            technique="Aquarela",
            style="Abstrato",
            width=30,
            height=40,
            price="400.00",
            image_url="https://example.com/recent.jpg",
        )
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Novidades de artistas que você segue")
        self.assertContains(response, "Obra recém-publicada")
        self.assertEqual(response.context["followed_works"][0], recent_work)

    def test_artist_cannot_upload_image_over_10mb(self):
        self.client.force_login(self.artist_user)
        oversized_image = SimpleUploadedFile(
            "obra.png",
            b"\x89PNG\r\n\x1a\n" + b"x" * (10 * 1024 * 1024),
            content_type="image/png",
        )
        response = self.client.post(
            reverse("artwork_create"),
            {
                "title": "Imagem muito grande",
                "series": "",
                "description": "",
                "material": "Papel",
                "technique": "Digital",
                "style": "Abstrato",
                "width": 30,
                "height": 40,
                "price": "320.00",
                "observations": "",
                "images": [oversized_image],
                "image_url": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cada imagem deve ter no máximo 10 MB.")
        self.assertFalse(Artwork.objects.filter(title="Imagem muito grande").exists())

    def test_artist_cannot_activate_promotion_at_or_above_regular_price(self):
        self.client.force_login(self.artist_user)
        for promotion_price in ("750.00", "800.00"):
            with self.subTest(promotion_price=promotion_price):
                response = self.client.post(
                    reverse("artwork_create"),
                    {
                        "title": "Oferta inválida",
                        "series": "",
                        "description": "",
                        "material": "Tela",
                        "technique": "Óleo",
                        "style": "Figurativo",
                        "width": 60,
                        "height": 80,
                        "price": "750.00",
                        "promotion": "on",
                        "promotion_price": promotion_price,
                        "observations": "",
                        "image_url": "https://example.com/invalid.jpg",
                    },
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(
                    response,
                    "O preço em promoção deve ser menor que o preço normal.",
                )
        self.assertFalse(
            Artwork.objects.filter(title="Oferta inválida").exists()
        )

    def test_artist_can_edit_owned_artwork_and_promotional_price(self):
        self.client.force_login(self.artist_user)
        response = self.client.post(
            reverse("artwork_edit", args=[self.artwork.pk]),
            {
                "title": "Luz de verão atualizada",
                "series": "",
                "description": "Descrição revisada",
                "material": "Tela",
                "technique": "Óleo",
                "style": "Figurativo",
                "width": 70,
                "height": 90,
                "price": "900.00",
                "promotion": "on",
                "promotion_price": "825.00",
                "observations": "",
                "image_url": "https://example.com/art.jpg",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.artwork.refresh_from_db()
        self.assertEqual(self.artwork.title, "Luz de verão atualizada")
        self.assertEqual(self.artwork.width, 70)
        self.assertTrue(self.artwork.promotion)
        self.assertEqual(str(self.artwork.promotion_price), "825.00")

        response = self.client.post(
            reverse("artwork_edit", args=[self.artwork.pk]),
            {
                "title": "Luz de verão atualizada",
                "series": "",
                "description": "Descrição revisada",
                "material": "Tela",
                "technique": "Óleo",
                "style": "Figurativo",
                "width": 70,
                "height": 90,
                "price": "900.00",
                "observations": "",
                "image_url": "https://example.com/art.jpg",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.artwork.refresh_from_db()
        self.assertFalse(self.artwork.promotion)
        self.assertIsNone(self.artwork.promotion_price)

    def test_artist_cannot_edit_another_artists_artwork(self):
        other_user = User.objects.create_user(
            username="other-artist@example.com",
            email="other-artist@example.com",
            password=None,
        )
        Profile.objects.create(
            user=other_user,
            role=Profile.Role.ARTIST,
            name="Outro artista",
            age=35,
            city="Recife",
            state="PE",
            contact="outro@example.com",
        )
        self.client.force_login(other_user)
        response = self.client.get(reverse("artwork_edit", args=[self.artwork.pk]))
        self.assertEqual(response.status_code, 404)

    def test_promotional_artwork_displays_both_prices_on_home(self):
        self.artwork.promotion = True
        self.artwork.promotion_price = "600.00"
        self.artwork.save()
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "regular-price")
        self.assertContains(response, "promotion-price")
        self.assertContains(response, "750,00")
        self.assertContains(response, "600,00")

    def test_artist_list_filters_by_city_and_artwork_detail_renders(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("artists"), {"city": "Salvador"})
        self.assertContains(response, "Artista Exemplo")
        self.assertNotContains(response, "Cliente Exemplo")
        detail = self.client.get(
            reverse("artwork_detail", args=[self.artwork.pk])
        )
        self.assertContains(detail, "Luz de verão")
        filtered_works = self.client.get(
            reverse("artworks"), {"artist": self.artist_profile.pk}
        )
        self.assertContains(filtered_works, "Luz de verão")
