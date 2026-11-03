"""Catálogo, ficha del libro, carrito, compra, reseñas y lista de deseos."""
import pytest

from conftest import id_usuario


# ---------- Inicio y catálogo ----------
def test_inicio_muestra_los_mas_vendidos(cliente):
    pagina = cliente.texto('/')
    assert 'Los más vendidos' in pagina and 'El señor de los anillos' in pagina


def test_catalogo_es_publico_y_pagina_de_a_12(cliente):
    pagina = cliente.texto('/catalogo')
    assert '18 libros' in pagina
    assert pagina.count('class="book-slot"') == 12
    assert cliente.texto('/catalogo/2').count('class="book-slot"') == 6


def test_catalogo_pagina_fuera_de_rango_muestra_la_ultima(cliente):
    assert cliente.texto('/catalogo/99').count('class="book-slot"') == 6


def test_catalogo_busca_por_titulo_y_autor(cliente):
    assert '3 libros' in cliente.texto('/catalogo?q=García Márquez')
    assert '1 libro' in cliente.texto('/catalogo?q=rayuela')


def test_catalogo_filtra_por_genero(cliente):
    pagina = cliente.texto('/catalogo?genero=Ciencia ficción')
    assert '2 libros' in pagina and 'Fahrenheit 451' in pagina


def test_catalogo_sin_resultados(cliente):
    assert 'No encontramos libros' in cliente.texto('/catalogo?q=zzzz')


@pytest.mark.parametrize('orden', ['titulo', 'vendidos', 'valorados', 'recientes', 'precio_asc', 'precio_desc', 'otro'])
def test_catalogo_ordenes(cliente, orden):
    assert cliente.get(f'/catalogo?orden={orden}').status_code == 200


def test_orden_por_precio(cliente):
    caro = cliente.texto('/catalogo?orden=precio_desc').split('class="book-slot"')[1]
    barato = cliente.texto('/catalogo?orden=precio_asc').split('class="book-slot"')[1]
    assert 'El señor de los anillos' in caro and 'El principito' in barato


def test_paginacion_conserva_los_filtros(cliente):
    assert '/catalogo/2?q=a' in cliente.texto('/catalogo?q=a')


def test_ficha_del_libro(cliente):
    pagina = cliente.texto('/libro/6')
    assert 'Cien años de soledad' in pagina and '$50.000' in pagina
    assert 'Más de Gabriel García Márquez' in pagina


def test_ficha_de_libro_inexistente(cliente):
    assert cliente.get('/libro/9999').location.endswith('/catalogo')


# ---------- Carrito y compra ----------
def test_carrito_requiere_sesion(cliente):
    assert cliente.get('/carrito').location.endswith('/registro')
    assert cliente.post('/agregar_carrito/6').location.endswith('/registro')
    assert cliente.post('/eliminar_carrito/1').location.endswith('/registro')
    assert cliente.get('/finalizar_compra').location.endswith('/login')


def test_agregar_y_quitar_del_carrito(lector, db):
    lector.post('/agregar_carrito/6')
    assert 'Cien años de soledad' in lector.texto('/carrito')
    item = db.execute('SELECT id FROM carrito').fetchone()['id']
    lector.post(f'/eliminar_carrito/{item}')
    assert 'Tu carrito está vacío' in lector.texto('/carrito')


def test_no_se_agrega_dos_veces_el_mismo_libro(lector, db):
    lector.post('/agregar_carrito/6')
    lector.post('/agregar_carrito/6')
    assert db.execute('SELECT COUNT(*) FROM carrito').fetchone()[0] == 1
    assert 'ya está en tu carrito' in lector.texto('/carrito')


def test_agregar_libro_inexistente(lector, db):
    lector.post('/agregar_carrito/9999')
    assert db.execute('SELECT COUNT(*) FROM carrito').fetchone()[0] == 0


def test_comprar_vacia_el_carrito_y_registra_la_compra(lector, db):
    lector.post('/agregar_carrito/13')
    lector.post('/agregar_carrito/14')
    pagina = lector.texto('/finalizar_compra')
    assert 'Rayuela' in pagina and '$87.000' in pagina
    assert lector.post('/finalizar_compra').location.endswith('/gracias')
    assert db.execute('SELECT COUNT(*) FROM carrito').fetchone()[0] == 0
    comprados = {r[0] for r in db.execute('SELECT libro_id FROM compras WHERE user_id = ?', (id_usuario(db, 'user2'),))}
    assert {13, 14} <= comprados
    assert 'Rayuela' in lector.texto('/usuario')


def test_comprar_con_carrito_vacio(lector, db):
    antes = db.execute('SELECT COUNT(*) FROM compras').fetchone()[0]
    lector.post('/finalizar_compra')
    assert db.execute('SELECT COUNT(*) FROM compras').fetchone()[0] == antes
    assert 'Tu carrito está vacío.' in lector.texto('/gracias')


# ---------- Lista de deseos ----------
def test_lista_de_deseos_agregar_y_quitar(lector, db):
    lector.post('/favorito/6')
    assert db.execute('SELECT COUNT(*) FROM favoritos').fetchone()[0] == 1
    assert 'En tu lista de deseos' in lector.texto('/libro/6')
    lector.post('/favorito/6')
    assert db.execute('SELECT COUNT(*) FROM favoritos').fetchone()[0] == 0


def test_lista_de_deseos_requiere_sesion(cliente):
    assert cliente.post('/favorito/6').location.endswith('/login')


def test_lista_de_deseos_libro_inexistente(lector, db):
    lector.post('/favorito/9999')
    assert db.execute('SELECT COUNT(*) FROM favoritos').fetchone()[0] == 0


# ---------- Reseñas ----------
def test_publicar_y_editar_resena(lector, db):
    lector.post('/resena/6', {'calificacion': '4', 'comentario': 'Muy bueno'})
    assert 'Muy bueno' in lector.texto('/libro/6')
    lector.post('/resena/6', {'calificacion': '5', 'comentario': 'Mejor aún'})
    filas = db.execute('SELECT calificacion, comentario FROM resenas').fetchall()
    assert [tuple(f) for f in filas] == [(5, 'Mejor aún')]
    assert '5.0 · 1 reseña' in lector.texto('/libro/6')


@pytest.mark.parametrize('calificacion', ['0', '6', 'abc', ''])
def test_resena_con_calificacion_invalida(lector, db, calificacion):
    lector.post('/resena/6', {'calificacion': calificacion})
    assert db.execute('SELECT COUNT(*) FROM resenas').fetchone()[0] == 0


def test_resena_requiere_sesion(cliente):
    assert cliente.post('/resena/6', {'calificacion': '5'}).location.endswith('/login')
    assert cliente.post('/eliminar_resena/1').location.endswith('/login')


def test_resena_libro_inexistente(lector, db):
    lector.post('/resena/9999', {'calificacion': '5'})
    assert db.execute('SELECT COUNT(*) FROM resenas').fetchone()[0] == 0


def test_eliminar_resena_propia(lector, db):
    lector.post('/resena/6', {'calificacion': '3'})
    resena = db.execute('SELECT id FROM resenas').fetchone()['id']
    lector.post(f'/eliminar_resena/{resena}')
    assert db.execute('SELECT COUNT(*) FROM resenas').fetchone()[0] == 0


def test_no_se_puede_eliminar_resena_ajena(app, lector, db):
    from conftest import Cliente
    otro = Cliente(app)
    otro.post('/registro', {'new-username': 'otro', 'email': 'otro@x.co', 'new-password': 'clave-segura'})
    otro.login('otro', 'clave-segura')
    lector.post('/resena/6', {'calificacion': '3'})
    resena = db.execute('SELECT id FROM resenas').fetchone()['id']
    assert 'No puedes eliminar esa reseña' in otro.post(f'/eliminar_resena/{resena}', follow_redirects=True).get_data(as_text=True)
    assert db.execute('SELECT COUNT(*) FROM resenas').fetchone()[0] == 1


def test_admin_puede_eliminar_cualquier_resena(lector, admin, db):
    lector.post('/resena/6', {'calificacion': '1'})
    resena = db.execute('SELECT id FROM resenas').fetchone()['id']
    admin.post(f'/eliminar_resena/{resena}')
    assert db.execute('SELECT COUNT(*) FROM resenas').fetchone()[0] == 0
