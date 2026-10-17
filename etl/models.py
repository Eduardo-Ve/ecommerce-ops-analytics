from django.db import models
from django.db.models import Q
from django.utils import timezone


class EtlRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "En ejecución"
        SUCCESS = "success", "Exitoso"
        WARNINGS = "warnings", "Con advertencias"
        FAILED = "failed", "Fallido"

    started_at = models.DateTimeField("inicio", default=timezone.now)
    finished_at = models.DateTimeField("término", null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.RUNNING
    )
    rows_read = models.PositiveIntegerField("filas leídas", default=0)
    rows_loaded = models.PositiveIntegerField("filas cargadas", default=0)
    rows_corrected = models.PositiveIntegerField("filas corregidas", default=0)
    rows_rejected = models.PositiveIntegerField("filas rechazadas", default=0)

    class Meta:
        verbose_name = "Ejecución ETL"
        verbose_name_plural = "Ejecuciones ETL"
        ordering = ["-started_at"]

    def __str__(self):
        return f"Run {self.pk} - {self.status}"


class EtlSourceFile(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        LOADED = "loaded", "Cargado"
        FAILED = "failed", "Fallido"

    run = models.ForeignKey(
        EtlRun, on_delete=models.CASCADE, related_name="source_files"
    )
    filename = models.CharField("archivo", max_length=255)
    file_hash = models.CharField("hash SHA-256", max_length=64)
    entity = models.CharField("entidad", max_length=30)
    rows = models.PositiveIntegerField("filas", default=0)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    class Meta:
        verbose_name = "Archivo fuente"
        verbose_name_plural = "Archivos fuente"
        constraints = [
            # Un mismo contenido solo puede cargarse con éxito una vez;
            # los intentos fallidos no bloquean el reintento.
            models.UniqueConstraint(
                fields=["file_hash"],
                condition=Q(status="loaded"),
                name="etl_source_file_unique_loaded_hash",
            ),
        ]

    def __str__(self):
        return f"{self.filename} ({self.status})"


class EtlReject(models.Model):
    run = models.ForeignKey(
        EtlRun, on_delete=models.CASCADE, related_name="rejects"
    )
    source_file = models.ForeignKey(
        EtlSourceFile, on_delete=models.CASCADE, related_name="rejects"
    )
    entity = models.CharField("entidad", max_length=30)
    row_number = models.PositiveIntegerField("fila")
    rule_code = models.CharField("regla", max_length=30)
    reason = models.TextField("motivo")
    raw_data = models.JSONField("fila original")

    class Meta:
        verbose_name = "Fila rechazada"
        verbose_name_plural = "Filas rechazadas"
        indexes = [
            models.Index(fields=["run", "rule_code"], name="etl_reject_run_rule_idx"),
        ]

    def __str__(self):
        return f"{self.entity} fila {self.row_number} - {self.rule_code}"


class EtlStagingRow(models.Model):
    source_file = models.ForeignKey(
        EtlSourceFile, on_delete=models.CASCADE, related_name="staging_rows"
    )
    entity = models.CharField(max_length=30)
    row_number = models.PositiveIntegerField()
    raw_data = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source_file", "row_number"],
                name="etl_staging_file_row_unique",
            ),
        ]