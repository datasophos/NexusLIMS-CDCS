"""
NexusLIMS post-migration signal handlers.
"""

from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def grant_anonymous_explore_permission(sender, **kwargs):
    """
    Grant the anonymous group permission to access explore keyword app.

    This runs after migrations complete, ensuring the permission exists.
    """
    # Only run for our app or for core_explore_keyword_app
    if sender.name not in ['nexuslims_overrides', 'core_explore_keyword_app']:
        return

    from django.contrib.auth.models import Group, Permission

    try:
        # Get or create the anonymous group
        anonymous_group, created = Group.objects.get_or_create(name='anonymous')

        # Get the permission (may not exist yet if this is running for nexuslims_overrides)
        try:
            permission = Permission.objects.get(codename='access_explore_keyword')

            # Only add if not already there
            if not anonymous_group.permissions.filter(codename='access_explore_keyword').exists():
                anonymous_group.permissions.add(permission)
                print(f"✓ Granted 'access_explore_keyword' permission to 'anonymous' group")

        except Permission.DoesNotExist:
            # Permission doesn't exist yet - will be handled when core_explore_keyword_app migrates
            pass

    except Exception as e:
        # Don't fail migrations if this fails
        print(f"Warning: Could not grant anonymous explore permission: {e}")
