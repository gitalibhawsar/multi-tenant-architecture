from django.db import models
from tenant_schemas.models import TenantMixin,DomainMixin

class Client(TenantMixin):
    name = models.CharField(max_length=100)
    paid_until =  models.DateField()
    on_trial = models.BooleanField()
    created_on = models.DateField(auto_now_add=True)

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True

class Tenant(TenantMixin):
    name = models.CharField(max_length=100, unique=True)
#default true, the schema will be automatically created and synced when it is saved
    auto_create_schema = True

class Domain(DomainMixin):
    pass