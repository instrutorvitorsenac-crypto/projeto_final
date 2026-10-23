from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db.models import Exists, F, OuterRef, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import ArtworkForm, ProfileForm, RegistrationForm
from .models import (
    ArtistFollow,
    Artwork,
    ArtworkImage,
    ArtworkInterest,
    ArtworkLike,
    Profile,
)


def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = User.objects.create_user(
            username=form.cleaned_data["email"],
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )
        login(request, user)
        return redirect("profile_setup")
    return render(request, "core/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = AuthenticationForm(request, data=request.POST or None)
    form.fields["username"].label = "E-mail"
    form.fields["username"].widget.attrs.update(
        {"autocomplete": "email", "placeholder": "voce@exemplo.com"}
    )
    next_url = request.POST.get("next", request.GET.get("next", ""))
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        if url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}
        ):
            return redirect(next_url)
        return redirect("home")
    return render(
        request, "core/login.html", {"form": form, "next": next_url}
    )


@login_required
def logout_view(request):
    if request.method != "POST":
        return redirect("home")
    logout(request)
    return redirect("login")


def home(request):
    try:
        profile = request.user.profile if request.user.is_authenticated else None
    except Profile.DoesNotExist:
        profile = None

    works = Artwork.objects.select_related(
        "artist", "artist__user"
    ).prefetch_related("images")
    promoted = works.filter(
        promotion=True,
        promotion_price__isnull=False,
        promotion_price__lt=F("price"),
    )[:2]
    regular = works.filter(promotion=False)[:2]
    artists = Profile.objects.filter(role=Profile.Role.ARTIST)

    if profile:
        promoted = _annotate_likes(promoted, profile)
        regular = _annotate_likes(regular, profile)
        artists = _annotate_follows(artists, profile)
    featured = list(promoted) + list(regular)
    followed_works = Artwork.objects.none()
    if profile:
        followed_works = _annotate_likes(
            Artwork.objects.filter(
                artist__artist_followers__follower=profile
            )
            .select_related("artist", "artist__user")
            .prefetch_related("images"),
            profile,
        )[:6]

    return render(
        request,
        "core/home.html",
        {
            "profile": profile,
            "featured": featured,
            "artists": artists[:3],
            "followed_works": followed_works,
        },
    )


@login_required
def profile_setup(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = None
    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        profile = form.save(commit=False)
        profile.user = request.user
        profile.save()
        messages.success(request, "Seu perfil foi salvo.")
        return redirect("dashboard")
    return render(request, "core/profile_form.html", {"form": form})


@login_required
def dashboard(request):
    profile = _profile_or_redirect(request)
    if not isinstance(profile, Profile):
        return profile
    if profile.role == Profile.Role.ARTIST:
        works = _annotate_likes(
            profile.artworks.select_related("artist").prefetch_related("images"),
            profile,
        )
        return render(
            request, "core/artist_dashboard.html", {"profile": profile, "works": works}
        )
    liked_works = _annotate_likes(
        Artwork.objects.filter(likes__profile=profile)
        .select_related("artist")
        .prefetch_related("images"),
        profile,
    )
    followed_artists = _annotate_follows(
        Profile.objects.filter(artist_followers__follower=profile), profile
    )
    interests = ArtworkInterest.objects.filter(profile=profile).select_related(
        "artwork", "artwork__artist"
    )
    return render(
        request,
        "core/client_dashboard.html",
        {
            "profile": profile,
            "liked_works": liked_works,
            "followed_artists": followed_artists,
            "interests": interests,
        },
    )


@login_required
def artwork_list(request, category="artworks"):
    profile = _profile_or_redirect(request)
    if not isinstance(profile, Profile):
        return profile
    if category == "artists":
        artists = Profile.objects.filter(role=Profile.Role.ARTIST)
        artists = _annotate_follows(artists, profile)
        if query := request.GET.get("q", "").strip():
            artists = artists.filter(
                Q(name__icontains=query)
                | Q(city__icontains=query)
                | Q(state__icontains=query)
                | Q(styles__icontains=query)
            )
        if city := request.GET.get("city", "").strip():
            artists = artists.filter(city__icontains=city)
        return render(
            request,
            "core/artist_list.html",
            {"profile": profile, "artists": artists, "filters": request.GET},
        )

    works = Artwork.objects.select_related("artist").prefetch_related("images")
    if category == "promotions":
        works = works.filter(promotion=True)
    if query := request.GET.get("q", "").strip():
        works = works.filter(
            Q(title__icontains=query)
            | Q(artist__name__icontains=query)
            | Q(description__icontains=query)
        )
    artist_id = request.GET.get("artist", "").strip()
    if artist_id.isdecimal():
        works = works.filter(artist_id=int(artist_id))
    if style := request.GET.get("style", "").strip():
        works = works.filter(style__iexact=style)
    if city := request.GET.get("city", "").strip():
        works = works.filter(artist__city__icontains=city)
    for key, lookup in (("min_price", "price__gte"), ("max_price", "price__lte")):
        raw_value = request.GET.get(key, "").strip()
        if raw_value:
            try:
                amount = Decimal(raw_value)
                if not amount.is_finite() or amount < 0:
                    messages.warning(
                        request, "Um filtro de preço inválido foi ignorado."
                    )
                    continue
                works = works.filter(**{lookup: amount})
            except InvalidOperation:
                messages.warning(request, "Um filtro de preço inválido foi ignorado.")
    styles = (
        Artwork.objects.order_by()
        .values_list("style", flat=True)
        .distinct()
    )
    works = _annotate_likes(works, profile)
    title = "Promoções" if category == "promotions" else "Obras"
    return render(
        request,
        "core/artwork_list.html",
        {
            "profile": profile,
            "works": works,
            "styles": styles,
            "filters": request.GET,
            "title": title,
            "category": category,
        },
    )


@login_required
def artwork_detail(request, pk):
    profile = _profile_or_redirect(request)
    if not isinstance(profile, Profile):
        return profile
    artwork = get_object_or_404(
        Artwork.objects.select_related("artist", "artist__user")
        .prefetch_related("images"),
        pk=pk,
    )
    artwork_images = artwork.images.all()
    artwork.is_liked = ArtworkLike.objects.filter(
        profile=profile, artwork=artwork
    ).exists()
    artwork.interested = ArtworkInterest.objects.filter(
        profile=profile, artwork=artwork
    ).exists()
    artwork.is_following = ArtistFollow.objects.filter(
        follower=profile, artist=artwork.artist
    ).exists()
    return render(
        request,
        "core/artwork_detail.html",
        {
            "profile": profile,
            "artwork": artwork,
            "artwork_images": artwork_images,
        },
    )


@login_required
def artwork_create(request):
    profile = _profile_or_redirect(request)
    if not isinstance(profile, Profile):
        return profile
    if profile.role != Profile.Role.ARTIST:
        messages.error(request, "Somente artistas podem publicar obras.")
        return redirect("dashboard")
    form = ArtworkForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        artwork = form.save(commit=False)
        artwork.artist = profile
        artwork.save()
        _save_artwork_images(artwork, form)
        messages.success(request, "Sua obra foi publicada na galeria.")
        return redirect("dashboard")
    return render(
        request,
        "core/artwork_form.html",
        {"profile": profile, "form": form, "is_edit": False},
    )


@login_required
def artwork_edit(request, pk):
    profile = _profile_or_redirect(request)
    if not isinstance(profile, Profile):
        return profile
    if profile.role != Profile.Role.ARTIST:
        messages.error(request, "Somente artistas podem editar obras.")
        return redirect("dashboard")
    artwork = get_object_or_404(Artwork, pk=pk, artist=profile)
    form = ArtworkForm(request.POST or None, request.FILES or None, instance=artwork)
    if request.method == "POST" and form.is_valid():
        form.save()
        _save_artwork_images(artwork, form)
        messages.success(request, "As informações da obra foram atualizadas.")
        return redirect("dashboard")
    return render(
        request,
        "core/artwork_form.html",
        {"profile": profile, "form": form, "is_edit": True, "artwork": artwork},
    )


@login_required
def toggle_like(request, pk):
    if request.method != "POST":
        return redirect("artworks")
    profile = _profile_or_redirect(request)
    if not isinstance(profile, Profile):
        return profile
    artwork = get_object_or_404(Artwork, pk=pk)
    like, created = ArtworkLike.objects.get_or_create(
        profile=profile, artwork=artwork
    )
    if not created:
        like.delete()
    return _safe_return(request, "artwork_detail", pk=pk)


@login_required
def toggle_follow(request, pk):
    if request.method != "POST":
        return redirect("artists")
    profile = _profile_or_redirect(request)
    if not isinstance(profile, Profile):
        return profile
    artist = get_object_or_404(Profile, pk=pk, role=Profile.Role.ARTIST)
    if artist == profile:
        messages.error(request, "Você não pode acompanhar o próprio perfil.")
        return _safe_return(request, "artists")
    follow, created = ArtistFollow.objects.get_or_create(
        follower=profile, artist=artist
    )
    if not created:
        follow.delete()
    return _safe_return(request, "artists")


@login_required
def register_interest(request, pk):
    if request.method != "POST":
        return redirect("artworks")
    profile = _profile_or_redirect(request)
    if not isinstance(profile, Profile):
        return profile
    if profile.role != Profile.Role.CLIENT:
        messages.error(request, "Somente clientes podem registrar interesse.")
        return redirect("dashboard")
    artwork = get_object_or_404(Artwork, pk=pk)
    _, created = ArtworkInterest.objects.get_or_create(
        profile=profile, artwork=artwork
    )
    if created:
        messages.success(
            request,
            "Interesse registrado. Nenhum pagamento foi realizado.",
        )
    else:
        messages.info(request, "Seu interesse nesta obra já está registrado.")
    return _safe_return(request, "artwork_detail", pk=pk)


def _profile_or_redirect(request):
    try:
        return request.user.profile
    except Profile.DoesNotExist:
        messages.info(request, "Complete seu perfil para acessar a galeria.")
        return redirect("profile_setup")


def _save_artwork_images(artwork, form):
    position = artwork.images.count()
    for image in form.cleaned_data.get("images", []):
        ArtworkImage.objects.create(
            artwork=artwork,
            image=image,
            position=position,
        )
        position += 1


def _annotate_likes(works, profile):
    return works.annotate(
        is_liked=Exists(
            ArtworkLike.objects.filter(profile=profile, artwork_id=OuterRef("pk"))
        )
    )


def _annotate_follows(artists, profile):
    return artists.annotate(
        is_following=Exists(
            ArtistFollow.objects.filter(
                follower=profile, artist_id=OuterRef("pk")
            )
        )
    )


def _safe_return(request, fallback, **kwargs):
    url = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()}):
        return redirect(url)
    return redirect(reverse(fallback, kwargs=kwargs))
