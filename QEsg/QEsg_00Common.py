# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QEsg_00Common
                                 A QGIS plugin
 Sanitary Sewage System Networks Design
                              -------------------
        begin                : 2018-03-19
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
from builtins import object
from qgis.core import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import QProgressBar, QToolButton
from qgis.utils import *


class QEsg_00Common(object):
    # Store all configuration data under this key
    SETTINGS = 'QEsg'
    msgBar = iface.messageBar()
    def startProgressBar(self, iniMsg):
        #iniMsg ="Disabling Snapping to Layer: "
        #iface=self.iface

        progressMessageBar = self.msgBar.createMessage(self.SETTINGS,iniMsg)
        progress = QProgressBar()
        progress.setMaximum(100)
        progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)

        cancelButton = QPushButton()
        cancelButton.setText(QCoreApplication.translate('QEsg','Cancelar'))

        #pass the progress bar to the message Bar
        progressMessageBar.layout().addWidget(progress)
        progressMessageBar.layout().addWidget(cancelButton)

        #find the x button and hide it
        self.msgBar.pushWidget(progressMessageBar)
        self.msgBar.findChildren(QToolButton)[0].setHidden(True)

        #cancelButton.clicked.connect(self.onCancelButton)

        return progress,progressMessageBar,cancelButton
    def onCancelButton(self):
        # fix_print_with_import
        print('Fechar')
        #self.msgBar.clearWidgets()
    def PegaQEsgLayer(self, aForma):
        proj = QgsProject.instance()
        #aForma='PIPES'
        ProjVar=proj.readEntry("QEsg", aForma)[0]
        if ProjVar=='':
            msgTxt=QCoreApplication.translate('QEsg','Layer Indefinido: ') +aForma
            #QMessageBox.warning(None,'QEsg',msgTxt)
            iface.messageBar().pushMessage("QEsg:", msgTxt, level=Qgis.Warning, duration=10)
            return False
        LayerLst=proj.mapLayersByName(ProjVar)
        if LayerLst:
            layer = proj.mapLayersByName(ProjVar)[0]
            return layer
        else:
            msgTxt=aForma+'='+ProjVar+QCoreApplication.translate('QEsg',u' (Layer não encontrado)')
            #QMessageBox.warning(None,'QEsg',msgTxt)
            iface.messageBar().pushMessage("QEsg:", msgTxt, level=Qgis.Warning, duration=10)
            return False