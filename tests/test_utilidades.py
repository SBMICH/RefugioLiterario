"""Funciones auxiliares de app.py."""
from datetime import datetime

import pytest

import app as app_module


@pytest.mark.parametrize('email, valido', [
    ('ana@correo.co', True),
    ('a.b+c@sub.dominio.com', True),
    ('sin-arroba.com', False),
    ('dos@@arrobas.com', False),
    ('con espacio@x.com', False),
    ('ana@sinpunto', False),
    ('ana@.com', False),
    ('ana@dominio.', False),
    ('@dominio.com', False),
    ('', False),
    (None, False),
    ('a@b.co' + 'x' * 260, False),
])
def test_email_valido(email, valido):
    assert app_module.email_valido(email) is valido


@pytest.mark.parametrize('valor, texto', [(40000, '$40.000'), (1234567.6, '$1.234.568'), (0, '$0'), (None, '$0')])
def test_formato_precio(valor, texto):
    assert app_module.formato_precio(valor) == texto


def test_formato_fecha():
    assert app_module.formato_fecha(datetime(2026, 11, 3, 10, 30)) == '03/11/2026'
    assert app_module.formato_fecha(None) == ''
    assert app_module.formato_fecha('texto') == 'texto'


def test_paginas_visibles():
    assert app_module.paginas_visibles(1, 3) == [1, 2, 3]
    assert app_module.paginas_visibles(10, 20) == [1, None, 8, 9, 10, 11, 12, None, 20]


def test_paginacion_ajusta_la_pagina():
    assert app_module.paginacion(25, 12, 1) == (1, 3, 0)
    assert app_module.paginacion(25, 12, 99) == (3, 3, 24)
    assert app_module.paginacion(0, 12, 0) == (1, 1, 0)


def test_secret_key_se_genera_y_se_reutiliza(tmp_path, monkeypatch):
    monkeypatch.delenv('SECRET_KEY')
    monkeypatch.setattr(app_module, 'BASE_DIR', str(tmp_path))
    primera = app_module.cargar_secret_key()
    assert len(primera) == 64 and (tmp_path / '.secret_key').exists()
    assert app_module.cargar_secret_key() == primera


def test_init_db_genera_contrasenas_aleatorias(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv('ADMIN_PASSWORD')
    monkeypatch.setattr(app_module, 'DATABASE', str(tmp_path / 'nueva.db'))
    app_module.init_db()
    salida = capsys.readouterr().out
    assert 'Contraseña inicial de "admin"' in salida and 'Contraseña inicial de "user2"' in salida
    assert 'se-genera-al-crear-la-base' not in salida


def test_comando_init_db(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, 'DATABASE', str(tmp_path / 'cli.db'))
    resultado = app_module.app.test_cli_runner().invoke(args=['init-db'])
    assert 'Base de datos creada' in resultado.output
    assert (tmp_path / 'cli.db').exists()
