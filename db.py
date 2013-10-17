# -*- coding: utf-8 -*-
from pymongo import MongoClient
import MySQLdb as sql


"""
    Author: Llanos Tobarra
    Date: 08/10/2013
    Description: Clase encargada de conectarse a una base de datos MySQL y ejecutar consultas.
"""
class mySQLConect(object):
    """
        Constructor a partir de la URL que puede ser localhost, user que es el usuario,
        pwd que es la contraseña y schema que es la base de datos a la que nos conectamos.
    """
    def __init__(self,url,user,pwd,schema):
        self.db = sql.connect(url,user,pwd,schema)
        
    """
         Ejecuta la consulta q en la base de datos y devuelve los resultados. 
    """
    def query(self,q):
        cursor=self.db.cursor()
        cursor.execute(q)
        records=cursor.fetchall()
        cursor.close()
        return records
    
    """
        Cierra la conexión con la base de datos
    """
    def close(self):
        self.db.close()

"""
    Author: Llanos Tobarra
    Date: 08/10/2013
    Description: Clase encargada de conectarse a una base de datos Mongo, almacenar informacion y ejecutar consultas.
"""
class mongoConect(object):
   
    def __init__(self,db):
        self.client= MongoClient()
        self.db=self.client[db]
    
    def getAll(self,collection):
        coleccion=self.db[collection]
        return coleccion.find()
        
    def query(self,collection,field,value):
        coleccion=self.db[collection]
        return coleccion.find({field:value})
        
    def insert(self,collection,registro):
        coleccion=self.db[collection]
        coleccion.insert(registro)
        
    def update(self,collection,registro):
        colleccion=self.db[collection]
        colleccion.save(registro)
    
    def delete(self,collection,obj_id):
        colleccion=self.db[collection]
        colleccion.remove({"_id":obj_id})

