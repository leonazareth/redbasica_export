# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QEsg_08Profiler
                                 A QGIS plugin
 Plugin para Calculo de redes de esgotamento sanitario
                              -------------------
        begin                : 2020-07-06
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Jorge Almerio
        email                : jorgealmerio@yahoo.com.br
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import absolute_import
from builtins import object
from qgis.core import *
from qgis.PyQt.QtWidgets import QMessageBox, QDialog, QDialogButtonBox ,QVBoxLayout, QCheckBox, QLabel
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.utils import *
import os.path
from .QEsg_00Model import *
from qgis.gui import QgsMessageBar, QgsMapLayerComboBox, QgsVertexMarker, QgsMapToolIdentify
from .QEsg_04Estilos import *
from .QEsg_00Common import *
import math
'''
Pegar o shape com a rede
Juntar a geometria das linhas em um polilinha
Pegar o MDT definido nas configurações ou manter o perfil do terreno como está (somente PVs e interferencias)
Verificar se o MDT é raster ou Mesh
Calcular a dist, cota
'''
class QEsg_08Profiler(object):
    common=QEsg_00Common()
    SETTINGS = common.SETTINGS
    def profile(self, layer, request, mdtLyr, resolution=1., ds_group_index=0, ds_index=0):        
        first=True
        for feat in layer.getFeatures(request):
            if first:
                geoUnida=feat.geometry()
                first=False
            else:
                geoUnida= geoUnida.combine(feat.geometry())
        if mdtLyr.type() == mdtLyr.MeshLayer:
            return self.profile_feature_fromMesh(geoUnida, mdtLyr, resolution, ds_group_index, ds_index)
        else: #Raster Layer
            return self.profile_feature_fromRaster(geoUnida, mdtLyr, resolution)
        #self.CriaTempLayer(geoUnida)
    
    #def faceToEdge(self):
    
    #def getMeshEdges(self):
    
    #NOT IN USE
    #Cria um layer temporario
    def CriaTempLayer(self, geometria):
        curSrc = iface.mapCanvas().mapSettings().destinationCrs().authid()
        tipoStr = "LineString?crs="+curSrc
        lineLayer = QgsVectorLayer(tipoStr, 'TuboUnido', "memory")
        
        feat = QgsFeature()
        feat.setGeometry(geometria)
        lineLayer.dataProvider().addFeature(feat)
        QgsProject.instance().addMapLayer(lineLayer)
    
    def get_mesh_geometry(self, mesh, index):
        face = mesh.face(index)
        points = [mesh.vertex(v) for v in face]
        polygon = QgsPolygon()
        polygon.setExteriorRing(QgsLineString(points))
        return QgsGeometry(polygon)
    
    #Returns a point VectorLayer with polyline (geometry) and mesh edges intersections
    #Uses get_mesh_geometry
    def Mesh_Intersections(self, geometry, mesh):
        import processing
        meshSpIndex = QgsMeshSpatialIndex(mesh)
        intFaces = meshSpIndex.intersects(geometry.boundingBox())
        
        canvas = iface.mapCanvas()
        curSrc = canvas.mapSettings().destinationCrs().authid()
        tipoStr = "Polygon?crs="+curSrc
        pollyr = QgsVectorLayer(tipoStr, 'Malha', "memory")
        
        tipoStr = "LineString?crs="+curSrc
        pipeLyr = QgsVectorLayer(tipoStr, 'TrechoRede', "memory")
        selFeat = QgsFeature()
        selFeat.setGeometry(geometry)
        pipeLyr.dataProvider().addFeature(selFeat)
        
        '''
        for face in intFaces:
            face = mesh.face(index)
            for v in face:
                points = [mesh.vertex(v) for v in face]                
                QgsGeometry
        '''

        for id in intFaces:
            meshPol = self.get_mesh_geometry(mesh,id)
            if meshPol.intersects(geometry):
                feat = QgsFeature()
                feat.setGeometry(meshPol)
                pollyr.dataProvider().addFeature(feat)
            
        pol2lines = processing.run("qgis:polygonstolines", {'INPUT':pollyr,'OUTPUT':'memory:'})["OUTPUT"]
        explodLines = processing.run("qgis:explodelines", {'INPUT':pol2lines,'OUTPUT':'memory:'})["OUTPUT"]
        uniqueLines = processing.run("qgis:deleteduplicategeometries", {'INPUT':explodLines,'OUTPUT':'memory:'})["OUTPUT"]
        ptosInt = processing.run("qgis:lineintersections", {'INPUT':pipeLyr,'INTERSECT':uniqueLines,'OUTPUT':'memory:'})["OUTPUT"]
        return ptosInt
    
    # Return Dist and elevation given a Polyline (geometry) and a Mesh MDT (layer)
    # Uses Mesh_Intersections
    def profile_feature_fromMesh(self, geometry, layer, resolution=1., ds_group_index=0, ds_index=0):
        """ return array with tuples defining X,Y points for plot """
        x,y = [], []
        if not layer:
            return x, y
            
        layer.createMapRenderer(QgsRenderContext())
        
        dp=layer.dataProvider()
        dataset = QgsMeshDatasetIndex(ds_group_index, ds_index)
        length = geometry.length()
        
        #if mesh has faces uses it to get elevation only on intersection points with polyline
        if dp.contains(QgsMesh.Face):
            QgsMessageLog.logMessage('Profiler using mesh faces intersections','QEsg_08Profiler',level=Qgis.Info)
            # get mesh faces within geometry extents
            # get mesh faces that intersects polyline geometry
            # get edges that intersects polyline geometry
            # get intersections between edges and polyline geometry
            # get polylines vertices
            # identifica e ordena os pontos pela localização na linha (ex.: Qgsgeometry.lineLocatePoint(Qgsgeometry &point))
            # captura a elevação dos pontos
            
            mesh = QgsMesh()
            dp.populateMesh(mesh) 
            ptosInt = self.Mesh_Intersections(geometry, mesh)
            
            # add polyline vertices too
            if geometry.isMultipart():
                vertices = geometry.asMultiPolyline()[0]
                QgsMessageLog.logMessage(u'Multiparte encontrada, apenas a primeira será usada! verifique a topologia da rede!','QEsg_08Profiler',level=Qgis.Warning)                
            else:
                vertices = geometry.asPolyline()
            for vert in vertices:
                ptoFeat = QgsFeature()
                ptoFeat.setGeometry(QgsGeometry(QgsPoint(vert[0],vert[1],0)))
                ptosInt.dataProvider().addFeature(ptoFeat)
               
            #self.CriaTempLayer(geometry)
            #QgsProject.instance().addMapLayer(ptosInt)
            
            parXY = []
            for feat in ptosInt.getFeatures():
                ptoGeo = feat.geometry()
                posAlong = geometry.lineLocatePoint(ptoGeo)
                value = layer.datasetValue(dataset, ptoGeo.asPoint()).scalar()
                parXY.append([posAlong,value])            
            
            #sort by posAlong (first column, index 0)
            parXY.sort(key=lambda x: x[0])
            for pto in parXY:
                x.append(pto[0])
                y.append(pto[1])
        else:
            QgsMessageLog.logMessage('Profiler using mesh with fixed distance: {} m'.format(resolution),'QEsg_08Profiler',level=Qgis.Info)
            offset = 0            
            while offset < length:
                pt = geometry.interpolate(offset).asPoint()
                value = layer.datasetValue(dataset, pt).scalar()
                x.append(offset)
                y.append(value)
                offset += resolution

            # let's make sure we include also the last point
            if geometry.isMultipart():
                last_pt = geometry.asMultiPolyline()[0][-1]
            else:
                last_pt = geometry.asPolyline()[-1]
            last_value = layer.datasetValue(dataset, last_pt).scalar()
            x.append(length)
            y.append(last_value)

        return x, y

    # Return Dist and elevation given a Polyline and a Raster MDT
    def profile_feature_fromRaster(self, geometry, layer, resolution=1., band=1):
        """ return array with tuples defining X,Y points for plot """
        x,y = [], []
        if not layer:
            return x, y
        #Get and use full raster resolution
        resolution = min(layer.rasterUnitsPerPixelX(), layer.rasterUnitsPerPixelY())
        offset = 0
        length = geometry.length()
        while offset < length:
            pt = geometry.interpolate(offset).asPoint()
            value = layer.dataProvider().identify(pt, QgsRaster.IdentifyFormatValue).results()[band]
            x.append(offset)
            y.append(value)
            offset += resolution

        # let's make sure we include also the last point
        last_pt = geometry.asPolyline()[-1]
        last_value = layer.dataProvider().identify(last_pt, QgsRaster.IdentifyFormatValue).results()[band]
        x.append(length)
        y.append(last_value)

        return x, y

    #NOT IN USE    
    def testeConsole(self):
        proj = QgsProject.instance()
        layer = proj.mapLayersByName("RA04A_Elevacoes_Proj")[0]
        MDT_lyr = proj.mapLayersByName("PqVerde_mesh")[0]
        coletor = 1