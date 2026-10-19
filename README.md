# ArtGallery

Aplicação Django para uma galeria de arte. O Django cuida das contas, perfis,
obras, curtidas, artistas acompanhados e registros de interesse.

## Executar no Windows

Ative o ambiente virtual e instale as dependências:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crie/atualize o banco de dados e inicie o servidor:

```powershell
python manage.py migrate
python manage.py runserver
```

Abra `http://127.0.0.1:8000/`. Acesse `http://127.0.0.1:8000/admin/` para
administrar os perfis e as obras. Crie um usuário administrador com
`python manage.py createsuperuser`.

Obras podem usar uma imagem enviada (JPG, PNG, WEBP ou GIF, até 5 MB) ou um
endereço de imagem. O registro de interesse é demonstrativo e não processa
pagamentos.

Antes de publicar o projeto, configure `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`
e `DJANGO_ALLOWED_HOSTS` no ambiente. A chave padrão é somente para
desenvolvimento local.
