from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.db import connection
from django.http import HttpResponseNotFound, JsonResponse
from django.urls import set_urlconf
from tenant.models import Tenant
from tenant_schemas.utils import get_public_schema_name, has_multi_type_tenants

class TenantMainMiddleware:

    TENANT_NOT_FOUND_EXCEPTION = HttpResponseNotFound

    @staticmethod
    def hostname_from_request(request):
        return request.get_host().split(":")[0].lower()

    def process_request(self, request):
        connection.set_schema_to_public()

        try:
            hostname = self.hostname_from_request(request)
        except DisallowedHost:
            return HttpResponseNotFound("Invalid Hostname")

        tenant_name = request.headers.get("Tenant-Header")
        try:
            tenant = Tenant.objects.get(name__iexact=tenant_name)
        except Tenant.DoesNotExist:
            if tenant_name != "public":
                return JsonResponse({"detail": "Tenant not found"}, status=400)
            self.no_tenant_found(request, hostname)
            return

        tenant.domain_url = hostname
        request.tenant = tenant
        connection.set_tenant(request.tenant)
        self.setup_url_routing(request)

    def no_tenant_found(self, request, hostname):
        if getattr(settings, "SHOW_PUBLIC_IF_NO_TENANT_FOUND", False):
            self.setup_url_routing(request, force_public=True)
        else:
            raise self.TENANT_NOT_FOUND_EXCEPTION(f"No tenant for hostname '{hostname}'")

    @staticmethod
    def setup_url_routing(request, force_public=False):
        public_schema_name = get_public_schema_name()
        if has_multi_type_tenants():
            tenant_types = get_tenant_types()
            if not hasattr(request, "tenant") or (force_public or request.tenant.schema_name == public_schema_name):
                request.urlconf = get_public_schema_urlconf()
            else:
                tenant_type = request.tenant.get_tenant_type()
                request.urlconf = tenant_types[tenant_type]["URLCONF"]
        else:
            if hasattr(settings, "PUBLIC_SCHEMA_URLCONF") and (force_public or request.tenant.schema_name == public_schema_name):
                request.urlconf = settings.PUBLIC_SCHEMA_URLCONF

        set_urlconf(request.urlconf)
