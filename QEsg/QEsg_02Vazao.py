# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QEsg_02Vazao
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
from __future__ import print_function
from __future__ import absolute_import
from builtins import str
from builtins import object
from qgis.core import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.utils import *
import os.path
from .QEsg_00Model import *
from .QEsg_04Estilos import *
#        from qgis.gui import QgsMessageBar
from .QEsg_00Common import *

class QEsg_02Vazao(object):
    common=QEsg_00Common()
    SETTINGS = common.SETTINGS
    goExec = True
    def onCancelButton(self):
        self.goExec=False
    def CalcVazao(self):
        proj = QgsProject.instance()
        ProjVar=proj.readEntry("QEsg", 'PIPES')[0]
        if ProjVar=='':
            msgTxt=QCoreApplication.translate('QEsg','Layer Indefinido: PIPES')
            iface.messageBar().pushMessage('QEsg', msgTxt, level=Qgis.Warning, duration=4)
            return False
        msg = QCoreApplication.translate('QEsg',u'Iniciando o Cálculo das Vazões...')
        progress,progressMBar,cancelButton=self.common.startProgressBar(msg)
        cancelButton.clicked.connect(self.onCancelButton)
        QApplication.processEvents()

        self.goExec=True     
        
        #Read pipe number order; True=Principal<Tributario
        pipeOrdem=proj.readNumEntry("QEsg", "PIPE_ORDEM",0)[0]==0  
        
        vLayer=proj.mapLayersByName(ProjVar)[0]
        if not self.VerificaNulos(vLayer):
            return False
        EmOrdem, msgOrdem = self.VerificaOrdem(vLayer, pipeOrdem)

        if not EmOrdem:
            # fix_print_with_import
            print(msgOrdem)
            self.Ordena(vLayer, pipeOrdem)
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
        msg = QCoreApplication.translate('QEsg',u'Calculando a Vazão do Trecho {}')

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
                        aviso = QCoreApplication.translate('QEsg',u'PV com mais de uma saída ou ordem de numeração dos coletores diferente da definida nas configurações! Identifique os "Ponta Seca" ou altere a ordem da numeração')
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
            if not EmOrdem:            
                msg = QCoreApplication.translate('QEsg',u'Vazões calculadas, mas ') + msgOrdem
                lvl = Qgis.Warning
            else:
                msg = QCoreApplication.translate('QEsg',u'Vazões calculadas com sucesso!')
                lvl = Qgis.Info            
            iface.messageBar().pushMessage(msg, level=lvl, duration=0)
        else:
            iface.messageBar().clearWidgets()
            iface.messageBar().findChildren(QToolButton)[0].setHidden(False)
            iface.messageBar().pushMessage("QEsg:", QCoreApplication.translate('QEsg',u'Cálculo de Vazões Interrompido! Favor NÃO salvar os resultados!'), level=Qgis.Warning, duration=0)

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
    def Vazoes(self):
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
            if etapa<=1:
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

    def VerificaOrdem(self,vLayer, Ordem=True):
        #vLayer=iface.activeLayer()
        cont=0
        msg=''
        sinal= 1 if Ordem else -1
        for feat in vLayer.getFeatures():
            cont+=1
            if cont>1:
                ClAtual=feat['Coletor']
                TrAtual=feat['Trecho']
                if ClAtual==Coletor:#Se o coletor atual é igual ao anterior
                    if TrAtual<=Trecho:
                        msg='Trecho {}-{} duplicado ou fora de ordem!'.format(ClAtual,TrAtual)
                        QgsMessageLog.logMessage(msg, self.SETTINGS, Qgis.Info)
                        return False,msg
                    elif TrAtual-Trecho>1:
                        msg='Trecho {}-{} Faltando!'.format(ClAtual, Trecho+1)
                        QgsMessageLog.logMessage(msg, self.SETTINGS, Qgis.Info)
                        return False,msg
                    else:
                        msg='ok'
                elif (Coletor-ClAtual==sinal) and (TrAtual==1):
                    msg='ok-novo trecho'
                else:
                    msg='Trecho {}-{} duplicado ou fora de ordem!'.format(ClAtual,TrAtual)
                    QgsMessageLog.logMessage(msg, self.SETTINGS, Qgis.Info)
                    return False,msg
            Coletor=feat['Coletor']
            Trecho=feat['Trecho']
            #print cont, Coletor, Trecho, msg
        return True, msg


    def Ordena(self,vLayer, Ordem=True):
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
        features = sorted(f_tr, key=get_Coletor, reverse=Ordem) #Now First index; reverse=True

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

