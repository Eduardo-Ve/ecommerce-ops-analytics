---
tags: [proyecto-ecommerce, roadmap]
---

# 10. Roadmap

Duraciones aproximadas a ritmo medio (10 a 15 horas por semana). Ajustar a la disponibilidad real.

## Fase 0: Diseño (1 semana)

Entregable: repo con documentación.

- [x] Problema, alcance, base de datos, fuente de datos, ETL, KPIs, pantallas, arquitectura, historias y roadmap documentados
- [ ] Crear el repo en GitHub y publicar esta documentación
- [ ] Validar el diagrama ER
- [ ] Wireframes de las pantallas 2, 3, 4 y 7
- [ ] Cerrar las decisiones abiertas del [índice](00-indice.md)

## Fase 1: Datos y modelo (1 a 2 semanas)

Entregable: archivos sucios generados y reproducibles.

- [ ] Proyecto Django base con Docker Compose y PostgreSQL (conexión local pendiente de validar)
- [x] Modelos, migraciones y constraints definidos; `makemigrations --check` sin cambios
- [x] Generador de datos sintéticos con semilla fija y tests
- [ ] Documento de ground truth con los patrones ocultos

## Fase 2: ETL (2 semanas)

Entregable: `run_etl` carga datos y reporta rechazos.

- [x] Extract con hash e idempotencia
- [x] Staging de filas crudas
- [ ] Completar tests de reglas, correcciones y rechazos
- [x] Load con upsert por dependencias
- [x] Logs en `etl_run`, `etl_source_file` y `etl_reject`
- [ ] Prueba de integración completa contra PostgreSQL

## Fase 3: KPIs en SQL (1 a 2 semanas)

Entregable: KPIs calculados y verificados.

- [ ] Fijar definiciones pendientes en [KPIs](06-kpis.md)
- [ ] Vistas materializadas y refresh post-ETL
- [ ] Tests con dataset pequeño y resultados conocidos

## Fase 4: App y dashboard (2 semanas)

Entregable: dashboard navegable.

- [ ] Login y roles
- [ ] Pantallas 2, 3, 4 y 7 con filtros
- [ ] Exportación a CSV

## Fase 5: Calidad y deploy (1 semana)

Entregable: demo pública.

- [ ] Docker Compose final
- [ ] CI con GitHub Actions
- [ ] Deploy con datos demo

## Fase 6: Documentación y hallazgos (1 semana)

Entregable: proyecto presentable.

- [ ] README completo con instrucciones de ejecución
- [ ] Pantalla de hallazgos e informe corto con recomendaciones
- [ ] Justificación Pandas vs SQL

## v2 (opcional)

- [ ] Pantallas 5 y 6
- [ ] Celery y subida de archivos desde la interfaz
- [ ] Modelo ML (atraso o devolución)

## Consejos de ejecución

- Commits regulares desde la fase 0: el historial también cuenta.
- Al cerrar cada fase, el proyecto debe quedar funcionando.
- Si hay que recortar, recortar pantallas, no la calidad del ETL ni los KPIs.

Anterior: [Historias de usuario](09-historias-de-usuario.md) | [Índice](00-indice.md)
