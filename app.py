from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import re
import secrets
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

# Clave secreta para firmar las sesiones. Se toma de la variable de entorno SECRET_KEY;
# si no existe, se genera una aleatoria y se guarda en .secret_key (no se sube a git).
def cargar_secret_key():
    if os.environ.get('SECRET_KEY'):
        return os.environ['SECRET_KEY']
    ruta = os.path.join(BASE_DIR, '.secret_key')
    if not os.path.exists(ruta):
        with open(ruta, 'w') as f:
            f.write(secrets.token_hex(32))
        os.chmod(ruta, 0o600)
    with open(ruta) as f:
        return f.read().strip()

app.secret_key = cargar_secret_key()

# Límite de intentos de inicio de sesión
MAX_INTENTOS = 5
BLOQUEO = timedelta(minutes=15)
intentos_fallidos = {}  # ip -> (cantidad, fecha del primer fallo)

# Ruta del archivo de base de datos SQLite
# Cookies de sesión más seguras
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('SESSION_COOKIE_SECURE') == '1',  # activar con HTTPS
)

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'libreria.db'))
SCHEMA = os.path.join(BASE_DIR, 'Base de datos', 'schema.sql')
MIGRACIONES = os.path.join(BASE_DIR, 'Base de datos', 'migraciones.sql')

# Conversión explícita de fechas (los conversores por defecto están obsoletos en Python 3.12)
sqlite3.register_adapter(datetime, lambda d: d.isoformat(' '))
sqlite3.register_converter('TIMESTAMP', lambda b: datetime.fromisoformat(b.decode()))

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Crea las tablas, carga los datos iniciales y cifra las contraseñas."""
    db = sqlite3.connect(DATABASE)
    with open(SCHEMA, encoding='utf-8') as f:
        db.executescript(f.read())
    # Las cuentas iniciales del esquema reciben contraseñas nuevas: las del archivo SQL son públicas.
    # La del admin se puede fijar con la variable ADMIN_PASSWORD; si no, se genera una aleatoria.
    for user_id, username, is_admin in db.execute('SELECT id, username, is_admin FROM users').fetchall():
        password = os.environ.get('ADMIN_PASSWORD') if is_admin else None
        if not password:
            password = secrets.token_urlsafe(9)
            print(f'Contraseña inicial de "{username}": {password}')
        db.execute('UPDATE users SET password = ? WHERE id = ?', (generate_password_hash(password), user_id))
    db.commit()
    db.close()

def actualizar_esquema(db):
    """Crea las tablas e índices nuevos si la base de datos es anterior a ellos."""
    with open(MIGRACIONES, encoding='utf-8') as f:
        db.executescript(f.read())

@app.cli.command('init-db')
def init_db_command():
    """Uso: flask --app app init-db"""
    init_db()
    print('Base de datos creada en', DATABASE)

# Protección CSRF: cada formulario POST debe enviar el token de la sesión
def csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = csrf_token

@app.before_request
def verificar_csrf():
    if request.method == 'POST':
        token = request.form.get('csrf_token', '')
        if not secrets.compare_digest(token, session.get('_csrf_token', '')):
            flash('La sesión expiró, vuelve a intentarlo.')
            return redirect(request.referrer or url_for('index'))

# Filtros para mostrar precios y fechas
@app.template_filter('precio')
def formato_precio(valor):
    if valor is None:
        return '$0'
    return '$' + f'{int(round(float(valor))):,}'.replace(',', '.')

@app.template_filter('fecha')
def formato_fecha(valor):
    if isinstance(valor, datetime):
        return valor.strftime('%d/%m/%Y')
    return valor or ''

def es_admin():
    return 'loggedin' in session and bool(session.get('is_admin'))

if not os.path.exists(DATABASE):
    init_db()
with sqlite3.connect(DATABASE) as _db:
    actualizar_esquema(_db)

# ---------- Consultas compartidas ----------
def mas_vendidos(limite=8):
    return get_db().execute('''
        SELECT ca.*, COUNT(c.id) AS ventas
        FROM compras c JOIN catalogo ca ON ca.id = c.libro_id
        GROUP BY ca.id
        ORDER BY ventas DESC, ca.titulo
        LIMIT ?
    ''', (limite,)).fetchall()

def valoraciones(libro_ids):
    """Devuelve {libro_id: (promedio, cantidad)} para los libros indicados."""
    if not libro_ids:
        return {}
    marcas = ','.join('?' * len(libro_ids))
    filas = get_db().execute(f'''
        SELECT libro_id, AVG(calificacion), COUNT(*) FROM resenas
        WHERE libro_id IN ({marcas}) GROUP BY libro_id
    ''', list(libro_ids)).fetchall()
    return {f[0]: (round(f[1], 1), f[2]) for f in filas}

def favoritos_de_usuario():
    if 'loggedin' not in session:
        return set()
    filas = get_db().execute('SELECT libro_id FROM favoritos WHERE user_id = ?', (session['id'],)).fetchall()
    return {f[0] for f in filas}

def paginacion(total, por_pagina, pagina):
    total_paginas = max(1, -(-total // por_pagina))
    pagina = min(max(1, pagina), total_paginas)
    return pagina, total_paginas, (pagina - 1) * por_pagina

@app.template_global()
def paginas_visibles(actual, total, alrededor=2):
    """Números de página a mostrar, con None donde va '…' (para catálogos grandes)."""
    paginas = []
    for p in range(1, total + 1):
        if p in (1, total) or abs(p - actual) <= alrededor:
            paginas.append(p)
        elif paginas[-1] is not None:
            paginas.append(None)
    return paginas

@app.route('/')
def index():
    vendidos = mas_vendidos(6)
    return render_template('index.html', vendidos=vendidos)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if 'loggedin' in session:
        return redirect(url_for('index'))  # Asegúrate de redirigir con page_num

    if request.method == 'POST' and 'new-username' in request.form and 'email' in request.form and 'new-password' in request.form:
        username = request.form['new-username']
        email = request.form['email']
        password = request.form['new-password']

        cursor = get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        cuenta = cursor.fetchone()

        if cuenta:
            flash('¡El usuario ya existe!')
        elif not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
            flash('Correo electrónico inválido')
        elif not re.fullmatch(r'[A-Za-z0-9]{3,30}', username):
            flash('El nombre de usuario debe tener entre 3 y 30 caracteres alfanuméricos')
        elif len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres')
        else:
            cursor.execute('INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, ?)', (username, email, generate_password_hash(password), False))
            get_db().commit()
            flash('¡Te has registrado exitosamente!')
            return redirect(url_for('login'))
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'loggedin' in session:
        return redirect(url_for('index'))  # Asegúrate de redirigir con page_num

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        ip = request.remote_addr
        fallos, desde = intentos_fallidos.get(ip, (0, datetime.now()))
        if datetime.now() - desde > BLOQUEO:
            fallos = 0
        if fallos >= MAX_INTENTOS:
            minutos = int((BLOQUEO - (datetime.now() - desde)).total_seconds() // 60) + 1
            flash(f'Demasiados intentos fallidos. Inténtalo de nuevo en {minutos} minutos.')
            return render_template('registro.html')

        cursor = get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        cuenta = cursor.fetchone()

        if cuenta:
            if check_password_hash(cuenta[3], password):
                intentos_fallidos.pop(ip, None)
                session.clear()
                session['loggedin'] = True
                session['id'] = cuenta[0]
                session['username'] = cuenta[1]
                session['is_admin'] = cuenta[4]  # Guardar si es admin
                flash('¡Inicio de sesión exitoso!')
                return redirect(url_for('catalogo', page_num=1))  # Asegúrate de redirigir con page_num
        if not cuenta or not check_password_hash(cuenta[3], password):
            intentos_fallidos[ip] = (fallos + 1, desde if fallos else datetime.now())
            restantes = MAX_INTENTOS - fallos - 1
            if restantes > 0:
                flash(f'Usuario o contraseña incorrectos. Te quedan {restantes} intentos.')
            else:
                flash('Demasiados intentos fallidos. Inténtalo de nuevo en 15 minutos.')

    return render_template('registro.html')

LIBROS_POR_PAGINA = 12

ORDENES = {
    'titulo': ('Título (A-Z)', 'ca.titulo COLLATE NOCASE'),
    'vendidos': ('Más vendidos', 'ventas DESC, ca.titulo COLLATE NOCASE'),
    'valorados': ('Mejor valorados', 'promedio DESC, ca.titulo COLLATE NOCASE'),
    'recientes': ('Recién añadidos', 'ca.id DESC'),
    'precio_asc': ('Precio: menor a mayor', 'ca.precio, ca.titulo COLLATE NOCASE'),
    'precio_desc': ('Precio: mayor a menor', 'ca.precio DESC, ca.titulo COLLATE NOCASE'),
}

@app.route('/catalogo')
@app.route('/catalogo/<int:page_num>')
def catalogo(page_num=1):
    db = get_db()
    q = request.args.get('q', '').strip()[:100]
    genero = request.args.get('genero', '').strip()
    orden = request.args.get('orden', 'titulo')
    if orden not in ORDENES:
        orden = 'titulo'

    condiciones, params = [], []
    if q:
        condiciones.append('(ca.titulo LIKE ? OR ca.autor LIKE ?)')
        params += [f'%{q}%', f'%{q}%']
    if genero:
        condiciones.append('ca.genero = ?')
        params.append(genero)
    where = ('WHERE ' + ' AND '.join(condiciones)) if condiciones else ''

    total_libros = db.execute(f'SELECT COUNT(*) FROM catalogo ca {where}', params).fetchone()[0]
    page_num, total_paginas, offset = paginacion(total_libros, LIBROS_POR_PAGINA, page_num)

    libros = db.execute(f'''
        SELECT ca.*,
               (SELECT COUNT(*) FROM compras c WHERE c.libro_id = ca.id) AS ventas,
               (SELECT AVG(calificacion) FROM resenas r WHERE r.libro_id = ca.id) AS promedio
        FROM catalogo ca {where}
        ORDER BY {ORDENES[orden][1]}
        LIMIT ? OFFSET ?
    ''', params + [LIBROS_POR_PAGINA, offset]).fetchall()

    generos = [f[0] for f in db.execute(
        "SELECT DISTINCT genero FROM catalogo WHERE genero IS NOT NULL AND genero != '' ORDER BY genero").fetchall()]
    filtrando = bool(q or genero)
    vendidos = mas_vendidos(8) if page_num == 1 and not filtrando else []

    return render_template('catalogo.html', libros=libros, total_paginas=total_paginas, page_num=page_num,
                           total_libros=total_libros, q=q, genero=genero, orden=orden, ordenes=ORDENES,
                           generos=generos, filtrando=filtrando, vendidos=vendidos,
                           valoraciones=valoraciones([l['id'] for l in libros]),
                           favoritos=favoritos_de_usuario())

@app.route('/libro/<int:libro_id>')
def libro(libro_id):
    db = get_db()
    libro = db.execute('SELECT * FROM catalogo WHERE id = ?', (libro_id,)).fetchone()
    if not libro:
        flash('Ese libro no existe.')
        return redirect(url_for('catalogo'))
    ventas = db.execute('SELECT COUNT(*) FROM compras WHERE libro_id = ?', (libro_id,)).fetchone()[0]
    resenas = db.execute('''
        SELECT r.*, u.username FROM resenas r JOIN users u ON u.id = r.user_id
        WHERE r.libro_id = ? ORDER BY r.fecha DESC
    ''', (libro_id,)).fetchall()
    mi_resena = None
    ya_comprado = False
    if 'loggedin' in session:
        mi_resena = next((r for r in resenas if r['user_id'] == session['id']), None)
        ya_comprado = db.execute('SELECT 1 FROM compras WHERE user_id = ? AND libro_id = ?',
                                 (session['id'], libro_id)).fetchone() is not None
    del_autor = db.execute('SELECT * FROM catalogo WHERE autor = ? AND id != ? ORDER BY titulo LIMIT 6',
                           (libro['autor'], libro_id)).fetchall()
    return render_template('libro.html', libro=libro, ventas=ventas, resenas=resenas, mi_resena=mi_resena,
                           ya_comprado=ya_comprado, del_autor=del_autor,
                           valoracion=valoraciones([libro_id]).get(libro_id),
                           es_favorito=libro_id in favoritos_de_usuario())

@app.route('/favorito/<int:libro_id>', methods=['POST'])
def favorito(libro_id):
    if 'loggedin' not in session:
        flash('Inicia sesión para guardar libros en tu lista de deseos.')
        return redirect(url_for('login'))
    db = get_db()
    if not db.execute('SELECT 1 FROM catalogo WHERE id = ?', (libro_id,)).fetchone():
        return redirect(url_for('catalogo'))
    if db.execute('SELECT 1 FROM favoritos WHERE user_id = ? AND libro_id = ?', (session['id'], libro_id)).fetchone():
        db.execute('DELETE FROM favoritos WHERE user_id = ? AND libro_id = ?', (session['id'], libro_id))
        flash('Quitado de tu lista de deseos.')
    else:
        db.execute('INSERT INTO favoritos (user_id, libro_id) VALUES (?, ?)', (session['id'], libro_id))
        flash('Guardado en tu lista de deseos.')
    db.commit()
    return redirect(request.referrer or url_for('libro', libro_id=libro_id))

@app.route('/resena/<int:libro_id>', methods=['POST'])
def resena(libro_id):
    if 'loggedin' not in session:
        flash('Inicia sesión para escribir una reseña.')
        return redirect(url_for('login'))
    db = get_db()
    if not db.execute('SELECT 1 FROM catalogo WHERE id = ?', (libro_id,)).fetchone():
        return redirect(url_for('catalogo'))
    try:
        calificacion = int(request.form.get('calificacion', 0))
    except ValueError:
        calificacion = 0
    comentario = request.form.get('comentario', '').strip()[:1000]
    if not 1 <= calificacion <= 5:
        flash('Elige una calificación de 1 a 5 estrellas.')
    else:
        db.execute('''
            INSERT INTO resenas (user_id, libro_id, calificacion, comentario, fecha) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (user_id, libro_id) DO UPDATE SET
                calificacion = excluded.calificacion, comentario = excluded.comentario, fecha = excluded.fecha
        ''', (session['id'], libro_id, calificacion, comentario, datetime.now()))
        db.commit()
        flash('¡Gracias por tu reseña!')
    return redirect(url_for('libro', libro_id=libro_id) + '#resenas')

@app.route('/eliminar_resena/<int:resena_id>', methods=['POST'])
def eliminar_resena(resena_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    db = get_db()
    fila = db.execute('SELECT user_id, libro_id FROM resenas WHERE id = ?', (resena_id,)).fetchone()
    if fila and (fila['user_id'] == session['id'] or es_admin()):
        db.execute('DELETE FROM resenas WHERE id = ?', (resena_id,))
        db.commit()
        flash('Reseña eliminada.')
        return redirect(url_for('libro', libro_id=fila['libro_id']) + '#resenas')
    flash('No puedes eliminar esa reseña.')
    return redirect(url_for('catalogo'))

@app.route('/agregar_carrito/<int:libro_id>', methods=['POST'])
def agregar_carrito(libro_id):
    if 'loggedin' in session:
        user_id = session['id']
        cursor = get_db().cursor()
        
        # Verificar si el libro existe en el catálogo
        cursor.execute('SELECT id FROM catalogo WHERE id = ?', (libro_id,))
        libro_existente = cursor.fetchone()

        if not libro_existente:
            flash('Este libro no está disponible en el catálogo.')
        else:
            # Verificar si el libro ya está en el carrito
            cursor.execute('SELECT * FROM carrito WHERE user_id = ? AND libro_id = ?', (user_id, libro_id))
            libro_en_carrito = cursor.fetchone()

            if libro_en_carrito:
                flash('Este libro ya está en tu carrito.')
            else:
                flash('Libro agregado al carrito!')
                # Insertar el libro al carrito usando la id de catalogo directamente
                cursor.execute('''
                    INSERT INTO carrito (user_id, libro_id, precio) 
                    VALUES (?, ?, (SELECT precio FROM catalogo WHERE id = ?))
                ''', (user_id, libro_id, libro_id))

            get_db().commit()
            
        return redirect(request.referrer or url_for('catalogo'))
    else:
        flash('Debes iniciar sesión para agregar libros al carrito.')
        return redirect(url_for('registro'))


# Ruta para ver el carrito
@app.route('/carrito')
def ver_carrito():
    if 'loggedin' in session:
        user_id = session['id']
        cursor = get_db().cursor()
        
        # Obtener los libros en el carrito
        cursor.execute('SELECT c.id, ca.titulo, ca.autor, c.precio FROM carrito c JOIN catalogo ca ON c.libro_id = ca.id WHERE c.user_id = ?', (user_id,))
        libros_carrito = cursor.fetchall()
        
        # Calcular el precio total de los libros en el carrito
        cursor.execute('SELECT SUM(precio) FROM carrito WHERE user_id = ?', (user_id,))
        total_precio = cursor.fetchone()[0] or 0  # Si el carrito está vacío, el total será 0
        
        return render_template('carrito.html', libros=libros_carrito, total_precio=total_precio)
    else:
        flash('Debes iniciar sesión para ver el carrito.')
        return redirect(url_for('registro'))

# Ruta para eliminar un libro del carrito
@app.route('/eliminar_carrito/<int:carrito_id>', methods=['POST'])
def eliminar_carrito(carrito_id):
    if 'loggedin' in session:
        user_id = session['id']
        cursor = get_db().cursor()
        
        # Eliminar el libro del carrito usando la ID del carrito
        cursor.execute('DELETE FROM carrito WHERE user_id = ? AND id = ?', (user_id, carrito_id))
        get_db().commit()
        
        flash('Libro eliminado del carrito.')
        return redirect(url_for('ver_carrito'))
    else:
        flash('Debes iniciar sesión para eliminar libros del carrito.')
        return redirect(url_for('registro'))

# Ruta para finalizar la compra (muestra la página de revisión antes de finalizar)
@app.route('/finalizar_compra', methods=['GET', 'POST'])
def finalizar_compra():
    if 'loggedin' in session:
        user_id = session['id']
        cursor = get_db().cursor()

        if request.method == 'POST':
            # Obtener todos los libros del carrito del usuario
            cursor.execute('SELECT libro_id, precio FROM carrito WHERE user_id = ?', (user_id,))
            libros_carrito = cursor.fetchall()

            if libros_carrito:
                # Registrar cada compra en la tabla compras
                for libro in libros_carrito:
                    libro_id, precio = libro
                    fecha_compra = datetime.now()

                    # Insertar la compra en la tabla compras
                    cursor.execute('''
                        INSERT INTO compras (user_id, libro_id, fecha_compra) 
                        VALUES (?, ?, ?)
                    ''', (user_id, libro_id, fecha_compra))
                
                # Limpiar el carrito después de la compra
                cursor.execute('DELETE FROM carrito WHERE user_id = ?', (user_id,))
                get_db().commit()

                flash('¡Compra realizada con éxito!')
            else:
                flash('Tu carrito está vacío.')

            return redirect(url_for('gracias'))  # Redirigir a una página de confirmación de compra

        # Si el método es GET, obtener los libros del carrito para mostrar al usuario
        cursor.execute('SELECT c.id, ca.titulo, ca.autor, c.precio FROM carrito c JOIN catalogo ca ON c.libro_id = ca.id WHERE c.user_id = ?', (user_id,))
        libros_carrito = cursor.fetchall()
        
        # Calcular el precio total de los libros en el carrito
        cursor.execute('SELECT SUM(precio) FROM carrito WHERE user_id = ?', (user_id,))
        total_precio = cursor.fetchone()[0] or 0  # Si el carrito está vacío, el total será 0
        
        return render_template('finalizar_compra.html', libros=libros_carrito, total_precio=total_precio)
    
    else:
        flash('Debes iniciar sesión para finalizar la compra.')
        return redirect(url_for('login'))

@app.route('/gracias')
def gracias():
    return render_template('gracias.html')

@app.route('/usuario')
def usuario():
    if 'loggedin' in session:
        cursor = get_db().cursor()
        
        # Obtener los detalles del usuario (username y email)
        cursor.execute('SELECT username, email FROM users WHERE id = ?', (session['id'],))
        usuario = cursor.fetchone()

        # Obtener los libros comprados por el usuario
        cursor.execute('''
            SELECT ca.titulo, ca.autor, ca.precio, c.fecha_compra 
            FROM compras c 
            JOIN catalogo ca ON c.libro_id = ca.id 
            WHERE c.user_id = ?
            ORDER BY c.fecha_compra DESC
        ''', (session['id'],))
        libros_comprados = cursor.fetchall()

        favoritos = get_db().execute('''
            SELECT ca.* FROM favoritos f JOIN catalogo ca ON ca.id = f.libro_id
            WHERE f.user_id = ? ORDER BY f.fecha DESC
        ''', (session['id'],)).fetchall()

        return render_template('usuario.html', 
                               username=usuario[0], 
                               email=usuario[1], 
                               libros_comprados=libros_comprados,
                               favoritos=favoritos)
    return redirect(url_for('registro'))

@app.route('/editar_perfil', methods=['POST'])
def editar_perfil():
    if 'loggedin' in session:
        nuevo_username = request.form.get('username')
        nuevo_email = request.form.get('email')

        if not nuevo_username or not re.fullmatch(r'[A-Za-z0-9]{3,30}', nuevo_username):
            flash('El nombre de usuario debe tener entre 3 y 30 caracteres alfanuméricos')
            return redirect(url_for('usuario'))
        if not nuevo_email or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', nuevo_email):
            flash('Correo electrónico inválido')
            return redirect(url_for('usuario'))

        cursor = get_db().cursor()

        # Verificar que el nuevo nombre de usuario o correo no estén en uso
        cursor.execute('SELECT * FROM users WHERE (username = ? OR email = ?) AND id != ?', 
                       (nuevo_username, nuevo_email, session['id']))
        usuario_existente = cursor.fetchone()
        
        if usuario_existente:
            flash('El nombre de usuario o correo electrónico ya están en uso por otro usuario.')
            return redirect(url_for('usuario'))
        
        # Actualizar el perfil del usuario en la base de datos
        cursor.execute('UPDATE users SET username = ?, email = ? WHERE id = ?', 
                       (nuevo_username, nuevo_email, session['id']))
        get_db().commit()
        
        # Actualizar la sesión con el nuevo nombre de usuario
        session['username'] = nuevo_username
        flash('Perfil actualizado exitosamente.')
        return redirect(url_for('usuario'))
    return redirect(url_for('registro'))

@app.route('/confirmar_logout', methods=['POST'])
def confirmar_logout():
    if 'loggedin' in session:
        session.clear()
        flash('¡Sesión cerrada!')
    return redirect(url_for('index'))

@app.route('/agregar_libro', methods=['GET', 'POST'])
def agregar_libro():
    if 'loggedin' in session and session.get('is_admin'):
        if request.method == 'POST' and 'titulo' in request.form and 'autor' in request.form and 'genero' in request.form and 'año_publicacion' in request.form and 'descripcion' in request.form and 'precio' in request.form:
            titulo = request.form['titulo']
            autor = request.form['autor']
            genero = request.form['genero']
            anio = request.form['año_publicacion']
            descripcion = request.form['descripcion']
            precio = request.form['precio']

            cursor = get_db().cursor()
            cursor.execute('INSERT INTO catalogo (titulo, autor, genero, año_publicacion, descripcion, precio) VALUES (?, ?, ?, ?, ?, ?)', (titulo, autor, genero, anio, descripcion, precio))
            get_db().commit()
            flash('¡Libro añadido exitosamente!')
            return redirect(url_for('admin'))
        
        return render_template('agregar_libro.html')
    else:
        flash('No tienes permiso para acceder a esta página.')
        return redirect(url_for('registro'))

@app.route('/editar_libro/<int:libro_id>', methods=['GET', 'POST'])
def editar_libro(libro_id):
    if 'loggedin' in session and session.get('is_admin'):
        cursor = get_db().cursor()

        if request.method == 'POST':
            titulo = request.form['titulo']
            autor = request.form['autor']
            genero = request.form['genero']
            año_publicacion = request.form['año_publicacion']
            descripcion = request.form['descripcion']
            precio = request.form['precio']

            cursor.execute('''
                UPDATE catalogo 
                SET titulo = ?, autor = ?, genero = ?, año_publicacion = ?, descripcion = ?, precio = ? 
                WHERE id = ?
            ''', (titulo, autor, genero, año_publicacion, descripcion, precio, libro_id))
            get_db().commit()
            flash('¡Libro actualizado exitosamente!')
            return redirect(url_for('admin'))

        cursor.execute('SELECT * FROM catalogo WHERE id = ?', (libro_id,))
        libro = cursor.fetchone()
        return render_template('editar_libro.html', libro=libro)
    else:
        flash('No tienes permiso para acceder a esta página.')
        return redirect(url_for('registro'))

@app.route('/eliminar_libro/<int:libro_id>', methods=['POST'])
def eliminar_libro(libro_id):
    if 'loggedin' in session and session.get('is_admin'):
        cursor = get_db().cursor()
        cursor.execute('DELETE FROM catalogo WHERE id = ?', (libro_id,))
        get_db().commit()
        flash('¡Libro eliminado exitosamente!')
        return redirect(url_for('admin'))
    else:
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('registro'))

ADMIN_POR_PAGINA = 25

@app.route('/admin')
def admin():
    if not es_admin():
        flash('No tienes permiso para acceder a esta página.')
        return redirect(url_for('registro'))
    db = get_db()
    tab = request.args.get('tab', 'libros')
    q = request.args.get('q', '').strip()[:100]
    try:
        pagina = int(request.args.get('pagina', 1))
    except ValueError:
        pagina = 1
    like = f'%{q}%'

    resumen = {
        'libros': db.execute('SELECT COUNT(*) FROM catalogo').fetchone()[0],
        'usuarios': db.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'compras': db.execute('SELECT COUNT(*) FROM compras').fetchone()[0],
        'ingresos': db.execute('SELECT COALESCE(SUM(ca.precio), 0) FROM compras c JOIN catalogo ca ON ca.id = c.libro_id').fetchone()[0],
    }
    filas, total = [], 0
    if tab == 'usuarios':
        filtro = 'WHERE username LIKE ? OR email LIKE ?'
        total = db.execute(f'SELECT COUNT(*) FROM users {filtro}', (like, like)).fetchone()[0]
        pagina, total_paginas, offset = paginacion(total, ADMIN_POR_PAGINA, pagina)
        filas = db.execute(f'''
            SELECT u.*, (SELECT COUNT(*) FROM compras c WHERE c.user_id = u.id) AS compras
            FROM users u {filtro} ORDER BY username COLLATE NOCASE LIMIT ? OFFSET ?
        ''', (like, like, ADMIN_POR_PAGINA, offset)).fetchall()
    elif tab == 'ventas':
        filas = mas_vendidos(25)
        total_paginas = 1
    else:
        tab = 'libros'
        filtro = 'WHERE titulo LIKE ? OR autor LIKE ? OR genero LIKE ?'
        total = db.execute(f'SELECT COUNT(*) FROM catalogo {filtro}', (like, like, like)).fetchone()[0]
        pagina, total_paginas, offset = paginacion(total, ADMIN_POR_PAGINA, pagina)
        filas = db.execute(f'''
            SELECT ca.*, (SELECT COUNT(*) FROM compras c WHERE c.libro_id = ca.id) AS ventas
            FROM catalogo ca {filtro} ORDER BY titulo COLLATE NOCASE LIMIT ? OFFSET ?
        ''', (like, like, like, ADMIN_POR_PAGINA, offset)).fetchall()

    return render_template('admin.html', tab=tab, q=q, filas=filas, total=total, pagina=pagina,
                           total_paginas=total_paginas, resumen=resumen)

@app.route('/ver_usuarios')
def ver_usuarios():
    return redirect(url_for('admin', tab='usuarios'))

@app.route('/editar_usuario/<int:user_id>', methods=['GET', 'POST'])
def editar_usuario(user_id):
    if 'loggedin' in session and session.get('is_admin'):
        cursor = get_db().cursor()
        
        # Al hacer clic en el botón "Actualizar" en la página de edición
        if request.method == 'POST' and 'username' in request.form and 'email' in request.form:
            new_username = request.form['username']
            new_email = request.form['email']
            is_admin = bool(request.form.get('is_admin'))

            cursor.execute("""
                UPDATE users SET username = ?, email = ?, is_admin = ? WHERE id = ?
            """, (new_username, new_email, is_admin, user_id))
            get_db().commit()
            flash('¡Usuario actualizado exitosamente!')
            return redirect(url_for('admin', tab='usuarios'))

        # Consulta de datos del usuario actual para mostrar en el formulario de edición
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        usuario = cursor.fetchone()
        return render_template('editar_usuario.html', usuario=usuario)
    else:
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('registro'))

@app.route('/eliminar_usuario/<int:user_id>', methods=['POST'])
def eliminar_usuario(user_id):
    if 'loggedin' in session and session.get('is_admin'):
        if user_id == session['id']:
            flash('No puedes eliminar tu propia cuenta.')
            return redirect(url_for('admin', tab='usuarios'))
        cursor = get_db().cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        get_db().commit()
        flash('¡Usuario eliminado exitosamente!')
        return redirect(url_for('admin', tab='usuarios'))
    else:
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('registro'))

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
