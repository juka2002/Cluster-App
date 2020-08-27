from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from MiApp.models import DataAnalysis

# Register your models here.
@admin.register(DataAnalysis)
class DataAnalysisAdmin(ImportExportModelAdmin):
	list_display 	= ('id', 'Segment', 'GastoOT', 'Cliente', 'PorCli', 'MontoOts', 'PorOts', 'Des',
					   'VIPx', 'VIP', 'Frecuencia', 'OtCli', 'Activo', 'Alerta', 'Desertor')