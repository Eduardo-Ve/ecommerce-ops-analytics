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

Simulan sistemas distintos, con formatos de fecha y nombres de columnas distintos entre sí:

- `pedidos_YYYYMM.csv`
- `despachos_courierX.csv`
- `devoluciones.csv`
- `maestro_productos.xlsx`

## Errores inyectados

Con tasas controladas (1 a 3% por tipo):

- Duplicados.
- SKUs con espacios o en minúsculas.
- Fechas en formatos mixtos.
- Nulos.
- Montos negativos.
- Estados mal escritos.
- Entrega antes del envío.
- Referencias a productos inexistentes.

## Nota para el README

Documentar que los datos son sintéticos y cómo se generan. Es una ventaja: demuestra control sobre el experimento.

Anterior: [Base de datos](03-base-de-datos.md) | Siguiente: [Pipeline ETL](05-pipeline-etl.md)
