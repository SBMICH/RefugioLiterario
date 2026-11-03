# Refugio Literario

Librería en línea hecha con Flask y SQLite: catálogo con búsqueda y filtros, carrito,
reseñas con estrellas, lista de deseos, libros más vendidos y panel de administración.

## Cómo ejecutarla

```bash
python3 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Abre http://127.0.0.1:5000. La base de datos (`libreria.db`) se crea sola la primera vez
a partir de `Base de datos/schema.sql`. Al crearla se muestran en la consola las contraseñas
iniciales de las cuentas (o se usa `ADMIN_PASSWORD` para la del administrador, si está definida).

Para cargar más libros, usuarios de prueba, compras y reseñas de ejemplo:

```bash
python herramientas/datos_ejemplo.py
```

Ese script crea usuarios de prueba con contraseñas conocidas: úsalo solo en tu computador,
no en el sitio publicado.

## Configuración en producción

| Variable | Para qué sirve |
|---|---|
| `SECRET_KEY` | Clave para firmar las sesiones. Si no se define, se genera una y se guarda en `.secret_key`. |
| `DATABASE_PATH` | Ruta del archivo SQLite (por defecto `libreria.db`). |
| `SESSION_COOKIE_SECURE=1` | Actívala cuando el sitio use HTTPS. |


## Pruebas automáticas

```bash
pip install -r requirements-dev.txt
python -m pytest --cov=app
```

Cada prueba usa una base de datos temporal, así que no toca `libreria.db`. GitHub Actions
las ejecuta en cada push y envía la cobertura a SonarCloud.

## Prueba de carga

```bash
python herramientas/prueba_carga.py            # 10.000 libros y 50.000 compras
python herramientas/prueba_carga.py 50000 200000
```

Trabaja sobre una copia de la base de datos y muestra cuánto tarda cada página.
