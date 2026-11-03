"""Registro, inicio y cierre de sesión, límite de intentos y perfil."""
from conftest import ADMIN, LECTOR, Cliente, id_usuario


def registrar(cliente, usuario='nuevo', email='nuevo@correo.co', clave='clave-segura'):
    return cliente.post('/registro', {'new-username': usuario, 'email': email, 'new-password': clave})


# ---------- Registro ----------
def test_registro_correcto_permite_iniciar_sesion(cliente):
    r = registrar(cliente)
    assert r.status_code == 302 and r.location.endswith('/login')
    assert cliente.login('nuevo', 'clave-segura').location.endswith('/catalogo/1')


def test_registro_guarda_la_contrasena_cifrada(cliente, db):
    registrar(cliente)
    guardada = db.execute("SELECT password FROM users WHERE username = 'nuevo'").fetchone()['password']
    assert guardada != 'clave-segura' and guardada.startswith('scrypt:')


def test_registro_rechaza_usuario_existente(cliente):
    assert '¡El usuario ya existe!' in registrar(cliente, usuario='admin').get_data(as_text=True)


def test_registro_rechaza_correo_existente(cliente):
    assert 'Ese correo ya está registrado.' in registrar(cliente, email='asd@gka.com').get_data(as_text=True)


def test_registro_rechaza_correo_invalido(cliente):
    assert 'Correo electrónico inválido' in registrar(cliente, email='sin-arroba').get_data(as_text=True)


def test_registro_rechaza_usuario_con_simbolos(cliente):
    assert 'alfanuméricos' in registrar(cliente, usuario='ana!').get_data(as_text=True)


def test_registro_rechaza_contrasena_corta(cliente):
    assert 'al menos 8 caracteres' in registrar(cliente, clave='1234567').get_data(as_text=True)


def test_registro_redirige_si_ya_hay_sesion(lector):
    assert lector.get('/registro').status_code == 302


# ---------- Inicio de sesión ----------
def test_login_correcto_guarda_la_sesion(cliente):
    cliente.login(*LECTOR)
    assert 'Hola, user2' in cliente.texto('/usuario')


def test_login_con_clave_incorrecta_no_revela_si_el_usuario_existe(cliente):
    existente = cliente.login('admin', 'mala').get_data(as_text=True)
    inexistente = cliente.login('nadie', 'mala').get_data(as_text=True)
    assert 'Usuario o contraseña incorrectos' in existente
    assert 'Usuario o contraseña incorrectos' in inexistente


def test_login_bloquea_tras_cinco_intentos(cliente):
    for restantes in (4, 3, 2, 1):
        assert f'Te quedan {restantes} intentos' in cliente.login('admin', 'mala').get_data(as_text=True)
    assert 'Demasiados intentos fallidos' in cliente.login('admin', 'mala').get_data(as_text=True)
    # Ni siquiera la contraseña correcta entra mientras dura el bloqueo
    r = cliente.login(*ADMIN)
    assert r.status_code == 200 and 'Demasiados intentos fallidos' in r.get_data(as_text=True)


def test_login_correcto_reinicia_el_contador(cliente):
    cliente.login('admin', 'mala')
    cliente.login(*ADMIN)
    otro = Cliente(cliente.http.application)
    assert 'Te quedan 4 intentos' in otro.login('admin', 'mala').get_data(as_text=True)


def test_el_bloqueo_expira(cliente, monkeypatch):
    import app as app_module
    for _ in range(5):
        cliente.login('admin', 'mala')
    ip, (fallos, desde) = next(iter(app_module.intentos_fallidos.items()))
    app_module.intentos_fallidos[ip] = (fallos, desde - app_module.BLOQUEO * 2)
    assert cliente.login(*ADMIN).status_code == 302


def test_login_redirige_si_ya_hay_sesion(lector):
    assert lector.get('/login').status_code == 302


def test_logout_cierra_la_sesion(lector):
    lector.post('/confirmar_logout')
    assert lector.get('/usuario').location.endswith('/registro')


def test_sesion_de_cuenta_eliminada_se_cierra(app, lector, admin, db):
    admin.post(f'/eliminar_usuario/{id_usuario(db, "user2")}')
    assert lector.get('/carrito').location.endswith('/registro')


def test_quitar_rol_admin_se_aplica_de_inmediato(app, admin, db):
    otro_admin = Cliente(app)
    db.execute("UPDATE users SET is_admin = 1 WHERE username = 'user2'")
    db.commit()
    otro_admin.login(*LECTOR)
    assert otro_admin.get('/admin').status_code == 200
    admin.post(f'/editar_usuario/{id_usuario(db, "user2")}', {'username': 'user2', 'email': 'user@m.com'})
    assert otro_admin.get('/admin').status_code == 302


# ---------- Perfil ----------
def test_ver_perfil_requiere_sesion(cliente):
    assert cliente.get('/usuario').location.endswith('/registro')


def test_perfil_muestra_compras_y_lista_de_deseos(lector):
    lector.post('/favorito/15')
    pagina = lector.texto('/usuario')
    assert 'El señor de los anillos' in pagina  # compra de los datos iniciales
    assert 'El principito' in pagina.split('Mi lista de deseos')[1]


def test_editar_perfil(lector):
    r = lector.post('/editar_perfil', {'username': 'lectora', 'email': 'lectora@correo.co'}, follow_redirects=True)
    assert 'Perfil actualizado exitosamente.' in r.get_data(as_text=True)
    assert 'Hola, lectora' in lector.texto('/usuario')


def test_editar_perfil_valida_los_datos(lector):
    assert 'alfanuméricos' in lector.post('/editar_perfil', {'username': 'a', 'email': 'a@b.co'},
                                         follow_redirects=True).get_data(as_text=True)
    assert 'Correo electrónico inválido' in lector.post('/editar_perfil', {'username': 'user2', 'email': 'malo'},
                                                        follow_redirects=True).get_data(as_text=True)


def test_editar_perfil_no_permite_datos_de_otra_cuenta(lector):
    r = lector.post('/editar_perfil', {'username': 'admin', 'email': 'user@m.com'}, follow_redirects=True)
    assert 'ya están en uso' in r.get_data(as_text=True)


def test_editar_perfil_requiere_sesion(cliente):
    assert cliente.post('/editar_perfil', {'username': 'x', 'email': 'x@y.co'}).location.endswith('/registro')
