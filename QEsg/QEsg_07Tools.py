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
from qgis.PyQt.QtWidgets import QMessageBox, QDialog, QDialogButtonBox, QVBoxLayout, QCheckBox, QLabel
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.utils import *
import os.path
from qgis.gui import QgsMessageBar, QgsMapLayerComboBox, QgsVertexMarker, QgsMapToolIdentify
from .QEsg_00Model import *
from .QEsg_04Estilos import *
from .QEsg_00Common import *
from .QEsg_01Campos import *
from .QEsg_08Profiler import *
import math

class QEsg_07Tools(object):
    common = QEsg_00Common()
    ProfilerClasse = QEsg_08Profiler()
    goExec = True
    SETTINGS = common.SETTINGS
    def onCancelButton(self):
        self.goExec = False
    # Create mininum covering points
    def CreateMinCovering_Points(self, mdtLyr, pipesLyr, interfLyr, meshFullRes=False):
        #Check if will run only on selected pipes
        if pipesLyr.selectedFeatureCount()==0:
            feicoes=pipesLyr.getFeatures()
        else:
            resp=QMessageBox.question(None,'QEsg',QCoreApplication.translate('QEsg','Verificar apenas os trechos selecionados em {}?'.format(pipesLyr.name())),
                                      QMessageBox.Yes, QMessageBox.No)
            if resp==QMessageBox.Yes:
                feicoes=pipesLyr.selectedFeatures()
            else:
                feicoes=pipesLyr.getFeatures()

        #Set the resolution to use for calculate
        try:
            rstRes = min(mdtLyr.rasterUnitsPerPixelX(),mdtLyr.rasterUnitsPerPixelY())
        except AttributeError:
            # MeshLayers have no rasterUnitsPerPixelX/Y attribute
            rstRes = 0.1

        canvas = iface.mapCanvas()
        interfCampos = interfLyr.fields()
        rowNumber = interfLyr.featureCount()

        # if meshlayer type create render before get values
        if mdtLyr.type() == mdtLyr.MeshLayer:
            mdtLyr.createMapRenderer(QgsRenderContext())
            dataset = QgsMeshDatasetIndex(0,0)

        msg = QCoreApplication.translate('QEsg',u'Iniciando execução...')
        progress,progressMBar,cancelButton=self.common.startProgressBar(msg)
        cancelButton.clicked.connect(self.onCancelButton)

        feicoesLst = list(feicoes) #converted to list to use more than one time
        nroTrechos = len(feicoesLst)
        trCont = 0

        interfLyr.startEditing()
        cont = 0
        msg = QCoreApplication.translate('QEsg', 'Verificando Trecho {}')
        for pipe in feicoesLst:
            if self.goExec:
                progressMBar.setText(msg.format(pipe['DC_ID']))
                QApplication.processEvents()

                geom = pipe.geometry()
                ext = geom.length()
                ccm = pipe['CCM']
                ccj = pipe['CCJ']
                diam_m = float(pipe['DIAMETER'])/1000
                decl = (ccm-ccj)/ext
                recMin = float(pipe['REC_MIN']) # Minimum design covering for this pipe
                recMinTr = recMin
                minFound=False
                dist=rstRes
                ptosList = []  # [distAlong]
                if meshFullRes:
                    ptosList, y = self.ProfilerClasse.profile_feature_fromMesh(geom, mdtLyr, resolution=rstRes)
                else:
                    while dist < (ext-rstRes):
                        ptosList.append(dist)
                        dist += rstRes
                # faz Looping nos pontos no trecho em analise a verificar o recobrimento
                for dist in ptosList:
                    pipeElev = ccm - dist * decl
                    ptoGeo = geom.interpolate(dist)
                    point = ptoGeo.asPoint()
                    if mdtLyr.type() == mdtLyr.MeshLayer:
                        try:
                            value = mdtLyr.datasetValue(dataset, point).scalar()
                        except:
                            QgsMessageLog.logMessage('Erro encontrado no trecho:' + pipe['DC_ID'],'QEsg_MinCovering_Points', Qgis.Info)
                            value = None

                        #workaround to qgis Mesh bug #36041, move point by 0.0001 to right and get value again
                        if math.isnan(value):
                            ptoGeo.translate(0.0001,0)
                            if ptoGeo.isMultipart():
                                point = ptoGeo.asMultiPoint()[0]
                            else:
                                point = ptoGeo.asPoint()
                            value = mdtLyr.datasetValue(dataset, point).scalar()
                            QgsMessageLog.logMessage('Ponto deslocado 0.0001 para pegar cota no trecho: {} (dist={})'.format(pipe['DC_ID'],dist),'QEsg_MinCovering_Points', Qgis.Info)

                    else: #Raster layer
                        value = float(mdtLyr.dataProvider().identify(point, QgsRaster.IdentifyFormatValue).results()[1])

                    if value and not math.isnan(value):
                        rec = round(value-pipeElev-diam_m,3) #Round to 3 digits because its enough to cover check
                        #print('trecho:{0} recMinTr:{1:.3f} recMin:{2:.3f} rec:{3:.3f}'.format(pipe['DC_ID'],recMinTr,recMin, rec ))
                        if (rec < recMinTr) and (rec < recMin):
                            minFound=True
                            recMinTr = rec # Minimum found covering for this pipe
                            ptoMin = ptoGeo
                            interfTN = value
                    # end for dos pontos no trecho em analise a verificar o recobrimento
                # Create interf point
                if minFound:
                    # if first min covering found, first remove all interf feature from previous calculation (INTERNAL==1 and TIPO_INT=='TN')
                    if cont == 0:
                        request = '"INTERNAL"=1 AND "TIPO_INT"=\'TN\''
                        it = interfLyr.getFeatures(QgsFeatureRequest().setFilterExpression(request))
                        idsLst = [i.id() for i in it]
                        #interfLyr.selectByIds(idsLst)
                        interfLyr.deleteFeatures(idsLst)

                    cont += 1
                    QgsMessageLog.logMessage(QCoreApplication.translate('QEsg','Recobrimento ({0:.2f}) menor que o minimo  encontrado no trecho:{1}'.format(recMinTr, pipe['DC_ID'])),
                                                'QEsg_MinCovering_Points', Qgis.Info)
                    feicao = QgsFeature(interfCampos)
                    feicao.setGeometry(ptoMin)
                    rowNumber += 1
                    feicao['DC_ID'] = rowNumber
                    feicao['TIPO_INT']='TN'
                    feicao['CS']=interfTN
                    feicao['CI']=interfTN-recMin
                    feicao['INTERNAL']=1
                    interfLyr.addFeature(feicao)

                    '''
                    r_pto = QgsVertexMarker(canvas)
                    r_pto.setCenter(ptoMin)
                    r_pto.setIconSize(30)
                    '''
                trCont+=1
                percent = int((trCont/float(nroTrechos)) * 100)
                progress.setValue(percent)
            else:
                break
            # end if goExec
        # end for Trechos
        iface.messageBar().clearWidgets()
        iface.messageBar().findChildren(QToolButton)[0].setHidden(False)
        if self.goExec:
            if cont>0:
                iface.messageBar().pushMessage('QEsg', QCoreApplication.translate('QEsg', u'{} ponto(s) com recobrimento menor que o mínimo encontrados(s)'.format(cont)), level=Qgis.Warning, duration=0)
                interfLyr.triggerRepaint()
            else:
                iface.messageBar().pushMessage('QEsg', QCoreApplication.translate('QEsg',u'Nenhum local encontrado com recobrimento menor que o mínimo!'), level=Qgis.Info, duration=10)
                iface.vectorLayerTools().stopEditing(interfLyr)
        else:
            iface.messageBar().pushMessage(self.SETTINGS, QCoreApplication.translate('QEsg',
                                                                                     u'Operação cancelada!Favor NÃO salvar os resultados!'),
                                           level=Qgis.Warning, duration=0)
            self.goExec = True

    # Create mininum covering points Tool
    def CreateMinCovering_Points_Tool(self):

        pipesLyr = self.common.PegaQEsgLayer('PIPES')
        if not pipesLyr:
            return False
        #Verifica se tem os campos padroes, em caso negativo, sugere criar e somente continua se forem criados
        CamposClasse=QEsg_01Campos()
        if not CamposClasse.CriaCampos('PIPES',pipesLyr):
            iface.messageBar().pushMessage('QEsg', QCoreApplication.translate('QEsg',u'Operação cancelada! Para continuar é necessário criar os campos obrigatórios!'), level=Qgis.Warning, duration=0)
            return False

        interfLyr = self.common.PegaQEsgLayer('INTERFERENCES')
        if not interfLyr:
            return False
        #Verifica se tem os campos padroes, em caso negativo, sugere criar e somente continua se forem criados
        if not CamposClasse.CriaCampos('INTERFERENCES',interfLyr):
            iface.messageBar().pushMessage('QEsg', QCoreApplication.translate('QEsg',u'Operação cancelada! Para continuar é necessário criar os campos obrigatórios!'), level=Qgis.Warning, duration=0)
            return False
        iface.messageBar().clearWidgets()

        #Create dialog for MDT choose
        dlg = QDialog()
        dlg.setWindowTitle(QCoreApplication.translate('QEsg',u'Selecione o MDT com a elevação'))

        #MDT Combobox
        ml=QgsMapLayerComboBox()
        ml.setFilters( QgsMapLayerProxyModel.RasterLayer | QgsMapLayerProxyModel.MeshLayer )
        #filter out raster without info capabilities
        outList=[]
        for i in range(0,ml.count()):
            layer = ml.layer(i)
            if layer.type() != layer.MeshLayer and not (layer.dataProvider().capabilities() & QgsRasterDataProvider.IdentifyValue):
                outList.append(layer)
        ml.setExceptedLayerList(outList)

        #checkBox
        chkMeshEdges = QCheckBox(QCoreApplication.translate('QEsg',u'Usar a resolução máxima da malha (mais lento)'))

        #ButtonBox
        bb=QDialogButtonBox()
        bb.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        #layout
        layOut = QVBoxLayout()#QGridLayout()#QVBoxLayout()
        layOut.addWidget(QLabel('MDT:'))
        layOut.addWidget(ml)
        layOut.addWidget(chkMeshEdges)
        layOut.addWidget(bb)
        dlg.setLayout(layOut)
        dlg.setMinimumWidth(300)

        # Signals answers
        def ok():
            dlg.close()
            self.CreateMinCovering_Points(ml.currentLayer(), pipesLyr, interfLyr, chkMeshEdges.isChecked())
        def cancel():
            dlg.close()
        def ml_onChange():
            layer = ml.currentLayer()
            isMesh = layer.type() == layer.MeshLayer
            chkMeshEdges.setVisible(isMesh)
            if not isMesh:
                chkMeshEdges.setChecked(isMesh)

        #connect to signals
        bb.accepted.connect(ok)
        bb.rejected.connect(cancel)
        ml.activated.connect(ml_onChange)

        ml_onChange() #chama para verificar se o checkbox chkMeshEdges deve ficar visivel
        dlg.show()