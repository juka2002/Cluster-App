from django.shortcuts import render
from .models import Data, DataAnalysis
# from .resources import DataResource
from django.contrib import messages
from tablib import Dataset
from MiApp.models import Data

from django_pandas.io import read_frame
import pandas as pd
from sklearn.cluster import KMeans
import warnings

warnings.filterwarnings("ignore")

# Create your views here.
#esta es la vista de carga de la data en excel
def simple_upload(request):
	if request.method == 'POST':
		# data_resource = DataResource()
		#defino el dataset
		dataset = Dataset()
		#defino el archivo cargado
		new_person = request.FILES['myfile']

		if not new_person.name.endswith('xlsx'):
			messages.info(request, 'formato incorrecto')
			return render(request, 'base.html')
		#coloco el archivo cargado en el dataset
		imported_data = dataset.load(new_person.read(), format='xlsx')
		for data in imported_data:
			value = Data(
				data[0],
				data[1],
				data[2],
				data[3],
				data[4],
				data[5],
				data[6],
				)
			value.save()

	return	render(request,'base.html')

		# #leer la data
		# Base = Data.objects.all()
		# df = read_frame(Base)
		# df["PrecioLista"] = df["PrecioLista"].astype(float)
		# df["PrecioFacturado"] = df["PrecioFacturado"].astype(float)
		#
		# #completar la data
		# df["OT FINAL"] = df["Identificador"].astype("str") + df["OC"].astype("str") \
		# 				 + df["FechaApertura"].map(lambda x: 10000 * x.year + 100 * x.month + x.day) \
		# 					 .astype("str")
		# df["OT FINAL"] = df["OT FINAL"].str.lower()
		# df["MONTO LISTA"] = df["Cantidad"] * df["PrecioLista"]
		# df["MontoFacturado"] = df["Cantidad"] * df["PrecioFacturado"]
		# df["Última compra"] = (df["FechaApertura"].max() - df["FechaApertura"]).dt.days
		# df["Actividad"] = df["FechaApertura"].map(lambda x: 10000 * x.year + 100 * x.month + x.day).astype(str) \
		# 				  + df["Identificador"]
		#
		# #sacar los one-timers
		# df_unico = df.groupby('Identificador')["Actividad"].nunique().reset_index()
		# df_unico.columns = ['Cliente', '#Actividad']
		# df_unico = df_unico.loc[df_unico["#Actividad"] > 1]
		#
		# # calcular valor monetario, crear el dataframe
		# df_revenue = df.groupby("Identificador")["MontoFacturado"].sum().reset_index()
		# df_revenue.columns = ['Cliente', 'Revenue']
		# df_unico1 = pd.merge(df_unico, df_revenue, on='Cliente', how='inner')
		#
		# print(df_unico1)

		# return	render(request,'base.html')





