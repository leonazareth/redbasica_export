# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QEsg_10Report
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
from statistics import mode
from qgis.PyQt.QtXml import QDomDocument
'''
Atualiza o relatório com os dados do projeto
'''
class QEsg_10Report(object):
    common=QEsg_00Common()
    SETTINGS = common.SETTINGS
    #Atualiza o relatório Planilha de Resultados
    def Report_PlanResults_update(self, rptName='QEsg - Planilha de Resultados'):        
        proj = QgsProject.instance()
        ProjVar=proj.readEntry("QEsg", 'PIPES')[0]
        if ProjVar=='':
            msgTxt=QCoreApplication.translate('QEsg','Layer Indefinido: PIPES')
            iface.messageBar().pushMessage('QEsg', msgTxt, level=Qgis.Warning, duration=4)
            return False
        
        pipeLyr=proj.mapLayersByName(ProjVar)[0]        
        lytMan = proj.layoutManager()
        layout = lytMan.layoutByName(rptName)
        if not layout:
            msgTxt = QCoreApplication.translate('QEsg',u'O relatório não existia: {}'.format(rptName))
            self.criaLayout(rptName,'style/report/QEsg_PlanResultados.qpt')
            layout = lytMan.layoutByName(rptName)
        else:
            msgTxt = QCoreApplication.translate('QEsg',u'O relatório foi atualizado: {}'.format(rptName))
        
        QgsMessageLog.logMessage(msgTxt, self.SETTINGS, Qgis.Info)
        pipe_meta = pipeLyr.metadata()
        
        #Titulo
        var='title'
        item = layout.itemById(var) #item é Layoutframe
        curVal=pipe_meta.title()
        
        composer_html = item.multiFrame()
        composer_html.setHtml('<p style="font-size:12px;text-align: center;">{}</p>'.format(curVal))
        composer_html.loadHtml()
        
        #Tabela de atributos
        var='Att_Table'
        item = layout.itemById(var)        
        attrTable = item.multiFrame()
        
        cols = attrTable.columns()
        attrTable.setVectorLayer(pipeLyr)
        attrTable.setColumns(cols)
        pipesCount = pipeLyr.featureCount()
        print(pipesCount)
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.abreLayout(layout)  
            attrTable.setResizeMode(0) #ExtendToNextPage= 1; RepeatOnEveryPage= 2; RepeatUntilFinished= 3
            QApplication.processEvents()
            attrTable.setMaximumNumberOfFeatures(pipesCount)
            #attrTable.RECALC FALTA            
            QApplication.processEvents()
            attrTable.setResizeMode(3) #ExtendToNextPage= 1; RepeatOnEveryPage= 2; RepeatUntilFinished= 3
            QApplication.processEvents()
            self.AtualizaNrosPagina(layout)
            layout.refresh()
            msgTxt=QCoreApplication.translate('QEsg',"Relatório atualizado com sucesso!")
            iface.messageBar().pushMessage('QEsg', msgTxt, level=Qgis.Info, duration=4)  
            #self.abreLayout(layout)    
        except Exception as error:
            # handle the exception
            msgTxt=QCoreApplication.translate('QEsg',"Ocorreu um erro:", type(error).__name__, "–", error)
            iface.messageBar().pushMessage('QEsg', msgTxt, level=Qgis.Critical, duration=4)            
        finally:
            QApplication.restoreOverrideCursor()
        
    
    #Atualiza o relatório Dados Gerais
    def Report_DadosGerais_update(self, rptName='QEsg - Dados Gerais do Projeto'):        
        proj = QgsProject.instance()
        ProjVar=proj.readEntry("QEsg", 'PIPES')[0]
        if ProjVar=='':
            msgTxt=QCoreApplication.translate('QEsg','Layer Indefinido: PIPES')
            iface.messageBar().pushMessage('QEsg', msgTxt, level=Qgis.Warning, duration=4)
            return False
        
        pipeLyr=proj.mapLayersByName(ProjVar)[0]        
        lytMan = proj.layoutManager()
        layout = lytMan.layoutByName(rptName)
        if not layout:
            msgTxt = QCoreApplication.translate('QEsg',u'O relatório não existia: {}'.format(rptName))
            self.criaLayout(rptName)
            layout = lytMan.layoutByName(rptName)
        else:
            msgTxt = QCoreApplication.translate('QEsg',u'O relatório foi atualizado: {}'.format(rptName))
        QgsMessageLog.logMessage(msgTxt, self.SETTINGS, Qgis.Info)
        
        pipe_meta = pipeLyr.metadata()
        #Identificador principal
        var='parentIdentifier'
        item = layout.itemById(var)
        curVal=pipe_meta.parentIdentifier()
        item.setText(curVal)

        #Titulo
        var='title'
        item = layout.itemById(var)
        curVal=pipe_meta.title()
        item.setText(curVal)

        #Bacia
        var='bacia'
        item = layout.itemById(var)
        curVal=pipe_meta.title().lower().replace('bacia','').upper()
        item.setText(curVal)

        #Cidade
        var='Cidade'
        keys = pipe_meta.keywords()
        if var in keys:
            curVal=keys[var][0]
        else:
            curVal=''
        item = layout.itemById(var)
        if item:
            item.setText(curVal)

        #Material predominante
        var='Material'
        keys = pipe_meta.keywords()
        if var in keys:
            curVal=keys[var][0]
        else:
            curVal='PVC'
            
        item = layout.itemById(var)
        if item:
            item.setText(curVal)
        
        variaveis=['POPINI','POPFIM','PERCAPTA','K1_DIA','K2_HORA','COEF_RET','DN_MIN','COEF_INF','REC_MIN']
        for var in variaveis:
            item = layout.itemById(var)
            curVal=proj.readEntry("QEsg", var)[0]
            item.setText(curVal)
        
        #recobrimento em passeio igual a rua, por enquanto
        var='REC_MIN2' 
        item = layout.itemById(var)
        curVal=proj.readEntry("QEsg", 'REC_MIN')[0]
        item.setText(curVal)
        
        var='MANNING'
        pipesAtr = list(pipeLyr.getFeatures())
        lstMan=[]
        for feature in pipesAtr:
            lstMan.append(feature[var])            
        item = layout.itemById(var)
        curVal=str(mode(lstMan)) #mode => Moda, valor que mais se repete
        item.setText(curVal)        
        
        #Extensao da rede 1a e 2a etapas
        Lini,Lfim = self.CompVirtualRede(pipeLyr)       
        
        var='Lini' 
        item = layout.itemById(var)
        curVal='{:.2f}'.format(Lini)
        item.setText(curVal)
        
        var='Lfim' 
        item = layout.itemById(var)
        curVal='{:.2f}'.format(Lfim)
        item.setText(curVal)        
        
        QiniTot,QfimTot = self.Vazoes()#Vazao total inicio e fim de plano
        if Lini==0:#Caso de Interceptor
            QdisIni=0
        else:
            QdisIni=QiniTot/Lini
        if Lfim==0:#Caso de Interceptor
            QdisFim=0
        else:
            QdisFim=QfimTot/Lfim
        
        var='QdisIni' 
        item = layout.itemById(var)
        curVal='{:.5f}'.format(QdisIni)
        item.setText(curVal)
        
        var='QdisFim' 
        item = layout.itemById(var)
        curVal='{:.5f}'.format(QdisFim)
        item.setText(curVal)        
        
        self.abreLayout(layout)
        #msgTxt = QCoreApplication.translate('QEsg',u'Feito!:{}!'.format(rptName))
        #iface.messageBar().pushMessage('QEsg', msgTxt, level=Qgis.Info, duration=4)
    def criaLayout(self, layoutName, templatePath='style/report/QEsg_DadosGerais.qpt'):
        project = QgsProject.instance()
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        
        basepath = os.path.dirname(__file__)
        templateFile=os.path.join(basepath, templatePath)

        with open(templateFile) as f:
            template_content = f.read()
            doc = QDomDocument()
            doc.setContent(template_content)
            items, ok = layout.loadFromTemplate(doc, QgsReadWriteContext(), True)
            layout.setName(layoutName)
            project.layoutManager().addLayout(layout)
    
    def AtualizaNrosPagina(self, layout):
        pc = layout.pageCollection()        
        # loop through a range 0-number of pages
        NroPages = pc.pageCount()
        
        #apaga numeros de paginas existentes
        for i in range(NroPages):
            item = layout.itemById('page_label_' + str(i))
            if item:
                layout.removeItem(item)
        
        #cria numeros de paginas    
        for i in range(NroPages):            
            # create a new label item
            label = QgsLayoutItemLabel(layout)
            # create a name for the label object (this is to enable easy removal)
            label.setId('page_label_' + str(i))
            # the page number (starting at 1)
            label.setText("Página {} de {}".format(str(i+1),NroPages))
            # change font style and size (optional)
            label.setFont(QFont("Calibri", 7))
            label.setHAlign(Qt.AlignRight)
            label.setReferencePoint(QgsLayoutItem.UpperRight)
            
            # set size of label item 
            label.attemptResize(QgsLayoutSize(30, 10, QgsUnitTypes.LayoutMillimeters))
            # add the label to your layout
            layout.addLayoutItem(label)
            # specify location *and page* for label
            label.attemptMove(QgsLayoutPoint(287, 195, QgsUnitTypes.LayoutMillimeters), page=i)
    
    def abreLayout(self, layout):
        iface.openLayoutDesigner(layout=layout)
        designer = iface.openLayoutDesigners()[0]            
        designer.window().showMaximized()
        QApplication.processEvents()
        designer.view().zoomFull()
        
    def Vazoes(self): #Cópia da função da Classe QEsg_02Vazao
        proj = QgsProject.instance()
        popini=float(proj.readEntry("QEsg", 'POPINI')[0])
        popfim=float(proj.readEntry("QEsg", 'POPFIM')[0])
        perCapt=float(proj.readEntry("QEsg", 'PERCAPTA')[0])
        k1=float(proj.readEntry("QEsg", 'K1_DIA')[0])
        k2=float(proj.readEntry("QEsg", 'K2_HORA')[0])
        coefRet=float(proj.readEntry("QEsg", 'COEF_RET')[0])
        Qini=popini*perCapt*k2*coefRet/86400
        Qfim=popfim*perCapt*k1*k2*coefRet/86400
        return Qini,Qfim
        
    def CompVirtualRede(self,vLayer): #Cópia da função da Classe QEsg_02Vazao
        tot1a=tot2a=0
        for feat in vLayer.getFeatures():
            ext=feat['LENGTH']
            if ext == NULL or ext==0:
                return 0,0 #'Campo LENGTH com valor zero ou nulo'
            lados=feat['CONTR_LADO']
            if lados==NULL:
                return 0,0 #'Campo CONTR_LADO com valor zero ou nulo'
            etapa=feat['ETAPA']
            lVirtual=ext*lados/2
            if etapa<=1:
                tot1a+=lVirtual
                tot2a+=lVirtual
            elif etapa==2:
                tot2a+=lVirtual
        return tot1a,tot2a        
        