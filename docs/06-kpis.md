---
tags: [proyecto-ecommerce, diseño, kpis]
---

# 6. KPIs (diccionario)

| KPI | Definición | Notas |
|---|---|---|
| Ventas brutas | Suma de `quantity × unit_price` de pedidos no cancelados | Por día, mes y categoría |
| Ventas netas | Ventas brutas − reembolsos | |
| Margen bruto | Ventas netas − suma de `quantity × unit_cost` de unidades no devueltas | También en % |
| Ticket promedio | Ventas brutas / número de pedidos | |
| Lead time de entrega | `delivered_at − created_at` | Usar **mediana y p90**, no solo promedio |
| Entregas a tiempo (OTD) | % de despachos con `delivered_at <= promised_at` | Por bodega, courier y región |
| Tiempo de preparación | `shipped_at − paid_at` | Mide la bodega, no el courier |
| Tasa de devolución | Unidades devueltas / unidades entregadas | Por categoría, producto y bodega |

## Desempeño de bodega

Vista compuesta: OTD, tiempo de preparación, tasa de devolución y pedidos por día.

## Decisiones de definición

Fijar y mantener en esta nota:

- [ ] Qué pedidos cuentan: los cancelados quedan fuera.
- [ ] Qué fecha agrupa las ventas: creación o pago.
- [ ] Devolución medida en unidades (propuesto) o en pedidos.
- [ ] Tratamiento de un pedido con varios despachos.

## Implementación

- KPIs calculados en SQL con CTEs y window functions (variación mes a mes con `LAG`, ranking de productos con `RANK`).
- Vistas materializadas propuestas: `mv_daily_sales`, `mv_shipment_performance`, `mv_returns_summary`, `mv_warehouse_scorecard`.
- Tests contra un dataset pequeño con resultados calculados a mano.

Anterior: [Pipeline ETL](05-pipeline-etl.md) | Siguiente: [Pantallas](07-pantallas.md)
