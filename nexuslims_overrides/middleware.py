"""
Demo auto-login middleware for NexusLIMS public demo.

When IS_PUBLIC_DEMO is True, anonymous users are automatically logged in as a
demo account. The ?demo_as=<username> query parameter selects which demo role
to use (defaults to 'admin'). Only usernames in DEMO_USERNAMES are accepted.

Future demo landing pages can link to /?demo_as=readonly_user or
/?demo_as=project_lead to give role-specific experiences.
"""

from django.conf import settings
from django.contrib.auth import login

DEMO_USER_PARAM = "demo_as"
DEMO_DEFAULT_USER = "admin"
EXCLUDED_PATHS = {"/accounts/login/", "/accounts/logout/", "/admin/login/"}


class DemoAutoLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            getattr(settings, "IS_PUBLIC_DEMO", False)
            and not request.user.is_authenticated
        ):
            if request.path not in EXCLUDED_PATHS:
                from django.contrib.auth import get_user_model

                User = get_user_model()

                username = request.GET.get(DEMO_USER_PARAM, DEMO_DEFAULT_USER)
                demo_usernames = getattr(
                    settings, "DEMO_USERNAMES", [DEMO_DEFAULT_USER]
                )
                if username not in demo_usernames:
                    username = DEMO_DEFAULT_USER

                user = User.objects.filter(username=username).first()
                if user:
                    login(
                        request,
                        user,
                        backend="django.contrib.auth.backends.ModelBackend",
                    )

        return self.get_response(request)
