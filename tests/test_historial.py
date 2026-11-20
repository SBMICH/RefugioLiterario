"""El historial de compras debe conservar lo que se pagó, aunque el libro cambie o se elimine."""
from conftest import id_usuario


def comprar(lector, libro_id):
    lector.post(f'/agregar_carrito/{libro_id}')
    lector.post('/finalizar_compra')


def test_la_compra_guarda_titulo_y_precio(lector, db):
    comprar(lector, 15)  # El principito, $30.000
    fila = db.execute('SELECT titulo, autor, precio FROM compras ORDER BY id DESC LIMIT 1').fetchone()
    assert (fila['titulo'], fila['autor'], fila['precio']) == ('El principito', 'Antoine de Saint-Exupéry', 30000)


def test_cambiar_el_precio_no_altera_compras_pasadas(lector, admin, db):
    comprar(lector, 15)
    ingresos_antes = admin.texto('/admin')
    admin.post('/editar_libro/15', {'titulo': 'El principito', 'autor': 'Antoine de Saint-Exupéry', 'genero': 'Fábula',
                                    'año_publicacion': '1943', 'descripcion': '', 'precio': '99000'})
    assert '$30.000' in lector.texto('/usuario')
    assert '$99.000' not in lector.texto('/usuario')
    assert _ingresos(admin.texto('/admin')) == _ingresos(ingresos_antes)


def test_eliminar_un_libro_no_borra_el_historial(lector, admin, db):
    comprar(lector, 15)
    ingresos_antes = _ingresos(admin.texto('/admin'))
    admin.post('/eliminar_libro/15')
    assert db.execute('SELECT 1 FROM catalogo WHERE id = 15').fetchone() is None
    assert 'El principito' in lector.texto('/usuario')
    assert _ingresos(admin.texto('/admin')) == ingresos_antes


def test_las_compras_antiguas_se_completan_al_migrar(app, db):
    """Las compras hechas antes de guardar título y precio se rellenan con los datos del catálogo."""
    user = id_usuario(db, 'user2')
    db.execute('UPDATE compras SET titulo = NULL, autor = NULL, precio = NULL')
    db.execute('INSERT INTO compras (user_id, libro_id, fecha_compra) VALUES (?, 4, CURRENT_TIMESTAMP)', (user,))
    db.commit()
    import app as app_module
    with app_module.sqlite3.connect(app_module.DATABASE) as conexion:
        app_module.actualizar_esquema(conexion)
    assert db.execute('SELECT COUNT(*) FROM compras WHERE precio IS NULL OR titulo IS NULL').fetchone()[0] == 0


def test_precio_infinito_no_rompe_el_formulario(admin):
    r = admin.post('/agregar_libro', {'titulo': 'X', 'autor': 'Y', 'genero': '', 'año_publicacion': '2000',
                                      'descripcion': '', 'precio': 'inf'})
    assert r.status_code == 400


def _ingresos(html):
    import re
    return re.search(r'(\$[\d.]+)</strong> en ventas', html).group(1)
