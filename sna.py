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
#############################################################################################################
def social_network():
    foros=db.mySQLConect("localhost","root","pfc2011","rita")
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
    wedges=[(x,y,{"weight": edges.count((x,y))}) for (x,y) in edges]
    graph=nx.DiGraph()
    graph.add_edges_from(wedges)
        
    data=dict(nodes=graph.nodes(), edges=graph.edges())
    #data=json_graph.node_link_data(graph)
    with io.open('C:/Users/Llanos/Documents/GitHub/AutoESDashboard/html/data/network.json', 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(data, ensure_ascii=False)))
#############################################################################################################

social_network()