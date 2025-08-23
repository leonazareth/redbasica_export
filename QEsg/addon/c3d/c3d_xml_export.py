# -*- coding: utf-8 -*-
"""
/***************************************************************************
 c3d_xml_export
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
from qgis.PyQt.QtWidgets import QMessageBox, QDialog, QDialogButtonBox ,QVBoxLayout, QCheckBox, QLabel, QFileDialog
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.utils import *
import os.path
from qgis.gui import QgsMessageBar, QgsMapLayerComboBox, QgsVertexMarker, QgsMapToolIdentify
import math
import xml.etree.ElementTree as ET
import xml.dom.minidom

from ...QEsg_00Model import *
from ...QEsg_00Common import *

class c3d_xml_export(object):
    common=QEsg_00Common()
    SETTINGS = common.SETTINGS
    ns = '{http://www.landxml.org/schema/LandXML-1.2}'
    ET.register_namespace('',ns[1:-1])
    nsLen = len(ns)    
    
    def XML_export(self):
        layer = self.common.PegaQEsgLayer('PIPES')
        structLayer = self.common.PegaQEsgLayer('JUNCTIONS')
        basePath = os.path.dirname(__file__)
        outXML, __ = QFileDialog.getSaveFileName(caption=self.tr(u'Salvar o arquivo como:'), filter="Autodesk Civil 3d XML (*.xml *.XML)")
        #outXML = os.path.join(basePath, 'template/c3d_pipenetwork_out.xml')
        if layer and structLayer and outXML:
            nsLen = self.nsLen
            ns = self.ns            
            template = os.path.join(basePath, 'template/c3d_pipenetwork.xml')                        
            tree = ET.parse(template)
            root = tree.getroot()
            pipeNt = root.find('.//{}PipeNetwork'.format(ns))
            pipeNt.set('name',layer.name())
            pipesRoot = root.find('.//{}Pipes'.format(ns))
            structsRoot = root.find('.//{}Structs'.format(ns))
            #structET = root.find('.//{}Struct'.format(ns))
            #structsRoot.append(structET)

            #Create pipes
            pipesList = [] #[[DC_ID,PVM,PVJ,CCM,CCJ]] list with network topology
            for feat in layer.getFeatures():                
                pipeET = ET.Element('Pipe')
                
                pipeET.set('slope','{:f}'.format(feat['DECL']))
                pipeET.set('refStart',feat['PVM'])
                pipeET.set('refEnd',feat['PVJ'])
                pipeET.set('length','{:f}'.format(feat['LENGTH']))
                descr = feat['Descript'] if layer.fields().indexFromName('Descript')>-1 else ''
                pipeET.set('desc',descr)
                pipeET.set('name',feat['DC_ID'])
                circAtt = ET.fromstring('<CircPipe diameter="{:f}" material="PVC" thickness="0.005"/>'.format(feat['DIAMETER']))
                FlowAtt = ET.fromstring('<PipeFlow areaCatchment="0." flowIn="0." hglDown="0." hglUp="0." runoffCoeff="0." timeInlet="0."/>')
                
                pipeET.append(circAtt)
                pipeET.append(FlowAtt)                
                
                pipesRoot.append(pipeET)
                pipesList.append([feat['DC_ID'],feat['PVM'],feat['PVJ'],feat['CCM'],feat['CCJ']])
            
            #Create Structs
            for feat in structLayer.getFeatures():
                structET = ET.Element('Struct')
                structET.set('elevRim','{:f}'.format(feat['COTA_TN']))
                if structLayer.fields().indexFromName('PROF')>-1:
                    structET.set('elevSump','{:f}'.format(feat['COTA_TN']-feat['PROF']))
                
                descr = feat['TIPO'] if structLayer.fields().indexFromName('TIPO')>-1 else ''
                structET.set('desc',descr)
                structET.set('name',feat['DC_ID'])
                
                geom = feat.geometry()
                if geom.isMultipart():
                    pto = geom.asMultiPoint()[0]
                else:
                    pto = geom.asPoint()
                    
                centerAtt = ET.fromstring('<Center>{:f} {:f}</Center>'.format(pto.y(), pto.x()))
                geomAtt = ET.fromstring('<CircStruct diameter="1050." material="Reinforced Concrete" thickness="0.065"></CircStruct>')
                sumpAtt = ET.fromstring('<Feature code="StructureFeature" source="Autodesk Civil 3D">'+
                                        '<Property label="controlSumpBy" value="depth"></Property>'+
                                        #'<Property label="SumpDepth" value="0"></Property>'+
                                        '</Feature>')
                
                pipesIN = [[DC_ID,CCJ] for [DC_ID,PVM,PVJ,CCM,CCJ] in pipesList if PVJ==feat['DC_ID']]                
                for pipe in pipesIN:
                    invAtt = ET.fromstring('<Invert elev="{1:f}" flowDir="in" refPipe="{0}"></Invert>'.format(pipe[0],float(pipe[1])))
                    structET.append(invAtt)
                
                pipesOUT = [[DC_ID,CCM] for [DC_ID,PVM,PVJ,CCM,CCJ] in pipesList if PVM==feat['DC_ID']]
                for pipe in pipesOUT:
                    invAtt = ET.fromstring('<Invert elev="{1:f}" flowDir="out" refPipe="{0}"></Invert>'.format(pipe[0],float(pipe[1])))
                    structET.append(invAtt)
                
                structET.append(centerAtt)
                structET.append(geomAtt)
                structET.append(sumpAtt)                
                structsRoot.append(structET)
            

                
            tree.write(outXML, encoding='utf-8', xml_declaration=True)
            self.prettyPrintXml(outXML) #Only for debug purpose while development phase     
            
            rawPath = r'{}'.format(outXML)
            folderLink='<a href=\"file:///{}\">{}</a>'.format(rawPath, rawPath) #.encode('unicode_escape')) #'LandXML created!'            
            iface.messageBar().pushMessage('QEsg', folderLink, level=Qgis.Info, duration=20)
            
    def prettyPrintXml(self, xml_fname):
        dom = xml.dom.minidom.parse(xml_fname) # or xml.dom.minidom.parseString(xml_string)
        xml_string = dom.toprettyxml()
        #xml_string = os.linesep.join([s for s in xml_string.splitlines() if s.strip()])
        xml_string = '\n'.join([s for s in xml_string.splitlines() if s.strip()])
        with open(xml_fname, "w") as file_out:
            file_out.write(xml_string)
    
    def tr(self, string):
        return QCoreApplication.translate('C3D', string)
        