# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QEsg_05Perfil
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
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.utils import *
import os.path
from .QEsg_00Model import *
from .QEsg_03Dimensionamento import *
from .QEsg_05ProfileDialog import ProfileDialog
from .QEsg_08Profiler import *

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle

from matplotlib.legend_handler import HandlerPatch
import matplotlib.patches as mpatches

import qgis

class HandlerEllipse(HandlerPatch):
    def create_artists(self, legend, orig_handle,
                       xdescent, ydescent, width, height, fontsize, trans):
        center = 0.5 * width - 0.5 * xdescent, 0.5 * height - 0.5 * ydescent
        p = mpatches.Ellipse(xy=center, width=width + xdescent,
                             height=height + ydescent)
        self.update_prop(p, orig_handle, legend)
        p.set_transform(trans)
        return [p]


class QEsg_05Perfil(object):
    inPipes={}
    def __init__(self):
        self.dlg=ProfileDialog()
        """
        proj = QgsProject.instance()
        #Technical Standard 0=Brazil;1=India
        self.Std_id=proj.readNumEntry("QEsg", "STD",0)[0]
        if self.Std_id==1: #if India Standard
            from .stds.IN.QEsg_IN_Design import QEsg_03Dimens
        else:
            from .QEsg_03Dimensionamento import QEsg_03Dimens
        """
        self.DimensClasse=QEsg_03Dimens()
        self.ProfilerClasse=QEsg_08Profiler()
        self.lastDialogGeo=None

    def run(self):
#        self.DimensClasse=QEsg_03Dimens()
        vLayer=self.DimensClasse.PegaQEsgLayer('PIPES')
        if vLayer==False:
            aviso=QCoreApplication.translate('QEsg',u'Layer Tipo \'PIPES\' indefinido ou não encontrado!')
            iface.messageBar().pushMessage("QEsg:", aviso, level=Qgis.Warning, duration=4)
            return False
            
        valores=[]
        idx = vLayer.fields().lookupField('Coletor')
        valInts = vLayer.uniqueValues( idx )
        valores=[str(i) for i in valInts]
        self.dlg.cmbColetores.clear()
        self.dlg.cmbColetores.addItems(valores)
        self.dlg.cmbColetores.setFocus()
        
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            try:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                Coletor=self.dlg.cmbColetores.itemText(self.dlg.cmbColetores.currentIndex())            
                self.Desenha_Perfil(vLayer,Coletor)
            finally:
                QApplication.restoreOverrideCursor()

    def Desenha_Perfil(self,vLayer,Coletor=1):
        campo='Coletor'
        coletor=Coletor
        request = QgsFeatureRequest()
        expres='\"'+campo+'\"='+coletor
        request.setFilterExpression(expres)
        request.addOrderBy('Trecho',True)
        lstCTx=[]
        lstCGx=[]
        lstCTy=[]
        cc=[]
        cgs=[]
        na=[]
        ext=0
                        
        if plt.get_fignums():
            mng = plt.get_current_fig_manager()
            self.lastDialogGeo=mng.window.geometry()#,mng.window.y()]
            
        titulo=QCoreApplication.translate('QEsg','Coletor ')+Coletor
        plt.figure(num=titulo)
        ax = plt.gca()
        
        #Lista os tubos que chegam nos PVs do coletor apenas uma vez
        self.inPipes = self.GetIncoming_Pipes(vLayer, coletor)
        
        #Lista as interfencias de todos os trechos apenas uma vez
        lstIds,lstTr_inter=self.DimensClasse.Lista_Interferencias(vLayer)        
                    
        #sort by distToMont (second column, index 1)
        if lstTr_inter:
            lstTr_inter.sort(key=lambda x: x[1])
        
        HasInter=False
        ColetorIds=[]
        for feat in vLayer.getFeatures(request):
            ident=feat['DC_ID']
            lstCTx.append(ext)
            lstCGx.append(ext)

            ctm=feat['CTM'] or None
            ccm=feat['CCM'] or ctm
            pvm=feat['PVM'] or None
            pvj=feat['PVJ'] or None
            namon=feat['NA_MON']
            diam=feat['DIAMETER']/1000.

            lstCTy.append(ctm)
            cc.append(ccm)
            na.append(namon)
            cgs.append(ccm+diam)

            if not (None in [ctm, ccm]):
                self.Desenha_PV(ax, ext, ctm, ccm, .8, .1, pvm)

            tr_id=feat.id()
            ColetorIds.append(tr_id)
            #lista as interferencias apenas do trecho
            interfs=[[distMont,cs,ci,tipoInt,idInt,diamInt,cgi_Int] for id,distMont,cs,ci,tipoInt,idInt,diamInt,cgi_Int in lstTr_inter if id == tr_id]
            for distMont,cs,ci,tipoInt,idInt,diamInt,cgi_Int in interfs:
                locX=ext+distMont
                if tipoInt=='TN':
                    lstCTx.append(locX)
                    lstCTy.append(cs)
                else:
                    ellipse = Ellipse(xy=(locX, (cs+ci)/2.), width=cs-ci, height=cs-ci, 
                                             edgecolor='r', fc='None', lw=.8, linestyle='dashed')
                    intLine=ax.add_patch(ellipse)
                    # if optional Interference fields DIAMETER and CGI are not null
                    if None not in (diamInt , cgi_Int):
                        d_m=diamInt/1000. #convert to meters
                        ellipse = Ellipse(xy=(locX, cgi_Int+d_m/2.), width=d_m, height=d_m, 
                                             edgecolor='r', fc='None', lw=2)
                        intLine=ax.add_patch(ellipse)                    
                    #plt.text(locX,ci,idInt,{'ha': 'center', 'va': 'top'},rotation=90,color='red')
                    plt.annotate(idInt,(locX,ci),horizontalalignment='center',verticalalignment='top',rotation=90,color='red')
                    HasInter=True

            ctj=feat['CTJ']
            ccj=feat['CCJ']
            najus=feat['NA_JUS']

            trLen = feat['LENGTH']
            plt.annotate(ident,(ext+trLen/2,ccj),horizontalalignment='center',verticalalignment='top')
            ext+=trLen

            lstCTx.append(ext)
            lstCGx.append(ext)

            lstCTy.append(ctj)
            cc.append(ccj)
            na.append(najus)
            cgs.append(ccj+diam)
        #end for Trechos
        
        #Draw last PV
        if not (None in [ctj, ccj]):
            self.Desenha_PV(ax, ext, ctj, ccj, .8, .1,pvj)
        
        #
        mdtLyr = self.DimensClasse.PegaQEsgLayer('MDT')
        if mdtLyr:
            lstCTx, lstCTy = self.ProfilerClasse.profile(vLayer, request, mdtLyr)            
        
        ctLine,=plt.plot(lstCTx,lstCTy,color='magenta')
        cgsLine,=plt.plot(lstCGx,cgs,color='green')
        naLine,=plt.plot(lstCGx,na,color='cyan')
        cgiLine,=plt.plot(lstCGx,cc,color='blue')
        plt.xlabel(QCoreApplication.translate('QEsg',u'Distância (m)'))
        plt.ylabel(QCoreApplication.translate('QEsg','Cota (m)'))
        plt.grid(True)
        LegLines=[ctLine,cgsLine,naLine,cgiLine]
        subs=[QCoreApplication.translate('QEsg','Cota do Terreno'),
                    QCoreApplication.translate('QEsg','Cota da Geratriz Superior'),
                    QCoreApplication.translate('QEsg','Cota do NA'),
                    QCoreApplication.translate('QEsg','Cota da Geratriz Inferior')
                    ]
        #QCoreApplication.translate('QEsg','PV\'s')
        
        if HasInter:
            LegLines.append(intLine)
            subs.append(QCoreApplication.translate('QEsg',u'Interferências'))
            hndMap={intLine: HandlerEllipse()}
        else:
            hndMap={}
        plt.legend(LegLines,subs,handler_map=hndMap,loc='best')
        plt.title(titulo)
        
        #to maximize window
        #mng = plt.get_current_fig_manager()
        #mng.window.showMaximized()
        
        #Select, pan and Flash chosed manifold features
        vLayer.selectByIds(ColetorIds)
        opt = self.dlg.cmbOption.currentIndex()
        if opt==1:
            iface.mapCanvas().panToSelected(vLayer)
        elif opt==2:
            iface.mapCanvas().zoomToSelected(vLayer)
        iface.mapCanvas().flashFeatureIds(vLayer, ColetorIds)
        
        #to move window and maximize    
        try:
            mng = plt.get_current_fig_manager()            
            if self.lastDialogGeo is not None:            
                mng.window.setGeometry(self.lastDialogGeo)  #.move(self.lastDialogPosX[0], self.lastDialogPosX[1])
                #mng.window.showMaximized()
        except:
            print(u'Could not move and maximize window!')

        plt.show()
        plt.draw()      

    def Desenha_PV(self,ax,ext,ctm,ccm,pvDiam,thick,PV_id):
        #Add PV wall
        #thick=.1 #espessura da parede
        #pvDiam=.8+2.*thick #PV diam
        pvBLx=(ext-pvDiam/2.) #PV Bottom Left X
        pvBLy=ccm-thick #PV Bottom Left Y
        pvH=ctm-ccm+thick #PV Height
        rect = plt.Rectangle((pvBLx, pvBLy), pvDiam, pvH, facecolor="#aaaaaa")#edgecolor='black', linewidth=2, alpha=.70
        ax.add_patch(rect)

        #Add PV
        #pvDiam=.8 #PV diam
        pvBLx=ext-pvDiam/2.+thick #PV Bottom Left X
        pvBLy=ccm #PV Bottom Left Y
        pvH=ctm-ccm-thick/2. #PV Height
        rect = plt.Rectangle((pvBLx, pvBLy), pvDiam-2*thick, pvH, facecolor="white")
        ax.add_patch(rect)
        
        #Add Incoming Pipe to PV with label do trecho(if exists)
        if PV_id in self.inPipes:
            #print(self.inPipes)
            tr_id = self.inPipes[PV_id][0]
            pipeDiam = self.inPipes[PV_id][1]/1000.
            ccj = self.inPipes[PV_id][2]
            ellipse = Ellipse(xy=(ext, ccj+pipeDiam/2), width=pipeDiam, height=pipeDiam, edgecolor='b', fc='None', lw=2, linestyle='solid')
            incPipe=ax.add_patch(ellipse)
            
            #bbox_props = dict(boxstyle="round4,pad=0.3", fc="white", ec="b", lw=0.1)
            plt.annotate(tr_id+' ->',(ext,pvBLy-thick),horizontalalignment='center',verticalalignment='top',rotation=90,color='b')#, bbox=bbox_props)
        
        #Linha vertical no eixo do PV
        plt.plot([ext,ext],[ctm,ccm],color='black',linestyle='--')
    
    #Retorna um lista com os PVs de um Coletor
    def listaPVs_coletor(self, vLayer, coletor):
        campo= 'Coletor'
        request = QgsFeatureRequest()
        expres='\"'+campo+'\"='+coletor
        request.setFilterExpression(expres)
        request.addOrderBy('Trecho',True)
        lista=[]
        for feat in vLayer.getFeatures(request):
            pvm=feat['PVM']
            pvj=feat['PVJ']
            if pvm not in lista:
                lista.append(pvm)
            if pvj not in lista:
                lista.append(pvj)
        return lista
    
    #Retorna um "dictionary" com os dados dos trechos que desaguam nos PVs de um coletor
    def GetIncoming_Pipes(self,vLayer,coletor):
        #Lista os PVs do coletor
        lstPVs = self.listaPVs_coletor(vLayer,coletor)
        
        campo= 'Coletor'
        request = QgsFeatureRequest()
        expres='\"'+campo+'\"!='+coletor #pega os outros coletores
        request.setFilterExpression(expres)
        request.addOrderBy('Trecho',True)        
        
        lstInPipes={}
        for feat in vLayer.getFeatures(request):
            PVid=feat['PVJ']
            if PVid in lstPVs:                
                Tr_id=feat['DC_ID']
                diam=feat['DIAMETER']
                ccj=feat['CCJ']
                lstInPipes[PVid]=[Tr_id,diam,ccj]
        return lstInPipes