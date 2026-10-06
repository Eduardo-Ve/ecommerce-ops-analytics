---
tags: [proyecto-ecommerce, diseño, datos]
---

# 4. Fuente de datos

## Decisión

Generador sintético propio, calibrado con ideas de un dataset real.

- **Olist (Kaggle)** es real y conocido, pero a mi conocimiento no trae costos de producto, bodegas propias ni devoluciones explícitas, tres de los ejes del proyecto. Se usa como referencia de distribuciones (tiempos de entrega, ticket, estacionalidad), no como fuente única. Verificar el contenido actual del dataset antes de apoyarse en él.
- **Generador propio** en Python, con Faker `es_CL` y semilla fija para reproducibilidad.

## Parámetros del generador

- 12 a 18 meses de historia.
- 40 a 60 mil pedidos.
- 3 bodegas, 3 couriers, 300 a 500 SKUs.

## Patrones ocultos (ground truth)

Se insertan a propósito y se documentan en un archivo aparte, para validar que el dashboard los encuentra y que los hallazgos tienen respaldo:

- Una bodega con más atrasos los lunes.
- Un courier peor en regiones extremas.
- Una categoría con tasa de devolución alta.
- Peaks de demanda en Cyber Day, Black Friday y Navidad.

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
`external_id` definidos en el modelo; los ítems siguen el formato `ORD-000001-L1`.
Los CSV se ignoran en Git mediante `data/`, por lo que se versiona el generador y no
los datos completos.

## Errores inyectados

Se inyectan errores reproducibles y se registran en el catálogo lateral con sus
`rule_code`:

- Pedidos duplicados (`DUP_ORDER`).
- SKUs inexistentes (`SKU_UNKNOWN`) o con espacios/minúsculas (`SKU_FMT`).
- Fechas inválidas o en formatos mixtos (`DATE_FMT`).
- Cantidades negativas (`AMOUNT_NEG`).
- Estados con variantes de texto en pedidos y despachos (`STATUS_MAP`).
- Entrega anterior al envío (`DATE_ORDER`).
- Regiones escritas distinto (`REGION_FMT`, regla documentada en
  [Pipeline ETL](05-pipeline-etl.md)).

## Nota para el README

Documentar que los datos son sintéticos y cómo se generan. Es una ventaja: demuestra control sobre el experimento.

Anterior: [Base de datos](03-base-de-datos.md) | Siguiente: [Pipeline ETL](05-pipeline-etl.md)
