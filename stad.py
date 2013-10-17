# -*- coding: utf-8 -*-
from pandas import DataFrame,Series
import pandas.io.sql as psql
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import agg2, json, pylab, vincent
import networkx as nx
from datetime import *
##################################################################################
#users
users=agg2.user_aggregation()
events=agg2.event_aggregation(users)
all_events=agg2.message_aggregation(users,events)
###################################################################################
#Fechas y eventos
devents=all_events
devents['date'] = devents['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
devents=devents.groupby(['date','user'])['type']
f = open('C:/Users/Llanos/Documents/GitHub/AutoESDashboard/html/calendar.csv', 'w')
f.write("Date,User,Type\n")
for idx,m in devents:
    f.write(str(idx[0])+","+str(idx[1])+","+m.values[0]+"\n")
f.close()
##################################################################################
#Eventos por alumno y tipo de evento
gevents=all_events.groupby(['user','type']).count()['course'].unstack()
gevents=events.fillna(value=0)
#Gráfica: events.plot(kind='bar',stacked=True)
stack = vincent.StackedBar(gevents)
stack.axis_titles(x='Users', y='Events')
stack.legend(title='Types of Events')
stack.colors(brew='Spectral')
stack.to_json('C:/Users/Llanos/Documents/GitHub/AutoESDashboard/html/events.json')
##################################################################################
#Fallos por practica y alumno
fails=all_events[all_events.type=='failed']
pfails=fails.groupby(['user','practice']).count()['report'].unstack()
pfails=pfails.fillna(value=0)
#Grafica: pfails.plot(kind='bar',stacked=True)
stack = vincent.StackedBar(pfails)
stack.axis_titles(x='Users', y='Failed evaluations')
stack.legend(title='Practice')
stack.colors(brew='Spectral')
stack.to_json('C:/Users/Llanos/Documents/GitHub/AutoESDashboard/html/fails.json')
##################################################################################
#Exitos por practica y alumno
success=all_events[all_events.type=='changed']
psuccess=success.groupby(['user','practice']).count()['report'].unstack()
psuccess=psuccess.fillna(0)
stack = vincent.StackedBar(psuccess)
stack.axis_titles(x='Users', y='Succesfull evaluations')
stack.legend(title='Practice')
stack.colors(brew='Set2')
stack.to_json('C:/Users/Llanos/Documents/GitHub/AutoESDashboard/html/success.json')
##################################################################################