"""Tests for demo auto-login around API token requests."""

from unittest.mock import Mock, patch

from django.test import RequestFactory, SimpleTestCase, override_settings

from nexuslims_overrides.middleware import DemoAutoLoginMiddleware


class DemoAutoLoginMiddlewareTests(SimpleTestCase):
    @override_settings(IS_PUBLIC_DEMO=True)
    @patch("nexuslims_overrides.middleware.login")
    def test_token_authenticated_rest_request_skips_auto_login(
        self, mock_login
    ):
        request = RequestFactory().post(
            "/rest/data/", HTTP_AUTHORIZATION="Token " + "a" * 40
        )
        request.user = Mock(is_authenticated=False)
        response = Mock()
        middleware = DemoAutoLoginMiddleware(lambda _request: response)

        self.assertIs(middleware(request), response)
        mock_login.assert_not_called()

    @override_settings(IS_PUBLIC_DEMO=True)
    @patch("nexuslims_overrides.middleware.login")
    @patch("django.contrib.auth.get_user_model")
    def test_browser_request_still_auto_logs_in(
        self, mock_user_model, mock_login
    ):
        request = RequestFactory().get("/")
        request.user = Mock(is_authenticated=False)
        demo_user = Mock()
        mock_user_model.return_value.objects.filter.return_value.first.return_value = demo_user
        response = Mock()

        self.assertIs(
            DemoAutoLoginMiddleware(lambda _request: response)(request),
            response,
        )
        mock_login.assert_called_once_with(
            request,
            demo_user,
            backend="django.contrib.auth.backends.ModelBackend",
        )
