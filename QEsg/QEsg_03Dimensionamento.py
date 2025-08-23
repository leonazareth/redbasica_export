# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QEsg_03Dimensionamento
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
from builtins import object
from qgis.core import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.utils import *
import os.path
from .QEsg_00Model import *
from .QEsg_04Estilos import *
import math
from math import acos
from .QEsg_00Common import *
from .QEsg_01Campos import *
import re

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
        if ProjVar=='':
            msgTxt=QCoreApplication.translate('QEsg','Layer Indefinido: PIPES')
            iface.messageBar().pushMessage('QEsg', msgTxt, level=Qgis.Warning, duration=4)
            return False
        vLayer=proj.mapLayersByName(ProjVar)[0]
        
        #Verifica se tem os campos padroes, em caso negativo, sugere criar e somente continua se forem criados
        CamposClasse=QEsg_01Campos()
        if not CamposClasse.CriaCampos('PIPES',vLayer):
            iface.messageBar().pushMessage(self.SETTINGS, QCoreApplication.translate('QEsg',u'Operação cancelada! Para o dimensionamento é necessário criar os campos obrigatórios!'), level=Qgis.Warning, duration=0)
            return False
            
        if not self.VerificaNulos(vLayer):
            return False
        if not self.Verifica_InterfsNulos():
            return False
        if not self.Verifica_TrechosExistentes(vLayer):
            return False            
        
        if vLayer.selectedFeatureCount()==0:
            feicoes=vLayer.getFeatures()
        else:
            resp=QMessageBox.question(None,'QEsg',QCoreApplication.translate('QEsg','Dimensionar apenas os trechos selecionados?'),
                                      QMessageBox.Yes, QMessageBox.No)
            if resp==QMessageBox.Yes:
                feicoes=vLayer.selectedFeatures()
            else:
                feicoes=vLayer.getFeatures()        
            
        #Trechos=vLayer.getFeatures()
        Trechos=list(feicoes)
        vLayer.startEditing()

        msg = QCoreApplication.translate('QEsg','Iniciando Dimensionamento...')
        progress,progressMBar,cancelButton=self.common.startProgressBar(msg)
        cancelButton.clicked.connect(self.onCancelButton)

        nroTrechos = len(Trechos)*3+ vLayer.featureCount() # Multiplied by 4 to have divide execution time. The loop is done twice, but the second loop is quick, so I assumed 25% of time for the second Loop.
        trCont = 0

        diam_min0=float(proj.readEntry("QEsg", "DN_MIN","150")[0])
        q_min=float(proj.readEntry("QEsg", "Q_MIN","1.50")[0])
        max_forcar=float(proj.readEntry("QEsg", "MAX_FORCAR","0.30")[0])#altura max para forcar a jusante
        deg_ignore=float(proj.readEntry("QEsg", "DEG_IGNORE","0.02")[0])#degrau para ser desprezado
        deg_min=float(proj.readEntry("QEsg", "DEG_MIN","0.00")[0])#degrau minimo
        deg_max=float(proj.readEntry("QEsg", "DEG_MAX","0.60")[0])#degrau maximo
        Diam_progress=proj.readNumEntry("QEsg", "DIAM_PROGRESS",1)[0]#diametros progressivos
        chkIgualaGS=proj.readNumEntry("QEsg", "IGUALA_GS",0)[0]#Iguala geratriz superior
        v_max=float(proj.readEntry("QEsg", "V_MAX","5.00")[0])#Velocidade maxima
        Imin_opt=proj.readNumEntry("QEsg", "I_MIN_OPT",0)[0]#Tipo de calculo para declividade mínima; 0=NBR 9649;1=NBR 14486;2=MANUAL
        
        tubosMat=proj.readEntry("QEsg", "TUBOS_MAT","0")[0]
        if tubosMat=='0':#se nao tiver lista de diametros definidas
            iface.messageBar().pushMessage(self.SETTINGS, QCoreApplication.translate('QEsg',u'Lista de diâmetros indefinida!'),
                                           level=Qgis.Warning, duration=4)
            return False
        else:
            tubos=eval(tubosMat)
        diam_minTAB,nTAB=[[d,n] for d,n in tubos if d >= diam_min0][0]

        interf_ON = proj.readNumEntry("QEsg", "INTERFERENCES_ON",1)[0]
        #Lista as interfencias de todos os trechos apenas uma vez se "INTERFERENCES_ON" Checkbox is ON
        if interf_ON:
            lstIds,lstTr_inter=self.Lista_Interferencias(vLayer)
        else: 
            lstIds,lstTr_inter=[],{}
        msg = QCoreApplication.translate('QEsg','Calculando Trecho {}')
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
                rec_min=float(trecho['REC_MIN'])
                lam_max=float(trecho['LAM_MAX'])#relacao y/d max
                Etapa=int(trecho['ETAPA'])
                ext=float(trecho['LENGTH'])
                
                #calcula declividade minima para qmin, ex:1.5L/s
                if Imin_opt==0:
                    Imin=0.0055*max(qini,q_min)**(-0.47) #NBR 9649 - Nov 1986 (Embasa-BA, Sabesp-SP) ;Manning n = 0,013
                elif Imin_opt==1:
                    Imin=0.0035*max(qini,q_min)**(-0.47) #NBR 14486 - Mar 2000 (Cagece-CE) ;Manning n = 0,010
                elif Imin_opt==2:
                    Imin=float(trecho['DECL_MIN']) #Valor informado manualmente na tabela de atributos
                
                #Inicio If da ETAPA>0 (rede projetada)
                if Etapa>0:
                    diamMont,n=self.pegaDiamMaxTrechosMont(vLayer, trecho['PVM'], diam_min,n)
                    #print 'tr={},diamMont={}'.format(trecho['DC_ID'],diamMont)
                    CCM_max=ctm-rec_min-diam_min/1000.
                    if trecho['PONTA_SECA']=='S':
                        CCM_Mont_min=CCM_max
                        NAMontMin=ctm
                    else:
                        CCM_Mont_min, NAMontMin=self.pegaCotasMinTrechosMont(vLayer,trecho['PVM'],CCM_max,ctm)
                        if Diam_progress:
                            diam_min=diamMont
                        #ccm=self.pegaNAMinColetorMont(vLayer,trecho['PVM'],CCM_max)                    
                    CCM_max=min(CCM_max,CCM_Mont_min)
                    CCJ_max=ccj=ctj-rec_min-diamMont/1000.

                    ccm=CCM_max
                    #calcula declividade economica                   
                    Ieco=(ccm-CCJ_max)/ext
                    
                    #escolhe a maior das duas declividade
                    Io=max(Ieco,Imin)

                    #calcula declividade maxima para v=5.0m/s, verificar essa formula
                    #Imax=4.65*qfim**(-2./3.)
                    qfim=max(qfim,q_min)
                    Imax,diam_Imax,n_Imax=self.CalcImax(qfim,v_max,lam_max,tubos)

                    #Se a declividade for maior que a maxima, usa a maxima e calcula a cota do ccm, baixando-a
                    if Io>=Imax:
                        #diam_min=max(diam_Imax,diamMont)
                        n=n_Imax
                        Io=Imax
                        ccm=CCJ_max+ext*Io #Tenta usar a declividade maxima
                        if ccm>CCM_max:
                            ccm=CCM_max
                            Io=(ccm-CCJ_max)/ext
                        #verificar profundidade maxima do PV e se superar, usar lamina igual a 0.50 como recomenda
                        #a norma para situacoes de v > vcritica
                    diam_calc=self.CalcDiametro(qfim, n, Io, lam_max)
                    diam=diam_min
                    if diam<diam_calc:#se o diam nao atende com a declividade
                        if max_forcar>0 and Io<Imax: #se nao estiver com a declividade Io=Imax tenta aprofundar a jusante
                            CCJ_forcado=CCJ_max-max_forcar
                            Iforcado=max(min((ccm-CCJ_forcado)/ext,Imax),Imin)
                            while diam<diam_calc:
                                diam_calc=self.CalcDiametro(qfim, n, Iforcado, lam_max)
                                if diam>diam_calc:
                                    #Se for verdadeiro, é possivel resolver aprofundando em ate 'max_forcar' a jusante sem mudar diametro
                                    #calcular a declividade minima que passa sem precisar aumentar o diametro
                                    #Pega o primeiro diametro maior ou igual ao calculado
                                    diam,n=[[d,n] for d,n in tubos if d >= diam_calc and d>=diam_min][0]
                                    Iajust=self.CalcDecl(qfim, n, diam, lam_max)
                                    Io=Iajust
                                else:
                                    if diam_calc>tubos[-1][0]:#Verifica se o maior tubo é insuficiente
                                        diam=tubos[-1][0]
                                        n=tubos[-1][1]
                                        obs=u'DIAM É INSUFICIENTE '
                                        diam_calc=0 #para sair do looping
                                    else:
                                        #Pega o proximo diametro maior que o anterior e calcula o diametro com a declividade minima
                                        diam,n=[[d,n] for d,n in tubos if d > diam][0]
                                        Io=max(Ieco,Imin)
                                        diam_calc=self.CalcDiametro(qfim, n, Io, lam_max)
                        else: #nao vai tentar rebaixar jusante
                            while diam<diam_calc:
                                if diam_calc>tubos[-1][0]:#Verifica se o maior tubo é insuficiente
                                    diam=tubos[-1][0]
                                    n=tubos[-1][1]
                                    obs=u'DIAM É INSUFICIENTE '
                                    diam_calc=0
                                else:
                                    #Pega o primeiro diametro maior ou igual ao calculado
                                    diam,n=[[d,n] for d,n in tubos if d >= diam_calc][0]
                                    diam_calc=self.CalcDiametro(qfim, n, Io, lam_max)

                    diam_m=diam/1000.
                    # ccm-=diam_m-(diamMont if trecho['Trecho']==1 or (not Diam_progress) else diam_min)/1000.

                    ccm=CCM_Mont_min
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
                    interfs=[[distMont,cs,ci,tipoInt] for id,distMont,cs,ci,tipoInt,idInt,diamInt,cgi_Int in lstTr_inter if id == tr_id]
                    ccm_p=ccm
                    ccj_p=ccj
                    Ip=Io
                    for distMont,cs,ci,tipoInt in interfs:
                        #Cota da geratriz superior e inferior do coletor no local da interferencia
                        ccGI_inter=ccm_p-Ip*distMont
                        ccGS_inter=ccGI_inter+diam_m
                        #Forcei a CS aqui para valor maximo para provocar o choque e forçar sempre passar por baixo quando a interferencia for 'TN'
                        if tipoInt=='TN':
                            cs=max(ctm,ctj)
                        if (ci<ccGS_inter<cs) or (ci<ccGI_inter<cs) or (ccGI_inter<cs<ccGS_inter): #verifica se ha choque com a interferencia
                            QgsMessageLog.logMessage('Interf em choque tr:'+trecho['DC_ID']+
                                                     ' distMont:{0:.2f}'.format(distMont), 'QEsg_03Dimensionamento',
                                                      Qgis.Info)
                            #se a interferencia esta mais proxima de montante; 
                            if distMont<(ext/2.): #or True: #tinha forcado aqui para sempre modificar montante
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
                            else: #se a interferencia esta no meio ou mais proxima de jusante 
                                  #aprofunda ccm e ccj igualmente;
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
                    ccm=float(trecho['CCM'])
                    ccj=float(trecho['CCJ'])
                    Io=(ccm-ccj)/ext
                    diam=float(trecho['DIAMETER'])
                    diam_m=diam/1000.
                    n=float(trecho['MANNING'])

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
                    obs=(obs+';Prof>5' if obs else 'Prof>5;')
                if v_ini>v_max or v_fim>v_max:
                    self.warnings=True
                    obs=(obs+';Vel>Vmax' if obs else 'Vel>Vmax;')
                if v_ini>v_crit or v_fim>v_crit:
                    self.warnings=True
                    obs=(obs+';Vel>Vcrit' if obs else 'Vel>Vcrit;')
                if y_d_ini-lam_max>=0.01:
                    self.warnings=True
                    obs=(obs+';y/d ini >max' if obs else 'y/d ini >max;')
                if y_d_fim-lam_max>=0.01:
                    self.warnings=True
                    obs=(obs+';y/d fim >max' if obs else 'y/d fim >max;')
                    
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
                trecho['DECL_MIN']=Imin
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
        #Trechos=feicoes
        #faz loop novamente para medir os degraus
        for trecho in Trechos:
            if self.goExec:
                progressMBar.setText(QCoreApplication.translate('QEsg','Finalizando...'))
                QApplication.processEvents()

                obs=trecho['OBS']
                if obs:
                    obs=re.sub(r'DG.*m|TQ.*m','',obs) #remove os DG ou TQ que possam existir no campo de observações
                pvj=trecho['PVJ']
                ccj=float(trecho['CCJ'])
                CCM_MinJus=float(self.pegaCotaMinTrechosJus(vLayer, pvj,ccj))
                degCC=ccj-CCM_MinJus
                #print('DC_ID={},ccj={},CCM_MinJus={}'.format(trecho['DC_ID'],ccj, CCM_MinJus))
                if degCC>0:
                    if degCC>deg_max: # quedas maiores que 0.50m usa TQ segundo Norma Brasileira 9649/1986 e 0.58m segundo NBR 14486/2000
                        tipo='TQ'
                    else:
                        tipo='DG'
                    trecho['OBS']=(obs if obs else '')+tipo+'={:.3f}m'.format(degCC)
                elif degCC<0:
                    self.warnings = True
                    trecho['OBS']=(obs if obs else '')+'DEGRAU NEGATIVO'+'={:.3f}m'.format(degCC)
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
                iface.messageBar().pushMessage(self.SETTINGS, QCoreApplication.translate('QEsg',u'Rede dimensionada com advertências. Favor verificar o campo "OBS" para cada trecho na Tabela de atributos!'),
                                           level=Qgis.Info, duration=0)
            else:
                iface.messageBar().pushMessage(self.SETTINGS, QCoreApplication.translate('QEsg',u'Rede dimensionada com sucesso!'),
                                           level=Qgis.Info, duration=10)
        else:
            iface.messageBar().clearWidgets()
            iface.messageBar().findChildren(QToolButton)[0].setHidden(False)
            iface.messageBar().pushMessage(self.SETTINGS, QCoreApplication.translate('QEsg',u'Operação cancelada!Favor NÃO salvar os resultados!'),
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
            spIndex.addFeature(feat)


        lstTr_inter=[]#Lista dos ids,distToMont dos trechos com interferencias
        lstIds=[]
        Invalidos=[NULL,None,'']
        aviso=''
        while interfFeats.nextFeature(feat):
            cs=feat['CS']
            ci=feat['CI']
            tipoInt=feat['TIPO_INT']
            idInt=feat['DC_ID'] or ''
            diamInt=feat['DIAMETER']
            cgi_Int=feat['CGI']
            interGeo = feat.geometry() #geometria da interferencia (ponto)
            pt=interGeo.asPoint()
            
            # QgsSpatialIndex.nearestNeighbor (QgsPoint point, int neighbors)
            nearestIds = spIndex.nearestNeighbor(pt,2) #return 2 nearest Neighbors
            
            lineIter = pipeLayer.getFeatures(QgsFeatureRequest().setFilterFids(nearestIds))
            featDist=[] #pipe list with [id,distance,feature]
            for linefeat in lineIter:
                lineGeo = linefeat.geometry()
                dist = interGeo.distance(lineGeo)
                featDist.append([linefeat.id(),dist, linefeat])

            #sort by dist (second column, index 1)
            if featDist:
                featDist.sort(key=lambda x: x[1])
            
            nearestId=featDist[0][0]
            lstIds.append(nearestId)

            ftr = featDist[0][2]

            ftrGeo = ftr.geometry()
            if ftrGeo.isMultipart():
                vertIni=ftrGeo.asMultiPolyline()[0][0]
            else:
                vertIni=ftrGeo.asPolyline()[0]
            
            #setup distance
            distance = QgsDistanceArea()
            distToMont=distance.measureLine(pt, vertIni)#poderia usar computeDistanceFlat
            lstTr_inter.append([nearestId,distToMont,cs,ci,tipoInt,idInt,diamInt,cgi_Int])
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
                    feat['CCM']=float(ctm)-float(prfm)
                else:
                    feat['PRFM']=float(ctm)-float(ccm)
                vLayer.updateFeature(feat)
            if (ccj in Invalidos) and (prfj in Invalidos):
                aviso=QCoreApplication.translate('QEsg',u'\'{}\' e \'{}\' com valores Nulos em Trecho Existente!').format('CCJ','PRFJ')
                self.FeicaoSelecionaMostraAvisa(vLayer, feat.id(), aviso)
                return False
            else:
                if ccj in Invalidos:
                    feat['CCJ']=float(ctj)-float(prfj)
                else:
                    feat['PRFJ']=float(ctj)-float(ccj)
                vLayer.updateFeature(feat)
            if ccj>=ccm:
                aviso=QCoreApplication.translate('QEsg',u'CCJ={} >= CCM={}  em Trecho Existente (Declividade nula ou negativa não permitida)!').format(ccj,ccm)
                self.FeicaoSelecionaMostraAvisa(vLayer, feat.id(), aviso)
                return False
        return True

    def Verifica_InterfsNulos(self):#retorna Falso se houver interfencia com CS ou CI nulos
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
                    if campo in ['Q_INI','Q_FIM']:
                        aviso=QCoreApplication.translate('QEsg',u'\'{}\' com valor Nulo! Utilize a Ferramenta para Cálculo de Vazão').format(campo)
                    else:
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
        #CCM_min=ccj
        lstCCM_jus=[] #Lista das cotas CCM dos trechos que recebem
        for feat in vLayer.getFeatures():
            if feat['PVM']==pvj:
                lstCCM_jus.append(feat['CCM'])
                #CCM_min=min(CCM_min,feat['CCM'])
        if lstCCM_jus:
            lstCCM_jus.sort() #ordena a lista das cotas CCM em ordem crescente
            CCM_min = lstCCM_jus[0] # pega o primeiro valor, o menor
        else: #Last reach does not have others to downstream
            CCM_min=ccj
        return CCM_min
    def pegaCotasMinTrechosMont(self,vLayer,pvm, CCM_max,NAMax):
        CCM_min=CCM_max
        NAMontMin=NAMax
        for feat in vLayer.getFeatures():
            if feat['PVJ']==pvm:
                CCM_min=min(CCM_min,feat['CCJ'] or 99999999)
                NAMontMin=min(NAMontMin,feat['NA_JUS'] or 99999999)
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
        #print('n={},q_ls{},Io={},diam_m={},M={}'.format(n,q_ls,Io,diam_m,M))
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
        PVsId=[]
        
        # Polygon of point buffers to avoid duplicate nodes in tolerance dist
        #ptosBuffer = QgsVectorLayer('Polygon', 'poly' , 'memory')
        #dP = ptosBuffer.dataProvider()
        #tol = 0.5 #tolerancia 0.5 unidades de distancia

        for linha in lines:
            glinha=linha.geometry()
            if glinha.isMultipart(): #glinha.wkbType()==QgsWkbTypes.MultiLineString
                g=glinha.asMultiPolyline()
                na=g[0][0]
                nb=g[-1][-1]
            else: #elif glinha.wkbType()==QgsWkbTypes.LineString
                g=glinha.asPolyline()
                na=g[0]
                nb=g[-1]            
            
            pvID = linha['PVM']
            if (pvID not in PVsId): # era (na not in nos) to avoid spatial duplicate. Now avoid duplicate attribute PV ID                
                PVsId.append(pvID)
                nos[na]=pvID
                cotasTN[na]=linha['CTM']
            
            pvID = linha['PVJ']
            if (pvID not in PVsId): #era (nb not in nos)                
                PVsId.append(pvID)
                nos[nb]=pvID
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
