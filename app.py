from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import pymysql
pymysql.install_as_MySQLdb()
from flask_mysqldb import MySQL
import re

app = Flask(__name__)

# Clave secreta para manejar sesiones
app.secret_key = 'tu_clave_secreta'

# Configuración de la base de datos MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'libreria'

# Inicializar MySQL
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if 'loggedin' in session:
        return redirect(url_for('index'))  # Asegúrate de redirigir con page_num

    if request.method == 'POST' and 'new-username' in request.form and 'email' in request.form and 'new-password' in request.form:
        username = request.form['new-username']
        email = request.form['email']
        password = request.form['new-password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        cuenta = cursor.fetchone()

        if cuenta:
            flash('¡El usuario ya existe!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Correo electrónico inválido')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('El nombre de usuario debe contener solo caracteres alfanuméricos')
        else:
            cursor.execute('INSERT INTO users (username, email, password, is_admin) VALUES (%s, %s, %s, %s)', (username, email, password, False))
            mysql.connection.commit()
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

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        cuenta = cursor.fetchone()

        if cuenta:
            if cuenta[3] == password:
                session['loggedin'] = True
                session['id'] = cuenta[0]
                session['username'] = cuenta[1]
                session['is_admin'] = cuenta[4]  # Guardar si es admin
                flash('¡Inicio de sesión exitoso!')
                return redirect(url_for('catalogo', page_num=1))  # Asegúrate de redirigir con page_num
            else:
                flash('¡Contraseña incorrecta!')
        else:
            flash('¡Usuario no encontrado!')

    return render_template('registro.html')

@app.route('/catalogo')
@app.route('/catalogo/<int:page_num>')
def catalogo(page_num=1):
    if 'loggedin' in session:
        cursor = mysql.connection.cursor()
        offset = (page_num - 1) * 10
        cursor.execute('SELECT * FROM catalogo LIMIT 10 OFFSET %s', (offset,))
        libros = cursor.fetchall()

        cursor.execute('SELECT COUNT(*) FROM catalogo')
        total_libros = cursor.fetchone()[0]
        total_paginas = (total_libros + 9) // 10

        return render_template('catalogo.html', username=session['username'], libros=libros, total_paginas=total_paginas, page_num=page_num)
    else:
        flash('Debes iniciar sesión para ver el catálogo.')
        return redirect(url_for('registro'))

@app.route('/agregar_carrito/<int:libro_id>', methods=['POST'])
def agregar_carrito(libro_id):
    if 'loggedin' in session:
        user_id = session['id']
        cursor = mysql.connection.cursor()
        
        # Verificar si el libro existe en el catálogo
        cursor.execute('SELECT id FROM catalogo WHERE id = %s', (libro_id,))
        libro_existente = cursor.fetchone()

        if not libro_existente:
            flash('Este libro no está disponible en el catálogo.')
        else:
            # Verificar si el libro ya está en el carrito
            cursor.execute('SELECT * FROM carrito WHERE user_id = %s AND libro_id = %s', (user_id, libro_id))
            libro_en_carrito = cursor.fetchone()

            if libro_en_carrito:
                flash('Este libro ya está en tu carrito.')
            else:
                flash('Libro agregado al carrito!')
                # Insertar el libro al carrito usando la id de catalogo directamente
                cursor.execute('''
                    INSERT INTO carrito (user_id, libro_id, precio) 
                    VALUES (%s, %s, (SELECT precio FROM catalogo WHERE id = %s))
                ''', (user_id, libro_id, libro_id))

            mysql.connection.commit()
            
        return redirect(url_for('catalogo'))
    else:
        flash('Debes iniciar sesión para agregar libros al carrito.')
        return redirect(url_for('registro'))


# Ruta para ver el carrito
@app.route('/carrito')
def ver_carrito():
    if 'loggedin' in session:
        user_id = session['id']
        cursor = mysql.connection.cursor()
        
        # Obtener los libros en el carrito
        cursor.execute('SELECT c.id, ca.titulo, ca.autor, c.precio FROM carrito c JOIN catalogo ca ON c.libro_id = ca.id WHERE c.user_id = %s', (user_id,))
        libros_carrito = cursor.fetchall()
        
        # Calcular el precio total de los libros en el carrito
        cursor.execute('SELECT SUM(precio) FROM carrito WHERE user_id = %s', (user_id,))
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
        cursor = mysql.connection.cursor()
        
        # Eliminar el libro del carrito usando la ID del carrito
        cursor.execute('DELETE FROM carrito WHERE user_id = %s AND id = %s', (user_id, carrito_id))
        mysql.connection.commit()
        
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
        cursor = mysql.connection.cursor()

        if request.method == 'POST':
            # Obtener todos los libros del carrito del usuario
            cursor.execute('SELECT libro_id, precio FROM carrito WHERE user_id = %s', (user_id,))
            libros_carrito = cursor.fetchall()

            if libros_carrito:
                # Registrar cada compra en la tabla compras
                for libro in libros_carrito:
                    libro_id, precio = libro
                    fecha_compra = datetime.now()

                    # Insertar la compra en la tabla compras
                    cursor.execute('''
                        INSERT INTO compras (user_id, libro_id, fecha_compra) 
                        VALUES (%s, %s, %s)
                    ''', (user_id, libro_id, fecha_compra))
                
                # Limpiar el carrito después de la compra
                cursor.execute('DELETE FROM carrito WHERE user_id = %s', (user_id,))
                mysql.connection.commit()

                flash('¡Compra realizada con éxito!')
            else:
                flash('Tu carrito está vacío.')

            return redirect(url_for('gracias'))  # Redirigir a una página de confirmación de compra

        # Si el método es GET, obtener los libros del carrito para mostrar al usuario
        cursor.execute('SELECT c.id, ca.titulo, ca.autor, c.precio FROM carrito c JOIN catalogo ca ON c.libro_id = ca.id WHERE c.user_id = %s', (user_id,))
        libros_carrito = cursor.fetchall()
        
        # Calcular el precio total de los libros en el carrito
        cursor.execute('SELECT SUM(precio) FROM carrito WHERE user_id = %s', (user_id,))
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
        cursor = mysql.connection.cursor()
        
        # Obtener los detalles del usuario (username y email)
        cursor.execute('SELECT username, email FROM users WHERE id = %s', (session['id'],))
        usuario = cursor.fetchone()

        # Obtener los libros comprados por el usuario
        cursor.execute('''
            SELECT ca.titulo, ca.autor, ca.precio, c.fecha_compra 
            FROM compras c 
            JOIN catalogo ca ON c.libro_id = ca.id 
            WHERE c.user_id = %s
        ''', (session['id'],))
        libros_comprados = cursor.fetchall()

        return render_template('usuario.html', 
                               username=usuario[0], 
                               email=usuario[1], 
                               libros_comprados=libros_comprados)
    return redirect(url_for('registro'))

@app.route('/editar_perfil', methods=['POST'])
def editar_perfil():
    if 'loggedin' in session:
        nuevo_username = request.form.get('username')
        nuevo_email = request.form.get('email')

        cursor = mysql.connection.cursor()
        
        # Verificar que el nuevo nombre de usuario o correo no estén en uso
        cursor.execute('SELECT * FROM users WHERE (username = %s OR email = %s) AND id != %s', 
                       (nuevo_username, nuevo_email, session['id']))
        usuario_existente = cursor.fetchone()
        
        if usuario_existente:
            flash('El nombre de usuario o correo electrónico ya están en uso por otro usuario.')
            return redirect(url_for('usuario'))
        
        # Actualizar el perfil del usuario en la base de datos
        cursor.execute('UPDATE users SET username = %s, email = %s WHERE id = %s', 
                       (nuevo_username, nuevo_email, session['id']))
        mysql.connection.commit()
        
        # Actualizar la sesión con el nuevo nombre de usuario
        session['username'] = nuevo_username
        flash('Perfil actualizado exitosamente.')
        return redirect(url_for('usuario'))
    return redirect(url_for('registro'))

@app.route('/confirmar_logout', methods=['POST'])
def confirmar_logout():
    if 'loggedin' in session:
        session.pop('loggedin', None)
        session.pop('id', None)
        session.pop('username', None)
        session.pop('is_admin', None)
        flash('¡Sesión cerrada!')
    return redirect(url_for('index'))

@app.route('/agregar_libro', methods=['GET', 'POST'])
def agregar_libro():
    if 'loggedin' in session and session['is_admin']:
        if request.method == 'POST' and 'titulo' in request.form and 'autor' in request.form and 'genero' in request.form and 'año_publicacion' in request.form and 'descripcion' in request.form and 'precio' in request.form:
            titulo = request.form['titulo']
            autor = request.form['autor']
            genero = request.form['genero']
            anio = request.form['año_publicacion']
            descripcion = request.form['descripcion']
            precio = request.form['precio']

            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO catalogo (titulo, autor, genero, año_publicacion, descripcion, precio) VALUES (%s, %s, %s, %s, %s, %s)', (titulo, autor, genero, anio, descripcion, precio))
            mysql.connection.commit()
            flash('¡Libro añadido exitosamente!')
            return redirect(url_for('catalogo', page_num=1))  # Asegúrate de redirigir con page_num
        
        return render_template('agregar_libro.html')
    else:
        flash('No tienes permiso para acceder a esta página.')
        return redirect(url_for('registro'))

@app.route('/editar_libro/<int:libro_id>', methods=['GET', 'POST'])
def editar_libro(libro_id):
    if 'loggedin' in session and session.get('is_admin'):
        cursor = mysql.connection.cursor()

        if request.method == 'POST':
            titulo = request.form['titulo']
            autor = request.form['autor']
            genero = request.form['genero']
            año_publicacion = request.form['año_publicacion']
            descripcion = request.form['descripcion']

            cursor.execute('''
                UPDATE catalogo 
                SET titulo = %s, autor = %s, genero = %s, año_publicacion = %s, descripcion = %s 
                WHERE id = %s
            ''', (titulo, autor, genero, año_publicacion, descripcion, libro_id))
            mysql.connection.commit()
            flash('¡Libro actualizado exitosamente!')
            return redirect(url_for('catalogo'))

        cursor.execute('SELECT * FROM catalogo WHERE id = %s', (libro_id,))
        libro = cursor.fetchone()
        return render_template('editar_libro.html', libro=libro)
    else:
        flash('No tienes permiso para acceder a esta página.')
        return redirect(url_for('registro'))

@app.route('/eliminar_libro/<int:libro_id>', methods=['POST'])
def eliminar_libro(libro_id):
    if 'loggedin' in session and session.get('is_admin'):
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM catalogo WHERE id = %s', (libro_id,))
        mysql.connection.commit()
        flash('¡Libro eliminado exitosamente!')
        return redirect(url_for('catalogo'))
    else:
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('registro'))

@app.route('/ver_usuarios')
def ver_usuarios():
    if 'loggedin' in session and session['is_admin']:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users')
        usuarios = cursor.fetchall()
        return render_template('ver_usuarios.html', usuarios=usuarios)
    else:
        flash('No tienes permiso para acceder a esta página.')
        return redirect(url_for('registro'))

@app.route('/editar_usuario/<int:user_id>', methods=['GET', 'POST'])
def editar_usuario(user_id):
    if 'loggedin' in session and session.get('is_admin'):
        cursor = mysql.connection.cursor()
        
        # Al hacer clic en el botón "Actualizar" en la página de edición
        if request.method == 'POST' and 'username' in request.form and 'email' in request.form:
            new_username = request.form['username']
            new_email = request.form['email']
            is_admin = bool(request.form.get('is_admin'))

            cursor.execute("""
                UPDATE users SET username = %s, email = %s, is_admin = %s WHERE id = %s
            """, (new_username, new_email, is_admin, user_id))
            mysql.connection.commit()
            flash('¡Usuario actualizado exitosamente!')
            return redirect(url_for('ver_usuarios'))

        # Consulta de datos del usuario actual para mostrar en el formulario de edición
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        usuario = cursor.fetchone()
        return render_template('editar_usuario.html', usuario=usuario)
    else:
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('registro'))

@app.route('/eliminar_usuario/<int:user_id>', methods=['POST'])
def eliminar_usuario(user_id):
    if 'loggedin' in session and session.get('is_admin'):
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.connection.commit()
        flash('¡Usuario eliminado exitosamente!')
        return redirect(url_for('ver_usuarios'))
    else:
        flash('No tienes permiso para realizar esta acción.')
        return redirect(url_for('registro'))

if __name__ == '__main__':
    app.run(debug=True)
