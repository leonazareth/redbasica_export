# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QEsg_06Export
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
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.utils import *
import os.path
import os
from .QEsg_00Model import *
from .QEsg_03Dimensionamento import *
import math

import qgis
from numpy import insert
from os.path import join
from .QEsg_06Export_dialog import dxfExport_Dialog
#from formatter import NullWriter

ClassName='QEsg_06Export'
UsrAppId='NUMEROTRE' #appid for DXF extended data
TemCTNula=False
class QEsg_06Export(object):
    def __init__(self):
        global ClassName
        self.DimensClasse=QEsg_03Dimens()

        # Create the dialog and keep reference
        self.dlg = dxfExport_Dialog()
        self.dlg.btnBrowse.clicked.connect(self.LoadFileName)
        self.dlg.chkSancad.clicked.connect(self.chkSancad_toggle)
    def ImportDxf_Lib(self):
        try:
            from .addon import ezdxf as dxf
            #QgsMessageLog.logMessage('ezdxf imported without need of change PATH variable',ClassName) 
        except ImportError:
            self.dirname, filename = os.path.split(os.path.abspath(__file__))
            addonPath = os.path.join(self.dirname,'addon')
            sys.path.append(addonPath)
            import ezdxf as dxf
            QgsMessageLog.logMessage('ezdxf imported, but PATH variable had to be changed',ClassName)#,level=QgsMessageLog.CRITICAL
        # self.dirname, filename = os.path.split(os.path.abspath(__file__))
        # sys.path.append(self.dirname)

        self.dxf=dxf
    def tr(self, Texto):
        return QCoreApplication.translate(ClassName,Texto)
    def nz(self, Valor):
        global TemCTNula
        #function to treat Null values
        if Valor==NULL:
            TemCTNula=True
            return 0
        else:
            return Valor
    def run(self):
        global UsrAppId, TemCTNula
        #dxfPath=os.path.join(self.dirname,'test.dxf')#substituir por filedialog
        self.ImportDxf_Lib()
        noth=['',' ','.dxf']
        if self.dlg.txtFile.text() in noth:
            proj = QgsProject.instance()
            #baseName=proj.readPath("./")
            prjfi = os.path.splitext(QgsProject.instance().fileName())[0]+'.dxf'
            self.dlg.txtFile.setText(prjfi)

        vLayer=self.DimensClasse.PegaQEsgLayer('PIPES')
        if vLayer==False:
            aviso=self.tr(u'Layer Tipo \'PIPES\' indefinido ou não encontrado!')
            iface.messageBar().pushMessage(ClassName, aviso, level=Qgis.Warning, duration=4)
            return False

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            dxfPath=self.dlg.txtFile.text()
            Invalidos=['',' ',None,NULL]
            if dxfPath in Invalidos:
                aviso=self.tr(u'Operação cancelada!')
                iface.messageBar().pushMessage(ClassName, aviso, level=Qgis.Info, duration=4)
                return
            dxf=self.dxf
            # Create a new drawing in the DXF format of AutoCAD 2010
            #drawing = dxf.new('ac1024')
            
            # Open DXF template
            basepath = os.path.dirname(__file__)#os.path.realpath(
            filename=os.path.join(basepath, 'template/QEsg_template.dxf')
            drawing = dxf.readfile(filename)
            self.drawing=drawing            
            
            #drawing.header['$INSUNITS'] = dxf.units.M #set units to meters (6)
            '''
            from ezdxf import units
            drawing.units = units.M
            
            drawing.header['$AUNITS'] = 0 #set angle unit to decimal degrees
            drawing.header['$AUPREC'] = 6 #set angles precision
            '''
            drawing.appids.new(UsrAppId) #Create AppId entry to xdata
            
            #Create network drawing
            self.criaRede(vLayer)

            
            # Get the modelspace of the drawing.
            msp = drawing.modelspace()  
            #Zoom to extents
            from ezdxf import zoom
            zoom.extents(msp)            

            # Try to Save the drawing.
            try:
                drawing.saveas(dxfPath)
            except:
                WriteErr=self.tr("Sem acesso para gravação no arquivo!")
                iface.messageBar().pushMessage(ClassName, WriteErr, level=Qgis.Warning, duration=4)
                return False            
            
            aviso=self.tr("Salvo em:") + dxfPath
            if TemCTNula:
                aviso=self.tr("Valores nulos foram substituidos por Zeros. ")+aviso
                iface.messageBar().pushMessage(ClassName, aviso, level=Qgis.Warning, duration=4)
            else:
                iface.messageBar().pushMessage(ClassName, aviso, level=Qgis.Info, duration=4)
    def chkSancad_toggle(self):
        chk=self.dlg.chkSancad.isChecked()
        if chk:
            self.dlg.txtPrefix.setText('SANC_')
        #self.dlg.txtPrefix.setEnabled(not chk)
    def LoadFileName(self):
        prjfi = self.dlg.txtFile.text()
        dxfPath, __ =QFileDialog.getSaveFileName(caption=self.tr(u'Exportar DXF como:'),
                                                 directory=prjfi,filter="AutoCAD DXF (*.dxf *.DXF)")
        if dxfPath:
            self.dlg.txtFile.setText(dxfPath)
    def criaRede(self, vLayer):
        global UsrAppId, ClassName, TemCTNula
        #from dxfwrite.const import CENTER, MIDDLE, TOP, LEFT, RIGHT
        drawing=self.drawing
        dxf=self.dxf
        
        #e=vLayer.extent()
        #drawing.header['$EXTMIN'] = (e.xMinimum(),e.yMinimum(),0) #Lower left corner
        #drawing.header['$EXTMAX'] = (e.xMaximum(),e.yMaximum(),0) #Upper Right corner
        
        '''
        xMeio=(e.xMinimum()+e.xMaximum())/2
        yMeio=(e.yMinimum()+e.yMaximum())/2
        alt = (e.yMaximum()-e.yMinimum())*1.5# 15 height of viewport
        print(xMeio, yMeio, alt)        
        drawing.set_modelspace_vport(height=alt, center=(xMeio, yMeio))
        '''
        
        prefix=self.dlg.txtPrefix.text()#'B'
        self.criaLayers(drawing,prefix)
        try:
            drawing.styles.new('ROMANS',{'font':'romans.shx'})
        except:
            pass
        
        #Here I Try to Set vport to initial display extents
        #print e.center().x(),e.center().y()
        #drawing.viewports.new('*ACTIVE',{'target_point':(e.center().x(),e.center().y(),0)})
        #tirei agora active_viewport = drawing.viewports.new('*ACTIVE')
        #drawing.viewports.new('*ACTIVE',{'height':(e.yMaximum()-e.yMinimum())*1.1, 'target_point':(e.center().x(),e.center().y(),0),'aspect_ratio':3})
        #tirei agora active_viewport.dxf.center = (e.center().x(),e.center().y()) #(40, 30)  # center of viewport, this parameter works
        #tirei agora active_viewport.dxf.height = (e.yMaximum()-e.yMinimum())*1.5# 15 height of viewport, this parameter works
        #tirei agora active_viewport.dxf.aspect_ratio = 2.5  #1.5 aspect ratio of viewport (x/y)
        
        #altura = (e.yMaximum()-e.yMinimum())*1.5
        #centro = (e.center().x(),e.center().y())        
        #drawing.set_modelspace_vport(altura, centro)
        
        # Get Scale Factor
        fatScale=self.dlg.spinScale.value()
        sc=fatScale/2000.

        # Create block SETA and add to drawing
        blkSeta=prefix+'SETA'
        oBlock = drawing.blocks.new(name=blkSeta)
        oBlock.add_solid([(4*sc, 0), (-4*sc,-1.33*sc), (-4*sc, 1.33*sc)], dxfattribs={'color':256, 'layer':blkSeta})
        
        # Get the modelspace of the drawing.
        msp = drawing.modelspace()        
        
        #Array of Lateral contribution to covert from QEsg to Sancad
        contLad_lst=[[0,'NAO'],[1,'UNI'],[2,'SIM']]
        
        #for add extended data to entities, here to be read in Sancad
        from ezdxf.lldxf.types import DXFTag
        SancadPad=self.dlg.chkSancad.isChecked()
        TemCTNula=False
        request = QgsFeatureRequest()
        request.addOrderBy('Coletor',False)
        request.addOrderBy('Trecho',True)
        for feat in vLayer.getFeatures(request):
            geom=feat.geometry()
            if geom.isMultipart():
                polilinha=geom.asMultiPolyline()[0] #Pega apenas a primeira parte das multipartes
            else:
                polilinha=geom.asPolyline()
            v1=polilinha[0]
            z1=self.nz(feat['CCM'])
            v2=polilinha[1]
            z2=self.nz(feat['CCJ'])
            ccm_tx='{:.3f}'.format(z1)
            ccj_tx='{:.3f}'.format(z2)
            
            ctm_tx='{:.3f}'.format(feat['CTM'])
            ctj_tx='{:.3f}'.format(feat['CTJ'])
            
            prfm_tx='{:.3f}'.format(feat['PRFM'])
            prfj_tx='{:.3f}'.format(feat['PRFJ'])

            lyr=prefix+'REDE'
            if feat['PONTA_SECA']=='S':
                v1d=self.PtoAlong(v1, v2, 4.*sc)
                pto1 = (v1d.x(),v1d.y(),z1)
                if not SancadPad:
                    ptPerLeft=self.PtoPerp(v1d, v2, -2*sc)
                    ptPerRight=self.PtoPerp(v1d, v2, 2*sc)
                    ptLeft=(ptPerLeft.x(),ptPerLeft.y(),z1)
                    ptRight=(ptPerRight.x(),ptPerRight.y(),z1)
                    lyr=prefix+'NO'
                    msp.add_line(ptLeft,ptRight,dxfattribs={'color':256, 'layer':lyr})#add perpendicular line
            else:
                pto1 = (v1.x(),v1.y(),z1)
            lyr=prefix+'REDE'
            line = msp.add_line(pto1,(v2.x(),v2.y(),z2),dxfattribs={'color':256, 'layer':lyr})

            #add extended data to the entity for sancad reading
            txtID=feat['DC_ID']
            txtPVM=feat['PVM']
            txtPAV='ASFALTO' #no futuro adaptar para compatibilizar com o Sancad que 
                                #considera a prof de recobrimento a partir do tipo de pavimento
            txtLADOS=contLad_lst[feat['CONTR_LADO']][1]
            line.set_xdata(appid=UsrAppId, tags=[DXFTag(1000,txtID),
                                                      DXFTag(1000,txtPVM),
                                                      DXFTag(1000,txtPAV),
                                                      DXFTag(1000,txtLADOS)])

            if not SancadPad:
                #Add Pipe ID text above pipe line
                from ezdxf.enums import TextEntityAlignment
                
                pos,rot=self.textIns(v1,v2,-1.25*sc)
                lyr=prefix+'NUMERO'
                texto=feat['DC_ID']
                msp.add_text(texto,
                            height=3*sc,
                            dxfattribs={'rotation':rot,'style':'ROMANS','color':256, 'layer':lyr}).set_placement(pos,align=TextEntityAlignment.BOTTOM_CENTER)
                                        #'width':.8

                #Add Pipe length, diameter, declividade text below pipe line                
                lyr=prefix+'TEXTO'
                ext=self.nz(feat["LENGTH"])
                dn=self.nz(feat["DIAMETER"])
                i=self.nz(feat["DECL"])
                texto='{:.0f}-{:.0f}-{:.5f}'.format(ext,dn,i)
                # Check if is a short reach
                if feat['LENGTH']>43*sc:
                    pos,rot=self.textIns(v1,v2,1.25*sc)
                    msp.add_text(texto,
                                height=3*sc,
                                dxfattribs={'rotation':rot,'style':'ROMANS','color':256, 'layer':lyr}).set_placement(pos,align=TextEntityAlignment.TOP_CENTER)
                                #'width':.8
                else:
                    pos,rot=self.textIns(v1,v2,0)
                    blockref = msp.add_blockref('tr_curto', pos, dxfattribs={'color':256,'layer':lyr,                                             
                                            'rotation': 0}).set_scale(sc*2)                
                    values = {
                                'DIST-DIAM-DECLV': texto
                            }
                    blockref.add_auto_attribs(values)
                
                
                #Add Upstream PV Data
                if feat['PONTA_SECA']=='S':
                    aux=QgsPointXY(pto1[0],pto1[1])
                else:
                    aux=self.PtoAlong(v1, v2, 2.99*sc)
                azim=v1.azimuth(v2)
                if 0<azim<90:
                    sign=-1
                    dir='SE'
                else:
                    sign=1
                    if 90<=azim<180:
                        dir='NE'
                    elif 180<=azim<270:
                        dir='NO'
                    else:
                        dir='NO'
                aux2=self.PtoAlong(v1, v2, 3*sign*sc)
                lt1=self.PtoPerp(aux2, v2, 10.0*sc)
                lt2=QgsPointXY(lt1.x()-12.*sign*sc,lt1.y())
                
                lyr=prefix+'TEXTOPVS'                
                blockref = msp.add_blockref('pv_dados_{}'.format(dir), aux, dxfattribs={'color':256,'layer':lyr,                                             
                                            'rotation': 0}).set_scale(sc*2)                
                
                values = {
                            'CT': ctm_tx,
                            'CF': ccm_tx,
                            'PROF': prfm_tx
                        }
                blockref.add_auto_attribs(values)               
                
                # Add CCJ if it Has Step
                obs=feat['OBS'] or ''
                #check if OBS field contains 'DG' or 'TQ'
                if  any(strDeg in obs for strDeg in ['DG','TQ']):
                    # Add CCJ to Manhole:
                    azim=v1.azimuth(v2)
                    if 0<azim<90:
                        sign=1
                        dir='NO'
                    else:
                        sign=1
                        if 90<=azim<180:
                            dir='NE'
                        elif 180<=azim<270:
                            dir='SE'
                        else:
                            dir='SO'
                    auxJ=self.PtoAlong(v2, v1, 3*sign*sc)
                    lt1=self.PtoPerp(auxJ, v1, 10.0*sc)
                    lt2=QgsPointXY(lt1.x()+12.*sign*sc,lt1.y())
                    lyr=prefix+'TEXTOPVS'
                    
                    blockref = msp.add_blockref('pv_dados_{}'.format(dir), auxJ, dxfattribs={'color':256,'layer':lyr,                                             
                                            'rotation': 0}).set_scale(sc*2)                
                    values = {                
                                'CF': ccj_tx,                              
                            }
                    blockref.add_auto_attribs(values)
                    #Add o simbolo de Tubo de queda se tiver TQ
                    if 'TQ' in obs:
                        lyr='ESG_TQ'
                        blockref = msp.add_blockref('notq', auxJ, dxfattribs={'color':256,'layer':lyr,                                             
                                            'rotation': 0}).set_scale(sc*2)                

    
                # Add SETA blocks to middle of reaches bigger than 20m
                if feat['LENGTH']>20*sc:
                    lyr=prefix+'SETA'
                    azim=v1.azimuth(v2)
                    if azim<0:
                        azim+=360
                    rot=90.-azim
    #                 if 180<=azim<360:
    #                     rot-=180
                    point=((v1.x()+v2.x())/2.,(v1.y()+v2.y())/2.,(z1+z2)/2.)
                    msp.add_blockref(blkSeta, point, dxfattribs={
                        'xscale': 1,
                        'yscale': 1,
                        'rotation': rot,
                        'layer':lyr
                    })
                #end if
            #endif SancadPad
        #end for
        
        #Write last Manhole (PV)        
        if feat['PONTA_SECA']=='S':
            aux=QgsPointXY(pto1[0],pto1[1])
        else:
            aux=self.PtoAlong(v1, v2, 2.99*sc)
        azim=v1.azimuth(v2)
        if 0<azim<90:
            sign=1
            dir='SE'
        else:
            sign=1
            if 90<=azim<180:
                dir='NE'
            elif 180<=azim<270:
                dir='NO'
            else:
                dir='SO'
        auxJ=self.PtoAlong(v2, v1, 3*sign*sc)
        lt1=self.PtoPerp(auxJ, v1, 10.0*sc)
        lt2=QgsPointXY(lt1.x()+12.*sign*sc,lt1.y())
        lyr=prefix+'TEXTOPVS'
        
        blockref = msp.add_blockref('pv_dados_{}'.format(dir), auxJ, dxfattribs={'color':256,'layer':lyr,                                             
                                'rotation': 0}).set_scale(sc*2)                
        values = {                
                    'CT': ctj_tx,
                    'CF': ccj_tx,
                    'PROF': prfj_tx
                }
        blockref.add_auto_attribs(values) 
        
        
        
        PVLayer=self.DimensClasse.PegaQEsgLayer('JUNCTIONS')
        if PVLayer==False:
            aviso=self.tr(u'Layer Tipo \'JUNCTIONS\' indefinido ou não encontrado! Os PVs não foram criados!')
            iface.messageBar().pushMessage("QEsg:", aviso, level=Qgis.Warning, duration=4)
            return
        
        #Name PV Block
        lyr=prefix+'PV'
        # Create a block
        oBlock = drawing.blocks.new(name=lyr)
        oBlock.add_circle(center=(0.,0.),radius=2.99*sc,dxfattribs={'color':256, 'layer':lyr})

        for feat in PVLayer.getFeatures():
            point=feat.geometry().asPoint()
            lyr=prefix+'PV'
            msp.add_blockref(lyr,point,dxfattribs={'layer':lyr})
            if not SancadPad:
                lyr=prefix+'NUMPV'
                texto=feat['DC_ID']
                pos=(point[0]+3.*sc,point[1]+3.*sc)
                msp.add_text(texto,
                            height=3*sc,
                            dxfattribs={'rotation':0,'width':.8,'style':'ROMANS','color':256, 'layer':lyr}).set_placement(pos,align=TextEntityAlignment.BOTTOM_LEFT)

    def criaLayers(self,drawing,prefix):
        #[Layer,Color]
        dxfLayers=[['AUX',241],['LIDER',2],['NO',3],['NUMERO',3],['NUMPV',3],['PV',3],['REDE',172],['SETA',172],['TEXTO',3],['TEXTOPVS',7]]
        for lyr,aColor in dxfLayers:
            NomeLyr=prefix+lyr
            drawing.layers.new(NomeLyr, dxfattribs={'color': aColor})
    def textIns(self,v1,v2,offset):
        azim=v1.azimuth(v2)
        if azim<0:
            azim+=360
        rot=90.-azim
        if 180<=azim<360:
            rot-=180
        pos=self.mid(v1,v2, offset, azim)
        return pos,rot
    def mid(self, pt1, pt2, offset, azim):
       if 180<=azim<360:
            sign=-1*math.copysign(1,offset)
       else:
            sign=1*math.copysign(1,offset)
       mx = (pt1.x() + pt2.x())/2
       my = (pt1.y() + pt2.y())/2
       Len = math.sqrt(pt1.sqrDist(pt2)) 
       x=mx+sign*abs(offset)*(pt2.y()-pt1.y())/Len
       y=my+sign*abs(offset)*(pt1.x()-pt2.x())/Len
       return QgsPointXY(x,y)
    def PtoAlong(self,pt1,pt2,Dist):
       Len = math.sqrt(pt1.sqrDist(pt2)) 
       x=pt1.x()+Dist/Len*(pt2.x()-pt1.x())
       y=pt1.y()+Dist/Len*(pt2.y()-pt1.y())
       return QgsPointXY(x,y)
    #Cria um ponto perpendicular ao segmento e distante em relacao ao pt1 em offset
    def PtoPerp(self,pt1,pt2,Offset):
       Len = math.sqrt(pt1.sqrDist(pt2)) 
       x=pt1.x()+Offset/Len*(pt2.y()-pt1.y())
       y=pt1.y()+Offset/Len*(pt1.x()-pt2.x())
       return QgsPointXY(x,y)
