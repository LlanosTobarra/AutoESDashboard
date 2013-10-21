# -*- coding: utf-8 -*-
from pandas import DataFrame,Series
import pandas.io.sql as psql
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json, io,db
import networkx as nx
from networkx.readwrite import json_graph
from datetime import *
import community
#############################################################################################################
def social_network():
    foros=db.mySQLConect("localhost","root","lego","rita")
    msg= psql.frame_query('select * from message;', foros.db)
    edges=[]

    for idx,m in msg[msg.referedTo.notnull()].iterrows():
        if(m['date']<datetime.strptime('08/01/11', "%m/%d/%y").date()): 
            course='2010-2011'
        elif(m['date']<datetime.strptime('08/01/12', "%m/%d/%y").date()): 
            course='2011-2012'
            sender=long(m['sender'])
            receiver=long(msg[msg.idMessage==m['referedTo']]['sender'])
            edges.append((sender,receiver))
        else:
            course='2012-2013'
    graph=nx.DiGraph()
    for (x,y) in edges:
        if graph.edges().count((x,y))==0:
            graph.add_edge(x,y,weight= edges.count((x,y)))
    
    partition = community.best_partition(nx.Graph(graph))
    for n in partition.keys():
        graph.node[n]["group"]=partition[n]
    return graph   
#############################################################################################################
def gen_network_json(graph):

    data=dict(nodes=graph.nodes(data=True), edges=graph.edges(data=True))
    #data=json_graph.node_link_data(graph)
    with io.open('C:/Users/Llanos/Documents/GitHub/AutoESDashboard/html/data/network.json', 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(data, ensure_ascii=False)))
    
#############################################################################################################
def social_parameters():
    g=social_network()


    degree=DataFrame(nx.degree_centrality(g).values(),index=g.nodes(),columns=['degree'])
    #closeness=DataFrame(nx.closeness_centrality(g,normalized=True).values(),index=g.nodes(),columns=['closeness'])
    between=DataFrame(nx.betweenness_centrality(g,normalized=True).values(),index=g.nodes(),columns=['between'])
    eigen=DataFrame(nx.eigenvector_centrality(g).values(),index=g.nodes(),columns=['eigen'])
    clustering=DataFrame(nx.clustering(nx.Graph(g)).values(),index=g.nodes(),columns=['clustering'])

    #data=pd.merge(degree,pd.merge(between,pd.merge(eigen,clustering)))
    data=degree.join(between.join(eigen.join(clustering)))
    return data
############################################################################################################
computed_social=social_parameters()
