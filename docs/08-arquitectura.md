---
tags: [proyecto-ecommerce, diseño, arquitectura]
---

# 8. Arquitectura técnica

Monolito Django con apps separadas por responsabilidad.

```
ecommerce-ops-analytics/
├── apps/
│   ├── core/         # modelos y admin
│   ├── etl/          # pipeline, reglas, comandos
│   ├── analytics/    # SQL de KPIs, vistas, servicios
│   ├── dashboard/    # vistas y templates
│   └── accounts/     # login y roles
├── data_generator/   # script de datos sintéticos
├── sql/              # vistas materializadas y queries
├── docs/             # diseño, ER, diccionario de KPIs, decisiones
├── tests/
├── docker-compose.yml
└── README.md
```

## Decisiones

- **Frontend (propuesto):** templates de Django + HTMX + Plotly (o Chart.js), con endpoints JSON para los gráficos. Rápido de construir y muestra dominio del lado servidor. La alternativa es Next.js consumiendo DRF, con más tiempo de desarrollo.
- **Ejecución del ETL:** comando de gestión (`python manage.py run_etl`) en el MVP. Celery y subida de archivos desde la interfaz quedan para v2.
- **Vistas materializadas:** creadas con migraciones `RunSQL` y refrescadas al final del ETL.
- **Tests con pytest:** reglas de validación con casos puntuales, KPIs contra un dataset pequeño con resultados conocidos, e idempotencia del ETL.
- **CI:** GitHub Actions con tests y linter.
- **Docker Compose:** servicios `web` y `db` como mínimo.
- **Configuración:** variables de entorno, con `.env.example`.
- **Deploy:** demo con datos sintéticos precargados, en un servicio gratuito o barato. Revisar las condiciones vigentes al elegir.

Anterior: [Pantallas](07-pantallas.md) | Siguiente: [Historias de usuario](09-historias-de-usuario.md)
