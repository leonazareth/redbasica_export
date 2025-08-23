# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QEsg_04Estilos
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
from qgis.PyQt.QtWidgets import QToolBar
import os.path
from .QEsg_00Model import *


class Estilos(object):
    def CarregaEstilo(self,vLayer,Estilo):
        basepath = os.path.dirname(__file__)#os.path.realpath(
        FullPath=os.path.join(basepath, 'style/'+Estilo)
        vLayer.loadNamedStyle(FullPath)
''' 
        # trying to get the style combo box from interface to change selected item
        QEsgToolBar = iface.mainWindow().findChild( QToolBar, '&QEsg' )
        if QEsgToolBar:
            for layout in QEsgToolBar.children():
                for button in layout.children():
                    print(layout, button)
'''                    