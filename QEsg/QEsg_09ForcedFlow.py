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
from .QEsg_09ForcedFlow_dialog import ForcedFlow_Dialog
from .QEsg_00Common import *
from qgis.PyQt.QtWidgets import *

ClassName='QEsg_09ForcedFlow'

class QEsg_09ForcedFlow(object):
    def __init__(self):
        global ClassName
        # Create the dialog and keep reference
        self.dlg = ForcedFlow_Dialog()
        self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)        
        self.common = QEsg_00Common()             
        
    def layer_selection_changed(self,selFeatures):
        nroSel = len(selFeatures)
        label = self.dlg.lblSelection
        if nroSel>0:
            Texto = QCoreApplication.translate(ClassName,'Feições selecionadas: {}')
            label.setStyleSheet('color: black')
            self.dlg.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            Texto = QCoreApplication.translate(ClassName,'Selecione os trechos!')
            label.setStyleSheet('color: red')
            self.dlg.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        label.setText(Texto.format(nroSel))

    def run(self):
        pipesLyr = self.common.PegaQEsgLayer('PIPES')
        if not pipesLyr:
            return False
        pipesLyr.selectionChanged.connect(self.layer_selection_changed)
        self.layer_selection_changed(pipesLyr.selectedFeatures()) #Run to refresh for first time 
        
        self.dlg.mFieldComboBox.setLayer(pipesLyr)
        self.dlg.mFieldComboBox.setField('Trecho')
        
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            flowIni = self.dlg.spFlowIni.value()
            flowFim = self.dlg.spFlowFim.value()
            sortField = self.dlg.mFieldComboBox.currentField()
            '''
            print('flowIni',flowIni)
            print('flowFim',flowFim)
            print('sortField',sortField)            
            return False
            '''
            
            def get_Trecho(f):
                return f[sortField]
            selection = sorted(pipesLyr.selectedFeatures(), key=get_Trecho) #sort selected features by Trecho
            acum=tot=0
            for feature in selection:
                ext = feature['LENGTH']
                tot += ext
            pipesLyr.startEditing()
            for feature in selection:
                dcid = feature['DC_ID']
                oTrecho = feature[sortField]
                ext = feature['LENGTH']
                acum += ext
                feature['Q_INI']=flowIni/tot*acum
                feature['Q_FIM']=flowFim/tot*acum
                pipesLyr.updateFeature(feature)
                print('{}->Qini={:.3f} Qfim={:.3f}'.format(dcid,feature['Q_INI'],feature['Q_FIM']))
            pipesLyr.triggerRepaint()            
        else:            
            print('Cancel')
            pipesLyr.selectionChanged.disconnect(self.layer_selection_changed)