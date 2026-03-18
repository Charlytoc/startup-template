from typing import List

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.db.models import Field, Model, QuerySet


class AdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        return urls

    def _build_app_dict(self, request, label=None):

        app_dict = super(AdminSite, self)._build_app_dict(request, label)
        return app_dict

    def match_objects(
        self, request, query: str, model_class: Model, model_fields: List[Field]
    ) -> QuerySet:
        if model_class in [LogEntry]:
            return model_class.objects.none()
        return super().match_objects(request, query, model_class, model_fields)


admin_site = AdminSite()
