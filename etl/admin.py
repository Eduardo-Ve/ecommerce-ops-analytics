from django.contrib import admin

from etl.models import EtlReject, EtlRun, EtlSourceFile


@admin.register(EtlRun)
class EtlRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "started_at",
        "finished_at",
        "status",
        "rows_read",
        "rows_loaded",
        "rows_corrected",
        "rows_rejected",
    )
    list_filter = ("status",)


@admin.register(EtlSourceFile)
class EtlSourceFileAdmin(admin.ModelAdmin):
    list_display = ("filename", "entity", "rows", "status", "run")
    list_filter = ("entity", "status")
    search_fields = ("filename", "file_hash")


@admin.register(EtlReject)
class EtlRejectAdmin(admin.ModelAdmin):
    list_display = ("entity", "row_number", "rule_code", "run", "source_file")
    list_filter = ("entity", "rule_code")
    search_fields = ("reason", "source_file__filename")
