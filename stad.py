# -*- coding: utf-8 -*-
from pandas import DataFrame,Series
import pandas.io.sql as psql
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import agg2, json, pylab, vincent,sna
import networkx as nx
from datetime import *
##################################################################################
#users
users=agg2.user_aggregation()
events=agg2.event_aggregation(users)
all_events=agg2.message_aggregation(users,events)
###################################################################################

#Fechas y eventos
def gen_calendar(events):
    devents=events
    devents['date'] = devents['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
    devents=devents.groupby(['date','user'])['type']
    f = open('C:/Users/Llanos/Documents/GitHub/AutoESDashboard/html/data/calendar.csv', 'w')
    f.write("Date,User,Type\n")
    for idx,m in devents:
        f.write(str(idx[0])+","+str(idx[1])+","+m.values[0]+"\n")
    f.close()
##################################################################################
#Eventos por alumno y tipo de evento
def gen_events(events):
    gevents=events.groupby(['user','type']).count()['course'].unstack()
    #Gráfica: events.plot(kind='bar',stacked=True)
    stack = vincent.StackedBar(events.groupby(['user','type']).count()['course'].unstack().fillna(0))
    stack.axis_titles(x='Users', y='Events')
    stack.legend(title='Types of Events')
    stack.colors(brew='Spectral')
    stack.to_json('C:/Users/Llanos/Documents/GitHub/AutoESDashboard/html/data/events.json')
##################################################################################
#Fallos por practica y alumno
def gen_fails(events):
    fails=events[all_events.type=='failed']
    pfails=fails.groupby(['user','practice']).count()['report'].unstack()
    pfails=pfails.fillna(value=0)
    compare=pfails.describe().unstack()
    value=[]
    for (p,us),u in pfails.unstack().iteritems():
        zscore=(u-compare.ix[p]['mean'])/compare.ix[p]['std']
        value.append([us,p,zscore])
    data=DataFrame(value,columns=['user','practice','fail'])
    #Grafica: pfails.plot(kind='bar',stacked=True)
    stack = vincent.StackedBar(pfails)
    stack.axis_titles(x='Users', y='Failed evaluations')
    stack.legend(title='Practice')
    stack.colors(brew='Spectral')
    stack.to_json('C:/Users/Llanos/Documents/GitHub/AutoESDashboard/html/data/fails.json')
    return data
##################################################################################
def gen_success(events):
    #Exitos por practica y alumno
    success=events[all_events.type=='changed']
    psuccess=success.groupby(['user','practice']).count()['report'].unstack()
    psuccess=psuccess.fillna(0)
    compare=psuccess.describe().unstack()
    value=[]
    for (p,us),u in psuccess.unstack().iteritems():
        zscore=(u-compare.ix[p]['mean'])/compare.ix[p]['std']
        value.append([us,p,zscore])
    data=DataFrame(value,columns=['user','practice','success'])
    stack = vincent.StackedBar(psuccess)
    stack.axis_titles(x='Users', y='Succesfull evaluations')
    stack.legend(title='Practice')
    stack.colors(brew='Set2')
    stack.to_json('C:/Users/Llanos/Documents/GitHub/AutoESDashboard/html/data/success.json')
    return data
##################################################################################
def practice_periods(events):
    tevents=events[events.type=='added_to']
    tevents['date'] = tevents['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
    tevents=tevents.groupby(['user','practice'])['date']
    starting_times=all_events[all_events.type=="created"][['user','date']]
    starting_times['date'] = starting_times['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
    last_report=all_events.groupby('user').max()[['practice','date']]
    last_report['date'] = last_report['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
    ranges=[]
    for  (user,practice),date in tevents:
        if practice==1:
            init=starting_times[starting_times.user==user]['date'].values[0]
        else:
            init=date.values[0]
        if practice==last_report.ix[user]['practice']:
            end=last_report.ix[user]['date']
        else:
            end=tevents.values[(user,practice+1)][0]
            
        days=(datetime.strptime(end, "%Y-%m-%d").date()-datetime.strptime(init, "%Y-%m-%d").date()).days
        ranges.append([user,practice,init,end,days])
    
    data=DataFrame(ranges,columns=['user','practice','init','ends','days'])
    return data
################################################################################  
def days_parameter(table):
    compare=table.groupby('practice')['days'].describe()
    values=[]
    for idx,data in table.iterrows():
        zscore=(data['days']-compare.ix[data['practice']]['mean'])/compare.ix[data['practice']]['std']
        values.append([data['user'],data['practice'],zscore])
    return DataFrame(values,columns=['user','practice','days'])
##################################################################################
computed_fails=gen_fails(all_events)
computed_success=gen_success(all_events)

table_delay=practice_periods(all_events)
computed_delays=days_parameter(table_delay)
computed_social=sna.social_parameters()

parameter=pd.merge(computed_delays,pd.merge(computed_fails,computed_success))

global_parameter=parameter.groupby('user')[['days','fail','success']].mean()
global_parameter=computed_social.join(global_parameter).fillna(0)
global_parameter=global_parameter.drop(['user'],1)
#Elimino los negativos
global_parameter['days']=global_parameter['days'].apply(lambda x: x+(-1*global_parameter['days'].min()))
global_parameter['fail']=global_parameter['fail'].apply(lambda x: x+(-1*global_parameter['fail'].min()))
global_parameter['success']=global_parameter['success'].apply(lambda x: x+(-1*global_parameter['success'].min()))

#cambio de escala
for c in global_parameter.columns:
    global_parameter[c]=global_parameter[c].apply(lambda x: int(math.floor(x*10/global_parameter[c].max())))
    
data=[]
for idx,v in global_parameter.iterrows():
    item={"user":idx, "parameter":1, "value":v['degree']}
    data.append(item)
    item={"user":idx, "parameter":2, "value":v['between']}
    data.append(item)
    item={"user":idx, "parameter":3, "value":v['eigen']}
    data.append(item)
    item={"user":idx, "parameter":4, "value":v['clustering']}
    data.append(item)
    item={"user":idx, "parameter":5, "value":v['days']}
    data.append(item)
    item={"user":idx, "parameter":6, "value":v['fail']}
    data.append(item)
    item={"user":idx, "parameter":7, "value":v['success']}
    data.append(item)
csv=DataFrame(data,columns=['user','parameter','value'])
csv.to_csv("C:/Users/Llanos/Documents/GitHub/AutoESDashboard/html/data/data.csv");

