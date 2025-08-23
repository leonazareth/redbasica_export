# -*- coding: utf-8 -*-
"""
/***************************************************************************
 A QGIS plugin for sewer network design
 QEsg_IN_Flow - Flow calculation according to India-CPHEEO:1993 Technical Standard
 
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
from __future__ import print_function
from __future__ import absolute_import
from builtins import str
from builtins import object
from qgis.core import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.utils import *
import os.path
from ...QEsg_00Model import *
from ...QEsg_04Estilos import *
#        from qgis.gui import QgsMessageBar
from ...QEsg_00Common import *

class QEsg_02Vazao(object):
    common=QEsg_00Common()
    SETTINGS = common.SETTINGS
    goExec = True
    def onCancelButton(self):
        self.goExec=False
    def CalcVazao(self):
        msg = QCoreApplication.translate('QEsg',u'(India) Iniciando o Cálculo das Vazões...')
        progress,progressMBar,cancelButton=self.common.startProgressBar(msg)
        cancelButton.clicked.connect(self.onCancelButton)
        QApplication.processEvents()

        self.goExec=True
        proj = QgsProject.instance()
        ProjVar=proj.readEntry("QEsg", 'PIPES')[0]
        vLayer=proj.mapLayersByName(ProjVar)[0]
        if not self.VerificaNulos(vLayer):
            return False
        EmOrdem, msg = self.VerificaOrdem(vLayer)
        if not EmOrdem:
            # fix_print_with_import
            print(msg)
            self.Ordena(vLayer)
        Lini,Lfim = self.CompVirtualRede(vLayer)#Extensao da rede 1a e 2a etapas
        QiniTot,QfimTot = self.Vazoes()#Vazao total inicio e fim de plano
        if Lini==0:#Caso de Interceptor
            QdisIni=0
        else:
            QdisIni=QiniTot/Lini
        if Lfim==0:#Caso de Interceptor
            QdisFim=0
        else:
            QdisFim=QfimTot/Lfim
        Qinfilt=float(proj.readEntry("QEsg", 'COEF_INF')[0])

        vLayer.startEditing()

        nroTrechos = vLayer.featureCount()
        trCont = 0
        msg = QCoreApplication.translate('QEsg',u'(India) Calculando a Vazão do Trecho {}')

        for feat in vLayer.getFeatures():
            if self.goExec:
                progressMBar.setText(msg.format(feat['DC_ID']))

                ext=feat['LENGTH']
                QconcIni=feat['Q_CONC_INI']
                QconcFim=feat['Q_CONC_FIM']
                oPVM=feat['PVM']
                pontaSeca=feat['PONTA_SECA']
                lados=feat['CONTR_LADO']
                if pontaSeca=='S':
                    QmontIni = QmontFim = 0
                else:
                    QmontIni, QmontFim, Valido=self.VazaoTrechosMont(vLayer, oPVM)
                    if not Valido:
                        aviso = QCoreApplication.translate('QEsg',u'Não é permitido PV com mais de uma saída! Identifique os "Ponta Seca"')
                        self.FeicaoSelecionaMostraAvisa(vLayer, feat.id(), aviso)
                        return False
                QtrIni=QmontIni+QconcIni+(Qinfilt+QdisIni*lados/2)*ext
                QtrFim=QmontFim+QconcFim+(Qinfilt+QdisFim*lados/2)*ext
                feat['Q_INI']=QtrIni
                feat['Q_FIM']=QtrFim
                vLayer.updateFeature(feat)

                trCont+=1
                percent = int((trCont/float(nroTrechos)) * 100)
                progress.setValue(percent)
                QApplication.processEvents()
            else:
                break
        if self.goExec:
            EstiloClasse=Estilos()
            EstiloClasse.CarregaEstilo(vLayer, 'rede_vazao.qml')
            vLayer.triggerRepaint()
            iface.messageBar().clearWidgets()
            iface.messageBar().findChildren(QToolButton)[0].setHidden(False)
            iface.messageBar().pushMessage("QEsg:", QCoreApplication.translate('QEsg',u'(India) Vazões calculadas com sucesso!'), level=Qgis.Info, duration=0)
        else:
            iface.messageBar().clearWidgets()
            iface.messageBar().findChildren(QToolButton)[0].setHidden(False)
            iface.messageBar().pushMessage("QEsg:", QCoreApplication.translate('QEsg',u'(India) Cálculo de Vazões Interrompido! Favor NÃO salvar os resultados!'), level=Qgis.Warning, duration=0)

    def VazaoTrechosMont(self,vLayer,pvm):
        #somar as vazoes dos trechos que desaguam em pvm
        QmontIni=QmontFim=0
        for feat in vLayer.getFeatures():
            if feat['PVJ']==pvm:
                if feat['Q_INI']==NULL or feat['Q_FIM']==NULL:
                    return 0,0, False
                QmontIni+=feat['Q_INI']
                QmontFim+=feat['Q_FIM']
        return QmontIni, QmontFim, True
    def getFromTable(self,popTbl,popul,Col_id):
        for linha in popTbl:
            lower=linha[0]
            upper=linha[1]
            if lower<popul<=upper:
                return float(linha[2])
        print('range not found')
        return 0 #range not found
    def Vazoes(self):
        #India Flow Calc
        proj = QgsProject.instance()
        popini=float(proj.readEntry("QEsg", 'POPINI')[0])
        popfim=float(proj.readEntry("QEsg", 'POPFIM')[0])
        perCapt=float(proj.readEntry("QEsg", 'PERCAPTA')[0])
        
        #k1 and k2 replaced by peak factor from table
        k1=float(proj.readEntry("QEsg", 'K1_DIA')[0])
        k2=float(proj.readEntry("QEsg", 'K2_HORA')[0])
        popTblVar=proj.readEntry("QEsg", "IN/POP_TBL","0")[0]
        if popTblVar=='0':
            print('No peak table found using peakCoef=3!')
            peakCoef_ini=3
            peakCoef_fim=3
        else:
            peakCoef_ini=self.getFromTable(eval(popTblVar),popini,2)
            #print('pk_ini={}'.format(peakCoef_ini))
            peakCoef_fim=self.getFromTable(eval(popTblVar),popfim,2)
            #print('pk_fim={}'.format(peakCoef_fim))
        coefRet=float(proj.readEntry("QEsg", 'COEF_RET')[0])
        Qini=popini*perCapt*peakCoef_ini*coefRet/86400 #peak factor k1*k2 replaced by peakCoef
        Qfim=popfim*perCapt*peakCoef_fim*coefRet/86400 #peak factor k1*k2 replaced by peakCoef
        return Qini,Qfim
    def CompVirtualRede(self,vLayer):
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
            if etapa==1:
                tot1a+=lVirtual
                tot2a+=lVirtual
            elif etapa==2:
                tot2a+=lVirtual
        return tot1a,tot2a

    def VerificaNulos(self,vLayer):#retorna Falso se houver trecho com identificacao nula
        CamposVerif=['DC_ID','Coletor','Trecho','PVM','PVJ','Q_CONC_INI','Q_CONC_FIM']
        Invalidos=[NULL,None,'']
        for feat in vLayer.getFeatures():
            for campo in CamposVerif:
                oValor=feat[campo]
                if oValor in Invalidos:
                    aviso=QCoreApplication.translate('QEsg',u'\'{}\' com valor Nulo! Utilize a Ferramenta de Numeração ou Preenchimento').format(campo)
                    self.FeicaoSelecionaMostraAvisa(vLayer, feat.id(), aviso)
                    return False
        return True

    def FeicaoSelecionaMostraAvisa(self,Layer,FeicaoID,aviso):
        Layer.select(FeicaoID)
        mapCanvas = iface.mapCanvas()
        mapCanvas.zoomToSelected(Layer)
        iface.messageBar().clearWidgets()
        iface.messageBar().findChildren(QToolButton)[0].setHidden(False)
        iface.messageBar().pushMessage("QEsg:", aviso, level=Qgis.Warning, duration=10)

    def VerificaOrdem(self,vLayer):
        #vLayer=iface.activeLayer()
        cont=0
        msg=''
        for feat in vLayer.getFeatures():
            cont+=1
            if cont>1:
                ClAtual=feat['Coletor']
                TrAtual=feat['Trecho']
                if ClAtual==Coletor:#Se o coletor atual é igual ao anterior
                    if TrAtual<=Trecho:
                        msg='Trecho ' + str(TrAtual)+' duplicado ou fora de ordem!'
                        QgsMessageLog.logMessage(msg, self.SETTINGS, Qgis.Info)
                        return False,msg
                    elif TrAtual-Trecho>1:
                        msg='Trecho ' + str(Trecho+1)+' Faltando!'
                        QgsMessageLog.logMessage(msg, self.SETTINGS, Qgis.Info)
                        return False,msg
                    else:
                        msg='ok'
                elif (Coletor-ClAtual==1) and (TrAtual==1):
                    msg='ok-novo trecho'
                else:
                    msg='Coletor ' + str(ClAtual)+' duplicado ou fora de ordem!'
                    QgsMessageLog.logMessage(msg, self.SETTINGS, Qgis.Info)
                    return False,msg
            Coletor=feat['Coletor']
            Trecho=feat['Trecho']
            #print cont, Coletor, Trecho, msg
        return True, msg


    def Ordena(self,vLayer):
        QgsMessageLog.logMessage('Chamou Ordena', self.SETTINGS, Qgis.Info)
        def get_Trecho(f):
            return f['Trecho']
        def get_Coletor(f):
            return f['Coletor']

        # Create a sorted list of features. The `sorted` function
        # will read all features into a list and return a new list
        # sorted in this case by the features name value returned
        # by the `get_name` function

        f_tr = sorted(vLayer.getFeatures(), key=get_Trecho) #Secondary index first
        features = sorted(f_tr, key=get_Coletor, reverse=True) #Now First index

        #Apago as feicoes originais
        vLayer.startEditing()
        listOfIds = [feat.id() for feat in vLayer.getFeatures()]
        vLayer.deleteFeatures( listOfIds )
        #for fid in featList:
        #    vLayer.deleteFeature(fid)

        #Create features again in right order
        for feicao in features:
            # geom=feicao.constGeometry()
            # attrs=feicao.attributes()
            # fet = QgsFeature()
            # fet.setGeometry( geom)
            # fet.setAttributes(attrs)
            if not(vLayer.addFeature(feicao)):#False=not update extent
                QMessageBox.warning(None,'QEsg',QCoreApplication.translate('QEsg',u'Falha ao adicionar feição'))
                return
        vLayer.updateExtents()

