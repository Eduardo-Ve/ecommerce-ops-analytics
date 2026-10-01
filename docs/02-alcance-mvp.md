---
tags: [proyecto-ecommerce, diseño]
---

# 2. Alcance del MVP

| Entra en el MVP | Queda para v2 |
|---|---|
| Modelo de datos completo (core, staging y logs de ETL) | Modelo ML (atraso o devolución) |
| ETL por archivos con validación y log de rechazos | Integración en vivo con APIs |
| Generador de datos sintéticos con errores inyectados | Multiempresa |
| 6 a 8 KPIs en SQL con vistas | Alertas y notificaciones |
| Dashboard con 5 pantallas y filtros | Forecast de ventas |
| Login con 2 roles (admin, lector) | Stock e inventario |
| Admin de Django para datos maestros | API pública documentada |
| Docker Compose, tests, CI, deploy, README | Celery y procesamiento asíncrono |

## Criterio de MVP terminado

Puedo levantar el proyecto con un comando, cargar archivos sucios, ver el reporte de la corrida, abrir el dashboard y responder las 4 preguntas de [Problema](01-problema.md) con datos.

Anterior: [Problema](01-problema.md) | Siguiente: [Base de datos](03-base-de-datos.md)
