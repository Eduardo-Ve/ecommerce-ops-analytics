---
tags: [proyecto-ecommerce, diseño, datos]
---

# 4. Fuente de datos

## Decisión

Generador sintético propio, calibrado con ideas de un dataset real.

- **Olist (Kaggle)** es real y conocido, pero a mi conocimiento no trae costos de producto, bodegas propias ni devoluciones explícitas, tres de los ejes del proyecto. Se usa como referencia de distribuciones (tiempos de entrega, ticket, estacionalidad), no como fuente única. Verificar el contenido actual del dataset antes de apoyarse en él.
- **Generador propio** en Python, con Faker `es_CL` y semilla fija para reproducibilidad.

## Parámetros del generador

- Ventana fija de 12 meses: desde el 1 de octubre de 2024 hasta el 30 de
  septiembre de 2025 (UTC).
- 3.000 pedidos por defecto, configurable; además se genera una fila duplicada
  deliberada, por lo que `pedidos.csv` contiene 3.001 filas de datos.
- Clientes: `max(500, pedidos // 3)`; para el valor por defecto son 1.000.
- 350 productos, 3 bodegas y 3 transportistas.
- Entre 1 y 4 ítems por pedido. Se crea un despacho por cada bodega distinta
  utilizada en un pedido. Solo los pedidos entregados pueden tener devoluciones.
- Los archivos se regeneran con la misma semilla y son idénticos mientras no
  cambien el código ni las versiones de Faker y Pandas.

## Alcance de los datos

Los datos cubren clientes, catálogo de productos, bodegas, transportistas,
pedidos, líneas, despachos y devoluciones. Las fechas de pedido y cliente se
distribuyen aleatoriamente en la ventana definida; los estados se sortean con
ponderaciones. El generador actual no introduce patrones ground truth de
estacionalidad, atrasos por bodega o courier ni tasas diferenciadas de
devolución por categoría.

## Archivos de salida

Ejecutar desde la raíz del proyecto:

```bash
python scripts/generate_synthetic_data.py
```

El script `scripts/generate_synthetic_data.py` utiliza Faker `es_CL` y Pandas.
Genera por defecto 3.000 pedidos con semilla fija (`20251006`) en `data/raw/`.
Se puede ajustar con `--orders`, `--seed` y `--output`. Por ejemplo:

```bash
python scripts/generate_synthetic_data.py --orders 5000 --seed 42
```

Produce un CSV por entidad (`clientes`, `productos`, `bodegas`, `transportistas`,
`pedidos`, `items`, `despachos` y `devoluciones`) más `catalogo_suciedad.csv`.
Este último identifica cada fila alterada por archivo, línea, clave y `rule_code`;
no añade columnas auxiliares a los CSV de entidades.

Los campos de referencia enlazan las entidades por `external_id`, SKU, código de
bodega o nombre de transportista. Clientes, pedidos, ítems y devoluciones usan los
`external_id` definidos en el modelo (`CUS-000001`, `ORD-000001`,
`ORD-000001-L1` y `RET-ORD-000001-L1` respectivamente). Los archivos de productos,
bodegas y transportistas usan `sku`, `code` y `name` como identificadores. Los
campos FK del CSV se exportan como `customer_external_id`, `order_external_id`,
`order_item_external_id`, `warehouse_code` y `carrier_name`; no son IDs numéricos
de base de datos.
Los CSV se ignoran en Git mediante `data/`, por lo que se versiona el generador y no
los datos completos.

## Errores inyectados

Se inyectan errores reproducibles y se registran en el catálogo lateral con sus
`rule_code`. Los porcentajes se aplican aproximadamente a 1% de pedidos o líneas
según corresponda (pueden variar por redondeo); además, se agrega una duplicación
por archivo de pedidos y una anomalía de orden de fechas en despachos:

- Pedidos duplicados (`DUP_ORDER`).
- SKUs inexistentes (`SKU_UNKNOWN`) o con espacios/minúsculas (`SKU_FMT`).
- Fechas imposibles (`DATE_INVALID`) o fechas válidas en formato mixto
  (`DATE_FMT`).
- Cantidades negativas (`AMOUNT_NEG`).
- Estados con variantes de texto en pedidos y despachos (`STATUS_MAP`).
- Entrega anterior al envío (`DATE_ORDER`).
- Regiones escritas distinto (`REGION_FMT`, regla documentada en
  [Pipeline ETL](05-pipeline-etl.md)).

`STATUS_MAP` puede aparecer tanto en pedidos como en despachos. `DATE_INVALID`
identifica una fecha imposible que debe rechazarse; `DATE_FMT` identifica una
fecha válida en formato día/mes/año que puede parsearse. El generador no inyecta
por ahora nulos de email ni anomalías de monto distintas a cantidad negativa.
`CUST_EMAIL_NULL` permanece como regla de advertencia del ETL, no como suciedad
producida actualmente.

## Nota para el README

Documentar que los datos son sintéticos y cómo se generan. Es una ventaja: demuestra control sobre el experimento.

Anterior: [Base de datos](03-base-de-datos.md) | Siguiente: [Pipeline ETL](05-pipeline-etl.md)
