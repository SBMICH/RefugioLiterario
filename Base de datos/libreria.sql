-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 23-11-2024 a las 03:03:32
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `libreria`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `carrito`
--

CREATE TABLE `carrito` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `libro_id` int(11) NOT NULL,
  `precio` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `catalogo`
--

CREATE TABLE `catalogo` (
  `id` int(11) NOT NULL,
  `titulo` varchar(255) NOT NULL,
  `autor` varchar(255) NOT NULL,
  `genero` varchar(100) DEFAULT NULL,
  `año_publicacion` int(11) DEFAULT NULL,
  `descripcion` text DEFAULT NULL,
  `precio` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `catalogo`
--

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

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `compras`
--

CREATE TABLE `compras` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `libro_id` int(11) DEFAULT NULL,
  `fecha_compra` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `compras`
--

INSERT INTO `compras` (`id`, `user_id`, `libro_id`, `fecha_compra`) VALUES
(16, 2, 2, '2024-11-19 08:30:10'),
(17, 2, 3, '2024-11-19 08:30:10'),
(18, 2, 3, '2024-11-22 20:27:58'),
(19, 2, 6, '2024-11-22 20:32:39');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(200) NOT NULL,
  `is_admin` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `users`
--

INSERT INTO `users` (`id`, `username`, `email`, `password`, `is_admin`) VALUES
(1, 'user', 'asd@gka.com', '123', 1),
(2, 'user2', 'user@m.com', '123', 0);

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `carrito`
--
ALTER TABLE `carrito`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `libro_id` (`libro_id`);

--
-- Indices de la tabla `catalogo`
--
ALTER TABLE `catalogo`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `compras`
--
ALTER TABLE `compras`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `libro_id` (`libro_id`);

--
-- Indices de la tabla `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `carrito`
--
ALTER TABLE `carrito`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- AUTO_INCREMENT de la tabla `catalogo`
--
ALTER TABLE `catalogo`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;

--
-- AUTO_INCREMENT de la tabla `compras`
--
ALTER TABLE `compras`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=20;

--
-- AUTO_INCREMENT de la tabla `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `carrito`
--
ALTER TABLE `carrito`
  ADD CONSTRAINT `carrito_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `carrito_ibfk_2` FOREIGN KEY (`libro_id`) REFERENCES `catalogo` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `compras`
--
ALTER TABLE `compras`
  ADD CONSTRAINT `compras_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `compras_ibfk_2` FOREIGN KEY (`libro_id`) REFERENCES `catalogo` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
