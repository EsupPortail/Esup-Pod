from django.db import migrations, models
import django.db.models.deletion


ROLE_DEFAULTS = [
    ("actor", "Actor", 0),
    ("author", "Author", 1),
    ("consultant", "Consultant", 2),
    ("contributor", "Contributor", 3),
    ("director", "Director", 4),
    ("speaker", "Speaker", 5),
    ("technician", "Technician", 6),
    ("voice-over", "Voice-over", 7),
]


def create_default_roles(apps, schema_editor):
    role_model = apps.get_model("completion", "Role")
    role_model.objects.bulk_create(
        [
            role_model(code=code, label=label, order=order)
            for code, label, order in ROLE_DEFAULTS
        ]
    )


class Migration(migrations.Migration):

    dependencies = [
        ("completion", "0002_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Role",
            fields=[
                (
                    "code",
                    models.SlugField(
                        help_text="Stable identifier used by the API and integrations.",
                        max_length=200,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Code",
                    ),
                ),
                ("label", models.CharField(max_length=200, verbose_name="Label")),
                ("is_active", models.BooleanField(default=True, verbose_name="Active")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Order")),
            ],
            options={
                "ordering": ["order", "label"],
                "verbose_name": "Role",
                "verbose_name_plural": "Roles",
            },
        ),
        migrations.RunPython(create_default_roles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="contribution",
            name="role",
            field=models.ForeignKey(
                default="author",
                db_column="role",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="contributions",
                to="completion.role",
                verbose_name="Role",
            ),
        ),
    ]
