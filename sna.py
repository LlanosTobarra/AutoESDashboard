# -*- coding: utf-8 -*-
from pandas import DataFrame,Series
import pandas.io.sql as psql
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json, io,db
import networkx as nx
from networkx.readwrite import json_graph

#############################################################################################################
def social_network():
    foros=db.mySQLConect("localhost","root","pfc2011","rita")
    msg= psql.frame_query('select * from message;', foros.db)
    edges=[]

    for idx,m in msg[msg.referedTo.notnull()].iterrows():
        sender=long(m['sender'])
        receiver=long(msg[msg.idMessage==m['referedTo']]['sender'])
        edges.append((sender,receiver))
    graph=nx.DiGraph()
    for (x,y) in edges:  
        graph.add_edge(x,y,weight=edges.count((x,y)))
        
    data=dict(nodes=graph.nodes(), edges=graph.edges())
    with io.open('C:/Users/Llanos/Documents/GitHub/AutoESDashboard/html/network.json', 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(data, ensure_ascii=False)))
#############################################################################################################

social_network()