from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from api.serializers import DataSerializer #DataAnalysisSerializer
from MiApp.models import Data, DataAnalysis
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import mixins
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from django_pandas.io import read_frame
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

# Create your views here.
#Hago la api con el data ViewSet
class DataViewSet(viewsets.ModelViewSet):
	serializer_class = DataSerializer
	queryset = Data.objects.all()
	# authentication_classes = [SessionAuthentication, BasicAuthentication]
	# permission_classes = [IsAuthenticated]

@api_view(['POST'])
def cluster_function(request):
	try:
		#carga la data
		base = request.data
		df = pd.DataFrame(base)
		df["PrecioLista"] = df["PrecioLista"].astype(float)
		df["PrecioFacturado"] = df["PrecioFacturado"].astype(float)
		df['FechaApertura'] = pd.to_datetime(df['FechaApertura'])

		#completa la data
		df["OT FINAL"] = df["Identificador"].astype("str") + df["OC"].astype("str") \
						 + df["FechaApertura"].map(lambda x: 10000 * x.year + 100 * x.month + x.day) \
							 .astype("str")
		df["OT FINAL"] = df["OT FINAL"].str.lower()
		df["MONTO LISTA"] = df["Cantidad"] * df["PrecioLista"]
		df["MontoFacturado"] = df["Cantidad"] * df["PrecioFacturado"]
		df["Última compra"] = (df["FechaApertura"].max() - df["FechaApertura"]).dt.days
		df["Actividad"] = df["FechaApertura"].map(lambda x: 10000 * x.year + 100 * x.month + x.day).astype(str) \
						  + df["Identificador"]

		# filtrar base de datos para sacar One-timers
		df_unico = df.groupby('Identificador')["Actividad"].nunique().reset_index()
		df_unico.columns = ['Cliente', '#Actividad']
		df_unico = df_unico.loc[df_unico["#Actividad"] > 1]

		# calcular valor monetario, crear el dataframe
		df_revenue = df.groupby("Identificador")["MontoFacturado"].sum().reset_index()
		df_revenue.columns = ['Cliente', 'Revenue']

		df_unico1 = pd.merge(df_unico, df_revenue, on='Cliente', how='inner')

		#función para clusterizar
		def clustering(cluster_number, cluster_data, target_field, cluster_name):
			# Revenue clusters
			kmeans = KMeans(n_clusters=cluster_number)
			kmeans.fit(cluster_data[[target_field]])
			cluster_data[cluster_name] = kmeans.predict(cluster_data[[target_field]])

			return cluster_data


		df_unico1 = clustering(4, df_unico1, 'Revenue', 'RevenueCluster')

		# funcion para ordenar los clusters del mejor al peor
		def order_cluster(cluster_field_name, target_field_name, df, ascending):
			new_cluster_field_name = "new_" + cluster_field_name
			df_new = df.groupby(cluster_field_name)[target_field_name].mean().reset_index()
			df_new = df_new.sort_values(by=target_field_name, ascending=ascending).reset_index(drop=True)
			df_new['index'] = df_new.index
			df_final = pd.merge(df, df_new[[cluster_field_name, 'index']], on=cluster_field_name)
			df_final = df_final.drop([cluster_field_name], axis=1)
			df_final = df_final.rename(columns={"index": cluster_field_name})

			return df_final

		df_unico1 = order_cluster('RevenueCluster', 'Revenue', df_unico1, True)

		# seleccionamos la fecha máxima de Apertura de OT para Recency y creamos el DataFrame
		df_max_purchase = df.groupby('Identificador')["FechaApertura"].max().reset_index()
		df_max_purchase.columns = ['Cliente', 'MaxPurchaseDate']

		# encontramos Recency en días y lo fucionamos al df_unico
		df_max_purchase['Recency'] = (df_max_purchase['MaxPurchaseDate'].max()
									  - df_max_purchase['MaxPurchaseDate']).dt.days

		df_unico3 = pd.merge(df_unico1, df_max_purchase[['Cliente', 'Recency']], on='Cliente', how='inner')

		#clusterizamos y ordenamos
		df_unico3 = clustering(4, df_unico3, 'Recency', 'RecencyCluster')
		df_unico3 = order_cluster('RecencyCluster', 'Recency', df_unico3, False)

		# construir los clusters para la frecuency
		df_frequency = df.groupby('Identificador')["Actividad"].nunique().reset_index()
		df_frequency.columns = ['Cliente', 'Frequency']

		df_unico4 = pd.merge(df_unico3, df_frequency, on='Cliente', how='inner')

		#clusterizamos y ordenamos
		df_unico4 = clustering(4, df_unico4, 'Frequency', 'FrequencyCluster')
		df_unico4 = order_cluster('FrequencyCluster', 'Frequency', df_unico4, True)

		# construyendo la segmentación total
		df_unico4['OverallScore'] = df_unico4['RecencyCluster'] + df_unico4['FrequencyCluster'] \
									+ df_unico4['RevenueCluster']

		# asignamos nombres a los segmentos
		df_unico4['Segment'] = 'Low-Value'
		df_unico4.loc[df_unico4['OverallScore'] > 3, 'Segment'] = 'Mid-Value'
		df_unico4.loc[df_unico4['OverallScore'] > 5, 'Segment'] = 'High-Value'
		df_unico4.loc[df_unico4['OverallScore'] > 7, 'Segment'] = 'VIP'

		# filtrar base de datos para One-timers
		df_one = df.groupby('Identificador')["Actividad"].nunique().reset_index()
		df_one.columns = ['Cliente', '#Actividad']
		df_one = df_one.loc[df_one["#Actividad"] == 1]

		df_unico_one_1 = pd.merge(df_one, df_revenue, on='Cliente', how='inner')

		#clusterizamos y ordenamos
		df_unico_one_1 = clustering(3, df_unico_one_1, 'Revenue', 'RevenueCluster')
		df_unico_one_1 = order_cluster('RevenueCluster', 'Revenue', df_unico_one_1, True)

		df_unico_one_2 = pd.merge(df_unico_one_1, df_max_purchase[['Cliente','Recency']], on='Cliente', how='inner')

		#clusterizamos y ordenamos
		df_unico_one_2 = clustering(3, df_unico_one_2, 'Recency', 'RecencyCluster')
		df_unico_one_2 = order_cluster('RecencyCluster', 'Recency', df_unico_one_2, False)

		df_unico_one_3 = pd.merge(df_unico_one_2, df_frequency, on='Cliente', how='left')

		#clusterizamos y ordenamos
		df_unico_one_3 = clustering(1, df_unico_one_3, 'Frequency', 'FrequencyCluster')
		df_unico_one_3 = order_cluster('FrequencyCluster', 'Frequency', df_unico_one_3, True)

		#construyendo la segmentación total one-timers
		df_unico_one_3['OverallScore'] = df_unico_one_3['RecencyCluster'] + df_unico_one_3['FrequencyCluster'] + \
										 df_unico_one_3['RevenueCluster']

		# asignamos nombres a los segmentos
		df_unico_one_3['Segment'] = 'One-Low-Value'
		df_unico_one_3.loc[df_unico_one_3['OverallScore'] > 4, 'Segment'] = 'One-Mid-Value'

		# filtrar para segmentación final one-timers
		df_unico_final = pd.DataFrame(df["Identificador"].unique())

		# Nombrar columna
		df_unico_final.columns = ['Cliente']

		df_seg_final_0 = pd.merge(df_unico_final, df_unico4[['Cliente', 'Segment']], on='Cliente', how="left")
		df_seg_final_0 = df_seg_final_0.set_index('Cliente')
		df_seg_final_1 = df_unico_one_3.set_index('Cliente')
		df_seg_final = df_seg_final_0.combine_first(df_seg_final_1).reset_index()
		df_seg_final_2 = df_seg_final[["Cliente", "Segment"]]

		# Definir Días entre la primera y la última compra
		#creamos un DataFrame con el ID Clientes y la primera fecha de compra en df_2p
		df_2p_first_purchase = df.groupby('Identificador')["FechaApertura"].min().reset_index()
		df_2p_first_purchase.columns = ['Cliente', 'MinPurchaseDate']

		# creamos un DataFrame con el ID UNICO de cliente y la última fecha de compra en df_1p
		df_1p_last_purchase = df.groupby('Identificador')["FechaApertura"].max().reset_index()
		df_1p_last_purchase.columns = ['Cliente', 'MaxPurchaseDate']

		# fucionamos ambos DataFrame
		df_purchase_dates = pd.merge(df_1p_last_purchase, df_2p_first_purchase, on='Cliente', how='left')

		# calculamos los días de diferencia entre las fechas:
		df_purchase_dates['#DiasPriUlt'] = (df_purchase_dates['MaxPurchaseDate']
											- df_purchase_dates['MinPurchaseDate']).dt.days

		# lo fusionamos con df_unico
		df_base = pd.merge(df_seg_final_2, df_purchase_dates[['Cliente', '#DiasPriUlt']], on='Cliente', how='left')

		# Calculamos #Ot total por cliente
		df_OT = df.groupby('Identificador')["OT FINAL"].nunique().reset_index()
		df_OT.columns = ['Cliente', '#Ots']
		df_base1 = pd.merge(df_base, df_OT, on='Cliente', how='left')

		# Calculamos Monto Total por cliente
		df_MONTO = df.groupby('Identificador')["MontoFacturado"].sum().reset_index()
		df_MONTO.columns = ['Cliente', '$Ots']
		df_base2 = pd.merge(df_base1, df_MONTO, on='Cliente', how='left')

		# agregamos días desde la última compra
		df_base3 = pd.merge(df_base2, df_max_purchase[['Cliente', 'Recency']], on='Cliente')

		# agregamos #de actividades y segmento cliente
		df_base4 = pd.merge(df_base3, df_frequency, on='Cliente')
		df_base4["Frecuencia"] = df_base4["#DiasPriUlt"] / (df_base4["Frequency"] - 1)

		df_imputar = df_base4.groupby("Segment")["Frecuencia"].mean().reset_index()

		#imputar el valor de frecuencia encontrado
		LV = df_imputar.iloc[1]["Frecuencia"]  # definimos variable Low Value
		MV = df_imputar.iloc[2]["Frecuencia"]  # definimos variable Mid Value

		mask1 = (df_imputar["Frecuencia"].isnull()) & (df_imputar["Segment"] == 'One-Low-Value')
		df_imputar.loc[mask1, 'Frecuencia'] = df_imputar.loc[mask1, 'Frecuencia'].apply(lambda x: LV)

		mask2 = (df_imputar["Frecuencia"].isnull()) & (df_imputar["Segment"] == 'One-Mid-Value')
		df_imputar.loc[mask2, 'Frecuencia'] = df_imputar.loc[mask2, 'Frecuencia'].apply(lambda x: MV)

		df_base5 = df_base4.set_index('Segment')
		df_imputar2 = df_imputar.set_index('Segment')
		df_base6 = df_base5.combine_first(df_imputar2).reset_index()
		df_base6["Factor"] = df_base6["Recency"] / df_base6["Frecuencia"]

		# Creando un segmentos de factor
		imp_segm = pd.cut(df_base6['Factor'], [-1, 4, 6, 1000])

		# Asignar etiquetas a los segmentos del factor
		df_base7 = pd.DataFrame(imp_segm)
		df_base7.columns = ['RangoFactor']
		bins = pd.IntervalIndex.from_tuples([(-1, 4), (4, 6), (6, 1000)])
		x = pd.cut(df_base7["RangoFactor"].to_list(), bins)
		x.categories = ["Activo", "Peligro", "Desertor"]
		df_base7['Ciclo'] = x

		# Fucionar tabla final
		df_base8 = pd.merge(df_base6, df_base7, left_index=True, right_index=True)

		# Agregar MOnto Lista
		df_LISTA = df.groupby('Identificador')["MONTO LISTA"].sum().reset_index()
		df_LISTA.columns = ['Cliente', '$LISTA']

		df_base9 = pd.merge(df_base8, df_LISTA, on="Cliente")

		#ordenamiento
		df_plot1 = df_base9.groupby("Segment")["Cliente"].count()
		df_plot1 = pd.DataFrame(df_plot1).reset_index()
		df_plot1["%Cli"] = (df_plot1["Cliente"] / df_plot1["Cliente"].sum() * 100).round(0)
		df_plot2 = df_base9.groupby("Segment")["$Ots"].sum()
		df_plot2 = pd.DataFrame(df_plot2).reset_index()
		df_plot3 = pd.merge(df_plot1, df_plot2, on='Segment').round(0)
		df_plot3["%$"] = (df_plot3["$Ots"] / df_plot3["$Ots"].sum() * 100).round(0)
		df_plot4 = df_base9.groupby("Segment")["$LISTA"].sum()
		df_plot4 = pd.DataFrame(df_plot4).reset_index()
		df_plot5 = pd.merge(df_plot3, df_plot4, on='Segment').round(0)
		df_plot5["Des%"] = ((1 - df_plot5["$Ots"] / df_plot5["$LISTA"]) * 100).round(0)
		df_plot5["VIP"] = (df_plot5["$Ots"] / df_plot5["Cliente"]).round(0)
		df_plot5["VIPx"] = (df_plot5["VIP"] / df_plot5["VIP"].min()).round(0)
		df_plot5 = df_plot5.sort_values(by=["VIPx"], ascending=False)
		df_plot6 = (df_base9.groupby("Segment")["Frecuencia"].mean()).round(0)
		df_plot6 = pd.DataFrame(df_plot6).reset_index()
		df_plot7 = pd.merge(df_plot5, df_plot6, on='Segment')
		df_plot8 = (df_base9.groupby("Segment")["#Ots"].sum()).round(0)
		df_plot8 = pd.DataFrame(df_plot8).reset_index()
		df_plot9 = pd.merge(df_plot7, df_plot8, on='Segment')
		df_plot9["#Ot/Cli"] = (df_plot9["#Ots"] / df_plot9["Cliente"]).round(0)
		df_plot10 = df_base9.loc[df_base9["Ciclo"] == "Activo"]
		df_plot10 = df_plot10.groupby("Segment")["Cliente"].count()
		df_plot10 = pd.DataFrame(df_plot10).reset_index()
		df_plot10.columns = ["Segment", "Activo"]
		df_plot11 = df_base9.loc[df_base9["Ciclo"] == "Peligro"]
		df_plot11 = df_plot11.groupby("Segment")["Cliente"].count()
		df_plot11 = pd.DataFrame(df_plot11).reset_index()
		df_plot11.columns = ["Segment", "Alerta"]
		df_plot12 = df_base9.loc[df_base9["Ciclo"] == "Desertor"]
		df_plot12 = df_plot12.groupby("Segment")["Cliente"].count()
		df_plot12 = pd.DataFrame(df_plot12).reset_index()
		df_plot12.columns = ["Segment", "Desertor"]
		df_plot13 = pd.merge(df_plot9, df_plot10, on='Segment', how="left")
		df_plot14 = pd.merge(df_plot13, df_plot11, on='Segment', how="left")
		df_plot15 = pd.merge(df_plot14, df_plot12, on='Segment', how="left")
		df_plot15 = df_plot15.fillna(0)
		df_plot15["Gasto/OT"] = (df_plot15["$Ots"] / df_plot15["#Ots"]).round(0)
		df_plot15 = df_plot15.append(df_plot15.sum(numeric_only=True), ignore_index=True)
		df_plot15 = df_plot15.fillna("Total")

		# Definimos variables a imputar finales
		# definimos las variables a imputar
		Lista_Total = pd.DataFrame(df_plot15.loc[df_plot15["Segment"] == "Total"]["$LISTA"])
		Lista_Total = Lista_Total.iloc[0]["$LISTA"]
		# definimos las variables a imputar
		Monto_Total = pd.DataFrame(df_plot15.loc[df_plot15["Segment"] == "Total"]["$Ots"])
		Monto_Total = Monto_Total.iloc[0]["$Ots"]

		Des_total = ((Lista_Total / Monto_Total - 1) * 100).round(0)

		mask3 = (df_plot15["Segment"] == 'Total')  # imputamos
		df_plot15.loc[mask3, 'Des%'] = df_plot15.loc[mask3, 'Des%'].apply(lambda x: Des_total)

		# definimos las variables a imputar
		Cliente_Total = pd.DataFrame(df_plot15.loc[df_plot15["Segment"] == "Total"]["Cliente"])
		Cliente_Total = Cliente_Total.iloc[0]["Cliente"]

		VIP_Total = (Monto_Total / Cliente_Total).round(0)

		# imputamos
		mask4 = (df_plot15["Segment"] == 'Total')
		df_plot15.loc[mask4, 'VIP'] = df_plot15.loc[mask4, 'VIP'].apply(lambda x: VIP_Total)

		Frecuencia_Total = df_base9["Frecuencia"].mean()

		mask5 = (df_plot15["Segment"] == 'Total')  # imputamos
		df_plot15.loc[mask5, 'Frecuencia'] = df_plot15.loc[mask5, 'Frecuencia'] \
			.apply(lambda x: Frecuencia_Total).round(0)

		# definimos las variables a imputar
		Ot_Total = pd.DataFrame(df_plot15.loc[df_plot15["Segment"] == "Total"]["#Ots"])
		Ot_Total = Ot_Total.iloc[0]["#Ots"]

		Ot_cliente_Total = (Ot_Total / Cliente_Total).round(0)

		mask6 = (df_plot15["Segment"] == 'Total')  # imputamos
		df_plot15.loc[mask6, '#Ot/Cli'] = df_plot15.loc[mask6, '#Ot/Cli'].apply(lambda x: Ot_cliente_Total)

		Gasto_OT_Total = (Monto_Total / Ot_Total).round(0)

		mask7 = (df_plot15["Segment"] == 'Total')  # imputamos
		df_plot15.loc[mask7, 'Gasto/OT'] = df_plot15.loc[mask7, 'Gasto/OT'].apply(lambda x: Gasto_OT_Total)

		df_plot16 = df_plot15[["Segment", "Gasto/OT", "Cliente", "%Cli", "$Ots", "%$", "Des%", "VIPx", "VIP",
							   "Frecuencia", "#Ot/Cli", "Activo", "Alerta", "Desertor"]]

		df_base10 = df_base9.copy()
		df_base10["Gasto/Oc"] = (df_base10["$Ots"] / df_base10["#Ots"]).round(0)
		df_base10["Descuento"] = ((df_base10["$LISTA"] / df_base10["$Ots"] - 1) * 100).round(0)
		df_base10 = df_base10.round(0)
		df_base10 = df_base10[["Cliente", "$LISTA", "$Ots", "Descuento", "#Ots", "Gasto/Oc", "#DiasPriUlt",
							   "Frequency", "Frecuencia", "Recency", "Factor", "RangoFactor", "Ciclo", "Segment"]]

		print(df_base10)
		df = df_base10.to_json()

		return JsonResponse( df, safe=False )
	except ValueError as e:
		return Response(e.args[0], status.HTTP_400_BAD_REQUEST)
# class DataAnalysisSet(viewsets.ModelViewSet):
# 	serializer_class = DataAnalysisSerializer
# 	queryset = DataAnalysis.objects.all()
	# authentication_classes = [SessionAuthentication, BasicAuthentication]
	# permission_classes = [IsAuthenticated]

#Aquí hago la api creada en forma Genérica
# class GenericAPIView(
# 	generics.GenericAPIView,
# 	mixins.ListModelMixin,
# 	mixins.CreateModelMixin,
# 	mixins.UpdateModelMixin,
# 	mixins.RetrieveModelMixin,
# 	mixins.DestroyModelMixin,
# 	):
# 	serializer_class = DataSerializer
# 	queryset = Data.objects.all()
# 	lookup_field = 'id'
# 	#quitar el BasicAuthentication en producción
# 	authentication_classes = [SessionAuthentication, BasicAuthentication]
# 	permission_classes = [IsAuthenticated]
#
# 	def get(self, request, id = None):
#
# 		if id:
# 			return self.retrieve(request)
#
# 		else:
# 			return self.list(request)
#
# 		return self.list(request)
#
# 	def post(self, request):
# 		return self.create(request)
#
# 	def put(self, request, id=None):
# 		return self.update(request, id)
#
# 	def delete(self, request, id):
# 		return self.destroy(request, id)

#Aquí se ve la api creada en forma de Clases
# class DataAPIView(APIView):
#
# 	def get(self, request):
# 		data = Data.objects.all()
# 		serializer = DataSerializer(data, many=True)
# 		return Response(serializer.data)
#
# 	def post(self, request):
# 		serializer = DataSerializer(data=request.data)
#
# 		if serializer.is_valid():
# 			serializer.save()
# 			return Response(serializer.data, status=status.HTTP_201_CREATED)
# 		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
# class DataDetails(APIView):
#
# 	def get_object(self, id):
# 		try:
# 			return Data.objects.get(id=id)
#
# 		except Data.DoesNotExist:
# 			return HttpResponse(status=status.HTTP_404_NOT_FOUND)
#
# 	def get(self, request, id):
# 		data = self.get_object(id)
# 		serializer = DataSerializer(data)
# 		return Response(serializer.data)
#
# 	def put(self, request, id):
# 		data = self.get_object(id)
# 		serializer = DataSerializer(data, data=request.data)
# 		if serializer.is_valid():
# 			serializer.save()
# 			return Response(serializer.data)
# 		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
# 	def delete(self, request, id):
# 		data = self.get_object(id)
# 		data.delete()
# 		return Response(status=status.HTTP_204_NO_CONTENT)
#
#
#
# #esta es la vista de la carga en la api en forma de funciones
# @api_view(['GET', 'POST'])
# def data_list(request):
# 	if request.method == 'GET':
# 		data = Data.objects.all()
# 		serializer = DataSerializer(data, many=True)
# 		return Response(serializer.data)
#
# 	elif request.method == 'POST':
# 		serializer = DataSerializer(data=request.data)
#
# 		if serializer.is_valid():
# 			serializer.save()
# 			return Response(serializer.data, status=status.HTTP_201_CREATED)
# 		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
# @api_view(['GET', 'PUT', 'DELETE'])
# def data_detail(request, pk):
# 	try:
# 		data = Data.objects.get(pk=pk)
#
# 	except Data.DoesNotExist:
# 		return HttpResponse(status=status.HTTP_404_NOT_FOUND)
#
# 	if request.method == 'GET':
# 		serializer = DataSerializer(data)
# 		return Response(serializer.data)
#
# 	elif request.method == 'PUT':
# 		serializer = DataSerializer(data, data=request.data)
# 		if serializer.is_valid():
# 			serializer.save()
# 			return Response(serializer.data)
# 		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
# 	elif request.method == 'DELETE':
# 		data.delete()
# 		return Response(status=status.HTTP_204_NO_CONTENT)




