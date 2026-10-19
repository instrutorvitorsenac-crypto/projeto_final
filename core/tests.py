import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Artwork, ArtworkInterest, ArtworkLike, ArtistFollow, Profile


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
            contact="artista@example.com",
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

    def test_auth_pages_render(self):
        self.assertContains(self.client.get(reverse("login")), "Entrar na ArtGallery")
        self.assertContains(self.client.get(reverse("register")), "Criar sua conta")

    def test_incomplete_profile_is_redirected_to_setup(self):
        incomplete_user = User.objects.create_user(
            username="incomplete@example.com",
            email="incomplete@example.com",
            password="StrongPassword123!",
        )
        self.client.force_login(incomplete_user)
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, reverse("profile_setup"))

    def test_seed_gallery_is_visible_on_homepage(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Entre marés")
        self.assertContains(response, "Lia Monteiro")
        self.assertContains(response, "/static/core/styles.css")

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
            {"next": reverse("artwork_detail", args=[self.artwork.pk])},
        )
        self.assertRedirects(
            response, reverse("artwork_detail", args=[self.artwork.pk])
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
                        "observations": "",
                        "image": image,
                        "image_url": "",
                    },
                )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(
            Artwork.objects.filter(
                artist=self.artist_profile, title="Novo trabalho", promotion=True
            ).exists()
        )

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
