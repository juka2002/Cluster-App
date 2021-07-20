from django.http import JsonResponse
from api.serializers import DataSerializer, DataAnalysisSerializer, UserSerializer
from MiApp.models import Data, DataAnalysis

from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User

import pandas as pd
from sklearn.cluster import KMeans
import datetime as dt
import json


# Create your views here.
#Hago la api con el data ViewSet
class DataViewSet(viewsets.ModelViewSet):
	serializer_class = DataSerializer
	queryset = Data.objects.all()
	# authentication_classes = [SessionAuthentication, BasicAuthentication]
	# permission_classes = (IsAuthenticated)

class DataAnalysisSet(viewsets.ModelViewSet):
	serializer_class = DataAnalysisSerializer
	queryset = DataAnalysis.objects.all()
	# authentication_classes = [SessionAuthentication, BasicAuthentication]
	# permission_classes = (IsAuthenticated)

class UserViewSet(viewsets.ModelViewSet):
	queryset = User.objects.all()
	serializer_class = UserSerializer
	permission_classes = (AllowAny, )

@api_view(['POST'])
def cluster_function(data):
	try:
		#base = request.data
		#base = read_frame(Data.objects.all())
		df = pd.read_json(data)

		df["PrecioLista"] = df["PrecioLista"].astype(float)
		df["PrecioFacturado"] = df["PrecioFacturado"].astype(float)
		df['FechaApertura'] = pd.TimedeltaIndex(df['FechaApertura'], unit='d') + dt.datetime(1900,1,1)
		df["Identificador"] = df["Identificador"].astype("str")
		df["OC"] = df["OC"].astype("str")

		for datos in df.itertuples():
			datos = Data.objects.create(
				Identificador = datos.Identificador,
				OC = datos.OC,
				FechaApertura = datos.FechaApertura,
				Cantidad = datos.Cantidad,
				PrecioLista = datos.PrecioLista,
				PrecioFacturado = datos.PrecioFacturado
			)

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

		Revenue = df_unico1[['Revenue']]

		#calculamos los puntos para la gráfica de codo que nos da el óptimo número de clusters
		min_clusters = 1
		max_clusters = 10
		muestra = df_unico1.Revenue.count()

		#calculamos los puntos para la gráfica de codo que nos da el óptimo número de clusters
		def calculate_wcss(df):
			wcss = []

			for n in range(min_clusters, min(muestra+1,max_clusters+1)):
				kmeans = KMeans(n_clusters=n, max_iter=1000)
				kmeans.fit(X=df)
				wcss.append(kmeans.inertia_)

			return wcss

		sum_of_squares_1 = calculate_wcss(Revenue)

		#calculamos el óptimo número de clusters
		def optimal_number_of_clusters(wcss):
			x0, y0 = min_clusters, wcss[0]
			x1, y1 = max_clusters, wcss[len(wcss)-1]

			distances = []
			for i in range(x0,min(muestra+1,max_clusters+1)):
				x = i
				y = wcss[i-min_clusters]
				numerator = abs((y1-y0)*x - (x1-x0)*y + x1*y0 - y1*x0)
				denominator = ((y1 - y0)**2 + (x1 - x0)**2)**0.5
				distances.append(numerator/denominator)

			return distances.index(max(distances)) + min_clusters

		n_1 = optimal_number_of_clusters(sum_of_squares_1)

		#función para clusterizar
		def clustering(cluster_number, cluster_data, target_field, cluster_name):
			# Revenue clusters
			kmeans = KMeans(n_clusters=cluster_number)
			kmeans.fit(cluster_data[[target_field]])
			cluster_data[cluster_name] = kmeans.predict(cluster_data[[target_field]])

			return cluster_data


		df_unico1 = clustering(n_1, df_unico1, 'Revenue', 'RevenueCluster')

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

		Recency = df_unico3[['Recency']]

		#Calculamos óptimo número de clusters
		sum_of_squares_2 = calculate_wcss(Recency)
		n_2 = optimal_number_of_clusters(sum_of_squares_2)

		#clusterizamos y ordenamos
		df_unico3 = clustering(n_2, df_unico3, 'Recency', 'RecencyCluster')
		df_unico3 = order_cluster('RecencyCluster', 'Recency', df_unico3, False)

		# construir los clusters para la frecuency
		df_frequency = df.groupby('Identificador')["Actividad"].nunique().reset_index()
		df_frequency.columns = ['Cliente', 'Frequency']

		df_unico4 = pd.merge(df_unico3, df_frequency, on='Cliente', how='inner')

		Frequency = df_unico4[['Frequency']]

		#Calculamos óptimo número de clusters
		sum_of_squares_3 = calculate_wcss(Frequency)
		n_3 = optimal_number_of_clusters(sum_of_squares_3)

		#clusterizamos y ordenamos
		df_unico4 = clustering(n_3, df_unico4, 'Frequency', 'FrequencyCluster')
		df_unico4 = order_cluster('FrequencyCluster', 'Frequency', df_unico4, True)

		#Escalamos la data de clusters para que todas las columnas tengan el mismo peso
		Revenue_max = max(df_unico4['RevenueCluster'])
		Recency_max = max(df_unico4['RecencyCluster'])
		Frequency_max = max(df_unico4['FrequencyCluster'])
		Indice = max(Revenue_max,Recency_max,Frequency_max)

		PesoRevenue = 2
		PesoRecency = 1
		PesoFrequency = 1

		escalar1 = df_unico4['RevenueCluster']
		lower, upper = 0, Indice
		df_unico4['RevenueClusterF'] = [lower + (upper - lower) * x/max(1,max(escalar1)) for x in escalar1]
		df_unico4['RevenueClusterF'] = df_unico4['RevenueClusterF'].astype('int')*PesoRevenue

		escalar2 = df_unico4['RecencyCluster']
		df_unico4['RecencyClusterF'] = [lower + (upper - lower) * x/max(1,max(escalar2)) for x in escalar2]
		df_unico4['RecencyClusterF'] = df_unico4['RecencyClusterF'].astype('int')*PesoRecency

		escalar3 = df_unico4['FrequencyCluster']
		df_unico4['FrequencyClusterF'] = [lower + (upper - lower) * x/max(1,max(escalar3)) for x in escalar3]
		df_unico4['FrequencyClusterF'] = df_unico4['FrequencyClusterF'].astype('int')*PesoFrequency

		# construyendo la segmentación total
		df_unico4['OverallScore'] = df_unico4['RecencyClusterF'] + df_unico4['FrequencyClusterF'] \
									+ df_unico4['RevenueClusterF']

		# asignamos nombres a los segmentos
		labelsNoOneTimers = ['Low-Value', 'Mid-Value', 'High-Value', 'VIP']
		df_unico4['Segment'] = pd.cut(df_unico4['OverallScore'], bins=4, labels=labelsNoOneTimers)

		# filtrar base de datos para One-timers
		df_one = df.groupby('Identificador')["Actividad"].nunique().reset_index()
		df_one.columns = ['Cliente', '#Actividad']
		df_one = df_one.loc[df_one["#Actividad"] == 1]

		df_unico_one_1 = pd.merge(df_one, df_revenue, on='Cliente', how='inner')

		RevenueOne = df_unico_one_1[['Revenue']]

		#Calculamos óptimo número de clusters
		sum_of_squares_4 = calculate_wcss(RevenueOne)
		n_4 = optimal_number_of_clusters(sum_of_squares_4)

		#clusterizamos y ordenamos
		df_unico_one_1 = clustering(n_4, df_unico_one_1, 'Revenue', 'RevenueCluster')
		df_unico_one_1 = order_cluster('RevenueCluster', 'Revenue', df_unico_one_1, True)

		df_unico_one_2 = pd.merge(df_unico_one_1, df_max_purchase[['Cliente','Recency']], on='Cliente', how='inner')

		RecencyOne = df_unico_one_2[['Recency']]

		#Calculamos óptimo número de clusters
		sum_of_squares_5 = calculate_wcss(RecencyOne)
		n_5 = optimal_number_of_clusters(sum_of_squares_5)

		#clusterizamos y ordenamos
		df_unico_one_2 = clustering(n_5, df_unico_one_2, 'Recency', 'RecencyCluster')
		df_unico_one_2 = order_cluster('RecencyCluster', 'Recency', df_unico_one_2, False)

		df_unico_one_3 = pd.merge(df_unico_one_2, df_frequency, on='Cliente', how='left')

		FrequencyOne = df_unico_one_3[['Frequency']]

		#Calculamos óptimo número de clusters
		sum_of_squares_6 = calculate_wcss(FrequencyOne)
		n_6 = optimal_number_of_clusters(sum_of_squares_6)

		#clusterizamos y ordenamos
		df_unico_one_3 = clustering(n_6, df_unico_one_3, 'Frequency', 'FrequencyCluster')
		df_unico_one_3 = order_cluster('FrequencyCluster', 'Frequency', df_unico_one_3, True)

		#Escalamos la data de clusters para que todas las columnas tengan el mismo peso
		Revenue_max2 = max(df_unico_one_3['RevenueCluster'])
		Recency_max2 = max(df_unico_one_3['RecencyCluster'])
		Frequency_max2 = max(df_unico_one_3['FrequencyCluster'])
		Indice2 = max(Revenue_max2,Recency_max2,Frequency_max2)

		escalar4 = df_unico_one_3['RevenueCluster']
		lower, upper = 0, Indice2
		df_unico_one_3['RevenueClusterF'] = [lower + (upper - lower) * x/max(1,max(escalar4)) for x in escalar4]
		df_unico_one_3['RevenueClusterF'] = df_unico_one_3['RevenueClusterF'].astype('int')*PesoRevenue

		escalar5 = df_unico_one_3['RecencyCluster']
		df_unico_one_3['RecencyClusterF'] = [lower + (upper - lower) * x/max(1,max(escalar5)) for x in escalar5]
		df_unico_one_3['RecencyClusterF'] = df_unico_one_3['RecencyClusterF'].astype('int')*PesoRecency

		escalar6 = df_unico_one_3['FrequencyCluster']
		df_unico_one_3['FrequencyClusterF'] = [lower + (upper - lower) * x/max(1,max(escalar6)) for x in escalar6]
		df_unico_one_3['FrequencyClusterF'] = df_unico_one_3['FrequencyClusterF'].astype('int')*PesoFrequency

		#construyendo la segmentación total one-timers
		df_unico_one_3['OverallScore'] = df_unico_one_3['RecencyClusterF'] + df_unico_one_3['FrequencyClusterF'] + \
										 df_unico_one_3['RevenueClusterF']

		# asignamos nombres a los segmentos
		labelsOneTimers = ['One-Low-Value', 'One-Mid-Value']
		df_unico_one_3['Segment'] = pd.cut(df_unico_one_3['OverallScore'], bins=2, labels=labelsOneTimers)

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

		df_imputar_Low = df_imputar.loc[df_imputar['Segment'] == 'Low-Value']
		df_imputar_Mid = df_imputar.loc[df_imputar['Segment'] == 'Mid-Value']

		#imputar el valor de frecuencia encontrado
		LV = df_imputar_Low.iloc[0]["Frecuencia"] # definimos variable Low Value
		MV = df_imputar_Mid.iloc[0]["Frecuencia"]  # definimos variable Mid Value

		mask1 = (df_imputar["Frecuencia"].isnull()) & (df_imputar["Segment"] == 'One-Low-Value')
		df_imputar.loc[mask1, 'Frecuencia'] = df_imputar.loc[mask1, 'Frecuencia'].apply(lambda x: LV)

		mask2 = (df_imputar["Frecuencia"].isnull()) & (df_imputar["Segment"] == 'One-Mid-Value')
		df_imputar.loc[mask2, 'Frecuencia'] = df_imputar.loc[mask2, 'Frecuencia'].apply(lambda x: MV)

		df_base5 = df_base4.set_index('Segment')
		df_imputar2 = df_imputar.set_index('Segment')
		df_base6 = df_base5.combine_first(df_imputar2).reset_index()
		df_base6["Factor"] = df_base6["Recency"] / df_base6["Frecuencia"]

		# Creando segmentos de factor
		imp_segm = pd.cut(df_base6['Factor'], [-1, 4, 6, 1000])

		# Asignar etiquetas a los segmentos del factor
		df_base7 = pd.DataFrame(imp_segm)
		df_base7.columns = ['RangoFactor']
		bins = pd.IntervalIndex.from_tuples([(-1, 4), (4, 6), (6, 1000)])
		x = pd.cut(df_base7["RangoFactor"].to_list(), bins)
		x.categories = ["Activo", "Peligro", "Desertor"]
		df_base7['Ciclo'] = x

		# Fusionar tabla final
		df_base8 = pd.merge(df_base6, df_base7, left_index=True, right_index=True)

		# Agregar MOnto Lista
		df_LISTA = df.groupby('Identificador')["MONTO LISTA"].sum().reset_index()
		df_LISTA.columns = ['Cliente', '$LISTA']

		df_base9 = pd.merge(df_base8, df_LISTA, on="Cliente")

		df_base9.loc[df_base9['Segment'] == 'One-Low-Value','Segment'] = 'One-Timer'
		df_base9.loc[df_base9['Segment'] == 'One-Mid-Value','Segment'] = 'One-Timer'

		#ordenamiento
		df_plot1 = df_base9.groupby("Segment")["Cliente"].count()
		df_plot1 = pd.DataFrame(df_plot1).reset_index()

		df_plot1["%Cli"] = (df_plot1["Cliente"] / (df_plot1["Cliente"].sum())).round(2)
		df_plot2 = df_base9.groupby("Segment")["$Ots"].sum()
		df_plot2 = pd.DataFrame(df_plot2).reset_index()

		df_plot3 = pd.merge(df_plot1, df_plot2, on='Segment').round(2)
		df_plot3["%$"] = (df_plot3["$Ots"] / (df_plot3["$Ots"].sum())).round(2)
		df_plot4 = df_base9.groupby("Segment")["$LISTA"].sum()
		df_plot4 = pd.DataFrame(df_plot4).reset_index()
		df_plot5 = pd.merge(df_plot3, df_plot4, on='Segment').round(2)
		df_plot5["Des%"] = (1 - df_plot5["$Ots"] / df_plot5["$LISTA"]).round(2)
		df_plot5["VIP"] = (df_plot5["$Ots"] / df_plot5["Cliente"]).round(2)
		df_plot5["VIPx"] = (df_plot5["VIP"] / df_plot5["VIP"].min()).round(0)
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
		df_plot15["Gasto/OT"] = (df_plot15["$Ots"] / df_plot15["#Ots"]).round(2)
		df_plot15 = df_plot15.append(df_plot15.sum(numeric_only=True), ignore_index=True)
		df_plot15 = df_plot15.fillna("Total")

		# Definimos variables a imputar finales
		# definimos las variables a imputar
		Lista_Total = pd.DataFrame(df_plot15.loc[df_plot15["Segment"] == "Total"]["$LISTA"])
		Lista_Total = Lista_Total.iloc[0]["$LISTA"]
		# definimos las variables a imputar
		Monto_Total = pd.DataFrame(df_plot15.loc[df_plot15["Segment"] == "Total"]["$Ots"])
		Monto_Total = Monto_Total.iloc[0]["$Ots"]

		Des_total = ((Lista_Total / Monto_Total - 1)).round(2)

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

		#Agregamos filas 0 en caso de clusters faltantes
		existe_VIP = df_plot15.loc[df_plot15['Segment'] == 'VIP']
		conteo1 = len(existe_VIP.index)
		if conteo1 == 0:
			df_plot15.loc[len(df_plot15)] = 0
			df_plot15['Segment'] = df_plot15['Segment'].replace({0:'VIP'})

		existe_High = df_plot15.loc[df_plot15['Segment'] == 'High-Value']
		conteo2 = len(existe_High.index)
		if conteo2 == 0:
			df_plot15.loc[len(df_plot15)] = 0
			df_plot15['Segment'] = df_plot15['Segment'].replace({0:'High-Value'})

		existe_Mid = df_plot15.loc[df_plot15['Segment'] == 'Mid-Value']
		conteo3 = len(existe_Mid.index)
		if conteo3 == 0:
			df_plot15.loc[len(df_plot15)] = 0
			df_plot15['Segment'] = df_plot15['Segment'].replace({0:'Mid-Value'})

		existe_Low = df_plot15.loc[df_plot15['Segment'] == 'Low-Value']
		conteo4 = len(existe_Low.index)
		if conteo4 == 0:
			df_plot15.loc[len(df_plot15)] = 0
			df_plot15['Segment'] = df_plot15['Segment'].replace({0:'Low-Value'})

		existe_One = df_plot15.loc[df_plot15['Segment'] == 'One-Timer']
		conteo5 = len(existe_One.index)
		if conteo5 == 0:
			df_plot15.loc[len(df_plot15)] = 0
			df_plot15['Segment'] = df_plot15['Segment'].replace({0:'One-Timer'})

		#orden final
		df_plot15['OrdenFinal'] = ''
		df_plot15.loc[df_plot15['Segment'] == 'VIP','OrdenFinal'] = 5
		df_plot15.loc[df_plot15['Segment'] == 'High-Value','OrdenFinal'] = 4
		df_plot15.loc[df_plot15['Segment'] == 'Mid-Value','OrdenFinal'] = 3
		df_plot15.loc[df_plot15['Segment'] == 'Low-Value','OrdenFinal'] = 2
		df_plot15.loc[df_plot15['Segment'] == 'One-Timer','OrdenFinal'] = 1
		df_plot15.loc[df_plot15['Segment'] == 'Total','OrdenFinal'] = 0
		df_plot15 = df_plot15.sort_values(by='OrdenFinal', ascending=False).reset_index(drop=True)

		df_plot16 = df_plot15[["Segment", "Gasto/OT", "Cliente", "%Cli", "$Ots", "%$", "Des%",
							   "VIPx", "VIP", "Frecuencia", "#Ot/Cli", "Activo", "Alerta",
							   "Desertor"]].rename(
			columns={
				'%Cli'   : 'PorCli',
				'$Ots'   : 'MontoOts',
				'%$'     : 'PorOts',
				'Des%'   : 'Des',
				'#Ot/Cli': 'OtCli',
				'Gasto/OT': 'GastoOT',
			}
		)

		for datos2 in df_plot16.itertuples():
			datos2 = DataAnalysis.objects.create(
				Segment = datos2.Segment,
				GastoOT = datos2.GastoOT,
				Cliente = datos2.Cliente,
				PorCli = datos2.PorCli,
				MontoOts = datos2.MontoOts,
				PorOts = datos2.PorOts,
				Des = datos2.Des,
				VIPx = datos2.VIPx,
				VIP = datos2.VIP,
				Frecuencia = datos2.Frecuencia,
				OtCli = datos2.OtCli,
				Activo = datos2.Activo,
				Alerta = datos2.Alerta,
				Desertor = datos2.Desertor,
				)

		df_base10 = df_base9.copy()
		df_base10["Gasto/Oc"] = (df_base10["$Ots"] / df_base10["#Ots"]).round(0)
		df_base10["Descuento"] = ((df_base10["$LISTA"] / df_base10["$Ots"] - 1) * 100).round(0)
		df_base10 = df_base10.round(0)
		df_base10 = df_base10[["Cliente", "$LISTA", "$Ots", "Descuento", "#Ots", "Gasto/Oc", "#DiasPriUlt",
					   "Frequency", "Frecuencia", "Recency", "Factor", "RangoFactor", "Ciclo", "Segment"]]

		df_base11 = df_base10[["Cliente", "$LISTA", "$Ots", "Descuento", "#Ots", "Gasto/Oc", "#DiasPriUlt",
					   "Frequency", "Frecuencia", "Recency", "Factor", "Ciclo", "Segment"]].rename(
			columns={
				'Cliente'   	: 'A.Cliente',
				'$LISTA'   		: 'B.$LISTA',
				'$Ots'     		: 'C.$Ots',
				'Descuento'   	: 'D.Descuento',
				'#Ots'			: 'E.#Ots',
				'Gasto/Oc'		: 'F.Gasto/Oc',
				'#DiasPriUlt'	: 'G.#DiasPriUlt',
				'Frequency'		: 'H.#Actividades',
				'Frecuencia'	: 'I.Frecuencia',
				'Recency'		: 'J.Recency',
				'Factor'		: 'K.FactorCiclo',
				'Ciclo'			: 'L.CicloDeVida',
				'Segment'		: 'M.Segmento',
			}
		)

		df = df_plot16.to_json()
		df2 = df_base11.to_json(orient="records")
		df3 = []
		df3.append(df)
		df3.append(df2)
		df4 = json.dumps(df3)

		return JsonResponse(df4, safe=False)
	except ValueError as e:
		return Response(e.args[0], status.HTTP_400_BAD_REQUEST)



