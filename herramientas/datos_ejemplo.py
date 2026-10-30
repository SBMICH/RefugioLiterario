"""Carga libros, usuarios de prueba, compras y reseñas de ejemplo.

Uso (desde la carpeta del proyecto):
    python herramientas/datos_ejemplo.py

Se puede ejecutar varias veces: no duplica libros ni usuarios que ya existan.

Usuarios de prueba que crea (rol lector):
    ana   / ana12345
    luis  / luis12345
    sofia / sofia12345
"""
import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from werkzeug.security import generate_password_hash
from app import DATABASE, actualizar_esquema

USUARIOS = [
    ('ana', 'ana@refugio.test', 'ana12345'),
    ('luis', 'luis@refugio.test', 'luis12345'),
    ('sofia', 'sofia@refugio.test', 'sofia12345'),
]

# (título, autor, género, año, descripción, precio)
LIBROS = [
    ('Pedro Páramo', 'Juan Rulfo', 'Realismo mágico', 1955, 'Juan Preciado viaja a Comala en busca de su padre y encuentra un pueblo habitado por voces.', 38000),
    ('Ficciones', 'Jorge Luis Borges', 'Cuento', 1944, 'Laberintos, bibliotecas infinitas y espejos en una colección de cuentos imprescindible.', 42000),
    ('El Aleph', 'Jorge Luis Borges', 'Cuento', 1949, 'Relatos sobre el infinito, la identidad y el tiempo.', 40000),
    ('La ciudad y los perros', 'Mario Vargas Llosa', 'Novela', 1963, 'La vida de un grupo de cadetes en un colegio militar de Lima.', 44000),
    ('La fiesta del Chivo', 'Mario Vargas Llosa', 'Novela histórica', 2000, 'Los últimos días de la dictadura de Trujillo en República Dominicana.', 52000),
    ('Como agua para chocolate', 'Laura Esquivel', 'Romance', 1989, 'Amor, cocina y tradición en el México revolucionario.', 36000),
    ('El túnel', 'Ernesto Sabato', 'Novela', 1948, 'La confesión de un pintor obsesionado con una mujer.', 32000),
    ('Los detectives salvajes', 'Roberto Bolaño', 'Novela', 1998, 'Dos poetas recorren el mundo tras la pista de una escritora desaparecida.', 58000),
    ('2666', 'Roberto Bolaño', 'Novela', 2004, 'Una novela monumental en torno a una ciudad fronteriza.', 68000),
    ('María', 'Jorge Isaacs', 'Romance', 1867, 'Un amor juvenil en el Valle del Cauca, clásico del romanticismo.', 30000),
    ('El coronel no tiene quien le escriba', 'Gabriel García Márquez', 'Novela', 1961, 'Un coronel retirado espera una pensión que nunca llega.', 34000),
    ('Del amor y otros demonios', 'Gabriel García Márquez', 'Realismo mágico', 1994, 'Una niña mordida por un perro y un sacerdote en la Cartagena colonial.', 38000),
    ('Noticia de un secuestro', 'Gabriel García Márquez', 'Crónica', 1996, 'La crónica de diez secuestros ocurridos en Colombia a comienzos de los noventa.', 39000),
    ('Paula', 'Isabel Allende', 'Memorias', 1994, 'Una carta de amor de una madre a su hija enferma.', 41000),
    ('Eva Luna', 'Isabel Allende', 'Novela', 1987, 'Una narradora nata sobrevive gracias a sus historias.', 39000),
    ('Veinte poemas de amor y una canción desesperada', 'Pablo Neruda', 'Poesía', 1924, 'Los poemas de amor más leídos en lengua española.', 25000),
    ('Canto general', 'Pablo Neruda', 'Poesía', 1950, 'Un canto épico a la historia y la naturaleza de América.', 45000),
    ('La tregua', 'Mario Benedetti', 'Novela', 1960, 'El diario de un viudo a punto de jubilarse que vuelve a enamorarse.', 31000),
    ('El laberinto de la soledad', 'Octavio Paz', 'Ensayo', 1950, 'Un ensayo sobre la identidad mexicana.', 37000),
    ('Aura', 'Carlos Fuentes', 'Terror', 1962, 'Un joven historiador entra en una casa donde el tiempo parece detenido.', 27000),
    ('La sombra del viento', 'Carlos Ruiz Zafón', 'Misterio', 2001, 'En el Cementerio de los Libros Olvidados, Daniel elige un libro que cambiará su vida.', 49000),
    ('El juego del ángel', 'Carlos Ruiz Zafón', 'Misterio', 2008, 'Un escritor recibe una oferta misteriosa en la Barcelona de los años veinte.', 49000),
    ('Nada', 'Carmen Laforet', 'Novela', 1945, 'Andrea llega a Barcelona y descubre una familia marcada por la posguerra.', 33000),
    ('La colmena', 'Camilo José Cela', 'Novela', 1951, 'Un retrato coral del Madrid de la posguerra.', 36000),
    ('Platero y yo', 'Juan Ramón Jiménez', 'Poesía', 1914, 'La tierna relación entre un poeta y su burro.', 24000),
    ('La casa de Bernarda Alba', 'Federico García Lorca', 'Teatro', 1945, 'Cinco hermanas encerradas por el luto que impone su madre.', 26000),
    ('Bodas de sangre', 'Federico García Lorca', 'Teatro', 1933, 'Una tragedia rural sobre el amor y el destino.', 26000),
    ('La Celestina', 'Fernando de Rojas', 'Clásico', 1499, 'La tragicomedia de Calisto y Melibea.', 28000),
    ('Lazarillo de Tormes', 'Anónimo', 'Clásico', 1554, 'Las andanzas de un niño pícaro en la España del siglo XVI.', 22000),
    ('Orgullo y prejuicio', 'Jane Austen', 'Romance', 1813, 'Elizabeth Bennet y el señor Darcy aprenden a mirar más allá de las apariencias.', 35000),
    ('Jane Eyre', 'Charlotte Brontë', 'Romance', 1847, 'Una institutriz independiente y el misterio de Thornfield Hall.', 37000),
    ('Cumbres borrascosas', 'Emily Brontë', 'Romance', 1847, 'Una pasión destructiva en los páramos de Yorkshire.', 36000),
    ('Frankenstein', 'Mary Shelley', 'Terror', 1818, 'Un científico da vida a una criatura y debe enfrentar las consecuencias.', 32000),
    ('Drácula', 'Bram Stoker', 'Terror', 1897, 'El conde vampiro viaja de Transilvania a Londres.', 34000),
    ('El retrato de Dorian Gray', 'Oscar Wilde', 'Clásico', 1890, 'Un joven conserva su belleza mientras su retrato envejece.', 31000),
    ('Crimen y castigo', 'Fiódor Dostoievski', 'Clásico', 1866, 'Raskólnikov comete un crimen y lucha con su conciencia.', 47000),
    ('Los hermanos Karamázov', 'Fiódor Dostoievski', 'Clásico', 1880, 'Tres hermanos, un padre y una profunda reflexión sobre la fe.', 55000),
    ('Ana Karénina', 'León Tolstói', 'Clásico', 1877, 'Una mujer desafía las normas de la alta sociedad rusa.', 52000),
    ('Guerra y paz', 'León Tolstói', 'Novela histórica', 1869, 'Varias familias rusas durante las guerras napoleónicas.', 65000),
    ('Madame Bovary', 'Gustave Flaubert', 'Clásico', 1857, 'Emma sueña con una vida distinta a la de su pueblo de provincia.', 33000),
    ('Los miserables', 'Victor Hugo', 'Novela histórica', 1862, 'Jean Valjean busca redención en la Francia del siglo XIX.', 58000),
    ('El conde de Montecristo', 'Alejandro Dumas', 'Aventura', 1844, 'Edmundo Dantès escapa de prisión y planea su venganza.', 54000),
    ('Moby Dick', 'Herman Melville', 'Aventura', 1851, 'El capitán Ahab persigue a la ballena blanca.', 46000),
    ('La isla del tesoro', 'Robert L. Stevenson', 'Aventura', 1883, 'Jim Hawkins y un mapa que lleva a un tesoro pirata.', 29000),
    ('Veinte mil leguas de viaje submarino', 'Julio Verne', 'Aventura', 1870, 'A bordo del Nautilus con el enigmático capitán Nemo.', 33000),
    ('La vuelta al mundo en ochenta días', 'Julio Verne', 'Aventura', 1872, 'Phileas Fogg apuesta que puede dar la vuelta al mundo a tiempo.', 30000),
    ('Alicia en el país de las maravillas', 'Lewis Carroll', 'Infantil', 1865, 'Alicia cae por una madriguera y llega a un mundo absurdo.', 27000),
    ('Mujercitas', 'Louisa May Alcott', 'Novela', 1868, 'Las hermanas March crecen durante la guerra civil estadounidense.', 34000),
    ('El gran Gatsby', 'F. Scott Fitzgerald', 'Novela', 1925, 'Fiestas, lujo y un amor imposible en los años veinte.', 32000),
    ('Las uvas de la ira', 'John Steinbeck', 'Novela', 1939, 'La familia Joad huye de la sequía en busca de trabajo en California.', 41000),
    ('El viejo y el mar', 'Ernest Hemingway', 'Novela', 1952, 'Un viejo pescador libra una batalla con un pez gigante.', 26000),
    ('Un mundo feliz', 'Aldous Huxley', 'Distopía', 1932, 'Una sociedad que ha sacrificado la libertad por la felicidad.', 36000),
    ('Rebelión en la granja', 'George Orwell', 'Distopía', 1945, 'Los animales de una granja se rebelan contra sus dueños.', 28000),
    ('El cuento de la criada', 'Margaret Atwood', 'Distopía', 1985, 'En la república de Gilead, las mujeres han perdido todos sus derechos.', 43000),
    ('Crónicas marcianas', 'Ray Bradbury', 'Ciencia ficción', 1950, 'La colonización de Marte contada en relatos poéticos.', 35000),
    ('Fundación', 'Isaac Asimov', 'Ciencia ficción', 1951, 'Un matemático predice la caída del Imperio galáctico.', 39000),
    ('Yo, robot', 'Isaac Asimov', 'Ciencia ficción', 1950, 'Relatos sobre las tres leyes de la robótica.', 34000),
    ('Dune', 'Frank Herbert', 'Ciencia ficción', 1965, 'Paul Atreides y la lucha por el planeta desierto Arrakis.', 56000),
    ('Solaris', 'Stanisław Lem', 'Ciencia ficción', 1961, 'Un océano vivo pone a prueba la mente de los científicos.', 37000),
    ('El hobbit', 'J.R.R. Tolkien', 'Fantasía', 1937, 'Bilbo Bolsón parte en una aventura inesperada con trece enanos.', 42000),
    ('Harry Potter y la piedra filosofal', 'J.K. Rowling', 'Fantasía', 1997, 'Un niño descubre que es mago y entra a Hogwarts.', 45000),
    ('La historia interminable', 'Michael Ende', 'Fantasía', 1979, 'Bastián lee un libro y termina dentro de Fantasía.', 44000),
    ('Momo', 'Michael Ende', 'Fantasía', 1973, 'Una niña se enfrenta a los hombres grises que roban el tiempo.', 35000),
    ('Las crónicas de Narnia', 'C.S. Lewis', 'Fantasía', 1950, 'Cuatro hermanos atraviesan un ropero hacia un mundo mágico.', 59000),
    ('El nombre del viento', 'Patrick Rothfuss', 'Fantasía', 2007, 'Kvothe narra la historia de su vida, de niño prodigio a leyenda.', 57000),
    ('Asesinato en el Orient Express', 'Agatha Christie', 'Misterio', 1934, 'Hércules Poirot investiga un crimen en un tren detenido por la nieve.', 33000),
    ('Diez negritos', 'Agatha Christie', 'Misterio', 1939, 'Diez desconocidos en una isla van muriendo uno a uno.', 33000),
    ('El sabueso de los Baskerville', 'Arthur Conan Doyle', 'Misterio', 1902, 'Sherlock Holmes y una leyenda familiar aterradora.', 30000),
    ('La chica del tren', 'Paula Hawkins', 'Misterio', 2015, 'Rachel observa cada día una casa desde el tren, hasta que ve algo extraño.', 40000),
    ('It', 'Stephen King', 'Terror', 1986, 'Un grupo de amigos se enfrenta a una entidad que despierta cada 27 años.', 62000),
    ('El resplandor', 'Stephen King', 'Terror', 1977, 'Un escritor cuida un hotel aislado durante el invierno.', 48000),
    ('Sapiens', 'Yuval Noah Harari', 'Historia', 2011, 'Una breve historia de la humanidad.', 54000),
    ('El diario de Ana Frank', 'Ana Frank', 'Memorias', 1947, 'El diario de una niña escondida durante la ocupación nazi.', 30000),
    ('El hombre en busca de sentido', 'Viktor Frankl', 'Ensayo', 1946, 'Un psiquiatra reflexiona sobre su experiencia en los campos de concentración.', 32000),
    ('Siddhartha', 'Hermann Hesse', 'Ficción filosófica', 1922, 'Un joven busca la iluminación a orillas del río.', 29000),
    ('El extranjero', 'Albert Camus', 'Ficción filosófica', 1942, 'Meursault comete un crimen y enfrenta el absurdo.', 28000),
    ('La metamorfosis', 'Franz Kafka', 'Clásico', 1915, 'Gregorio Samsa despierta convertido en un insecto.', 22000),
    ('Tokio blues', 'Haruki Murakami', 'Novela', 1987, 'Toru recuerda su juventud y sus amores en el Tokio de los sesenta.', 42000),
    ('Kafka en la orilla', 'Haruki Murakami', 'Novela', 2002, 'Un adolescente huye de casa y un anciano que habla con gatos.', 46000),
    ('Ensayo sobre la ceguera', 'José Saramago', 'Novela', 1995, 'Una epidemia de ceguera blanca se extiende por una ciudad.', 41000),
    ('El perfume', 'Patrick Süskind', 'Misterio', 1985, 'Un hombre con un olfato prodigioso busca crear el perfume perfecto.', 37000),
    ('La ladrona de libros', 'Markus Zusak', 'Novela histórica', 2005, 'Liesel roba libros en la Alemania nazi, narrada por la Muerte.', 44000),
    ('Los juegos del hambre', 'Suzanne Collins', 'Distopía', 2008, 'Katniss se ofrece como tributo en un cruel espectáculo televisado.', 41000),
    ('Mafalda: todas las tiras', 'Quino', 'Humor gráfico', 1993, 'La niña más reflexiva de Argentina y sus amigos.', 75000),
]

COMENTARIOS = {
    5: ['Una joya, no pude dejarlo.', 'De mis favoritos de siempre.', 'Imprescindible en cualquier biblioteca.'],
    4: ['Muy recomendable.', 'Me gustó mucho, aunque tiene partes lentas.', 'Una lectura muy bonita.'],
    3: ['Está bien, esperaba un poco más.', 'Interesante pero no me atrapó del todo.'],
}


def main():
    db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
    db.execute('PRAGMA foreign_keys = ON')
    actualizar_esquema(db)

    # Corrección de datos: 1984 se publicó en 1949
    db.execute("UPDATE catalogo SET año_publicacion = 1949 WHERE titulo = '1984' AND año_publicacion = 1921")

    nuevos_libros = 0
    for titulo, autor, genero, anio, descripcion, precio in LIBROS:
        existe = db.execute('SELECT 1 FROM catalogo WHERE titulo = ? AND autor = ?', (titulo, autor)).fetchone()
        if not existe:
            db.execute('INSERT INTO catalogo (titulo, autor, genero, año_publicacion, descripcion, precio) VALUES (?, ?, ?, ?, ?, ?)',
                       (titulo, autor, genero, anio, descripcion, precio))
            nuevos_libros += 1

    nuevos_usuarios = []
    for username, email, password in USUARIOS:
        if not db.execute('SELECT 1 FROM users WHERE username = ?', (username,)).fetchone():
            db.execute('INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, 0)',
                       (username, email, generate_password_hash(password)))
            nuevos_usuarios.append(username)

    # Compras y reseñas de ejemplo para los usuarios nuevos (así hay "más vendidos")
    random.seed(7)
    libro_ids = [r[0] for r in db.execute('SELECT id FROM catalogo')]
    populares = random.sample(libro_ids, 12)
    compras = resenas = 0
    for username in nuevos_usuarios:
        user_id = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()[0]
        elegidos = set(random.sample(populares, 7) + random.sample(libro_ids, 5))
        for libro_id in elegidos:
            fecha = datetime.now() - timedelta(days=random.randint(1, 300), minutes=random.randint(0, 1440))
            db.execute('INSERT INTO compras (user_id, libro_id, fecha_compra) VALUES (?, ?, ?)', (user_id, libro_id, fecha))
            compras += 1
            if random.random() < .6:
                nota = random.choice([5, 5, 4, 4, 3])
                db.execute('INSERT OR IGNORE INTO resenas (user_id, libro_id, calificacion, comentario, fecha) VALUES (?, ?, ?, ?, ?)',
                           (user_id, libro_id, nota, random.choice(COMENTARIOS[nota]), fecha + timedelta(days=3)))
                resenas += 1

    db.commit()
    total = db.execute('SELECT COUNT(*) FROM catalogo').fetchone()[0]
    db.close()
    print(f'Libros nuevos: {nuevos_libros} (total en catálogo: {total})')
    print(f'Usuarios nuevos: {", ".join(nuevos_usuarios) or "ninguno"}')
    print(f'Compras de ejemplo: {compras} · Reseñas de ejemplo: {resenas}')


if __name__ == '__main__':
    main()
