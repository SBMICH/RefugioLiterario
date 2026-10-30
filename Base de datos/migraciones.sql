-- Tablas e índices añadidos después del esquema original.
-- Se ejecuta en cada arranque; IF NOT EXISTS evita errores si ya existen.

CREATE TABLE IF NOT EXISTS favoritos (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  libro_id INTEGER NOT NULL REFERENCES catalogo(id) ON DELETE CASCADE,
  fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, libro_id)
);

CREATE TABLE IF NOT EXISTS resenas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  libro_id INTEGER NOT NULL REFERENCES catalogo(id) ON DELETE CASCADE,
  calificacion INTEGER NOT NULL CHECK (calificacion BETWEEN 1 AND 5),
  comentario TEXT,
  fecha TIMESTAMP,
  UNIQUE (user_id, libro_id)
);

CREATE INDEX IF NOT EXISTS idx_compras_libro ON compras(libro_id);
CREATE INDEX IF NOT EXISTS idx_compras_user ON compras(user_id);
CREATE INDEX IF NOT EXISTS idx_carrito_user ON carrito(user_id);
CREATE INDEX IF NOT EXISTS idx_catalogo_titulo ON catalogo(titulo);
CREATE INDEX IF NOT EXISTS idx_catalogo_genero ON catalogo(genero);
CREATE INDEX IF NOT EXISTS idx_resenas_libro ON resenas(libro_id);
