# Generated migration for NexusLIMS search operators

from django.db import migrations


def create_instrument_pid_operator(apps, schema_editor):
    """Create the instrument-pid search operator for clickable badge filtering."""
    # Get the SearchOperator model
    SearchOperator = apps.get_model('core_explore_keyword_app', 'SearchOperator')

    # Check if operator already exists
    if SearchOperator.objects.filter(name='instrument-pid').exists():
        print("  → Search operator 'instrument-pid' already exists, skipping...")
        return

    # Create the operator
    SearchOperator.objects.create(
        name='instrument-pid',
        xpath_list=['/nx:Experiment/nx:summary/nx:instrument/@pid'],
        dot_notation_list=['Experiment.summary.instrument.@pid']
    )
    print("  ✓ Created search operator 'instrument-pid'")


def remove_instrument_pid_operator(apps, schema_editor):
    """Remove the instrument-pid search operator (for migration rollback)."""
    SearchOperator = apps.get_model('core_explore_keyword_app', 'SearchOperator')

    # Delete the operator if it exists
    deleted_count, _ = SearchOperator.objects.filter(name='instrument-pid').delete()

    if deleted_count > 0:
        print(f"  ✓ Removed search operator 'instrument-pid'")
    else:
        print("  → Search operator 'instrument-pid' not found, nothing to remove")


class Migration(migrations.Migration):

    dependencies = [
        # This migration depends on core_explore_keyword_app being installed
        # If core_explore_keyword_app has migrations, reference the latest one here
        # For now, we assume the app is already set up
    ]

    operations = [
        migrations.RunPython(
            create_instrument_pid_operator,
            reverse_code=remove_instrument_pid_operator
        ),
    ]
