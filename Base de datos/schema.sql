-- Esquema SQLite de Refugio Literario

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  is_admin INTEGER DEFAULT 0
);

CREATE TABLE catalogo (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  titulo TEXT NOT NULL,
  autor TEXT NOT NULL,
  genero TEXT,
  año_publicacion INTEGER,
  descripcion TEXT,
  precio INTEGER
);

CREATE TABLE carrito (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  libro_id INTEGER NOT NULL REFERENCES catalogo(id) ON DELETE CASCADE,
  precio REAL NOT NULL
);

CREATE TABLE compras (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  libro_id INTEGER REFERENCES catalogo(id) ON DELETE SET NULL,
  fecha_compra TIMESTAMP
);

-- Datos iniciales
INSERT INTO `catalogo` (`id`, `titulo`, `autor`, `genero`, `año_publicacion`, `descripcion`, `precio`) VALUES
(2, '1984', 'George Orwell', 'Distopía', 1921, 'Una novela que presenta un futuro totalitario donde el estado controla la vida de los ciudadanos.', 40000),
(3, 'El señor de los anillos', 'J.R.R. Tolkien', 'Fantasía', 1954, 'Una épica historia de la lucha entre el bien y el mal en la Tierra Media.', 80000),
(4, 'Don Quijote de la Mancha', 'Miguel de Cervantes', 'Novela', 1605, 'La historia de un hidalgo que decide convertirse en caballero andante.', 35000),
(6, 'Cien años de soledad', 'Gabriel García Márquez', 'Realismo mágico', 1967, 'Una saga familiar que narra la historia de los Buendía en Macondo.', 50000),
(7, 'El amor en los tiempos del cólera', 'Gabriel García Márquez', 'Romance', 1985, 'Una historia de amor que abarca más de cinco décadas.', 45000),
(8, 'La vorágine', 'José Eustasio Rivera', 'Novela de la selva', 1924, 'Una obra sobre la crudeza de la explotación del caucho en la selva.', 40000),
(9, 'El ruido de las cosas al caer', 'Juan Gabriel Vásquez', 'Ficción contemporánea', 2011, 'Una reflexión sobre el impacto del narcotráfico en Colombia.', 35000),
(10, 'Delirio', 'Laura Restrepo', 'Drama', 2004, 'Un hombre busca la causa del estado delirante de su esposa.', 38000),
(11, 'Los días de la sombra', 'Luis Noriega', 'Ciencia ficción', 2016, 'Una historia intrigante que combina humor y crítica social.', 32000),
(12, 'Crónica de una muerte anunciada', 'Gabriel García Márquez', 'Realismo mágico', 1981, 'Una historia sobre un asesinato anunciado en un pequeño pueblo.', 42000),
(13, 'Rayuela', 'Julio Cortázar', 'Ficción', 1963, 'Una novela experimental que explora la vida, el amor y el arte.', 48000),
(14, 'Fahrenheit 451', 'Ray Bradbury', 'Ciencia ficción', 1953, 'Una distopía donde los libros están prohibidos y los bomberos los queman.', 39000),
(15, 'El principito', 'Antoine de Saint-Exupéry', 'Fábula', 1943, 'Un cuento filosófico sobre la amistad y el sentido de la vida.', 30000),
(16, 'La casa de los espíritus', 'Isabel Allende', 'Realismo mágico', 1982, 'La saga de una familia a lo largo de varias generaciones en Chile.', 45000),
(17, 'El nombre de la rosa', 'Umberto Eco', 'Misterio', 1980, 'Un monje investiga una serie de asesinatos en una abadía medieval.', 50000),
(18, 'El alquimista', 'Paulo Coelho', 'Ficción filosófica', 1988, 'Un joven pastor busca un tesoro mientras aprende sobre la vida y los sueños.', 35000),
(19, 'Matar a un ruiseñor', 'Harper Lee', 'Drama', 1960, 'Una historia conmovedora sobre la justicia y el racismo en el sur de los Estados Unidos.', 40000),
(20, 'Las venas abiertas de América Latina', 'Eduardo Galeano', 'Ensayo', 1971, 'Un análisis crítico de la explotación económica y social de América Latina.', 46000);

INSERT INTO `compras` (`id`, `user_id`, `libro_id`, `fecha_compra`) VALUES
(16, 2, 2, '2024-11-19 08:30:10'),
(17, 2, 3, '2024-11-19 08:30:10'),
(18, 2, 3, '2024-11-22 20:27:58'),
(19, 2, 6, '2024-11-22 20:32:39');

INSERT INTO `users` (`id`, `username`, `email`, `password`, `is_admin`) VALUES
(1, 'admin', 'asd@gka.com', 'se-genera-al-crear-la-base', 1),
(2, 'user2', 'user@m.com', 'se-genera-al-crear-la-base', 0);

