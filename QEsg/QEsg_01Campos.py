# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QEsg_01Campos
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
from builtins import object
from qgis.core import *
from qgis.PyQt.QtWidgets import QMessageBox, QDialog, QDialogButtonBox ,QVBoxLayout, QCheckBox, QLabel
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.utils import *
import os.path
from .QEsg_00Model import *
from qgis.gui import QgsMessageBar, QgsMapLayerComboBox, QgsMapToolIdentify
from .QEsg_04Estilos import *
from .QEsg_00Common import *
import math

class QEsg_01Campos(object):
    common=QEsg_00Common()
    SETTINGS = common.SETTINGS
#     def __init__(self):
#         self.initGui()
    def CarregaCampos(self):
        self.proj = QgsProject.instance()
        ProjVar=self.proj.readEntry("QEsg", 'PIPES')[0]
        if ProjVar!='':
            self.RedeLayer=proj.mapLayersByName(ProjVar)[0]
            dp=self.RedeLayer.dataProvider()
            return [field.name() for field in dp.fields()]
        #print self.fieldNames
    def Verifica(self, Opcao):
        proj = QgsProject.instance()
        Formas=QEsgModel.GIS_SHAPES
        msgTxt=''
        for aForma in Formas:
            ProjVar=proj.readEntry("QEsg", aForma)[0]
            if ProjVar!='':
                #msgTxt+=QCoreApplication.translate('QEsg','Layer Indefinido: ') +aForma+ '\n'
            #else:
                vLayerLst=proj.mapLayersByName(ProjVar)
                if vLayerLst:
                    vLayer=vLayerLst[0]
                    #msgTxt+=aForma+ '='+vLayer.name()+ '\n' #dataProvider().dataSourceUri()
                    if Opcao=='Criar':
                        self.CriaCampos(aForma,vLayer)
                    elif Opcao=='Preencher' and aForma=='PIPES': #so estou preenchendo o layer de tubos por enquanto
                        #Verifica se existem os campos antes de preencher
                        if not self.CriaCampos('PIPES',vLayer):
                            iface.messageBar().pushMessage(self.SETTINGS, QCoreApplication.translate('QEsg',u'Operação cancelada! Para preencher é necessário criar os campos obrigatórios!'), level=Qgis.Warning, duration=0)
                            return False
                        self.Preenche(aForma,vLayer)
                else:
                    msgTxt+=aForma+'='+ProjVar+QCoreApplication.translate('QEsg',u' (Layer não encontrado)')+'\n'
        if msgTxt!='':
            iface.messageBar().pushMessage("QEsg:", msgTxt, level=Qgis.Warning, duration=4)
            #QMessageBox.information(None,'QEsg',msgTxt)
    def CriaCampos(self, aForma, vLayer, SilentRun=False):
        field_names = [field.name() for field in vLayer.fields()]
        attributes=[]
        dP = vLayer.dataProvider()
        msgTxt=QCoreApplication.translate('QEsg','Campos ausentes em ')+ vLayer.name()+':\n'
        CamposAusentes=False
        
        proj = QgsProject.instance()
        #Technical Standard 0=Brazil;1=India
        self.Std_id=proj.readNumEntry("QEsg", "STD",0)[0]
        if self.Std_id==1: #if India Standard
            Campos = QEsgModel.INDIA_COLUMNS[aForma]
        else:
            Campos = QEsgModel.COLUMNS[aForma]
        for campo in Campos:#COLUMNS
            if campo not in field_names:
                #print campo, QEsgModel.COLUMN_TYPES[campo]
                CamposAusentes=True
                msgTxt+=campo+'\n'
                attributes.append(QgsField(campo, QEsgModel.CAMPOSDEF[campo][0],
                                           QEsgModel.CAMPOSDEF[campo][1],
                                           QEsgModel.CAMPOSDEF[campo][2], 
                                           QEsgModel.CAMPOSDEF[campo][3])
                                  )
        #vLayer.startEditing()
        #vLayer.beginEditCommand('Criando campos')
        if CamposAusentes:
            if SilentRun:
                dP.addAttributes(attributes)
                vLayer.updateFields()
                sucesso=True
            else:
                resp=QMessageBox.question(None,'QEsg',msgTxt+QCoreApplication.translate('QEsg','Deseja criar os campos?'),
                                          QMessageBox.Yes, QMessageBox.No)
                if resp==QMessageBox.Yes:
                    vLayer.startEditing()
                    for campo in attributes:
                        vLayer.addAttribute(campo)
#                     dP.addAttributes(attributes)
#                     vLayer.updateFields()
                    sucesso=True
                else:
                    sucesso=False
        else:
            sucesso=True
            if not SilentRun:
                iface.messageBar().pushMessage('QEsg',QCoreApplication.translate('QEsg',u'Os campos necessários já existem em ')+vLayer.name())
        return sucesso

    def Preenche(self, aForma, vLayer):
        if vLayer.selectedFeatureCount()==0:
            feicoes=vLayer.getFeatures()
        else:
            resp=QMessageBox.question(None,'QEsg',QCoreApplication.translate('QEsg','Preencher apenas os registros selecionados?'),
                                      QMessageBox.Yes, QMessageBox.No)
            if resp==QMessageBox.Yes:
                feicoes=vLayer.selectedFeatures()
            else:
                feicoes=vLayer.getFeatures()
        #camposPadroes=['DIAMETER','MANNING','Q_CONC_INI','Q_CONC_FIM', 'REC_MIN']# No futuro usar: QEsgModel.COLUMNS[aForma]       
        proj = QgsProject.instance()
        dn_min=float(proj.readEntry("QEsg", "DN_MIN","150")[0])
        tubosMat=proj.readEntry("QEsg", "TUBOS_MAT","0")[0]
        if tubosMat=='0':#se nao tiver lista de diametros definidas
            iface.messageBar().pushMessage("QEsg:", QCoreApplication.translate('QEsg',u'Lista de diâmetros indefinida!'), 
                                           level=Qgis.Warning, duration=4)
            return False
        else:
            tubos=eval(tubosMat)
        diam_min,manning=[[d,n] for d,n in tubos if d >= dn_min][0]
        #manning=float(proj.readEntry("QEsg", "MANNING","0.013")[0])
        rec_min=float(proj.readEntry("QEsg", "REC_MIN","0.90")[0])
        lam_max=float(proj.readEntry("QEsg", "LAM_MAX","0.75")[0])
        ProjNode=proj.readEntry("QEsg", "JUNCTIONS")[0]
        PrecSancad=proj.readNumEntry("QEsg", "PREC_SANCAD",0)[0]#diametros progressivos
        NodeCotas={}
        notFoundNode=set()
        if ProjNode!='':
            vLayerLst=proj.mapLayersByName(ProjNode)
            if vLayerLst:
                NodeLayer=vLayerLst[0]
                Nodefeats=NodeLayer.getFeatures()
                Fld_id=QEsgModel.COLUMNS['JUNCTIONS'][0]
                Fld_Cota=QEsgModel.COLUMNS['JUNCTIONS'][1]
                #Looping nas junctions
                for Nodefeat in Nodefeats:
                    NodeCotas[Nodefeat[Fld_id]]=Nodefeat[Fld_Cota]
        camposPadroes={'LENGTH':'CALCULA','DIAMETER':diam_min,'MANNING':manning,
                       'Q_CONC_INI':0,'Q_CONC_FIM':0, 'REC_MIN': rec_min, 'LAM_MAX': lam_max,
                       'CONTR_LADO':2,'ETAPA':1,'PONTA_SECA':'N'}## No futuro usar direto do modelo
        if bool(NodeCotas): #se o dicionario nao estiver nulo
            camposPadroes.update({'CTM':'PREENCHE','CTJ':'PREENCHE'})
        self.Std_id=proj.readNumEntry("QEsg", "STD",0)[0]
        if self.Std_id==1: #if India Standard
            camposPadroes.update({'VEL_PROJ':0.8})
        
        #Inicia progress Bar
        msg = QCoreApplication.translate('QEsg','Iniciando Preenchimento...')
        progress,progressMBar,cancelButton=self.common.startProgressBar(msg)
        feicoesLst = list(feicoes) #converted to list to use more than one time
        nroTrechos = len(feicoesLst) #vLayer.featureCount() #len(list(feicoesCopy))        
        trCont=0
        msg = QCoreApplication.translate('QEsg','Calculando Trecho {}')
        
        vLayer.startEditing()        
        for feicao in feicoesLst:
            progressMBar.setText(msg.format(feicao['DC_ID']))
            for (campo,valorPad) in camposPadroes.items():
                featVal=feicao[campo]
                if campo=='LENGTH':
                    ext=feicao.geometry().length()
                    if PrecSancad:
                        ext=round(ext,0)
                    feicao[campo]=ext
                elif campo=='CTM':
                    pvm=feicao['PVM']
                    if pvm in NodeCotas:
                        feicao[campo]=NodeCotas[pvm]
                    else:
                        notFoundNode.add(pvm)
                elif campo=='CTJ':
                    pvj=feicao['PVJ']
                    if pvj in NodeCotas:
                        feicao[campo]=NodeCotas[pvj]
                    else:
                        notFoundNode.add(pvj)
                else:                    
                    if featVal==NULL or featVal is None:
                        feicao[campo]=valorPad
            vLayer.updateFeature(feicao)
            trCont+=1
            percent = int((trCont/float(nroTrechos)) * 100)
            progress.setValue(percent)
            
        vLayer.triggerRepaint()
        iface.messageBar().clearWidgets()
        iface.messageBar().findChildren(QToolButton)[0].setHidden(False)
        if len(notFoundNode)==0:
            iface.messageBar().pushMessage("QEsg:", QCoreApplication.translate('QEsg',u'Dados preenchidos com sucesso!'), level=Qgis.Info, duration=4)
        else:
            iface.messageBar().pushMessage("QEsg:", QCoreApplication.translate('QEsg',u'Dados preenchidos, exceto quanto aos nós não encontrados: '+', '.join(notFoundNode)), level=Qgis.Warning, duration=0)

    #Substitui o nome dos PVs (campos PVM e PVJ) dos tubos pelo Nome (DC_ID) do layer de nós
    #atraves da posicao espacial
    def AtualizaNomePVs(self):
        proj = QgsProject.instance()
        Formas=['PIPES','JUNCTIONS']
        msgTxt=''
        vLayer={}
        for aForma in Formas:
            ProjNode=proj.readEntry("QEsg", aForma)[0]
            if ProjNode!='':
                vLayerLst=proj.mapLayersByName(ProjNode)
                if vLayerLst:
                    vLayer[aForma]=vLayerLst[0]
                else:
                    msgTxt=QCoreApplication.translate('QEsg',u'Layer \'{}\' não encontrado!').format(ProjNode)
                    break
            else:
                msgTxt=QCoreApplication.translate('QEsg','Layer Indefinido: {}').format(aForma)
                break
        if msgTxt!='':
            iface.messageBar().pushMessage("QEsg:", msgTxt, level=Qgis.Warning, duration=5)
            return False
        tol=0.5 #tolerancia 0.5 unidades de distancia 
        vLayer['PIPES'].startEditing()
        for ptofeat in vLayer['JUNCTIONS'].getFeatures():
            node = ptofeat.geometry().asPoint()

            rectangle = QgsRectangle(node.x() - tol, node.y() - tol, node.x() + tol, node.y() + tol)
            request = QgsFeatureRequest().setFilterRect(rectangle)
            linefeats = vLayer['PIPES'].getFeatures(request)

            for linefeat in linefeats:
                #get list of nodes                
                glinha=linefeat.geometry()
                if QgsWkbTypes.isMultiType(glinha.wkbType()):
                    nodes=glinha.asMultiPolyline()
                    #get up and end node
                    up_node=nodes[0][0]
                    down_node=nodes[-1][-1]
                else: #if glinha.wkbType()==QgsWkbTypes.LineString:
                    nodes=glinha.asPolyline()
                    #get up and end node
                    up_node=nodes[0]
                    down_node=nodes[-1]

                #setup distance
                distance = QgsDistanceArea()
                #get distance from up_node and down_node to point
                distUp = distance.measureLine(up_node, node)
                distDown = distance.measureLine(down_node, node)
                if distUp < tol:
                    linefeat['PVM']=ptofeat['DC_ID']
                elif distDown < tol:
                    linefeat['PVJ']=ptofeat['DC_ID']
                vLayer['PIPES'].updateFeature(linefeat)
        iface.messageBar().pushMessage("QEsg:", QCoreApplication.translate('QEsg','Nomes dos PVS atualizados com sucesso!'),
                                        level=Qgis.Info, duration=5)
    
    #Get elevation from Raster
    def AtualizaCotaTN(self):
        proj = QgsProject.instance()
        msgTxt=''
        lyrTipos = ['JUNCTIONS','INTERFERENCES']
        lyrList={}
        notFound=[]
        unDefined=[]
        for lyrTipo in lyrTipos:
            ProjNode=proj.readEntry("QEsg", lyrTipo)[0]
            if ProjNode!='':
                vLayerLst=proj.mapLayersByName(ProjNode)
                if vLayerLst:
                    vLayer=vLayerLst[0]
                    lyrList[lyrTipo]= vLayer
                else:
                    notFound.append(ProjNode)
            else:
                unDefined.append(lyrTipo)         
        if notFound:
            msgTxt= QCoreApplication.translate('QEsg',u'Layer(s) não encontrado(s): {}').format(', '.join(notFound))
        if unDefined:
            msgTxt= msgTxt +' / '+ QCoreApplication.translate('QEsg','Layer(s) Indefinido(s): {}').format(', '.join(unDefined))
        if msgTxt!=''and not lyrList:
            iface.messageBar().pushMessage("QEsg:", msgTxt, level=Qgis.Warning, duration=5)
            return False
        self.GetElevation(lyrList)
        #vLayer.startEditing()        
        #iface.messageBar().pushMessage("QEsg:", QCoreApplication.translate('QEsg','Atualiza cota TN from raster!'),
        #                                level=Qgis.Info, duration=5)
    def GetElevation(self, pointsLyr):
        dlg = QDialog()
        dlg.setWindowTitle(QCoreApplication.translate('QEsg',u'Selecione o MDT com a elevação'))
        
        #Raster Combobox
        ml=QgsMapLayerComboBox()
        ml.setFilters( QgsMapLayerProxyModel.RasterLayer | QgsMapLayerProxyModel.MeshLayer )
        #filter out raster without info capabilities
        outList=[]
        for i in range(0,ml.count()):
            layer = ml.layer(i)
            if layer.type() != layer.MeshLayer:
                cap = layer.dataProvider().capabilities()
                if cap<6:
                    outList.append(layer)
        ml.setExceptedLayerList(outList)        
        
        #Junction Checkbox        
        if 'JUNCTIONS' in pointsLyr:
            nome = pointsLyr['JUNCTIONS'].name()
            chkJunction = QCheckBox('Junction: '+nome)
            chkJunction.setEnabled(True)
        else:
            chkJunction = QCheckBox('Junction: <undefined>')
            chkJunction.setEnabled(False)        
        
        #Interference Checkbox        
        if 'INTERFERENCES' in pointsLyr:
            nome = pointsLyr['INTERFERENCES'].name()
            chkInterf = QCheckBox('Interference: '+nome)
            chkInterf.setEnabled(True)
        else:
            chkInterf = QCheckBox('Interference: <undefined>')
            chkInterf.setEnabled(False) 
        
        #ButtonBox
        bb=QDialogButtonBox()
        bb.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        #layout
        layOut = QVBoxLayout()#QGridLayout()#QVBoxLayout()
        layOut.addWidget(QLabel('MDT:'))
        layOut.addWidget(ml)
        layOut.addWidget(chkJunction)
        layOut.addWidget(chkInterf)
        layOut.addWidget(bb)
        dlg.setLayout(layOut)        
        dlg.setMinimumWidth(300)

        
        # Signals answers
        def ok():
            dlg.close()
            if chkJunction.isChecked():
                tipo='JUNCTIONS'
                self.RasterSampling(ml.currentLayer(), pointsLyr[tipo], tipo)
            if chkInterf.isChecked():
                tipo='INTERFERENCES'
                self.RasterSampling(ml.currentLayer(), pointsLyr[tipo], tipo)
        def cancel():
            dlg.close()
            
        #connect to signals
        bb.accepted.connect(ok)
        bb.rejected.connect(cancel)
        
        dlg.show()
    def RasterSampling(self, mdtLyr, nodeLyr, tipo):
        tnField={'JUNCTIONS': 'COTA_TN',
                 'INTERFERENCES': 'CS'}
        if nodeLyr.selectedFeatureCount()==0:
            feicoes=nodeLyr.getFeatures()
        else:
            resp=QMessageBox.question(None,'QEsg',QCoreApplication.translate('QEsg','Atualizar apenas os registros selecionados em {}?'.format(nodeLyr.name())),
                                      QMessageBox.Yes, QMessageBox.No)
            if resp==QMessageBox.Yes:
                feicoes=nodeLyr.selectedFeatures()
            else:
                feicoes=nodeLyr.getFeatures()
        noElevPtos=[]
        
        # if meshlayer type create render before get values
        if mdtLyr.type() == mdtLyr.MeshLayer:
            mdtLyr.createMapRenderer(QgsRenderContext())
            dataset = QgsMeshDatasetIndex(0,0)
        nodeLyr.startEditing()
        for pto in feicoes:
            ptoGeo = pto.geometry()
            if ptoGeo.isMultipart():
                point = ptoGeo.asMultiPoint()[0]
            else:
                point = ptoGeo.asPoint()
            
            if mdtLyr.type() == mdtLyr.MeshLayer:
                try:                    
                    value = mdtLyr.datasetValue(dataset, point).scalar()
                except:                    
                    value = None

                #workaround to qgis Mesh bug #36041, move point by 0.0001 to right and get value again
                if math.isnan(value):
                    ptoGeo.translate(0.0001,0)
                    if ptoGeo.isMultipart():
                        point = ptoGeo.asMultiPoint()[0]
                    else:
                        point = ptoGeo.asPoint()
                    value = mdtLyr.datasetValue(dataset, point).scalar()
                    QgsMessageLog.logMessage('Ponto deslocado 0.0001 para pegar cota: {}'.format(pto['DC_ID']),'QEsg', Qgis.Info)

            else: #Raster layer
                value = mdtLyr.dataProvider().identify(point, QgsRaster.IdentifyFormatValue).results()[1]            
            if value and not math.isnan(value):
                if tipo=='JUNCTIONS' or (tipo=='INTERFERENCES' and pto['TIPO_INT']=='TN'):                   
                    pto[tnField[tipo]]=value
                    nodeLyr.updateFeature(pto)
            else:
                noElevPtos.append(pto.id())
        if noElevPtos:            
            nodeLyr.selectByIds(noElevPtos) 
            mapCanvas = iface.mapCanvas()
            mapCanvas.zoomToSelected(nodeLyr)
            iface.messageBar().pushMessage('QEsg', u'Verifique a ausência de informação nos pontos selecionados em {}:'.format(nodeLyr.name()), level=Qgis.Warning, duration=0)
        else:
            iface.messageBar().pushMessage('QEsg', u'Atualizou a elevação com sucesso em {}! Use o comando \'04 Preenche os campos\' para propagar a atualização para os Tubos'.format(nodeLyr.name()), level=Qgis.Info, duration=10)
        nodeLyr.triggerRepaint()