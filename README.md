# E-commerce Ops Analytics

Plataforma web de análisis operacional para una empresa de e-commerce. Combina una aplicación Django + PostgreSQL con un pipeline ETL en Python/Pandas (extracción, limpieza, validación y carga) y dashboards con indicadores de negocio: ventas, margen, tiempos de entrega, tasa de devoluciones y desempeño de bodegas.

> **Estado:** implementación de la Fase 1 y primera versión del ETL. La conexión de PostgreSQL debe validarse en el entorno local. Toda la documentación de diseño está en [`docs/`](docs/00-indice.md).

## Objetivo

Mostrar el recorrido completo de un dato operacional: desde archivos sucios de distintos sistemas hasta información útil para la toma de decisiones, dentro de una sola aplicación fullstack.

## Stack

- Python, Django, PostgreSQL, Pandas
- Frontend propuesto: templates de Django + HTMX + Plotly
- Docker Compose, Django TestCase/unittest, GitHub Actions

## Documentación

1. [Problema](docs/01-problema.md)
2. [Alcance del MVP](docs/02-alcance-mvp.md)
3. [Base de datos](docs/03-base-de-datos.md)
4. [Fuente de datos](docs/04-fuente-de-datos.md)
5. [Pipeline ETL](docs/05-pipeline-etl.md)
6. [KPIs](docs/06-kpis.md)
7. [Pantallas](docs/07-pantallas.md)
8. [Arquitectura técnica](docs/08-arquitectura.md)
9. [Historias de usuario](docs/09-historias-de-usuario.md)
10. [Roadmap](docs/10-roadmap.md)

## Datos

Todos los datos del proyecto son sintéticos y se generan con un script reproducible (ver [Fuente de datos](docs/04-fuente-de-datos.md)). No se usa información real de personas ni empresas.

## Cómo ejecutarlo en desarrollo

Requisitos: Python compatible con las dependencias y Docker Compose.

1. Crea tu archivo local de configuración y cambia las claves de ejemplo:

   ```bash
   cp .env.example .env
   ```

2. Inicia PostgreSQL. Compose publica el puerto `5433` del host hacia el `5432`
   del contenedor:

   ```bash
   docker compose up -d db
   ```

3. Activa tu entorno virtual e instala las dependencias:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Aplica las migraciones y genera los CSV sintéticos:

   ```bash
   python manage.py migrate
   python scripts/generate_synthetic_data.py
   ```

5. Valida y carga los CSV:

   ```bash
   python manage.py run_etl
   ```

   La primera ejecución valida y carga los archivos; las siguientes omiten los
   archivos cuyo SHA-256 ya se procesó correctamente.

6. Inicia Django:

   ```bash
   python manage.py runserver
   ```

Para ejecutar Django directamente desde el host, `.env` usa `DB_HOST=127.0.0.1`
y `DB_PORT=5433`. Si la app se ejecuta dentro de otro contenedor Compose, debe
conectarse al servicio `db` por el puerto `5432`. No publiques `.env` ni uses las
credenciales de ejemplo fuera del desarrollo local.
