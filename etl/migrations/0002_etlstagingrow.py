from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("etl", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EtlStagingRow",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("entity", models.CharField(max_length=30)),
                ("row_number", models.PositiveIntegerField()),
                ("raw_data", models.JSONField()),
                (
                    "source_file",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="staging_rows",
                        to="etl.etlsourcefile",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="etlstagingrow",
            constraint=models.UniqueConstraint(
                fields=("source_file", "row_number"),
                name="etl_staging_file_row_unique",
            ),
        ),
    ]
