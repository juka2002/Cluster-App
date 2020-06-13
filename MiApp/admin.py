from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Data

# Register your models here.
@admin.register(Data)
class DataAdmin(ImportExportModelAdmin):
	list_display 	= ('Identificador', 'OC', 'FechaApertura', 'Cantidad', 'PrecioLista', 'PrecioFacturado')