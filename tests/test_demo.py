"""Modo demostración: cuentas de prueba visibles y protegidas."""
import pytest

import app as app_module
from conftest import id_usuario


@pytest.fixture
def demo(monkeypatch):
    monkeypatch.setattr(app_module, 'MODO_DEMO', True)


def test_sin_modo_demo_no_se_muestran_cuentas(cliente):
    assert 'Sitio de demostración' not in cliente.texto('/registro')


def test_modo_demo_muestra_las_cuentas(demo, cliente):
    pagina = cliente.texto('/registro')
    assert 'Sitio de demostración' in pagina and 'admin' in pagina


def test_modo_demo_protege_las_cuentas_de_prueba(demo, admin, db):
    admin_id = id_usuario(db, 'admin')
    admin.post('/editar_perfil', {'username': 'otro', 'email': 'otro@correo.com'})
    assert db.execute('SELECT username FROM users WHERE id = ?', (admin_id,)).fetchone()[0] == 'admin'


def test_modo_demo_no_protege_cuentas_normales(demo, admin, db):
    lector_id = id_usuario(db, 'user2')
    admin.post(f'/eliminar_usuario/{lector_id}')
    assert db.execute('SELECT 1 FROM users WHERE id = ?', (lector_id,)).fetchone() is None


def test_modo_demo_sin_clave_de_admin_no_la_muestra_vacia(demo, cliente, monkeypatch):
    monkeypatch.setattr(app_module, 'CUENTAS_DEMO', {'ana': 'ana12345'})
    pagina = cliente.texto('/registro')
    assert '<code>ana</code>' in pagina and '<code>admin</code>' not in pagina
