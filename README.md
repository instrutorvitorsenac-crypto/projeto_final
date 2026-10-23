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
Artistas podem editar suas obras no painel e definir um preço promocional
inferior ao preço normal; ambos os valores são exibidos durante a oferta.
Ao atualizar o banco, ofertas antigas sem preço promocional serão desativadas
até que o artista informe um valor válido.
Cada obra aceita várias imagens JPG, PNG, WEBP, HEIC ou HEIF, com até 10 MB
por arquivo. A prévia HEIC/HEIF depende do suporte de imagem do navegador;
quando não suportada, o formulário exibe o formato e o nome do arquivo.

Antes de publicar o projeto, configure `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`
e `DJANGO_ALLOWED_HOSTS` no ambiente. A chave padrão é somente para
desenvolvimento local. A página inicial é pública; as páginas internas da
galeria continuam exigindo login.

O reset de senha usa o fluxo padrão de tokens do Django. Em desenvolvimento, o
link é escrito no console. Para enviar e-mails em produção, configure
`DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`,
`DJANGO_EMAIL_HOST`, `DJANGO_EMAIL_PORT`, `DJANGO_EMAIL_HOST_USER`,
`DJANGO_EMAIL_HOST_PASSWORD`, `DJANGO_EMAIL_USE_TLS` e
`DJANGO_DEFAULT_FROM_EMAIL` no ambiente.
