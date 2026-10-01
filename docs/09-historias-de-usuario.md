---
tags: [proyecto-ecommerce, diseño, historias]
---

# 9. Historias de usuario

Cortas, cada una con criterios de aceptación. Sirven como checklist del MVP.

## Administrador de datos

- [ ] Como admin, quiero cargar archivos nuevos para actualizar la base. *Criterio: reejecutar el mismo archivo no duplica datos.*
- [ ] Como admin, quiero ver por qué se rechazó cada fila. *Criterio: cada rechazo muestra regla, motivo y dato original.*
- [ ] Como admin, quiero ver el historial de corridas. *Criterio: conteos de leídas, cargadas, corregidas y rechazadas.*

## Gerente / lector

- [ ] Como gerente, quiero ver ventas y margen por período. *Criterio: filtro por fechas, categoría y bodega.*
- [ ] Como gerente, quiero saber qué bodega cumple peor los plazos. *Criterio: OTD y tiempo de preparación comparables por bodega.*
- [ ] Como gerente, quiero ver qué categorías tienen más devoluciones. *Criterio: tasa por categoría y motivo.*
- [ ] Como gerente, quiero ver la variación contra el período anterior. *Criterio: indicador con flecha y porcentaje en las tarjetas.*

## Analista

- [ ] Como analista, quiero exportar las tablas a CSV. *Criterio: respeta los filtros activos.*
- [ ] Como analista, quiero consultar la definición de cada KPI. *Criterio: enlace al [diccionario de KPIs](06-kpis.md) desde cada tarjeta.*

## Seguridad

- [ ] Como admin, quiero que solo usuarios autenticados vean los datos. *Criterio: rutas protegidas y roles diferenciados.*

Anterior: [Arquitectura técnica](08-arquitectura.md) | Siguiente: [Roadmap](10-roadmap.md)
