import base64
from ninja.security import APIKeyHeader
from core.models import ApiToken


class ApiKeyAuth(APIKeyHeader):
    param_name = "Authorization"

    def authenticate(self, request, key: str):
        try:
            raw_token = key.split(" ")[-1]
            decoded_token = base64.b64decode(raw_token).decode("utf-8")

            api_token = ApiToken.objects.select_related("user", "user__organization").get(
                token=decoded_token, is_active=True
            )
            if api_token.is_valid:
                # Update last used timestamp
                api_token.mark_as_used()

                setattr(request, "user", api_token.user)
                setattr(request, "organization", api_token.user.organization)
                return api_token.user
        except:
            pass
