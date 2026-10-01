---
tags: [proyecto-ecommerce, indice]
estado: diseño
---

# E-commerce Ops Analytics: índice

Plataforma web de análisis operacional para un e-commerce, con Django + PostgreSQL, ETL en Pandas y dashboards de KPIs. Este índice enlaza todas las notas de diseño.

## Notas de diseño

| # | Nota | Para qué sirve |
|---|---|---|
| 1 | [Problema](01-problema.md) | Qué problema resuelve y para quién |
| 2 | [Alcance del MVP](02-alcance-mvp.md) | Qué entra, qué queda fuera, cuándo está terminado |
| 3 | [Base de datos](03-base-de-datos.md) | Modelo de datos y decisiones de diseño |
| 4 | [Fuente de datos](04-fuente-de-datos.md) | Generador sintético y errores inyectados |
| 5 | [Pipeline ETL](05-pipeline-etl.md) | Etapas, reglas de validación y reglas de operación |
| 6 | [KPIs](06-kpis.md) | Diccionario de indicadores |
| 7 | [Pantallas](07-pantallas.md) | Diseño del dashboard |
| 8 | [Arquitectura técnica](08-arquitectura.md) | Estructura, stack y decisiones |
| 9 | [Historias de usuario](09-historias-de-usuario.md) | Checklist funcional del MVP |
| 10 | [Roadmap](10-roadmap.md) | Fases, entregables y tareas |

## Decisiones abiertas

- [ ] Frontend: templates + HTMX + Plotly (propuesto) o Next.js consumiendo DRF.
- [ ] Tasa de devolución: por unidades (propuesto) o por pedidos.
- [ ] Fecha que agrupa las ventas: creación del pedido o pago.
- [ ] Hosting de la demo.

## Principio de recorte

Si hay que recortar alcance, se recortan pantallas, no la calidad del ETL ni los KPIs.
