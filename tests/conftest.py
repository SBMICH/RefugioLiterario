"""Configuración compartida de las pruebas.

Cada prueba trabaja con una base de datos nueva y temporal: nunca se toca libreria.db.
"""
import os
import re
import sys
import tempfile

import pytest

# Variables que app.py lee al importarse: van antes del import.
_TMP = tempfile.mkdtemp()
os.environ['SECRET_KEY'] = 'clave-solo-para-pruebas'
os.environ['DATABASE_PATH'] = os.path.join(_TMP, 'inicial.db')
os.environ['ADMIN_PASSWORD'] = 'admin-de-prueba'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402

ADMIN = ('admin', 'admin-de-prueba')
LECTOR = ('user2', 'lector-de-prueba')
TOKEN_RE = re.compile(r'name="csrf_token" value="([^"]+)"')


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, 'DATABASE', str(tmp_path / 'prueba.db'))
    app_module.init_db()
    with app_module.sqlite3.connect(app_module.DATABASE) as db:
        app_module.actualizar_esquema(db)
        db.execute('UPDATE users SET password = ? WHERE username = ?', (generate_password_hash(LECTOR[1]), LECTOR[0]))
    app_module.intentos_fallidos.clear()
    app_module.app.config['TESTING'] = True
    return app_module.app


class Cliente:
    """Navegador de prueba: obtiene el token CSRF solo y sabe iniciar sesión."""

    def __init__(self, flask_app):
        self.http = flask_app.test_client()

    def token(self):
        for pagina in ('/registro', '/usuario'):
            encontrado = TOKEN_RE.search(self.http.get(pagina).get_data(as_text=True))
            if encontrado:
                return encontrado.group(1)
        raise AssertionError('No se encontró un token CSRF')

    def get(self, url, **kwargs):
        return self.http.get(url, **kwargs)

    def post(self, url, data=None, token=True, **kwargs):
        data = dict(data or {})
        if token:
            data['csrf_token'] = self.token()
        return self.http.post(url, data=data, **kwargs)

    def login(self, usuario, clave):
        return self.post('/login', {'username': usuario, 'password': clave})

    def texto(self, url, **kwargs):
        return self.get(url, follow_redirects=True, **kwargs).get_data(as_text=True)


@pytest.fixture
def cliente(app):
    return Cliente(app)


@pytest.fixture
def lector(app):
    c = Cliente(app)
    assert c.login(*LECTOR).status_code == 302
    return c


@pytest.fixture
def admin(app):
    c = Cliente(app)
    assert c.login(*ADMIN).status_code == 302
    return c


@pytest.fixture
def db(app):
    """Conexión directa a la base de la prueba, para preparar o comprobar datos."""
    conexion = app_module.sqlite3.connect(app_module.DATABASE, detect_types=app_module.sqlite3.PARSE_DECLTYPES)
    conexion.row_factory = app_module.sqlite3.Row
    yield conexion
    conexion.close()


def id_usuario(db, nombre):
    return db.execute('SELECT id FROM users WHERE username = ?', (nombre,)).fetchone()['id']
