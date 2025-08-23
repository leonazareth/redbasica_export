# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QEsg is a QGIS plugin
 QEsg_IN_Design
 Class for Sewer network design according to India Technical Standard (CPHEEO:1993)
                              -------------------
        begin                : 2018-05-31
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
from builtins import object
from qgis.core import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.utils import *
import os.path
from ...QEsg_00Model import *
from ...QEsg_04Estilos import *
import math
from math import acos
from ...QEsg_00Common import *

class QEsg_03Dimens(object):
    common=QEsg_00Common()
    SETTINGS = common.SETTINGS
    goExec = True
    warnings = False
    def onCancelButton(self):
        self.goExec=False
    def Dimensiona(self):
        self.warnings = False
        proj = QgsProject.instance()
        ProjVar=proj.readEntry("QEsg", 'PIPES')[0]
        vLayer=proj.mapLayersByName(ProjVar)[0]
        if not self.VerificaNulos(vLayer):
            return False
        if not self.Verifica_InterfsNulos():
            return False
        if not self.Verifica_TrechosExistentes(vLayer):
            return False
        Trechos=vLayer.getFeatures()
        vLayer.startEditing()

        msg = '(India) '+QCoreApplication.translate('QEsg','Iniciando Dimensionamento...')
        progress,progressMBar,cancelButton=self.common.startProgressBar(msg)
        cancelButton.clicked.connect(self.onCancelButton)

        nroTrechos = vLayer.featureCount()*4 #Multiplied by 4 to have divide execution time. The loop is done twice, but the second loop is quick, so I assumed 25% of time for the second Loop.
        trCont = 0

        diam_min0=float(proj.readEntry("QEsg", "DN_MIN","150")[0])
        q_min=float(proj.readEntry("QEsg", "Q_MIN","1.50")[0])
        max_forcar=float(proj.readEntry("QEsg", "MAX_FORCAR","0.30")[0])#altura max para forcar a jusante
        deg_ignore=float(proj.readEntry("QEsg", "DEG_IGNORE","0.02")[0])#degrau para ser desprezado
        deg_min=float(proj.readEntry("QEsg", "DEG_MIN","0.00")[0])#degrau minimo
        Diam_progress=proj.readNumEntry("QEsg", "DIAM_PROGRESS",1)[0]#diametros progressivos
        chkIgualaGS=proj.readNumEntry("QEsg", "IGUALA_GS",0)[0]#diametros progressivos
        v_max=float(proj.readEntry("QEsg", "V_MAX","5.00")[0])#Velocidade maxima
        tubosMat=proj.readEntry("QEsg", "TUBOS_MAT","0")[0]
        if tubosMat=='0':#se nao tiver lista de diametros definidas
            iface.messageBar().pushMessage(self.SETTINGS, QCoreApplication.translate('QEsg',u'Lista de diâmetros indefinida!'),
                                           level=Qgis.Warning, duration=4)
            return False
        else:
            tubos=eval(tubosMat)
        diam_minTAB,nTAB=[[d,n] for d,n in tubos if d >= diam_min0][0]

        #Lista as interfencias de todos os trechos apenas uma vez
        lstIds,lstTr_inter=self.Lista_Interferencias(vLayer)
        msg = '(India) ' + QCoreApplication.translate('QEsg','Calculando Trecho {}')
        for trecho in Trechos:
            if self.goExec:
                progressMBar.setText(msg.format(trecho['DC_ID']))
                obs=''
                diam_min=diam_minTAB
                n=nTAB
                ctm=float(trecho['CTM'])
                ctj=float(trecho['CTJ'])
                qini=float(trecho['Q_INI'])
                qfim=float(trecho['Q_FIM'])
                qfim=max(qfim,q_min)
                rec_min=float(trecho['REC_MIN'])
                lam_max=float(trecho['LAM_MAX'])#relacao y/d max
                Etapa=int(trecho['ETAPA'])
                ext=float(trecho['LENGTH'])
                spdProj=float(trecho['VEL_PROJ'])
                #Inicio If da ETAPA>0 (rede projetada)
                if Etapa>0:
                    diamMont,n=self.pegaDiamMaxTrechosMont(vLayer, trecho['PVM'], diam_min,n)
                    #print 'tr={},diamMont={}'.format(trecho['DC_ID'],diamMont)
                    CCM_max=ctm-rec_min-diam_min/1000.
                    CCM_Mont_min, NAMontMin=self.pegaCotasMinTrechosMont(vLayer,trecho['PVM'],CCM_max,ctm)
                    CCM_max=min(CCM_max,CCM_Mont_min)
                    CCJ_max=ccj=ctj-rec_min-diamMont/1000.
                    if trecho['PONTA_SECA']=='S':
                        NAMontMin=ctm
                    else:
                        if Diam_progress:
                            diam_min=diamMont
                        #ccm=self.pegaNAMinColetorMont(vLayer,trecho['PVM'],CCM_max)
                    ccm=CCM_max
                    #calcula declividade economica
                    Ieco=(ccm-CCJ_max)/ext
                    
                    areaFull=qfim/1000./spdProj
                    diamFull=math.sqrt(areaFull/math.pi)*2*1000
                    
                    diam_min=max(diamFull,diam_min)
                    #Get Diameter and n from table, with Diameter greater or equal then calculated
                    diam,n=[[d,n] for d,n in tubos if d >= diam_min][0]
                    
                    #calcula declividade minima; India standard for Full Flow
                    Imin=self.CalcDecliBySpeed(spdProj, diam, n)
                    #Imin=0.0055*max(qini,q_min)**(-0.47)
                    #escolhe a maior das duas declividade
                    Io=max(Ieco,Imin)

                    #Imax=4.65*qfim**(-2./3.)                    
                    Imax,diam_Imax,n_Imax=self.CalcImax(qfim,v_max,lam_max,tubos)
                    #Imax=Imin

                    #Se a declividade for maior que a maxima, usa a maxima e calcula a cota do ccm, baixando-a
                    if Io>=Imax:
                        n=n_Imax
                        Io=Imax
                        ccm=CCJ_max+ext*Io #Tenta usar a declividade maxima
                        if ccm>CCM_max:
                           ccm=CCM_max
                           Io=(ccm-CCJ_max)/ext
                        #verificar profundidade maxima do PV e se superar, usar lamina igual a 0.50 como recomenda
                        #a norma para situacoes de v > vcritica
                    diam_m=diam/1000.
                    # ccm-=diam_m-(diamMont if trecho['Trecho']==1 or (not Diam_progress) else diam_min)/1000.

                    ccj=ccm-ext*Io

                    prfm=ctm-ccm
                    #print 'tr={},ccm={:.2f},ccj={:.2f},prfm={:.2f}'.format(trecho['DC_ID'],ccm,ccj,prfm)
                    if prfm<rec_min+diam_m:
                        ccm=ctm-rec_min-diam_m
                        ccj=ccm-ext*Io
                    prfj=ctj-ccj
                    if prfj<rec_min+diam_m:
                        ccj=ctj-rec_min-diam_m
                        ccm=ccj+ext*Io

                    if chkIgualaGS and trecho['Trecho']>1:
                        cgsAnt=CCM_Mont_min+diamMont/1000.
                        cgs=ccm+diam_m
                        if cgs>cgsAnt:
                            ccm-=cgs-cgsAnt
                            ccj=ccm-ext*Io

                    #Verifica Interferencias
                    tr_id=trecho.id()
                    #lista as interferencias apenas do trecho
                    interfs=[[distMont,cs,ci] for id,distMont,cs,ci,tipoInt in lstTr_inter if id == tr_id]
                    ccm_p=ccm
                    ccj_p=ccj
                    Ip=Io
                    for distMont,cs,ci in interfs:
                        #Cota da geratriz superior e inferior do coletor no local da interferencia
                        ccGI_inter=ccm_p-Ip*distMont
                        ccGS_inter=ccGI_inter+diam_m
                        if (ci<ccGS_inter<cs) or (ci<ccGI_inter<cs): #verifica se ha choque com a interferencia
                            QgsMessageLog.logMessage('Interf em choque tr:'+trecho['DC_ID']+
                                                     ' distMont:{0:.2f}'.format(distMont), 'QEsg_03Dimensionamento',
                                                      QgsMessageLog.INFO)
                            #if distMont<(ext/2.) or True:#se a interferencia esta mais proxima de montante; forcei aqui para sempre modificar montante
                            if Ip==Imin:
                                #aprofundar ccm e ccj igualmente
                                degInt=ccGS_inter-ci
                                ccm_p=ccm_p-degInt
                                ccj_p=ccj_p-degInt
                            else:
                                #fixa jusante e calcula declividade (menor) entre ci-diam_m e ccj
                                Ip=((ci-diam_m)-ccj_p)/(ext-distMont)
                                Ip=max(Ip,Imin)
                                diam_calc=self.CalcDiametro(qfim, n, Ip, lam_max)
                                if diam_calc<diam:
                                    if Ip>Imin:
                                        ccm_p=ccj_p+Ip*ext
                                    else:#Ip=Imin
                                        ccGS_inter2=ci
                                        ccGI_inter2=ccGS_inter2-diam_m
                                        ccm_p=ccGI_inter2+Ip*distMont
                                        ccj_p=ccm_p-ext*Ip
                                else:
                                    Ip=Io
                                    #aprofundar ccm e ccj igualmente
                                    degInt=ccGS_inter-ci
                                    ccm_p=ccm_p-degInt
                                    ccj_p=ccj_p-degInt
                    ccm=ccm_p
                    ccj=ccj_p
                    Io=Ip
                    #Fim das interferencias

                    qmax=max(qini,q_min)
                    theta_ini=self.CalcTheta(qmax, n, Io, diam, 0.00000001)
                    y_d_ini=0.5*(1.-math.cos(theta_ini/2.))

                    qmax=max(qfim,q_min)
                    theta_fim=self.CalcTheta(qmax, n, Io, diam, 0.00000001)
                    y_d_fim=0.5*(1.-math.cos(theta_fim/2.))

                    y=y_d_fim*diam_m
                    NAmon=ccm+y
                    degNA=NAmon-NAMontMin
                    if degNA>deg_ignore:#se verdade, existe um degrau negativo no NA maior que o degrau a ser desprezado, entao
                               #rebaixa ccm, Namon e ccj do trecho em calculo
                        degfim=max(degNA,deg_min)
                        ccmDegFim=ccm-degfim
                        if ccmDegFim<ccm:
                            ccm-=degfim
                            ccj-=degfim
                            NAmon=ccm+y
                    NAjus=ccj+y
                else: #else ETAPA=0 (Rede existente)
                    ccm=trecho['CCM']
                    ccj=trecho['CCJ']
                    Io=(ccm-ccj)/ext
                    diam=trecho['DIAMETER']
                    diam_m=diam/1000.
                    n=trecho['MANNING']

                    theta_ini=self.CalcTheta(max(qini,q_min), n, Io, diam, 0.00000001)
                    y_d_ini=0.5*(1.-math.cos(theta_ini/2.))
                    theta_fim=self.CalcTheta(max(qfim,q_min), n, Io, diam, 0.00000001)
                    y_d_fim=0.5*(1.-math.cos(theta_fim/2.))

                    y=y_d_fim*diam_m
                    NAmon=ccm+y
                    NAjus=ccj+y
                    obs='EXISTENTE/'
                #fim do if ETAPA

                #calcula Am,Rh,veloc, veloc_critiva, trativa, etc
                Amini=diam_m**2.*(theta_ini-math.sin(theta_ini))/8.
                Amfim=diam_m**2.*(theta_fim-math.sin(theta_fim))/8.
                v_ini=max(qini,q_min)/1000./Amini
                v_fim=max(qfim,q_min)/1000./Amfim

                Rh_ini=diam_m*(theta_ini-math.sin(theta_ini))/(4.*theta_ini)
                Rh_fim=diam_m*(theta_fim-math.sin(theta_fim))/(4.*theta_fim)
                v_crit=6.*(9.81*Rh_fim)**0.5
                trativa=10000*Rh_ini*Io

                prfm=ctm-ccm
                prfj=ctj-ccj

                #Verifica warnings and Observations
                if prfm>5 or prfj>5:
                    self.warnings=True
                    obs=(obs+';Prof>5' if obs else 'Prof>5')
                if v_ini>v_max or v_fim>v_max:
                    self.warnings=True
                    obs=(obs+';Vel>Vmax' if obs else 'Vel>Vmax')
                if v_ini>v_crit or v_fim>v_crit:
                    self.warnings=True
                    obs=(obs+';Vel>Vcrit' if obs else 'Vel>Vcrit')

                #Insere os resultados na tabela
                trecho['NA_MON']=NAmon
                trecho['NA_JUS']=NAjus
                trecho['PRFM']=prfm
                trecho['PRFJ']=prfj
                trecho['VEL_INI']=v_ini
                trecho['VEL_FIM']=v_fim
                trecho['VEL_CRI']=v_crit
                trecho['TRATIVA']=trativa
                trecho['LAM_INI']=y_d_ini
                trecho['LAM_FIM']=y_d_fim
                trecho['DIAMETER']=diam
                trecho['MANNING']=n
                trecho['DECL']=Io
                trecho['CCM']=ccm
                trecho['CCJ']=ccj
                trecho['OBS']=obs
                vLayer.updateFeature(trecho)
                trCont+=3
                percent = int((trCont/float(nroTrechos)) * 100)
                progress.setValue(percent)
                QApplication.processEvents()
            else:
                break
            #end if goExec
        #end for Trechos

        Trechos=vLayer.getFeatures()
        #faz loop novamente para medir os degraus
        for trecho in Trechos:
            if self.goExec:
                progressMBar.setText('(India) '+QCoreApplication.translate('QEsg','Finalizando...'))
                QApplication.processEvents()

                obs=trecho['OBS']
                pvj=trecho['PVJ']
                ccj=trecho['CCJ']
                CCM_MinJus=self.pegaCotaMinTrechosJus(vLayer, pvj,ccj)
                degCC=ccj-CCM_MinJus
                if degCC>0:
                    if degCC>0.5: # quedas maiores que 0.50 usa TQ segundo Norma Brasileira
                        tipo='TQ'
                    else:
                        tipo='DG'
                    trecho['OBS']=(obs if obs else '')+tipo+'={:.3f}m'.format(degCC)
                vLayer.updateFeature(trecho)

                trCont+=1
                percent = int((trCont/float(nroTrechos)) * 100)
                progress.setValue(percent)
            else:
                break
        if self.goExec:
            EstiloClasse=Estilos()
            EstiloClasse.CarregaEstilo(vLayer, 'rede_dimensionamento.qml')
            vLayer.triggerRepaint()
            iface.messageBar().clearWidgets()
            iface.messageBar().findChildren(QToolButton)[0].setHidden(False)
            if self.warnings:
                iface.messageBar().pushMessage(self.SETTINGS,'(India) '+ QCoreApplication.translate('QEsg',u'Rede dimensionada com advertências. Favor verificar o campo "OBS" para cada trecho na Tabela de atributos!'),
                                           level=Qgis.Info, duration=0)
            else:
                iface.messageBar().pushMessage(self.SETTINGS,'(India) '+ QCoreApplication.translate('QEsg',u'Rede dimensionada com sucesso!'),
                                           level=Qgis.Info, duration=0)
        else:
            iface.messageBar().clearWidgets()
            iface.messageBar().findChildren(QToolButton)[0].setHidden(False)
            iface.messageBar().pushMessage(self.SETTINGS, '(India) '+ QCoreApplication.translate('QEsg',u'Operação cancelada!Favor NÃO salvar os resultados!'),
                                           level=Qgis.Warning, duration=0)
            self.goExec=True

    #Lista as interferecias associando-as ao trecho mais proximo encontrado
    #incluindo a distancia ao PV de montante
    def Lista_Interferencias(self,pipeLayer):
        interfLayer=self.PegaQEsgLayer('INTERFERENCES')
        if interfLayer==False:
            return [],{}
        interfFeats=interfLayer.getFeatures()#

        pipeFeats=pipeLayer.getFeatures()#
        spIndex = QgsSpatialIndex() #create spatial index object
        feat = QgsFeature()
        # insert features to index
        while pipeFeats.nextFeature(feat):
            spIndex.insertFeature(feat)


        lstTr_inter=[]#Lista dos ids,distToMont dos trechos com interferencias
        lstIds=[]
        Invalidos=[NULL,None,'']
        aviso=''
        while interfFeats.nextFeature(feat):
            cs=feat['CS']
            ci=feat['CI']
            tipoInt=feat['TIPO_INT']
            geometry = feat.geometry()
            pt=geometry.asPoint()
            # QgsSpatialIndex.nearestNeighbor (QgsPoint point, int neighbors)
            nearestIds = spIndex.nearestNeighbor(pt,1) # we need only one neighbour
            nearestId=nearestIds[0]
            lstIds.append(nearestId)

            lineIter = pipeLayer.getFeatures(QgsFeatureRequest().setFilterFid(nearestId))
            ftr = QgsFeature()
            lineIter.nextFeature(ftr)
            #setup distance
            distance = QgsDistanceArea()
            distToMont=distance.measureLine(pt, ftr.geometry().asPolyline()[0])#poderia usar computeDistanceFlat
            lstTr_inter.append([nearestId,distToMont,cs,ci,tipoInt])
#         pipeLayer.setSelectedFeatures(lstIds)
#         print lstTr_inter
        return lstIds,lstTr_inter

    def PegaQEsgLayer(self,aForma):
        proj = QgsProject.instance()
        #aForma='PIPES'
        ProjVar=proj.readEntry("QEsg", aForma)[0]
        if ProjVar=='':
#             msgTxt=QCoreApplication.translate('QEsg','Layer Indefinido: ') +aForma
#             QMessageBox.warning(None,'QEsg',msgTxt)
            return False
        LayerLst=proj.mapLayersByName(ProjVar)
        if LayerLst:
            layer = proj.mapLayersByName(ProjVar)[0]
            return layer
        else:
#             msgTxt=aForma+'='+ProjVar+QCoreApplication.translate('QEsg',u' (Layer não encontrado)')
#             QMessageBox.warning(None,'QEsg',msgTxt)
            return False

    def Verifica_TrechosExistentes(self,vLayer):#retorna Falso se houver trecho com identificacao nula
        Invalidos=[NULL,None,'']
        request = QgsFeatureRequest()
        request.setFilterExpression('"ETAPA"=0')
        i=0
        for feat in vLayer.getFeatures(request):
            if i==0:
                vLayer.startEditing()
            i+=1
            ccm=feat['CCM']
            ccj=feat['CCJ']
            ctm=feat['CTM']
            ctj=feat['CTJ']
            prfm=feat['PRFM']
            prfj=feat['PRFJ']
            diam=feat['DIAMETER']
            n=feat['MANNING']
            if n in Invalidos:
                aviso=QCoreApplication.translate('QEsg',u'\'{}\' com valor Nulo em Trecho Existente!').format('MANNING')
                self.FeicaoSelecionaMostraAvisa(vLayer, feat.id(), aviso)
                return False
            if diam in Invalidos:
                aviso=QCoreApplication.translate('QEsg',u'\'{}\' com valor Nulo em Trecho Existente!').format('DIAMETER')
                self.FeicaoSelecionaMostraAvisa(vLayer, feat.id(), aviso)
                return False
            if (ccm in Invalidos) and (prfm in Invalidos):
                aviso=QCoreApplication.translate('QEsg',u'\'{}\' e \'{}\' com valores Nulos em Trecho Existente!').format('CCM','PRFM')
                self.FeicaoSelecionaMostraAvisa(vLayer, feat.id(), aviso)
                return False
            else:
                if ccm in Invalidos:
                    feat['CCM']=ctm-prfm
                else:
                    feat['PRFM']=ctm-ccm
                vLayer.updateFeature(feat)
            if (ccj in Invalidos) and (prfj in Invalidos):
                aviso=QCoreApplication.translate('QEsg',u'\'{}\' e \'{}\' com valores Nulos em Trecho Existente!').format('CCJ','PRFJ')
                self.FeicaoSelecionaMostraAvisa(vLayer, feat.id(), aviso)
                return False
            else:
                if ccj in Invalidos:
                    feat['CCJ']=ctj-prfj
                else:
                    feat['PRFJ']=ctj-ccj
                vLayer.updateFeature(feat)
        return True

    def Verifica_InterfsNulos(self):#retorna Falso se houver trecho com identificacao nula
        interfLayer=self.PegaQEsgLayer('INTERFERENCES')
        if interfLayer!=False:
            CamposVerif=['CS','CI'] #QEsgModel.COLUMNS['INTERFERENCES']
            Invalidos=[NULL,None,'']
            for feat in interfLayer.getFeatures():
                for campo in CamposVerif:
                    oValor=feat[campo]
                    if oValor in Invalidos:
                        aviso=QCoreApplication.translate('QEsg',u'\'{}\' com valor Nulo!').format(campo)
                        self.FeicaoSelecionaMostraAvisa(interfLayer, feat.id(), aviso)
                        return False
        return True


    def VerificaNulos(self,vLayer):#retorna Falso se houver trecho com identificacao nula
        CamposVerif=['DC_ID','Coletor','Trecho','PVM','PVJ','CTM','CTJ','Q_CONC_INI','Q_CONC_FIM','Q_INI','Q_FIM','REC_MIN','LAM_MAX','LENGTH','PONTA_SECA']
        Invalidos=[NULL,None,'']
        for feat in vLayer.getFeatures():
            for campo in CamposVerif:
                oValor=feat[campo]
                if oValor in Invalidos:
                    aviso=QCoreApplication.translate('QEsg',u'\'{}\' com valor Nulo! Utilize a Ferramenta de Preenchimento').format(campo)
                    self.FeicaoSelecionaMostraAvisa(vLayer, feat.id(), aviso)
                    return False
        return True

    def FeicaoSelecionaMostraAvisa(self,Layer,FeicaoID,aviso):
        Layer.select(FeicaoID)
        mapCanvas = iface.mapCanvas()
        mapCanvas.zoomToSelected(Layer)
        iface.messageBar().pushMessage("QEsg:", aviso, level=Qgis.Warning, duration=4)

    def pegaCotaMinTrechosJus(self,vLayer,pvj,ccj):
        CCM_min=ccj
        for feat in vLayer.getFeatures():
            if feat['PVM']==pvj:
                CCM_min=min(CCM_min,feat['CCM'])
        return CCM_min
    def pegaCotasMinTrechosMont(self,vLayer,pvm, CCM_max,NAMax):
        CCM_min=CCM_max
        NAMontMin=NAMax
        for feat in vLayer.getFeatures():
            if feat['PVJ']==pvm:
                CCM_min=min(CCM_min,feat['CCJ'])
                NAMontMin=min(NAMontMin,feat['NA_JUS'])
        return CCM_min,NAMontMin
    def pegaDiamMaxTrechosMont(self,vLayer, pvm, diam_min,n):
        diam_max=diam_min
        manning=n
        for feat in vLayer.getFeatures():
            if feat['PVJ']==pvm:
                if feat['DIAMETER']>diam_max:
                    diam_max=feat['DIAMETER']
                    manning=feat['MANNING']
        return diam_max, manning
    def CalcDecl(self,q_ls,n,D, y_d):
        #Ariovaldo Nuvolari, Esgoto sanitário, pagina 50
        theta=2*math.acos(1.-2.*y_d)
        Am_D2=(theta-math.sin(theta))/8.
        Rh_D=(theta-math.sin(theta))/(4.*theta)
        DeclCalc=(n*(q_ls/1000.)/(Am_D2*Rh_D**(2./3.)*(D/1000.)**(8./3.)))**(2.)
        return DeclCalc
    def CalcDiametro(self,q_ls,n,Io, y_d):
        #Ariovaldo Nuvolari, Esgoto sanitário, pagina 50
        theta=2*math.acos(1.-2.*y_d)
        Am_D2=(theta-math.sin(theta))/8.
        Rh_D=(theta-math.sin(theta))/(4.*theta)
        DiamCalc=((n*(q_ls/1000.)/(Io**0.5*Am_D2*Rh_D**(2./3.)))**(3./8.))*1000
        return DiamCalc
    def CalcAm(self, Diam_mm, Ang):
        Diam_m=Diam_mm/1000.
        resp=Diam_m**2.*(Ang-math.sin(Ang))/8.
        return resp
    def CalcTheta(self,q_ls,n,Io, diam, precisao):
        diam_m=float(diam)/1000.
        M=n*(float(q_ls)/1000.)/(Io**0.5*diam_m**(8./3.))
        MaxIter = 1000
        #'0<x<2Pi
        theta_s = 5.27810713800479
        if M >= 0.335282:
            aviso=QCoreApplication.translate('QEsg','Trecho em carga! Verifique a rede')
            iface.messageBar().pushMessage("QEsg:", aviso, level=Qgis.Warning, duration=4)
            return math.pi*2
        theta_i = 0
        conclui=True
        cont=0
        while conclui:
            theta = (theta_s + theta_i) / 2.
            M1 = ((theta - math.sin(theta)) / 8.) * ((theta - math.sin(theta)) / (4 * theta)) ** (2. / 3.)
            if M1 > M and M1 < 0.335282:
                theta_s = theta
            else:
                theta_i = theta
            cont += 1
            conclui = not ((abs(M1 - M) <= precisao) or (cont >= MaxIter))
        if cont >= MaxIter:
            # fix_print_with_import
            print('(MaxIter com erro={0:8f})'.format(abs(M1 - M)))
        return theta
    def CalcImax(self,qfim,v_max,lam_max,tubos):
        Amfim_nec=qfim/1000./v_max
        theta=2.*math.acos(1.-2.*lam_max)
        Dmin=1000.*math.sqrt(8.*Amfim_nec/(theta-math.sin(theta)))

        if Dmin>=tubos[-1][0]:#Verifica se o maior tubo é insuficiente
            diam=tubos[-1][0]
            n=tubos[-1][1]
            Imax=4.65*qfim**(-2./3.)#Formula aproximada, Nuvolari
        else:
            #Pega o primeiro diametro e seu manning da tabela maior do que Dmin
            diam,n=[[d,n] for d,n in tubos if d > Dmin][0]
            #ReCalcula o theta para a Am necessaria e o Diam da tabela
            theta=self.CalcThetaByAm_Diam(Amfim_nec,diam)
            Rh=(theta-math.sin(theta))/4./theta*diam/1000
            Imax=(v_max*n/Rh**(2./3.))**2
        return Imax,diam,n
    #India slope calculation
    def CalcDecliBySpeed(self, Spd, D, n):
        result = 1/((n*Spd)/((3.968*10**-3)*(D**0.667)))**2
        result = math.trunc(result/10)*10
        return 1/result
    def CalcThetaByAm_Diam(self,Am,Diam_mm,precisao=1e-9,MaxIter=1000):
        d=Diam_mm/1000
        L1=Am*8./d**2.
        xs=2*math.pi
        xi=0
        conclui=True
        cont=0
        while conclui:
            x=(xs+xi)/2
            L2=x - math.sin(x)
            if L2>L1:
                xs=x
            else:
                xi=x
            cont+=1
            conclui = not ((abs(L1 - L2) <= precisao) or (cont >= MaxIter))
        if cont >= MaxIter:
            # fix_print_with_import
            print(' (erro={0:8f})'.format(abs(L1 - L2)))
        return x
    def CriaNos(self,prefixo,Adiciona):
        #Codigo adaptado do plugin Networks
        #copyright            : (C) 2014 by CEREMA Nord-Picardie
        #email                : patrick.palmier@cerema.fr
        #layer=self.iface.activeLayer()
        proj = QgsProject.instance()
        
        layer=self.PegaQEsgLayer('PIPES')
        if layer==False:
            aviso=QCoreApplication.translate('QEsg',u'Layer Tipo \'PIPES\' indefinido ou não encontrado!')
            iface.messageBar().pushMessage('CriaNos', aviso, level=Qgis.Warning, duration=4)
            return False
        
        #ProjVar=proj.readEntry("QEsg", 'PIPES')[0]
        #layer=proj.mapLayersByName(ProjVar)[0]
        
        uriPath=layer.dataProvider().dataSourceUri()
        baseName = os.path.split(uriPath)[0]
        #baseName = fileInfo.baseName()
        #os.getcwd()
        nome_arquivo, __=QFileDialog.getSaveFileName(caption=QCoreApplication.translate('QEsg',u'Salvar o layer de nós como:'),
                                                 directory=baseName,filter="ESRI Shape File (*.shp)")
        if not nome_arquivo:
            #QMessageBox.information(None,'QEsg',u'Operação cancelada!')
            return

        #Apenas para lidar com o bug do QT4 no linux, que nao coloca a extensao automaticamente no filename
#         if not nome_arquivo.endswith('.shp'):
#             nome_arquivo+='.shp'

        campos=QgsFields()
        for campo in QEsgModel.COLUMNS['JUNCTIONS']:
            campos.append(QgsField(campo, QEsgModel.CAMPOSDEF[campo][0],
                                           QEsgModel.CAMPOSDEF[campo][1],
                                           QEsgModel.CAMPOSDEF[campo][2],
                                           QEsgModel.CAMPOSDEF[campo][3])
                              )
        layer_nos=QgsVectorFileWriter(nome_arquivo,"UTF-8",campos,QgsWkbTypes.Point,layer.crs(),"ESRI Shapefile")
        if layer_nos.hasError() != QgsVectorFileWriter.NoError:
            msgTxt=layer_nos.errorMessage()
            QgsMessageLog.logMessage(msgTxt,'QEsg_03Dimensionamento',level=Qgis.Critical)
            QMessageBox.critical(None,'QEsg',msgTxt)
            return
        nos={}
        cotasTN={}
        lines=layer.getFeatures()
        for linha in lines:
            glinha=linha.geometry()
            if glinha.wkbType()==QgsWkbTypes.MultiLineString:
                g=glinha.asMultiPolyline()
                na=g[0][0]
                nb=g[-1][-1]
            elif glinha.wkbType()==QgsWkbTypes.LineString:
                g=glinha.asPolyline()
                na=g[0]
                nb=g[-1]
            if (na not in nos):
                nos[na]=linha['PVM']
                cotasTN[na]=linha['CTM']
            if (nb not in nos):
                nos[nb]=linha['PVJ']
                cotasTN[nb]=linha['CTJ']

        #outs=open("c:/temp/nos.txt","w")
        for i,n in enumerate(nos):
            node=QgsFeature()
            node.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(n[0],n[1])))
            if cotasTN[n]:
                CotaTN=float(cotasTN[n])
            else:
                CotaTN=None
            node.setAttributes([nos[n],CotaTN])#str(nos[n]) passou a dar erro em qgis 2.16
            layer_nos.addFeature(node)
        #outs.write(str(n)+";"+str(nos[n])+"\n")
        #outs.close()
        del layer_nos
        if Adiciona:
            nome_camada=os.path.splitext(os.path.basename(nome_arquivo))[0]
            vlayer=QgsVectorLayer(nome_arquivo,nome_camada,'ogr')
            proj.addMapLayer(vlayer)

            EstiloClasse=Estilos()
            EstiloClasse.CarregaEstilo(vlayer, 'nos_nomes.qml')
            proj.writeEntry("QEsg", "JUNCTIONS", nome_camada)