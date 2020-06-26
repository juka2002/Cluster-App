from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Data #DataAnalysis

# Register your models here.
@admin.register(Data)
class DataAdmin(ImportExportModelAdmin):
	list_display 	= ('id', 'Identificador', 'OC', 'FechaApertura', 'Cantidad', 'PrecioLista', 'PrecioFacturado')

# @admin.register(DataAnalysis)
# class DataAnalysisAdmin(ImportExportModelAdmin):
# 	list_display 	= ('id', 'Segment', 'GastoOT', 'Cliente', 'PorCliente', 'MontoOts', 'PorMontoOts', 'Descuento',
# 					   'VIPx', 'VIP', 'Frecuencia', 'OtCliente', 'Activo', 'Alerta', 'Desertor')
