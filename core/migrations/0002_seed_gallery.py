from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations


ARTISTS = (
    {
        "username": "demo-lia",
        "name": "Lia Monteiro",
        "city": "São Paulo",
        "state": "SP",
        "styles": "Abstrato, Acrílica",
    },
    {
        "username": "demo-caio",
        "name": "Caio Nascimento",
        "city": "Salvador",
        "state": "BA",
        "styles": "Figurativo, Óleo",
    },
    {
        "username": "demo-malu",
        "name": "Malu Sato",
        "city": "Curitiba",
        "state": "PR",
        "styles": "Minimalista, Aquarela",
    },
    {
        "username": "demo-joao",
        "name": "João Vilela",
        "city": "Recife",
        "state": "PE",
        "styles": "Colagem, Contemporâneo",
    },
)

WORKS = (
    {
        "artist": "demo-lia",
        "title": "Entre marés",
        "series": "Cartografias do vento",
        "description": "Camadas de cor que lembram o encontro entre cidade e oceano.",
        "material": "Tela de algodão",
        "technique": "Acrílica",
        "style": "Abstrato",
        "width": 80,
        "height": 100,
        "promotion": True,
        "observations": "Obra assinada no verso.",
        "price": "1450.00",
        "image_url": "https://images.unsplash.com/photo-1541961017774-22349e4a1262?auto=format&fit=crop&w=1200&q=85",
    },
    {
        "artist": "demo-caio",
        "title": "Domingo de sol",
        "series": "Pequenos rituais",
        "description": "Uma tarde tranquila traduzida em pinceladas quentes.",
        "material": "Linho",
        "technique": "Óleo",
        "style": "Figurativo",
        "width": 60,
        "height": 80,
        "promotion": False,
        "observations": "Moldura não inclusa.",
        "price": "2100.00",
        "image_url": "https://images.unsplash.com/photo-1578301978693-85fa9c0320b9?auto=format&fit=crop&w=1200&q=85",
    },
    {
        "artist": "demo-malu",
        "title": "Jardim suspenso",
        "series": "Herbário íntimo",
        "description": "Formas botânicas em uma composição leve e contemplativa.",
        "material": "Papel algodão 300g",
        "technique": "Aquarela",
        "style": "Minimalista",
        "width": 42,
        "height": 59,
        "promotion": True,
        "observations": "Acompanha certificado de autenticidade.",
        "price": "780.00",
        "image_url": "https://images.unsplash.com/photo-1577083552431-6e5fd01aa342?auto=format&fit=crop&w=1200&q=85",
    },
    {
        "artist": "demo-joao",
        "title": "Inventário das coisas",
        "series": "Arquivo vivo",
        "description": "Papéis encontrados se reorganizam em uma paisagem imaginada.",
        "material": "Madeira e papel",
        "technique": "Colagem",
        "style": "Colagem",
        "width": 70,
        "height": 70,
        "promotion": False,
        "observations": "Peça única.",
        "price": "1250.00",
        "image_url": "https://images.unsplash.com/photo-1549490349-8643362247b5?auto=format&fit=crop&w=1200&q=85",
    },
    {
        "artist": "demo-lia",
        "title": "Luz de dentro",
        "series": "Cartografias do vento",
        "description": "Um estudo de transparências e movimento em tons minerais.",
        "material": "Tela de algodão",
        "technique": "Acrílica",
        "style": "Abstrato",
        "width": 50,
        "height": 70,
        "promotion": True,
        "observations": "Pronta para pendurar.",
        "price": "990.00",
        "image_url": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?auto=format&fit=crop&w=1200&q=85",
    },
    {
        "artist": "demo-caio",
        "title": "Janela azul",
        "series": "Pequenos rituais",
        "description": "Um retrato de interior feito em uma paleta de azuis e ocres.",
        "material": "Tela de linho",
        "technique": "Óleo",
        "style": "Figurativo",
        "width": 90,
        "height": 90,
        "promotion": True,
        "observations": "Obra original, peça única.",
        "price": "2350.00",
        "image_url": "https://images.unsplash.com/photo-1577083552431-6e5fd01aa342?auto=format&fit=crop&w=1200&q=85",
    },
)


def seed_gallery(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    Profile = apps.get_model("core", "Profile")
    Artwork = apps.get_model("core", "Artwork")
    database = schema_editor.connection.alias
    profiles = {}

    for artist in ARTISTS:
        username = artist["username"]
        user, _ = User.objects.using(database).get_or_create(
            username=username,
            defaults={"email": f"{username}@artgallery.test"},
        )
        user.password = make_password(None)
        user.save(using=database, update_fields=["password"])
        profile, _ = Profile.objects.using(database).get_or_create(
            user_id=user.pk,
            defaults={
                "role": "artist",
                "name": artist["name"],
                "age": 30,
                "city": artist["city"],
                "state": artist["state"],
                "country": "Brasil",
                "contact": f"{username}@artgallery.test",
                "styles": artist["styles"],
            },
        )
        profiles[username] = profile

    for work in WORKS:
        artist = profiles[work["artist"]]
        Artwork.objects.using(database).get_or_create(
            artist_id=artist.pk,
            title=work["title"],
            defaults={key: value for key, value in work.items() if key != "artist"},
        )


def remove_seed_gallery(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    database = schema_editor.connection.alias
    User.objects.using(database).filter(
        username__in=[artist["username"] for artist in ARTISTS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_gallery, remove_seed_gallery),
    ]
