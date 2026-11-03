"""CSRF, redirecciones, cabeceras, permisos y escapes de HTML."""
import pytest

from conftest import id_usuario

RUTAS_ADMIN_GET = ['/admin', '/admin?tab=usuarios', '/admin?tab=ventas', '/agregar_libro',
                   '/editar_libro/2', '/editar_usuario/1']
RUTAS_ADMIN_POST = ['/agregar_libro', '/editar_libro/2', '/eliminar_libro/2', '/editar_usuario/1', '/eliminar_usuario/1']


def test_post_sin_token_csrf_se_rechaza(lector, db):
    r = lector.post('/favorito/6', token=False)
    assert r.status_code == 302
    assert db.execute('SELECT COUNT(*) FROM favoritos').fetchone()[0] == 0
    assert 'La sesión expiró' in lector.texto('/catalogo')


def test_post_con_token_falso_se_rechaza(lector, db):
    lector.post('/favorito/6', {'csrf_token': 'falso'}, token=False)
    assert db.execute('SELECT COUNT(*) FROM favoritos').fetchone()[0] == 0


def test_no_redirige_a_otros_sitios(lector):
    r = lector.post('/agregar_carrito/6', headers={'Referer': 'https://sitio-malicioso.test/robar'})
    assert r.location.endswith('/catalogo')


def test_redirige_a_la_pagina_anterior_del_mismo_sitio(lector):
    r = lector.post('/agregar_carrito/6', headers={'Referer': 'http://localhost/catalogo/2?q=a'})
    assert r.location == 'http://localhost/catalogo/2?q=a'


def test_cabeceras_de_seguridad(cliente):
    cabeceras = cliente.get('/').headers
    assert cabeceras['X-Frame-Options'] == 'DENY'
    assert cabeceras['X-Content-Type-Options'] == 'nosniff'
    assert "frame-ancestors 'none'" in cabeceras['Content-Security-Policy']


def test_cookie_de_sesion_no_accesible_desde_javascript(cliente):
    from conftest import LECTOR
    r = cliente.login(*LECTOR)
    cookie = r.headers['Set-Cookie']
    assert 'HttpOnly' in cookie and 'SameSite=Lax' in cookie


@pytest.mark.parametrize('ruta', RUTAS_ADMIN_GET)
def test_lector_no_entra_a_paginas_de_admin(lector, ruta):
    assert lector.get(ruta).location.endswith('/registro')


@pytest.mark.parametrize('ruta', RUTAS_ADMIN_GET)
def test_visitante_no_entra_a_paginas_de_admin(cliente, ruta):
    assert cliente.get(ruta).location.endswith('/registro')


@pytest.mark.parametrize('ruta', RUTAS_ADMIN_POST)
def test_lector_no_puede_hacer_acciones_de_admin(lector, db, ruta):
    libros, usuarios = (db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ('catalogo', 'users'))
    r = lector.post(ruta, {'titulo': 'X', 'autor': 'Y', 'genero': 'Z', 'año_publicacion': '2000',
                           'descripcion': 'd', 'precio': '1', 'username': 'hack', 'email': 'h@a.co', 'is_admin': 'on'})
    assert r.location.endswith('/registro')
    assert db.execute('SELECT COUNT(*) FROM catalogo').fetchone()[0] == libros
    assert db.execute('SELECT COUNT(*) FROM users').fetchone()[0] == usuarios
    assert db.execute("SELECT is_admin FROM users WHERE username = 'user2'").fetchone()[0] == 0


def test_el_html_de_los_usuarios_se_escapa(lector):
    lector.post('/resena/6', {'calificacion': '5', 'comentario': '<script>alert(1)</script>'})
    pagina = lector.texto('/libro/6')
    assert '<script>alert(1)</script>' not in pagina
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in pagina


def test_busqueda_resiste_inyeccion_sql(cliente):
    r = cliente.get("/catalogo?q=' OR 1=1 --")
    assert r.status_code == 200 and '0 libros' in r.get_data(as_text=True)


def test_orden_desconocido_no_se_inserta_en_la_consulta(cliente):
    assert cliente.get('/catalogo?orden=titulo;DROP TABLE users').status_code == 200


def test_no_se_puede_borrar_el_carrito_de_otro(app, lector, db):
    from conftest import Cliente
    otro = Cliente(app)
    otro.post('/registro', {'new-username': 'otro', 'email': 'otro@x.co', 'new-password': 'clave-segura'})
    otro.login('otro', 'clave-segura')
    otro.post('/agregar_carrito/6')
    item = db.execute('SELECT id FROM carrito WHERE user_id = ?', (id_usuario(db, 'otro'),)).fetchone()['id']
    lector.post(f'/eliminar_carrito/{item}')
    assert db.execute('SELECT COUNT(*) FROM carrito WHERE id = ?', (item,)).fetchone()[0] == 1
