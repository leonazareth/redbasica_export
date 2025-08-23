# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QEsg_20ImportaSancad_DXF
                                 A QGIS plugin
 Plugin para Calculo de redes de esgotamento sanitario
                              -------------------
        begin                : 2016-03-15
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
from builtins import str
from builtins import object
from qgis.core import *
from qgis.PyQt.QtWidgets import QMessageBox, QFileDialog
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.utils import *
import os.path
from .QEsg_01Campos import *
from osgeo import ogr
import math, re
from .QEsg_04Estilos import *
from .QEsg_00Common import *
#from QEsg_00Model import *


UsrAppId='NUMEROTRE' #appid for DXF extended data
class QEsg_20Sancad(object):
    common=QEsg_00Common()
    goExec = True
    def onCancelButton(self):
        self.goExec=False
    def ImportDxf_Lib(self):
        try:
            from .addon import ezdxf as dxf
            #QgsMessageLog.logMessage('ezdxf imported without need of change PATH variable',ClassName) 
        except ImportError:
            self.dirname, filename = os.path.split(os.path.abspath(__file__))
            addonPath = os.path.join(self.dirname,'addon')
            sys.path.append(addonPath)
            import ezdxf as dxf
            QgsMessageLog.logMessage('ezdxf imported, but PATH variable had to be changed',self.__class__.__name__)#,level=QgsMessageLog.CRITICAL
        # self.dirname, filename = os.path.split(os.path.abspath(__file__))
        # sys.path.append(self.dirname)

        self.dxf=dxf
    def ImportaDXF(self):
        global UsrAppId
        proj = QgsProject.instance()
        baseName=proj.readPath("./")
        nome_arquivo, __=QFileDialog.getOpenFileName(caption=QCoreApplication.translate('QEsg',u'Abrir o arquivo DXF da rede SANCAD:'),
                                                 filter="AutoCAD DXF (*.dxf *.DXF)")
        if not nome_arquivo:
            #iface.messageBar().pushMessage('QEsg',QCoreApplication.translate('QEsg',u'Operação cancelada!'),level=Qgis.Warning, duration=3)
            return
        
        dxf_output_filename = os.path.splitext(os.path.basename(nome_arquivo))[0] 
        
        #Inicializa a classe ezdxf e suas variaveis principais
        self.ImportDxf_Lib()
        dxf=self.dxf
        doc = dxf.readfile(nome_arquivo)
        msp = doc.modelspace()
        
        #for use extended data
        try:
            from ezdxf.lldxf.types import DXFTag
            #QgsMessageLog.logMessage('DXFTag imported',self.__class__.__name__,level=Qgis.Info)
        except ImportError:
            QgsMessageLog.logMessage('DXFTag not imported',self.__class__.__name__,level=Qgis.Warning)
            
        #Pega o crs do Projeto atual        
        destCrs=iface.mapCanvas().mapSettings().destinationCrs()
        crsAuthID = destCrs.authid()
        
        #s=QSettings()
        #Userconfig=s.value("/Projections/defaultBehavior",'prompt')
        #s.setValue('/Projections/defaultBehavior', 'useProject')
        
        success = False
        hasPVs = False
        missingLayers=[]
        emptyLayers=[]
        PVLayer='SANC_PV'
        # check for existing PV layer definition
        cont=0
        if PVLayer in doc.layers:            
            qryStr = '*[layer=="'+PVLayer+'"]'
            DxfPVsquery = msp.query(qryStr)
            queryCount = DxfPVsquery.__len__()
            QgsMessageLog.logMessage(QCoreApplication.translate('QEsg',u'Nro de elementos em SANC_PV: {}').format(queryCount), 
                    self.__class__.__name__, Qgis.Info)
            if queryCount>0:
                hasPVs = True
                
                #Inicia a progress bar
                msg = QCoreApplication.translate('QEsg','Importando os PVs do Sancad dxf...')
                progress,progressMBar,cancelButton=self.common.startProgressBar(msg)
                cancelButton.clicked.connect(self.onCancelButton)
                
                #Cria um layer de pontos temporario e cria um ponto no centro da polilinha (circulo do PV) que representa um PV
                vPVs = QgsVectorLayer("Point"+'?crs='+crsAuthID, "PVs", "memory")
                prPVs=vPVs.dataProvider()
                feat = QgsFeature()                
                for e in DxfPVsquery:
                    insPto = e.dxf.insert
                    #geom=QgsGeometry.fromPoint(insPto) #feat.geometry().centroid()
                    geom=QgsGeometry(QgsPoint(insPto[0],insPto[1]))#,insPto[2]))
                    feat.setGeometry(geom)
                    vPVs.updateFeature(feat)
                    prPVs.addFeatures([feat])

                    #update progressBar
                    cont+=1
                    percent = int((cont/float(queryCount*2)) * 100) #o total aqui corresponde a 50% do processo
                    progress.setValue(percent)
                    QApplication.processEvents()
                #end for
                
                spIndex = QgsSpatialIndex() #create spatial index object        
                PViterator=vPVs.getFeatures()#
                # insert features to index
                while PViterator.nextFeature(feat):
                    spIndex.insertFeature(feat)
                
            else:
                emptyLayers.append(PVLayer) #Layer sem elementos
        else:
            missingLayers.append(PVLayer)
            #QgsMessageLog.logMessage(QCoreApplication.translate('QEsg',u'Layer: \'{}\' não encontrado no arquivo DXF!').format(PVLayer), 
            #    self.__class__.__name__, Qgis.Warning)        

        #Cria um layer temporario (PIPES)
        vPipes = QgsVectorLayer("MultiLineString"+'?crs='+crsAuthID, dxf_output_filename, "memory")
        prPipes=vPipes.dataProvider()
        
        #Cria os campos padroes sem perguntar
        CamposClasse=QEsg_01Campos()
        CamposClasse.CriaCampos('PIPES',vPipes, SilentRun=True)
        
        RedeEtapa={'SANC_REDE':1,'SANC_REDE2T':2, 'SANC_REDEEXIST':0}              
        # check for existing Pipe layer definition
        for pipeLayer in RedeEtapa:
            if pipeLayer in doc.layers:
                Dxfquery = msp.query('*[layer=="'+pipeLayer+'"]')                
                queryCount = Dxfquery.__len__()
                QgsMessageLog.logMessage(QCoreApplication.translate('QEsg',u'Nro de elementos em {0}: {1}').format(pipeLayer,queryCount), 
                        self.__class__.__name__, Qgis.Info)
                if queryCount>0:
                    success = True
                    
                    #Se nao tinha PVs entao a progressBar ainda nao fora iniciada
                    msg = QCoreApplication.translate('QEsg','Importando os tubos do Sancad dxf...')
                    if not hasPVs:                
                        #Inicia a progress bar                        
                        progress,progressMBar,cancelButton=self.common.startProgressBar(msg)
                        cancelButton.clicked.connect(self.onCancelButton)
                    else:
                        progressMBar.setText(msg)
                    totalCont=cont+queryCount                    
                    
                    for e in Dxfquery:
                        p1 = e.dxf.start
                        startPto = QgsPoint(p1[0],p1[1],p1[2])
                        p2 = e.dxf.end
                        endPto = QgsPoint(p2[0],p2[1],p2[2])
                        aGeo=QgsGeometry.fromPolyline([startPto,endPto])
                        ctm= startPto.z() #float(pontos3D[0][2]) #geom_wkb.GetZ() #aPolilinha[0].x()
                        ctj= endPto.z() #float(pontos3D[1][2]) #aGeo.vertexAt(1)
                        
                        # add a feature
                        feat = QgsFeature(vPipes.fields())
                        # https://ezdxf.readthedocs.io/en/master/dxfentities/dxfentity.html
                        if e.has_xdata(UsrAppId):
                            elemXData = e.get_xdata(UsrAppId)
                            XDataTags=[] # [DC_ID,PVM,Pavimento,Bilateral]  
                            for tag in elemXData: #.__iter__()
                                XDataTags.append(tag[1])                                
                            dcid=XDataTags[0] #XDataTags[0] = 'Coletor-Trecho'
                            #strPos1=XDataTags[0].find('-')
                            colTre = re.findall(r"\d+", dcid) #[Coletor, Trecho] # list without any strings
                            pvm=XDataTags[1] #PV de montante
                            pav=XDataTags[2] #Pavimento, ex:ASFALTO, TERRENO NATURAL
                            Bilateral=XDataTags[3] #Sim=Bilateral;Uni=Unilateral;Nao=Sem contribuicao
                            if Bilateral=='SIM':
                                contrlado=2
                            elif Bilateral=='UNI':
                                contrlado=1
                            elif Bilateral=='NAO':
                                contrlado=0
                            else:
                                contrlado=2
                            coletor=int(colTre[0]) #first number
                            trecho=int(colTre[-1]) #last number

                            feat.setGeometry(aGeo)
                            feat['Coletor']=coletor
                            feat['Trecho']=trecho
                            feat['DC_ID']=dcid
                            feat['PVM']=pvm
                            feat['CONTR_LADO']=contrlado
                            
                        else: #if has no Xdata
                            noXdataElem = True                            

                        if hasPVs: #Se tiver PVs verfica se os pipes precisam ser estendidos e se sao ponta seca
                            # QgsSpatialIndex.nearestNeighbor (QgsPoint point, int neighbors)
                            startPtoGeo=QgsGeometry(startPto)
                            nearestIds = spIndex.nearestNeighbor(startPtoGeo,1) # we need only one neighbour
                            featureId = nearestIds[0]
                            #print startPto,featureId
                            fit2 = vPVs.getFeatures(QgsFeatureRequest().setFilterFid(featureId))
                            ftr = QgsFeature()
                            fit2.nextFeature(ftr)
                            pvProx=ftr.geometry().asPoint() #asPolyline()[0]
                            #setup distance
                            distance = QgsDistanceArea()
                            #get distance
                            #dist = distance.measureLine(startPtoGeo, pvProx)
                            point1=startPto
                            point2=pvProx
                            dist = math.sqrt((point2.x()-point1.x())**2 + (point2.y()-point1.y())**2)
                            if dist>3:
                                pontaseca='S'
                                #estende trecho ponta seca para montante
                                aGeo=self.ExtendToMont(aGeo, dist=4)
                            else:
                                pontaseca='N'
                        else:
                            pontaseca='N'
                        
                        #Pega a Etapa de acordo com o layer que se encontra
                        oLayer=e.dxf.layer
                        etapa=RedeEtapa[oLayer]
                        
                        feat['ETAPA']=etapa
                        feat['PONTA_SECA']=pontaseca
                        feat['CTM']=ctm
                        feat['CTJ']=ctj
                        feat.setGeometry(aGeo)
                        vPipes.updateFeature(feat)
                        prPipes.addFeatures([feat])
                    
                        #update progressBar
                        cont+=1
                        percent = int((cont/float(totalCont)) * 100)
                        progress.setValue(percent)
                        QApplication.processEvents()
                    #end for
                else:
                    emptyLayers.append(pipeLayer) #Nenhum elemento no Layer
            else:
                missingLayers.append(pipeLayer) #Layer não encontrado no arquivo
        #end for RedeEtapa = {'SANC_REDE':1,'SANC_REDE2T':2, 'SANC_REDEEXIST':0}
        if hasPVs:
            del vPVs
        if missingLayers:
            QgsMessageLog.logMessage(QCoreApplication.translate('QEsg',u'Layers ausentes: \'{}\'').format(missingLayers), 
                    self.__class__.__name__, Qgis.Info)
        if emptyLayers:
            QgsMessageLog.logMessage(QCoreApplication.translate('QEsg',u'Layers vazios: \'{}\'').format(emptyLayers), 
                    self.__class__.__name__, Qgis.Info)              
        if success:
            vPipes.updateExtents()
            self.PreenchePVJ(vPipes)
            #vPipes.setCrs(crs) #Configura CRS para o mesmo do projeto atual            
            proj.addMapLayer(vPipes)            
            EstiloClasse=Estilos()
            EstiloClasse.CarregaEstilo(vPipes, 'rede_tipo_contribuicao.qml')
            iface.setActiveLayer(vPipes)
            
            iface.messageBar().clearWidgets()
            iface.messageBar().findChildren(QToolButton)[0].setHidden(False)
            iface.messageBar().pushMessage('QEsg',QCoreApplication.translate('QEsg',u'Importação concluída com sucesso!'), 
                                           duration=3)
        else:          
            dxf_info = "|layername=entities|geometrytype=LineString"                       
            uri=nome_arquivo  + dxf_info # + '|crs=' + crsAuthID
            #print('uri:',uri)
            iface.mainWindow().blockSignals(True)
            dxf_vl = QgsVectorLayer(uri, dxf_output_filename + ".dxf", 'ogr')            
            dxf_vl.setCrs(destCrs)
            iface.mainWindow().blockSignals(False)
            if dxf_vl.isValid() == True:
                proj.addMapLayer(dxf_vl)
                iface.setActiveLayer(dxf_vl)
                
                msg=QCoreApplication.translate('QEsg',u'DXF adicionado, mas não parece ser um arquivo DXF do Sancad! Veja o log para detalhes')
            else:
                msg=QCoreApplication.translate('QEsg',u'Arquivo DXF inválido!uri:'+uri)
            iface.messageBar().clearWidgets()
            iface.messageBar().pushMessage('QEsg',msg,level=Qgis.Warning,duration=10)            
        iface.zoomToActiveLayer()
        #s.setValue("/Projections/defaultBehavior", Userconfig)
        
    def ExtendToMont(self,Geom, dist=4):#Retorna geometria com linha estendida #x1,y1,x2,y2
        poli=Geom.asPolyline()
        pto1=poli[0]
        pto2=poli[1]
        x1=pto1.x()
        y1=pto1.y()
        x2=pto2.x()
        y2=pto2.y()
        Alfa=math.atan2(y2-y1,x2-x1)
        dx=dist*math.cos(Alfa)
        dy=dist*math.sin(Alfa)
        xp=x1-dx
        yp=y1-dy
        pto1_est=QgsPoint(xp,yp)
        pto2=QgsPoint(x2,y2)
        newGeo=QgsGeometry.fromPolyline([pto1_est,pto2])
        return newGeo
    def PreenchePVJ(self, vLayer):
        #proj = QgsProject.instance()
        #vLayer=iface.activeLayer()
        tol=0.5 #tolerancia 0.5 unidades de distancia 
        vLayer.startEditing()
        for upfeat in vLayer.getFeatures():
            #get up reach list of nodes
            nodes = upfeat.geometry().asPolyline()
            #get up end node downstream
            up_end_node = nodes[-1]
            rectangle = QgsRectangle(up_end_node.x() - tol, up_end_node.y() - tol, up_end_node.x() + tol, up_end_node.y() + tol)
            request = QgsFeatureRequest().setFilterRect(rectangle)
            downfeats = vLayer.getFeatures(request)
            # start nodes into tolerance        
            n_start_node=0
            for downfeat in downfeats:
                #get list of nodes
                nodes = downfeat.geometry().asPolyline()
                #get start node downstream
                down_start_node = nodes[0]
                #setup distance
                distance = QgsDistanceArea()
                #get distance from up_end_node to down_start_node
                dist = distance.measureLine(up_end_node, down_start_node)
                if dist < tol:
                    n_start_node+=1
                    downPVM=downfeat['PVM']
            if n_start_node>0:
                upfeat['PVJ']=downPVM
                #QMessageBox.warning(None,'QEsg','Mais de uma saida no PV='+downPVM)
            else:
                upfeat['PVJ']='FIM'
            vLayer.updateFeature(upfeat)

        

