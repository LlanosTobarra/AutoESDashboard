# -*- coding: utf-8 -*-
from pandas import DataFrame,Series
import pandas.io.sql as psql
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import pylab
import db
from datetime import *
import networkx as nx
import vincent

########################################################################
"""
    Organización:
        1. Crear la tabla de usuarios unificando los diferentes hostnames. Usaremos el identificador del foro como identificador único del usuario.
        2. Procesar los eventos añadiendo el usuario único
        3. Añadir a los eventos los mensajes
"""
#######################################################################
def user_aggregation():
    #Conexión a la base de datos MySQL
    dashboard=db.mySQLConect("localhost","root","pfc2011","dashboard")
    foros=db.mySQLConect("localhost","root","pfc2011","rita")
    #Lectura de los nodos de autoes
    nodos= psql.frame_query('select * from nodes;', dashboard.db)
    #Lectura de los usuarios de los foros
    usuarios=psql.frame_query('select * from user;', foros.db)
    #Lista con los usuarios: luego habrá que insertarlos en Mongo pero primero hay que calcular correctamente
    final_users=[]
    #Listado de usuarios especiales, que tienen una asociación concreta
    personal_rel=[(5,8),(1,25),(1,42),(9,15),(11,31),(6,47),(7,10),(7,41),(13,22),(14,77),(12,9),(15,11),(20,34),(23,45),(23,35),(24,36),(38,38)]
    #Para cada usuario de los foros
    for idx,user in usuarios.iterrows():
        #Calculamos un posible hostname y lo buscamos en la tabla
        hostname=user['name'].lower().split()[0][0]+user['name'].lower().split()[1].encode()
        autoes_user=nodos[nodos['name'].str.contains(hostname)]
        #Si lo hemos encontrado
        if len(autoes_user)>0:
            for idx,au in autoes_user.iterrows():
                if(au['created_at'].date()<datetime.strptime('08/01/11', "%m/%d/%y").date()): 
                    course='2010-2011'
                elif(au['created_at'].date()<datetime.strptime('08/01/12', "%m/%d/%y").date()): 
                    course='2011-2012'
                else:
                    course='2012-2013'
                new_user={"code":au['id'], "user":user['iduser'], "name":user['name'], "host":au['name'], "course":course}
                final_users.append(new_user)
        #usuarios cuyo nombre no es regular: los hemos buscado a mano :(
        elif user['iduser'] in (x[0] for x in personal_rel):
            hosts=[(x,y) for (x,y) in personal_rel if x == user['iduser']]
            for host in hosts:
                au=nodos[nodos.id==host[1]].iloc[0]
                if(au['created_at'].date()<datetime.strptime('08/01/11', "%m/%d/%y").date()): 
                    course='2010-2011'
                elif(au['created_at'].date()<datetime.strptime('08/01/12', "%m/%d/%y").date()): 
                    course='2011-2012'
                else:
                    course='2012-2013'
                code=long(au['id'])
                host=au['name']
                new_user={"code":code, "user":user['iduser'], "name":user['name'], "host":host, "course":course}
                final_users.append(new_user)
        #Sino
        else:
            new_user={"code":None, "user":user['iduser'], "name":user['name'], "host":None, "course": None}
            final_users.append(new_user)
    #Adaptaciones personales
    users_frame=DataFrame(final_users)
    return users_frame 
#############################################################################################################
def event_aggregation(users):
    #Lista de eventos
    json_node_events=[]
    #conexión a la base de datos local
    conexion=db.mySQLConect("localhost","root","pfc2011","dashboard")
    #events+reports
    query="SELECT dashboard.reports.id as report_id,dashboard.timeline_events.id as event_id, dashboard.reports.node_id,dashboard.reports.status, dashboard.reports.time FROM dashboard.reports,dashboard.timeline_events where timestampdiff(MINUTE,dashboard.timeline_events.updated_at,dashboard.reports.time)<=3 AND  dashboard.reports.time>=dashboard.timeline_events.updated_at AND node_id=subject_id AND event_type='updated';";
    er=psql.frame_query(query,conexion.db)
    #Para todos los nodos que poseen un nombre de host asociado
    for idx,u in users[users.host.notnull()].iterrows():
        #variables para rellenar el registro
        nid=u['code']
        user=u['user']
        host=u['host']
        course=u['course']
        #busco en la base de datos los eventos relacionados con ese codigo de autoes
        query="SELECT * FROM timeline_events WHERE (subject_id ="+str(nid)+" AND subject_type='Node') OR (secondary_subject_id="+str(nid)+");"
        node_events=psql.frame_query(query,conexion.db)
        #siempre el alumno empieza en la práctica 1
        current_practice=1
        #para cada evento encontrado
        for idx,event in node_events.iterrows():    
            #Evento de creación del usuario de autoes
            if event['event_type']=="created":
                register_event={ "user":user, "course":course,"host":host,"type":"created","report":None,"practice":current_practice, "date":event['created_at']}
                json_node_events.append(register_event)
            #Evento de moverse de práctica
            elif event['event_type']=="added_to":
                #si solo avanza una práctica
                if(current_practice+1==event['subject_id']):
                    register_event={ "user":user,"course":course,"host":host, "type":"added_to","report":None,"practice":event['subject_id'], "date":event['created_at']}
                    current_practice=event['subject_id']
                    json_node_events.append(register_event)
                #si avanza varias practicas a la vez
                else:
                    for i in range(current_practice,event['subject_id']+1):
                        register_event={ "user":user,"course":course,"host":host, "type":"added_to","report":None,"practice":i, "date":event['created_at']}
                        json_node_events.append(register_event)           
                    current_practice=event['subject_id']   
            #Evento updated: significa o bien login, o bien evaluación correcta o bien evaluación fallida
            elif event['event_type']=="updated":     
                #buscamos el informe
                report_event=er[er.event_id==event['id']]
                #para cada informe posible
                for idx2,report in report_event.iterrows():
                    register_event={ "user":user,"course":course,"host":host, "type":report['status'],"report":report['report_id'],"practice":current_practice, "date":event['created_at']}
                    json_node_events.append(register_event)
            #Evento para salir de una práctia
            elif event['event_type']=="removed_from":
                register_event={ "user":user, "course":course,"host":host, "type":"removed_from","report":None,"practice":event['subject_id'], "date":event['created_at']}
                json_node_events.append(register_event)
            #evento de borrado de la plataforma: muy raro
            elif event['event_type']=="removed":
                register_event={ "user":user, "course":course,"host":host,"type":"removed","report":None,"practice":current_practice, "date":event['created_at']}
                json_node_events.append(register_event)

    events_frame=DataFrame(json_node_events)
    return events_frame

#############################################################################################################
def message_aggregation(users,events):
    foros=db.mySQLConect("localhost","root","pfc2011","rita")
    msg= psql.frame_query('select * from message;', foros.db)
    list_messages=[]
    for idx, m in msg.iterrows():
        if(m['date']<datetime.strptime('08/01/12', "%m/%d/%y").date()): 
            course='2011-2012'
        else:
            course='2012-2013'
        #Si es un usuario del sistema
        u=users[users.user==m['sender']]
        if len(u)>0:
            nid=m['sender']
            host=None
            date=datetime(m['date'].year, m['date'].month, m['date'].day)
            if m['referedTo']>=0:
                register_event={ "user":nid, "course":course,"host":host,"type":"response_to","report":long(m['idMessage']),"practice":None, "date":date}
                list_messages.append(register_event)
            else:
                register_event={ "user":nid, "course":course,"host":host,"type":"message_init","report":long(m['idMessage']),"practice":None, "date":date}
                list_messages.append(register_event)
    messages=DataFrame(list_messages)
    all_events=pd.concat([events,messages])
    return all_events
#############################################################################################################
def message_info_aggregation():
    foros=db.mySQLConect("localhost","root","pfc2011","rita")
    msg= psql.frame_query('select * from message;', foros.db)
    list_messages=[]

    
#############################################################################################################
def social_network():
    foros=db.mySQLConect("localhost","root","pfc2011","rita")
    msg= psql.frame_query('select * from message;', foros.db)
    edges=[]

    for idx,m in msg[msg.referedTo.notnull()].iterrows():
        sender=long(m['sender'])
        receiver=long(msg[msg.idMessage==m['referedTo']]['sender'])
        edges.append((sender,receiver))
    wedges=[(x,y,{"weight":edges.count((x,y))}) for (x,y) in edges]
    graph=nx.DiGraph()
    graph.add_edges_from(wedges)


#############################################################################################################
#Conexión a la base de datos de mongo

#users
users=user_aggregation()
events=event_aggregation(users)
all_events=message_aggregation(users,events)


#Eventos por alumno y tipo de evento
events=all_events.groupby(['user','type']).count()['course'].unstack()
events=events.fillna(value=0)
#Gráfica: events.plot(kind='bar',stacked=True)

stack = vincent.StackedBar(events)
stack.axis_titles(x='Users', y='Events')
stack.legend(title='Types of Events')
stack.colors(brew='Spectral')
stack.to_json('C:/Users/Llanos/Dropbox SCC/Dropbox/Cositas/lak 2014/python/LAK2014/html/events.json')

#Fallos por practica y alumno
fails=all_events[all_events.type=='failed']
fails['date'] = fails['date'].apply(lambda x: x.strftime('%d/%m/%Y'))
pfails=fails.groupby(['user','practice']).count()['report'].unstack()
pfails=pfails.fillna(value=0)
#Grafica: pfails.plot(kind='bar',stacked=True)
stack = vincent.StackedBar(pfails)
stack.axis_titles(x='Users', y='Failed evaluations')
stack.legend(title='Practice')
stack.colors(brew='Spectral')
stack.to_json('C:/Users/Llanos/Dropbox SCC/Dropbox/Cositas/lak 2014/python/LAK2014/html/fails.json')

#Exitos por practica y alumno
success=all_events[all_events.type=='changed']
success['date'] = success['date'].apply(lambda x: x.strftime('%d/%m/%Y'))
psuccess=success.groupby(['user','practice']).count()['report'].unstack()
psuccess=psuccess.fillna(0)
stack = vincent.StackedBar(psuccess)
stack.axis_titles(x='Users', y='Succesfull evaluations')
stack.legend(title='Practice')
stack.colors(brew='Set2')
stack.to_json('C:/Users/Llanos/Dropbox SCC/Dropbox/Cositas/lak 2014/python/LAK2014/html/success.json')



#Grafica: psuccess.plot(kind='bar',stacked=True)