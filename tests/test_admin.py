"""Panel de administración: libros, usuarios y ventas."""
import pytest

from conftest import id_usuario

LIBRO = {'titulo': 'Libro nuevo', 'autor': 'Autora', 'genero': 'Novela', 'año_publicacion': '2020',
         'descripcion': 'Descripción', 'precio': '25000'}


def test_panel_muestra_resumen_y_pestanas(admin):
    pagina = admin.texto('/admin')
    assert '18 resultados' in pagina and 'Más vendidos' in pagina
    assert 'Cien años de soledad' in pagina
    assert 'user2' in admin.texto('/admin?tab=usuarios')
    assert 'El señor de los anillos' in admin.texto('/admin?tab=ventas')


def test_panel_busca_y_pagina(admin, db):
    assert '3 resultados' in admin.texto('/admin?q=García Márquez')
    db.executemany('INSERT INTO catalogo (titulo, autor, precio) VALUES (?, ?, ?)',
                   [(f'Extra {i}', 'Autor', 1000) for i in range(30)])
    db.commit()
    assert 'página 2 de 2' in admin.texto('/admin?pagina=2')
    assert 'página 1 de 2' in admin.texto('/admin?pagina=abc')
    assert '1 resultado' in admin.texto('/admin?tab=usuarios&q=user2')


def test_ver_usuarios_redirige_al_panel(admin):
    assert admin.get('/ver_usuarios').location.endswith('/admin?tab=usuarios')


# ---------- Libros ----------
def test_agregar_libro(admin, db):
    assert admin.get('/agregar_libro').status_code == 200
    assert admin.post('/agregar_libro', LIBRO).location.endswith('/admin')
    fila = db.execute("SELECT autor, año_publicacion, precio FROM catalogo WHERE titulo = 'Libro nuevo'").fetchone()
    assert tuple(fila) == ('Autora', 2020, 25000)


@pytest.mark.parametrize('cambio, mensaje', [
    ({'titulo': ''}, 'obligatorios'),
    ({'precio': 'gratis'}, 'deben ser números'),
    ({'año_publicacion': '3000'}, 'no es válido'),
    ({'precio': '-5'}, 'no puede ser negativo'),
    ({'titulo': 'x' * 300}, 'demasiado largo'),
])
def test_agregar_libro_valida_los_datos(admin, db, cambio, mensaje):
    r = admin.post('/agregar_libro', {**LIBRO, **cambio})
    assert r.status_code == 400 and mensaje in r.get_data(as_text=True)
    assert db.execute('SELECT COUNT(*) FROM catalogo').fetchone()[0] == 18


def test_editar_libro(admin, db):
    assert '1984' in admin.texto('/editar_libro/2')
    admin.post('/editar_libro/2', {**LIBRO, 'titulo': '1984', 'año_publicacion': '1949', 'precio': '41000'})
    assert tuple(db.execute('SELECT año_publicacion, precio FROM catalogo WHERE id = 2').fetchone()) == (1949, 41000)


def test_editar_libro_valida_los_datos(admin, db):
    r = admin.post('/editar_libro/2', {**LIBRO, 'precio': 'mucho'})
    assert r.status_code == 400
    assert db.execute('SELECT titulo FROM catalogo WHERE id = 2').fetchone()[0] == '1984'


def test_editar_libro_inexistente(admin):
    assert admin.get('/editar_libro/9999').location.endswith('/admin')


def test_eliminar_libro(admin, db):
    admin.post('/eliminar_libro/15')
    assert db.execute('SELECT COUNT(*) FROM catalogo WHERE id = 15').fetchone()[0] == 0


# ---------- Usuarios ----------
def test_editar_usuario(admin, db):
    uid = id_usuario(db, 'user2')
    assert 'user2' in admin.texto(f'/editar_usuario/{uid}')
    admin.post(f'/editar_usuario/{uid}', {'username': 'lector2', 'email': 'lector2@x.co', 'is_admin': 'on'})
    assert tuple(db.execute('SELECT username, email, is_admin FROM users WHERE id = ?', (uid,)).fetchone()) == ('lector2', 'lector2@x.co', 1)


@pytest.mark.parametrize('datos, mensaje', [
    ({'username': 'a', 'email': 'a@b.co'}, 'alfanuméricos'),
    ({'username': 'user2', 'email': 'malo'}, 'Correo electrónico inválido'),
    ({'username': 'admin', 'email': 'user@m.com'}, 'ya están en uso'),
])
def test_editar_usuario_valida_los_datos(admin, db, datos, mensaje):
    r = admin.post(f'/editar_usuario/{id_usuario(db, "user2")}', datos)
    assert r.status_code == 400 and mensaje in r.get_data(as_text=True)


def test_admin_no_puede_quitarse_su_propio_rol(admin, db):
    r = admin.post(f'/editar_usuario/{id_usuario(db, "admin")}', {'username': 'admin', 'email': 'asd@gka.com'})
    assert 'No puedes quitarte a ti mismo' in r.get_data(as_text=True)
    assert db.execute("SELECT is_admin FROM users WHERE username = 'admin'").fetchone()[0] == 1


def test_editar_usuario_inexistente(admin):
    assert admin.get('/editar_usuario/9999').location.endswith('/admin?tab=usuarios')


def test_eliminar_usuario(admin, db):
    admin.post(f'/eliminar_usuario/{id_usuario(db, "user2")}')
    assert db.execute("SELECT COUNT(*) FROM users WHERE username = 'user2'").fetchone()[0] == 0


def test_admin_no_puede_eliminarse_a_si_mismo(admin, db):
    r = admin.post(f'/eliminar_usuario/{id_usuario(db, "admin")}', follow_redirects=True)
    assert 'No puedes eliminar tu propia cuenta' in r.get_data(as_text=True)
    assert db.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'").fetchone()[0] == 1
