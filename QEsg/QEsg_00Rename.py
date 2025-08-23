# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name		     : QEsg Rename Tools
Description          : 
Date                 : 28/Jan/2016/ 
copyright            : (C) 2016 by Jorge Almerio
email                : jorgealmerio@gmail.com 
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
from builtins import range
from builtins import object
# Import the PyQt and QGIS libraries
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.core import *
from qgis.gui import *
import processing
#import math

import qgis.utils
from .QEsg_01Campos import *
import os
from .QEsg_04Estilos import *

class Rename_Tools(object):
    
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.EstiloClasse=Estilos()

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(QIcon(":/plugins/network_tools/icon.png"), "Renomeia Rede", self.iface.mainWindow())
        #Add toolbar button and menu item
        #self.iface.addPluginToMenu("&Renomeia Rede", self.action)
        #self.iface.addToolBarIcon(self.action)
        
        proj = QgsProject.instance()
        aForma='PIPES'
        ProjVar=proj.readEntry("QEsg", aForma)[0]
        if ProjVar=='':
            msgTxt=QCoreApplication.translate('QEsg','Layer Indefinido: ') +aForma+ '\n'
            iface.messageBar().pushMessage('QEsg', msgTxt, level=Qgis.Warning, duration=4)
            return False
        else:
            vLayerLst=proj.mapLayersByName(ProjVar)
            if vLayerLst:
                vl=vLayerLst[0]
                #Cria os campos padroes sem perguntar
                CamposClasse=QEsg_01Campos()
                CamposClasse.CriaCampos(aForma,vl, SilentRun=True)
                #Chama a rotina que Verifica se existem multipartes ou polilinhas
                self.CheckPolylines(vl,SilentRun=True)
            else:
                msgTxt=aForma+'='+ProjVar+QCoreApplication.translate('QEsg',u' (Layer não encontrado)')
                iface.messageBar().pushMessage('QEsg', msgTxt, level=Qgis.Warning, duration=4)
                return False
        
        #load the form
        path = os.path.dirname(os.path.abspath(__file__))
        self.dock = uic.loadUi(os.path.join(path, "QEsg_Rename_dialog.ui"))
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)#Qt.RightDockWidgetArea
        
        #connect the action to each method
        self.action.triggered.connect(self.show)
        
        #tool button
        self.sourceIdEmitPoint = QgsMapToolEmitPoint(self.iface.mapCanvas())
        
        self.dock.buttonSelectSourceId.clicked.connect(self.selectSourceId)
        self.dock.buttonSelectSourceId.setCheckable(True)
        self.iface.mapCanvas().mapToolSet.connect(self.deactivated)
        self.sourceIdEmitPoint.canvasClicked.connect(self.setSourceId)
        self.iface.mapCanvas().setMapTool(self.sourceIdEmitPoint)
        
        self.dock.buttonRun.clicked.connect(self.run)
        self.dock.buttonClear.clicked.connect(self.clear)
        self.dock.buttonVerifica.clicked.connect(self.call_Verifica)

        self.sourceFeatID = None
        self.TrechosChained=[]
        self.PVfim='FIM'
    #Qgis mapTool deactivated signal
    def deactivated(self):
        curMapTool = self.iface.mapCanvas().mapTool()
        #if current mapTool is not this tool (self.sourceIdEmitPoint) deactivates this tool
        if curMapTool != self.sourceIdEmitPoint:
            self.iface.mapCanvas().unsetMapTool(self.sourceIdEmitPoint)
            self.dock.buttonSelectSourceId.setChecked(False)
    def show(self):
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
       
    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu("&Renomeia Rede", self.action)
        self.iface.removeDockWidget(self.dock)

    def selectSourceId(self, checked):
        if checked:
            self.iface.mapCanvas().setMapTool(self.sourceIdEmitPoint)
        else:
            self.iface.mapCanvas().unsetMapTool(self.sourceIdEmitPoint)

    def PegaPipeLayer(self):
        proj = QgsProject.instance()
        aForma='PIPES'
        ProjVar=proj.readEntry("QEsg", aForma)[0]
        if ProjVar=='':
            msgTxt=QCoreApplication.translate('QEsg','Layer Indefinido: ') +aForma
            QMessageBox.warning(None,'QEsg',msgTxt)
            return False
        LayerLst=proj.mapLayersByName(ProjVar)
        if LayerLst:
            layer = proj.mapLayersByName(ProjVar)[0]
            return layer
        else:
            msgTxt=aForma+'='+ProjVar+QCoreApplication.translate('QEsg',u' (Layer não encontrado)')
            QMessageBox.warning(None,'QEsg',msgTxt)
            return False

    def setSourceId(self, pt):
        proj = QgsProject.instance()
        aForma='PIPES'
        ProjVar=proj.readEntry("QEsg", aForma)[0]
        if ProjVar=='':
            msgTxt=QCoreApplication.translate('QEsg','Layer Indefinido: ') +aForma
            QMessageBox.warning(None,'QEsg',msgTxt)
            return
        layer = proj.mapLayersByName(ProjVar)[0]
        layer.removeSelection()
        width = self.iface.mapCanvas().mapUnitsPerPixel() * 4
        rect = QgsRectangle(pt.x() - width,
                                  pt.y() - width,
                                pt.x() + width,
                                pt.y() + width)
        layer.selectByRect(rect, QgsVectorLayer.SetSelection) #Before version 3.22.2 was: layer.selectByRect(rect, True) ;argument 2 has unexpected type 'bool'
        selected_features = layer.selectedFeatures()
        if layer.selectedFeatureCount()>1:
            QMessageBox.Warning(self.dock, self.dock.windowTitle(),
                    'WARNING: more than one feature selected!\n')
            return
        if layer.selectedFeatureCount()==0:
            return
        for feat in selected_features:
            sourceID='1-1'#feat['DC_ID']
            self.sourceFeatID=feat.id()
            self.selectDownstream(layer)

    def getLength(self,layer):
        totalLen = 0
        count = 0
        for feature in layer.selectedFeatures():
            geom = feature.geometry()
#            idtxt = feature[str(self.dock.comboFields.currentText())]
#            self.dock.textEditLog.append(idtxt)
            totalLen = totalLen + geom.length()
            count = count + 1
        return totalLen, count

    def run(self):
#        QMessageBox.warning(self.dock, self.dock.windowTitle(),
#                'WARNING: run action, renomear')
        QApplication.setOverrideCursor(Qt.WaitCursor)
        proj = QgsProject.instance()
        aForma='PIPES'
        ProjVar=proj.readEntry("QEsg", aForma)[0]
        if ProjVar=='':
            msgTxt='Layer Indefinido: ' +aForma+ '\n'
            QMessageBox.warning(None,'QEsg',msgTxt)
            return
        layer = proj.mapLayersByName(ProjVar)[0]
        
        campoID='DC_ID'
        Coletor=self.dock.spinColetor.value()
        Trecho=1
        NroDigitos = self.dock.spinColetorDigitos.value()
        NroDigitosPV = self.dock.spinPVDigitos.value()
        Colpref =self.dock.lineEditCol_pref.text()
        Colsuf =self.dock.lineEditCol_suf.text()
        PVpref =self.dock.lineEditPV_pref.text()
        PVsuf =self.dock.lineEditPV_suf.text()
        
        OrdCresc=self.dock.radioCrescente.isChecked()
        NroElems=len(self.TrechosChained)
        PVini=self.dock.spinPV_ini.value()
        if OrdCresc:
            PVnro = PVini
            Dir=1
        else:
            PVnro =PVini+NroElems-1
            Dir=-1
        layer.startEditing()
        for index, elem in enumerate(self.TrechosChained):
#            print(index, elem)
            request = QgsFeatureRequest().setFilterFid(elem)
            feat=next(layer.getFeatures(request))
            feat['Coletor']=Coletor
            feat['Trecho']=Trecho
            feat['DC_ID']=Colpref+str(Coletor).rjust(NroDigitos,'0')+'-'+str(Trecho).rjust(NroDigitos,'0')+Colsuf
            Trecho += 1
            if index==0:#No primeiro trecho Verifica se tem algum trecho saindo do mesmo PV de montante
                Tem, NomePVM = self.VerificaPVMont_comun_comID(layer, feat)
                if Tem:
                    feat['PVM']=NomePVM
                else:
                    feat['PVM']=PVpref+str(PVnro).rjust(NroDigitosPV,'0')+PVsuf
            else:
                feat['PVM']=PVpref+str(PVnro).rjust(NroDigitosPV,'0')+PVsuf
            PVnro += Dir
            if index<NroElems-1:#Numera o PVJ final do coletor
                feat['PVJ']=PVpref+str(PVnro).rjust(NroDigitosPV,'0')+PVsuf
            else:
                feat['PVJ']=self.PVfim
            layer.updateFeature(feat)
        self.dock.textEditLog.append("N. of Renamed: "+str(len(self.TrechosChained)))
        self.EstiloClasse.CarregaEstilo(layer, 'rede_nomes.qml')
        layer.triggerRepaint()
        
        if self.dock.buttonSelectSourceId.isChecked():
            self.dock.buttonSelectSourceId.click()
        QApplication.restoreOverrideCursor()
    
    def round_down(self, x, a):
        return math.floor(x / a) * a

    def getStatsByCat(self, layer):
        #Returns features table with count grouped by PVM
        params = {'INPUT':layer,
            'VALUES_FIELD_NAME':'',
            'CATEGORIES_FIELD_NAME':['PVM'],
            'OUTPUT':'TEMPORARY_OUTPUT'}
        res = processing.run('qgis:statisticsbycategories', params)
        return res['OUTPUT'] 
 
    def checkPontaSeca(self, layer):
        resp=True
        psFld='PONTA_SECA'
        validos=['S','N']        
        for feature in layer.getFeatures():
            pSeca = feature[psFld]
            if pSeca not in validos:                        
                msgTxt=QCoreApplication.translate('QEsg',u'O campo [PONTA_SECA] deve conter \'S\' ou \'N\'')
                self.dock.textEditLog.append(msgTxt)                
                selExp='\"{0}\" not in {1} or \"{0}\" is null'.format(psFld,('S','N'))
                layer.selectByExpression(selExp)
                self.iface.mapCanvas().zoomToSelected(layer)
                resp=False
                break
        if not resp:
            QMessageBox.warning(None,'QEsg',msgTxt)
        return resp
 
    def AllSamePlace(self, features):
        tol = self.dock.spinBoxTol.value()
        resp=True
        first=True
        allCoords=[]
        for feature in features:
            coords = self.getNodes(feature)[0] #get upstream node as XY
            PVMcoords = [self.round_down(item,tol) for item in coords] #Round node coords to tolerance
            if first:
                allCoords.append(PVMcoords)
                first=False
            else:
                if PVMcoords not in allCoords:
                    resp=False
                    break
        return resp
    def VerificaPVMont_Duplicado(self, layer):        
        #Grouped features with stats
        featStats = self.getStatsByCat(layer)
        exp = QgsExpression('count > 1') #To get only duplicated
        reqStats = QgsFeatureRequest(exp)       
        featALL = layer.getFeatures()
        AchouDuplic=False        
        
        for featStat in featStats.getFeatures(reqStats):
            pvm=featStat['PVM'] #or 'NULL'
            request = QgsFeatureRequest()
            expres='\"PVM\"=\'' + pvm + '\'' #filtra os coletores com esse PVM                
            request.setFilterExpression(expres)    
            mesmoLocal = self.AllSamePlace(layer.getFeatures(request))
            if not mesmoLocal:
                AchouDuplic=True
                msgTxt=QCoreApplication.translate('QEsg',u'PVM duplicado em locais distintos')
                self.dock.textEditLog.append(msgTxt+': '+pvm)
                layer.selectByExpression(expres)
                self.iface.mapCanvas().zoomToSelected(layer)
            else:
                request = QgsFeatureRequest()
                expres='\"PVM\"=\'' + pvm + '\' and \"PONTA_SECA\"=\'S\''           
                request.setFilterExpression(expres)
                countPS = len(list(layer.getFeatures(request)))
                if countPS==0:
                    AchouDuplic=True
                    msgTxt=QCoreApplication.translate('QEsg',u'PV Montante com mais de uma saida')
                    self.dock.textEditLog.append(msgTxt+': '+pvm)
                    selExp='\"PVM\"=\'' + pvm + '\''
                    layer.selectByExpression(selExp)
                    self.iface.mapCanvas().zoomToSelected(layer)
                else:
                    request = QgsFeatureRequest()
                    expres='\"PVM\"=\'' + pvm + '\' and \"PONTA_SECA\"=\'N\''           
                    request.setFilterExpression(expres)
                    countNPS = len(list(layer.getFeatures(request)))
                    if countNPS==0:
                        AchouDuplic=True
                        msgTxt=QCoreApplication.translate('QEsg',u'PV Montante sem saida')
                        self.dock.textEditLog.append(msgTxt+': '+pvm)
                        selExp='\"PVM\"=\'' + pvm + '\''
                        layer.selectByExpression(selExp)
                        self.iface.mapCanvas().zoomToSelected(layer)
                    elif countNPS>1:
                        AchouDuplic=True
                        msgTxt=QCoreApplication.translate('QEsg',u'PV Montante com mais de uma saida')
                        self.dock.textEditLog.append(msgTxt+': '+pvm)
                        layer.selectByExpression(expres)
                        self.iface.mapCanvas().zoomToSelected(layer)
            if AchouDuplic:
                break                
        if AchouDuplic:            
            QMessageBox.warning(None,'QEsg',msgTxt)
        else:
            layer.removeSelection()
            self.dock.textEditLog.append(QCoreApplication.translate('QEsg','PV\'s Montantes sem duplicidade!'))
    
    #Verifica Se ja tem um trecho saindo do mesmo PV de Montante
    def VerificaPVMont_comun_comID(self, layer, feat):
        tol = self.dock.spinBoxTol.value()
        # get list of nodes
        nodes = self.getNodes(feat)
        # get end node upstream 
        up_end_node = nodes[0]
        # select all features around upstream coordinate using a bounding box
        rectangle = QgsRectangle(up_end_node.x() - tol, up_end_node.y() - tol, up_end_node.x() + tol, up_end_node.y() + tol)
        request = QgsFeatureRequest().setFilterRect(rectangle)
        features = layer.getFeatures(request)
        # start nodes into tolerance        
        n_start_node=0
        features = layer.getFeatures(request)
        #iterate thru requested features
        for feature in features:
            if feat.id()!=feature.id():
                #get list of nodes
                nodes = self.getNodes(feature)
                #get start node upstream
                outro_up_node = nodes[0]
                #setup distance
                distance = QgsDistanceArea()
                #get distance from up_end_node to outro_up_node
                dist = distance.measureLine(up_end_node, outro_up_node)
                if dist < tol:
                    n_start_node=n_start_node+1
                    #add feature to selection list to iterate over it (if it not is the target)
                    pvm=feature['PVM']
                    if pvm!=NULL:
                        return True, pvm
        return False, 0
    def selectDownstream(self,layer):
        self.dock.textEditLog.clear()
        campo='DC_ID' 
        #QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
    
        final_list = self.TrechosChained
        selection_list = []
        tol = self.dock.spinBoxTol.value()
        self.dock.textEditLog.append("Starting...")

        layer.removeSelection()
        
        layer.select(self.sourceFeatID)
        provider = layer.dataProvider()
        selection_list.append(self.sourceFeatID)
        final_list.append(self.sourceFeatID)
        self.PVfim='FIM'
        # this part partially based on flowTrace by "Ed B"
        while selection_list:
            request = QgsFeatureRequest().setFilterFid(selection_list[0])
            feature = next(layer.getFeatures(request))
            # get list of nodes
            nodes = self.getNodes(feature)
            # get end node upstream 
            up_end_node = nodes[-1]
            # select all features around upstream coordinate using a bounding box
            rectangle = QgsRectangle(up_end_node.x() - tol, up_end_node.y() - tol, up_end_node.x() + tol, up_end_node.y() + tol)
            request = QgsFeatureRequest().setFilterRect(rectangle)
            features = layer.getFeatures(request)
            # start nodes into tolerance        
            n_start_node=0
            features = layer.getFeatures(request)
            #iterate thru requested features
            for feature in features:
                #get list of nodes
                nodes = self.getNodes(feature)
                #get start node downstream
                down_start_node = nodes[0]
                #setup distance
                distance = QgsDistanceArea()
                #get distance from up_end_node to down_start_node
                dist = distance.measureLine(up_end_node, down_start_node)
                if dist < tol and feature['PONTA_SECA']!='S':
                    n_start_node=n_start_node+1
                    #add feature to final list
                    final_list.append(feature.id())
                    #add feature to selection list to iterate over it (if it not is the target)
                    pvm=feature['PVM']
                    if self.dock.checkBifurcat.isChecked() and (pvm != NULL):
                        final_list[len(final_list)-n_start_node:len(final_list)] = []
                        self.dock.textEditLog.append("Stop at PVM="+pvm)
                        self.PVfim=pvm
                        if self.dock.chkGetPreffromJus.isChecked():
                            self.dock.lineEditPV_pref.setText(pvm+'.')
                        break
                    if feature.id() not in selection_list:
                        selection_list.append(feature.id())
            if n_start_node > 1:
                self.dock.textEditLog.append("Bifurcation at end of: ")#+    feature[campo])
            if n_start_node > 1 and self.dock.checkBifurcat.isChecked():
                #remove last n_start_node items from final_list                
                final_list[len(final_list)-n_start_node:len(final_list)] = []
                self.dock.textEditLog.append("Stop at bifurcation!")
                break            
            #remove feature "0" from selection list
            selection_list.pop(0)
        #select features using final_list            
        layer.selectByIds(final_list)
        self.TrechosChained=final_list
        tot = self.getLength(layer)
        self.dock.textEditLog.append("")
        self.dock.textEditLog.append("N. of selected feature(s): " + str(tot[1]))
        self.dock.textEditLog.append("Length of selected feature(s): " + str(round(tot[0],3)))
        #zoom to selected feature if requested by ui
        if self.dock.checkZoomToSel.isChecked():
            mapCanvas = self.iface.mapCanvas()
            mapCanvas.zoomToSelected(layer)
        QApplication.restoreOverrideCursor()
            
    def call_Verifica(self):
#        qgis.utils.showPluginHelp()
        proj = QgsProject.instance()
        aForma='PIPES'
        ProjVar=proj.readEntry("QEsg", aForma)[0]
        if ProjVar=='':
            msgTxt=QCoreApplication.translate('QEsg','Layer Indefinido: {}').format(aForma)
            QMessageBox.warning(None,'QEsg',msgTxt)
            return
        layer = proj.mapLayersByName(ProjVar)[0]
        LinesOK=self.CheckPolylines(layer)
        if LinesOK:
            psOK = self.checkPontaSeca(layer)
            if psOK:
                self.VerificaPVMont_Duplicado(layer)    
    
    
    def CheckPolylines(self, layer,SilentRun=False):
        for feature in layer.getFeatures():
            geom=feature.geometry()
            NroVertices=0
            if geom.isMultipart():
                mPoly = geom.asMultiPolyline()
                for poly in mPoly:
                    NroVertices=max(NroVertices,len(poly))
                if NroVertices>2:
                    layer.removeSelection()
                    layer.select(feature.id())
                    msgTxt=QCoreApplication.translate('QEsg',u'Existem elementos multipartes com até {:d} vértices.').format(NroVertices)
                    resp=QMessageBox.question(None,'QEsg',msgTxt+QCoreApplication.translate('QEsg',u' Deseja convertê-los para partes simples?'),QMessageBox.Yes, QMessageBox.No)
    #                self.iface.messageBar().pushMessage("QEsg:", "Existem elementos multipartes com "+
    #                                                    str(NroVertices)+ " vertices", duration=0)
    #                QgsMessageLog.logMessage(msgTxt, 'QEsg', QgsMessageLog.INFO)
                    if resp==QMessageBox.Yes:
                        self.run_segmenter(layer)
                        return True
                    return False
                    #print 'Multipolilinha', [len(v) for v in vertices]
            else:
                vertices = geom.asPolyline()
                NroVertices=len(vertices)
                if NroVertices>2:
                    msgTxt=QCoreApplication.translate('QEsg',u'Existem elementos com {:d} vértices.').format(NroVertices)
                    resp=QMessageBox.question(None,'QEsg',msgTxt+QCoreApplication.translate('QEsg',u' Deseja convertê-los para linhas simples?'),QMessageBox.Yes, QMessageBox.No)
    #                self.iface.messageBar().pushMessage("QEsg:", "Existem elementos multipartes com "+
    #                                                    str(NroVertices)+ " vertices", duration=0)
#                    QgsMessageLog.logMessage(msgTxt, 'QEsg', QgsMessageLog.INFO)
                    if resp==QMessageBox.Yes:
                        self.run_segmenter(layer)
                        return True
                    return False
        if not SilentRun:            
            msgTxt=QCoreApplication.translate('QEsg',u'A geometria das feições foram verificadas com sucesso!')
            self.dock.textEditLog.setText(msgTxt)
            #QMessageBox.information(None,'QEsg',msgTxt)
            return True
    def run_segmenter(self, layer):
        #Routine from Networks Plugin from CEREMA Nord-Picardie
        #layer = self.iface.activeLayer()
        if not layer==None:
            if layer.featureCount()>0 and layer.geometryType()==1:
                layer.startEditing()
                layer.beginEditCommand("Split polylines into lines")
                for feature in layer.getFeatures():
                    geom = feature.geometry()
                    nodes = geom.convertToType(QgsWkbTypes.LineGeometry,True).asMultiPolyline()
                    att=feature.attributes()
                    id=feature.id()
                    for poly in nodes:
                        for pt in range(len(poly)-1):
                            segment=QgsFeature()
                            segment.setGeometry(QgsGeometry.fromPolylineXY([poly[pt],poly[pt+1]]))
                            segment.setAttributes(att)
                            layer.addFeature(segment)
                    layer.deleteFeature(id)
                layer.endEditCommand()
            elif not layer.geometryType()==1:
                QMessageBox().information(None,"Split",u'O layer não é de linhas')
            else:
                QMessageBox().information(None,"Split","Layer vazio")
        else:
            QMessageBox().information(None,"Split","Layer indefinido")

    def clear(self):        
        proj = QgsProject.instance() 
        #Read pipe number order; True=Principal<Tributario (value=0)
        OrdCresc=proj.readNumEntry("QEsg", "PIPE_ORDEM",0)[0]==0 #self.dock.radioCrescente.isChecked()
        sinal= 1 if OrdCresc else -1
        self.dock.spinColetor.setValue(self.dock.spinColetor.value()+sinal)
        self.TrechosChained=[]
        self.dock.textEditLog.clear()
        #self.dock.buttonSelectSourceId.click()
        layer=self.PegaPipeLayer()
        if layer!=False:
            layer.removeSelection()
        #self.iface.mapCanvas().unsetMapTool(self.sourceIdEmitPoint)
        #self.iface.mapCanvas().setMapTool(self.sourceIdEmitPoint)
        if not self.dock.buttonSelectSourceId.isChecked():
            self.dock.buttonSelectSourceId.click()
        QApplication.restoreOverrideCursor()

    def LimpaNomesColetores(self):
        vLayer=self.PegaPipeLayer()
        if vLayer==False:
            return
        if vLayer.selectedFeatureCount()==0:
            feicoes=vLayer.getFeatures()
        else:
            resp=QMessageBox.question(None,'QEsg',QCoreApplication.translate('QEsg','Apagar os nomes apenas dos coletores selecionados?'),
                                      QMessageBox.Yes, QMessageBox.No)
            if resp==QMessageBox.Yes:
                feicoes=vLayer.selectedFeatures()
            else:
                feicoes=vLayer.getFeatures()
        vLayer.startEditing()
        campos=['DC_ID','Coletor','Trecho','PVM','PVJ']
        for feicao in feicoes:
            for campo in campos:
                feicao[campo]=NULL
            vLayer.updateFeature(feicao)
        vLayer.triggerRepaint()
        self.iface.mapCanvas().refresh()

    def toggleSelectButton(self, button):
        selectButtons = [
            self.dock.buttonSelectSourceId
        ]
        for selectButton in selectButtons:
            if selectButton != button:
                if selectButton.isChecked():
                    selectButton.click()
    def getNodes(self, aFeat):
        aGeom = aFeat.geometry()
        if aGeom.isMultipart():
            return aGeom.asMultiPolyline()[0] #pega a primeira
        else:
            return aGeom.asPolyline()
        

