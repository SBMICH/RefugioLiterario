"""Prueba de carga: mide cuánto tardan las páginas con muchos datos.

Trabaja sobre una COPIA de la base de datos (no toca libreria.db).

Uso (desde la carpeta del proyecto):
    python herramientas/prueba_carga.py              # 10.000 libros, 50.000 compras
    python herramientas/prueba_carga.py 50000 200000 # libros y compras a medida
"""
import os
import secrets
import re
import shutil
import sqlite3
import sys
import tempfile
import time
from datetime import datetime, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N_LIBROS = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
N_COMPRAS = int(sys.argv[2]) if len(sys.argv) > 2 else 50_000
N_USUARIOS = 2_000

copia = os.path.join(tempfile.mkdtemp(), 'carga.db')
shutil.copy(os.path.join(RAIZ, 'libreria.db'), copia)
os.environ['DATABASE_PATH'] = copia
sys.path.insert(0, RAIZ)
from app import app  # noqa: E402  (importar después de fijar DATABASE_PATH)
from werkzeug.security import generate_password_hash  # noqa: E402

azar = secrets.SystemRandom()
PALABRAS = ('sombra luz río casa noche mar jardín memoria viento ciudad silencio fuego '
            'tiempo camino isla piedra sueño bosque espejo carta').split()
GENEROS = ['Novela', 'Misterio', 'Fantasía', 'Ciencia ficción', 'Romance', 'Ensayo', 'Poesía', 'Historia']

print(f'Generando {N_LIBROS:,} libros, {N_USUARIOS:,} usuarios y {N_COMPRAS:,} compras…')
inicio = time.perf_counter()
db = sqlite3.connect(copia)
db.executemany('INSERT INTO catalogo (titulo, autor, genero, año_publicacion, descripcion, precio) VALUES (?, ?, ?, ?, ?, ?)',
               ((f'El {azar.choice(PALABRAS)} de la {azar.choice(PALABRAS)} {i}', f'Autor de prueba {i % 900}',
                 azar.choice(GENEROS), azar.randint(1800, 2025), 'Libro generado para la prueba de carga.',
                 azar.randrange(20000, 90000, 1000)) for i in range(N_LIBROS)))
# Administrador temporal con clave aleatoria, solo existe en la copia
CLAVE_ADMIN = secrets.token_urlsafe(16)
db.execute("INSERT INTO users (username, email, password, is_admin) VALUES ('admin_carga', 'admin@prueba.test', ?, 1)",
           (generate_password_hash(CLAVE_ADMIN),))
db.executemany('INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, 0)',
               ((f'carga{i}', f'carga{i}@prueba.test', '!') for i in range(N_USUARIOS)))
libros = [r[0] for r in db.execute('SELECT id FROM catalogo')]
usuarios = [r[0] for r in db.execute('SELECT id FROM users')]
ahora = datetime.now()
db.executemany('INSERT INTO compras (user_id, libro_id, fecha_compra) VALUES (?, ?, ?)',
               ((azar.choice(usuarios), azar.choice(libros), ahora - timedelta(minutes=i)) for i in range(N_COMPRAS)))
db.executemany('INSERT OR IGNORE INTO resenas (user_id, libro_id, calificacion, comentario, fecha) VALUES (?, ?, ?, ?, ?)',
               ((azar.choice(usuarios), azar.choice(libros), azar.randint(1, 5), 'Reseña de prueba', ahora)
                for _ in range(N_COMPRAS // 5)))
db.commit()
db.close()
print(f'Datos creados en {time.perf_counter() - inicio:.1f} s\n')

cliente = app.test_client()
token = re.search(r'csrf_token" value="([^"]+)', cliente.get('/registro').text).group(1)
cliente.post('/login', data={'username': 'admin_carga', 'password': CLAVE_ADMIN, 'csrf_token': token})

ultima = -(-(N_LIBROS + 102) // 12)
PAGINAS = [
    ('Inicio (más vendidos)', '/'),
    ('Catálogo, página 1', '/catalogo'),
    (f'Catálogo, última página ({ultima})', f'/catalogo/{ultima}'),
    ('Búsqueda por texto', '/catalogo?q=memoria'),
    ('Filtro por género', '/catalogo?genero=Misterio'),
    ('Orden: más vendidos', '/catalogo?orden=vendidos'),
    ('Orden: mejor valorados', '/catalogo?orden=valorados'),
    ('Ficha de un libro', f'/libro/{libros[len(libros) // 2]}'),
    ('Admin: libros', '/admin'),
    ('Admin: búsqueda', '/admin?q=sombra'),
    ('Admin: usuarios', '/admin?tab=usuarios'),
    ('Admin: más vendidos', '/admin?tab=ventas'),
]

print(f'{"Página":38} {"Estado":>6} {"Promedio":>10} {"Peor":>9}')
peor_total = 0
for nombre, url in PAGINAS:
    tiempos = []
    for _ in range(5):
        t = time.perf_counter()
        r = cliente.get(url)
        tiempos.append((time.perf_counter() - t) * 1000)
    peor_total = max(peor_total, max(tiempos))
    print(f'{nombre:38} {r.status_code:>6} {sum(tiempos) / len(tiempos):>8.0f}ms {max(tiempos):>7.0f}ms')

print(f'\nPágina más lenta: {peor_total:.0f} ms')
os.remove(copia)
