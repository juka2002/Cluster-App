from django_pandas.io import read_frame
from datetime import datetime
import pandas as pd

from sklearn.cluster import KMeans #realizar el clustering

import warnings
warnings.filterwarnings("ignore")

#importar los serializers
from MiApp.models import Data

Base = Data.objects.all()
df = read_frame(Base)
df["PrecioLista"] = df["PrecioLista"].astype(float)
df["PrecioFacturado"] = df["PrecioFacturado"].astype(float)

df["OT FINAL"] = df["Identificador"].astype("str") + df["OC"].astype("str")\
                 + df["FechaApertura"].map(lambda x:10000*x.year + 100*x.month + x.day)\
                  .astype("str")   #concateno convirtiendo la fecha a string
df["OT FINAL"] = df["OT FINAL"].str.lower()
df["MONTO LISTA"] = df["Cantidad"]*df["PrecioLista"]
df["MontoFacturado"] = df["Cantidad"]*df["PrecioFacturado"]
df["Última compra"] = ((df["FechaApertura"].max()-df["FechaApertura"]).dt.days)
df["Actividad"] = df["FechaApertura"].map(lambda x:10000*x.year + 100*x.month + x.day).astype(str)\
                +df["Identificador"]

#filtrar base de datos para sacar One-timers
df_unico = df.groupby('Identificador')["Actividad"].nunique().reset_index()
df_unico.columns = ['Cliente','#Actividad']
df_unico = df_unico.loc[df_unico["#Actividad"]>1]

#calcular valor monetario, crear el dataframe
df_revenue = df.groupby("Identificador")["MontoFacturado"].sum().reset_index()
df_revenue.columns = ['Cliente','Revenue']

#add Revenue column to tx_user
df_unico1 = pd.merge(df_unico, df_revenue, on='Cliente')

#Revenue clusters 
kmeans = KMeans(n_clusters=4)
kmeans.fit(df_unico1[['Revenue']])
df_unico1['RevenueCluster'] = kmeans.predict(df_unico1[['Revenue']])

#funcion para ordenar los clusters del mejor al peor

def order_cluster(cluster_field_name, target_field_name,df,ascending): 
    new_cluster_field_name = "new_" + cluster_field_name
    df_new = df.groupby(cluster_field_name)[target_field_name].mean().reset_index()
    df_new = df_new.sort_values(by=target_field_name,ascending=ascending).reset_index(drop=True)
    df_new['index'] = df_new.index
    df_final = pd.merge(df,df_new[[cluster_field_name,'index']], on=cluster_field_name)
    df_final = df_final.drop([cluster_field_name],axis=1)
    df_final = df_final.rename(columns={"index":cluster_field_name})
    return df_final

# #ordering clusters and who the characteristics
df_unico1 = order_cluster('RevenueCluster', 'Revenue',df_unico1,True)

#seleccionamos la fecha máxima de Apertura de OT para Recency y creamos el DataFrame
df_max_purchase = df.groupby('Identificador')["FechaApertura"].max().reset_index()
df_max_purchase.columns = ['Cliente','MaxPurchaseDate']

#encontramos Recency en días y lo fucionamos al df_unico
df_max_purchase['Recency'] = (df_max_purchase['MaxPurchaseDate'].max() - df_max_purchase['MaxPurchaseDate']).dt.days
df_unico3 = pd.merge(df_unico1, df_max_purchase[['Cliente','Recency']], on='Cliente')

#construir los clusters para la recency
kmeans = KMeans(n_clusters=4)  #numero de clusters a crear
kmeans.fit(df_unico3[['Recency']]) #seleccionar la columna que le pega
df_unico3['RecencyCluster'] = kmeans.predict(df_unico3[['Recency']])

df_unico3 = order_cluster('RecencyCluster', 'Recency',df_unico3,False)

#construir los clusters para la frecuency
df_frequency = df.groupby('Identificador')["Actividad"].nunique().reset_index()
df_frequency.columns = ['Cliente','Frequency']

#agregar la columna frecuencia a df_final
df_unico4 = pd.merge(df_unico3, df_frequency, on='Cliente',how='left')

#clustering para frequency
kmeans = KMeans(n_clusters=4)
kmeans.fit(df_unico4[['Frequency']])
df_unico4['FrequencyCluster'] = kmeans.predict(df_unico4[['Frequency']])

#ordenamiento de los cluster de frequency para mostrar características
df_unico4 = order_cluster('FrequencyCluster', 'Frequency',df_unico4,True)
df_unico4.groupby('FrequencyCluster')['Frequency'].describe()

#construyendo la segmentación total
df_unico4['OverallScore'] = df_unico4['RecencyCluster'] + df_unico4['FrequencyCluster'] + df_unico4['RevenueCluster']

#assign segment names
df_unico4['Segment'] = 'Low-Value'
df_unico4.loc[df_unico4['OverallScore']>3,'Segment'] = 'Mid-Value' 
df_unico4.loc[df_unico4['OverallScore']>5,'Segment'] = 'High-Value'
df_unico4.loc[df_unico4['OverallScore']>7,'Segment'] = 'VIP'

#filtrar base de datos para One-timers
df_one = df.groupby('Identificador')["Actividad"].nunique().reset_index()
df_one.columns = ['Cliente','#Actividad']
df_one = df_one.loc[df_one["#Actividad"]==1]
df_one.columns = ['Cliente',"#Actividad"] #Nombrar columna

#calcular valor monetario, crear el dataframe
df_revenue_one = df.groupby("Identificador")["MontoFacturado"].sum().reset_index()
df_revenue_one.columns = ['Cliente','Revenue']

#add Revenue column to tx_user
df_unico_one_1 = pd.merge(df_one, df_revenue_one, on='Cliente')

#Revenue clusters 
kmeans = KMeans(n_clusters=3)
kmeans.fit(df_unico_one_1[['Revenue']])
df_unico_one_1['RevenueCluster'] = kmeans.predict(df_unico_one_1[['Revenue']])

#ordering clusters and who the characteristics
df_unico_one_1 = order_cluster('RevenueCluster', 'Revenue',df_unico_one_1,True)

#fución para Rececency de one-timers
df_unico_one_2 = pd.merge(df_unico_one_1, df_max_purchase[['Cliente','Recency']], on='Cliente')

#construir los clusters para la recency one-timers
kmeans = KMeans(n_clusters=3)  #numero de clusters a crear
kmeans.fit(df_unico_one_2[['Recency']]) #seleccionar la columna que le pega
df_unico_one_2['RecencyCluster'] = kmeans.predict(df_unico_one_2[['Recency']])

df_unico_one_2 = order_cluster('RecencyCluster', 'Recency',df_unico_one_2,False)

#construir los clusters para la frecuency one-timers
df_unico_one_3 = pd.merge(df_unico_one_2, df_frequency, on='Cliente',how='left')

#clustering para frequency
kmeans = KMeans(n_clusters=1)
kmeans.fit(df_unico_one_3[['Frequency']])
df_unico_one_3['FrequencyCluster'] = kmeans.predict(df_unico_one_3[['Frequency']])

#ordenamiento de los cluster de frequency para mostrar características
df_unico_one_3 = order_cluster('FrequencyCluster', 'Frequency',df_unico_one_3,True)

#construyendo la segmentación total one-timers
df_unico_one_3['OverallScore'] = df_unico_one_3['RecencyCluster'] + df_unico_one_3['FrequencyCluster']+\
                                 df_unico_one_3['RevenueCluster']

#assign segment names
df_unico_one_3['Segment'] = 'One-Low-Value'
df_unico_one_3.loc[df_unico_one_3['OverallScore']>4,'Segment'] = 'One-Mid-Value'

#filtrar para segmentación final
df_unico_final = pd.DataFrame(df["Identificador"].unique()) #DataFrame con ID
df_unico_final.columns = ['Cliente'] #Nombrar columna

df_unico_final
df_seg_final_0 = pd.merge(df_unico_final, df_unico4[['Cliente','Segment']], on='Cliente', how ="left")
df_seg_final_0 = df_seg_final_0.set_index('Cliente')
df_seg_final_1 = df_unico_one_3.set_index('Cliente')
df_seg_final = df_seg_final_0.combine_first(df_seg_final_1).reset_index()
df_seg_final = df_seg_final[["Cliente","Segment"]]

#filtrar para segmentación final
df_unico_final = pd.DataFrame(df["Identificador"].unique()) #DataFrame con ID
df_unico_final.columns = ['Cliente'] #Nombrar columna
df_unico_final
df_seg_final_0 = pd.merge(df_unico_final, df_unico4[['Cliente','Segment']], on='Cliente', how ="left")
df_seg_final_0 = df_seg_final_0.set_index('Cliente')
df_seg_final_1 = df_unico_one_3.set_index('Cliente')
df_seg_final = df_seg_final_0.combine_first(df_seg_final_1).reset_index()
df_seg_final = df_seg_final[["Cliente","Segment"]]

#Definir Días entre la primera y la última compra

#creamos un DataFrame con el ID Clientes y la primera fecha de compra en df_2p
df_2p_first_purchase = df.groupby('Identificador')["FechaApertura"].min().reset_index()
df_2p_first_purchase.columns = ['Cliente','MinPurchaseDate']

#creamos un DataFrame con el ID UNICO de cliente y la última fecha de compra en df_1p
df_1p_last_purchase = df.groupby('Identificador')["FechaApertura"].max().reset_index()
df_1p_last_purchase.columns = ['Cliente','MaxPurchaseDate']

#fucionamos ambos DataFrame
df_purchase_dates = pd.merge(df_1p_last_purchase,df_2p_first_purchase,on='Cliente',how='left')

#calculamos los días de diferencia entre las fechas:
df_purchase_dates['#DiasPriUlt'] = (df_purchase_dates['MaxPurchaseDate'] - df_purchase_dates['MinPurchaseDate']).dt.days

#lo fucionamos con df_unico 
df_base = pd.merge(df_seg_final, df_purchase_dates[['Cliente','#DiasPriUlt']],on='Cliente',how='left')

#Cambiamos los NAN por 999
#df_unico = df_unico.fillna(999)

#Calculamos #Ot total por cliente

df_OT = df.groupby('Identificador')["OT FINAL"].nunique().reset_index()
df_OT.columns = ['Cliente','#Ots']
df_base1 = pd.merge(df_base, df_OT,on='Cliente',how='left')

#Calculamos Monto Total por cliente
df_MONTO = df.groupby('Identificador')["MontoFacturado"].sum().reset_index()
df_MONTO.columns = ['Cliente','$Ots']
df_base2 = pd.merge(df_base1, df_MONTO,on='Cliente',how='left')

#agregamos días desde la última compra
df_base3 = pd.merge(df_base2, df_max_purchase[['Cliente','Recency']], on='Cliente')

#agregamos #de actividades y segmento cliente
df_base4 = pd.merge(df_base3, df_frequency, on='Cliente')
df_base4["Frecuencia"] = df_base4["#DiasPriUlt"]/(df_base4["Frequency"]-1)

df_imputar = df_base4.groupby("Segment")["Frecuencia"].mean().reset_index()

#imputar el valor de frecuencia encontrado
LV = df_imputar.iloc[1]["Frecuencia"] #definimos variable Low Value
MV = df_imputar.iloc[2]["Frecuencia"] #definimos variable Mid Value

mask1 = (df_imputar["Frecuencia"].isnull()) & (df_imputar["Segment"] == 'One-Low-Value') #imputamos One-Low
df_imputar.loc[mask1, 'Frecuencia'] = df_imputar.loc[mask1, 'Frecuencia'].apply(lambda x:LV)   

mask2 = (df_imputar["Frecuencia"].isnull()) & (df_imputar["Segment"] == 'One-Mid-Value') #imputamos One-Mid
df_imputar.loc[mask2, 'Frecuencia'] = df_imputar.loc[mask2, 'Frecuencia'].apply(lambda x:MV) 

df_base5 = df_base4.set_index('Segment')
df_imputar2 = df_imputar.set_index('Segment')
df_base6 = df_base5.combine_first(df_imputar2).reset_index()
df_base6["Factor"] = df_base6["Recency"]/df_base6["Frecuencia"]

# Creando un segmentos de factor
imp_segm = pd.cut(df_base6['Factor'], 
                  [-1, 4, 6, 1000])

#Asignar etiquetas a los segmentos del factor
df_base7 = pd.DataFrame(imp_segm)
df_base7.columns = ['RangoFactor']
bins = pd.IntervalIndex.from_tuples([(-1, 4), (4, 6), (6, 1000)])
x = pd.cut(df_base7["RangoFactor"].to_list(),bins)
x.categories = ["Activo","Peligro","Desertor"]
df_base7['Ciclo'] = x
df_base7

#Fucionar tabla final
df_base8 = pd.merge(df_base6, df_base7,left_index=True,right_index=True)

#Agregar MOnto Lista
df_LISTA = df.groupby('Identificador')["MONTO LISTA"].sum().reset_index()
df_LISTA.columns = ['Cliente','$LISTA']

df_base9 = pd.merge(df_base8, df_LISTA, on ="Cliente")

df_plot1 = df_base9.groupby("Segment")["Cliente"].count()
df_plot1 = pd.DataFrame(df_plot1).reset_index()
df_plot1["%Cli"] = (df_plot1["Cliente"]/df_plot1["Cliente"].sum()*100).round(0)
df_plot2 = df_base9.groupby("Segment")["$Ots"].sum()
df_plot2 = pd.DataFrame(df_plot2).reset_index()
df_plot3 = pd.merge(df_plot1, df_plot2, on='Segment').round(0)
df_plot3["%$"] = (df_plot3["$Ots"]/df_plot3["$Ots"].sum()*100).round(0)
df_plot4 = df_base9.groupby("Segment")["$LISTA"].sum()
df_plot4 = pd.DataFrame(df_plot4).reset_index()
df_plot5 = pd.merge(df_plot3, df_plot4, on='Segment').round(0)
df_plot5["Des%"] = ((1-df_plot5["$Ots"]/df_plot5["$LISTA"])*100).round(0)
df_plot5["VIP"] = (df_plot5["$Ots"]/df_plot5["Cliente"]).round(0)
df_plot5["VIPx"] = (df_plot5["VIP"]/df_plot5["VIP"].min()).round(0)
df_plot5 = df_plot5.sort_values(by=["VIPx"],ascending=False)
df_plot6 = (df_base9.groupby("Segment")["Frecuencia"].mean()).round(0)
df_plot6 = pd.DataFrame(df_plot6).reset_index()
df_plot7 = pd.merge(df_plot5, df_plot6, on='Segment')
df_plot8 = (df_base9.groupby("Segment")["#Ots"].sum()).round(0)
df_plot8 = pd.DataFrame(df_plot8).reset_index()
df_plot9 = pd.merge(df_plot7, df_plot8, on='Segment')
df_plot9["#Ot/Cli"] = (df_plot9["#Ots"]/df_plot9["Cliente"]).round(0)
df_plot10 = df_base9.loc[df_base9["Ciclo"]=="Activo"]
df_plot10 = df_plot10.groupby("Segment")["Cliente"].count()
df_plot10 = pd.DataFrame(df_plot10).reset_index()
df_plot10.columns = ["Segment","Activo"]
df_plot11 = df_base9.loc[df_base9["Ciclo"]=="Peligro"]
df_plot11 = df_plot11.groupby("Segment")["Cliente"].count()
df_plot11 = pd.DataFrame(df_plot11).reset_index()
df_plot11.columns = ["Segment","Alerta"]
df_plot12 = df_base9.loc[df_base9["Ciclo"]=="Desertor"]
df_plot12 = df_plot12.groupby("Segment")["Cliente"].count()
df_plot12 = pd.DataFrame(df_plot12).reset_index()
df_plot12.columns = ["Segment","Desertor"]
df_plot13 = pd.merge(df_plot9, df_plot10, on='Segment',how="left")
df_plot14 = pd.merge(df_plot13, df_plot11, on='Segment',how="left")
df_plot15 = pd.merge(df_plot14, df_plot12, on='Segment',how="left")
df_plot15 = df_plot15.fillna(0)
df_plot15["Gasto/OT"] = (df_plot15["$Ots"]/df_plot15["#Ots"]).round(0)
df_plot15 = df_plot15.append(df_plot15.sum(numeric_only=True), ignore_index=True)
df_plot15 = df_plot15.fillna("Total")

#Definimos variables a imputar finales
Lista_Total = pd.DataFrame(df_plot15.loc[df_plot15["Segment"]=="Total"]["$LISTA"]) #definimos las variables a imputar
Lista_Total = Lista_Total.iloc[0]["$LISTA"]

Monto_Total = pd.DataFrame(df_plot15.loc[df_plot15["Segment"]=="Total"]["$Ots"]) #definimos las variables a imputar
Monto_Total = Monto_Total.iloc[0]["$Ots"]

Des_total = ((Lista_Total/Monto_Total-1)*100).round(0)

mask3 = (df_plot15["Segment"] == 'Total') #imputamos
df_plot15.loc[mask3, 'Des%'] = df_plot15.loc[mask3, 'Des%'].apply(lambda x:Des_total) 
df_plot15

Cliente_Total = pd.DataFrame(df_plot15.loc[df_plot15["Segment"]=="Total"]["Cliente"]) #definimos las variables a imputar
Cliente_Total = Cliente_Total.iloc[0]["Cliente"]

VIP_Total = (Monto_Total/Cliente_Total).round(0)

mask4 = (df_plot15["Segment"] == 'Total') #imputamos
df_plot15.loc[mask4, 'VIP'] = df_plot15.loc[mask4, 'VIP'].apply(lambda x:VIP_Total) 

Frecuencia_Total = df_base9["Frecuencia"].mean()

mask5 = (df_plot15["Segment"] == 'Total') #imputamos
df_plot15.loc[mask5, 'Frecuencia'] = df_plot15.loc[mask5, 'Frecuencia'].apply(lambda x:Frecuencia_Total).round(0)

Ot_Total = pd.DataFrame(df_plot15.loc[df_plot15["Segment"]=="Total"]["#Ots"]) #definimos las variables a imputar
Ot_Total = Ot_Total.iloc[0]["#Ots"]

Ot_cliente_Total = (Ot_Total/Cliente_Total).round(0)

mask6 = (df_plot15["Segment"] == 'Total') #imputamos
df_plot15.loc[mask6, '#Ot/Cli'] = df_plot15.loc[mask6, '#Ot/Cli'].apply(lambda x:Ot_cliente_Total) 

Gasto_OT_Total = (Monto_Total/Ot_Total).round(0)

mask7 = (df_plot15["Segment"] == 'Total') #imputamos
df_plot15.loc[mask7, 'Gasto/OT'] = df_plot15.loc[mask7, 'Gasto/OT'].apply(lambda x:Gasto_OT_Total) 

df_plot16 = df_plot15[["Segment","Gasto/OT","Cliente","%Cli","$Ots","%$","Des%","VIPx","VIP","Frecuencia",\
                       "#Ot/Cli","Activo","Alerta","Desertor"]]

df_base10 = df_base9.copy()
df_base10["Gasto/Oc"] = (df_base10["$Ots"]/df_base10["#Ots"]).round(0)
df_base10 ["Descuento"] = ((df_base10["$LISTA"]/df_base10["$Ots"]-1)*100).round(0)
df_base10 = df_base10.round(0)
df_base10 = df_base10[["Cliente","$LISTA","$Ots","Descuento","#Ots","Gasto/Oc","#DiasPriUlt","Frequency","Frecuencia",\
                       "Recency","Factor","RangoFactor","Ciclo","Segment"]]
