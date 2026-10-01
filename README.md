# E-commerce Ops Analytics

Plataforma web de análisis operacional para una empresa de e-commerce. Combina una aplicación Django + PostgreSQL con un pipeline ETL en Python/Pandas (extracción, limpieza, validación y carga) y dashboards con indicadores de negocio: ventas, margen, tiempos de entrega, tasa de devoluciones y desempeño de bodegas.

> **Estado:** en diseño (fase 0). Toda la documentación de diseño está en [`docs/`](docs/00-indice.md).

## Objetivo

Mostrar el recorrido completo de un dato operacional: desde archivos sucios de distintos sistemas hasta información útil para la toma de decisiones, dentro de una sola aplicación fullstack.

## Stack

- Python, Django, PostgreSQL, Pandas
- Frontend propuesto: templates de Django + HTMX + Plotly
- Docker Compose, pytest, GitHub Actions

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

## Cómo ejecutarlo

Pendiente: se completará al terminar la fase 1.
