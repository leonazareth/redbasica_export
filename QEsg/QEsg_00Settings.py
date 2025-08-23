# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QEsg_00Settings
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
from builtins import range
from builtins import object
from qgis.core import *
#from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QObject, SIGNAL
#from PyQt4.QtGui import QAction, QIcon, QMessageBox
#from PyQt4 import QtGui, QtCore
from qgis.PyQt.QtWidgets import QAction, QMenu, QLabel, QComboBox, QTableWidget, QTableWidgetItem
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.utils import *
from qgis.gui import QgsMessageBar
# Initialize Qt resources from file resources.py
from . import resources_rc
# Import the code for the dialog
import os.path
from .QEsg_Settings_dialog import SettingsDialog
from .QEsg_00Common import *
from .QEsg_00Model import *
from .QEsg_00Rename import *
from .QEsg_01Campos import *
from .QEsg_02Vazao import *
from .QEsg_03Dimensionamento import *
from .QEsg_05Perfil import *
from .QEsg_06Export import *
from .QEsg_07Tools import *
from .QEsg_09ForcedFlow import *
from .QEsg_10Report import *
from .QEsg_20Sancad import *
from .QEsg_04Estilos import *
from .addon.c3d.c3d import *
from .addon.c3d.c3d_xml import *
from .addon.c3d.c3d_xml_export import *

class QEsg(object):
    """QGIS Plugin Implementation."""
    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        self.locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'QEsg_en.qm')# 'QEsg_{}.qm'.format(locale) -> mudei para sempre traduzir qdo n for pt

        if os.path.exists(locale_path) and self.locale!='pt':#se n for pt traduz pra ingles
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = SettingsDialog()

        # Connect to Dialog Buttons
        #self.dlg.pushButton.clicked.connect(self.tableToArray)
        self.dlg.chkIgualaGS.clicked.connect(self.chkIgualaGS_toggle)
        self.dlg.btnDel.clicked.connect(self.btnDel_push)
        self.dlg.btnIns.clicked.connect(self.btnIns_push)
        self.dlg.cmbStd.activated.connect(self.cmbStdChange)
        self.dlg.cmbMDT.layerChanged.connect(self.cmbMDT_onChange)
        self.dlg.cmbGrpDS.activated.connect(self.cmbGrpDS_onChange)
        #self.cmbStdChange(0)

        # Declare instance attributes
        self.actions = []
        self.separators=[]
        self.menu = '&QEsg'
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar('&QEsg')
        self.toolbar.setObjectName('&QEsg')

        #Cria instancias das Classes utilizadas
        self.RenameClasse=Rename_Tools(self.iface)
        self.CommonClasse=QEsg_00Common()
        self.CamposClasse=QEsg_01Campos()
        self.VazaoClasse=QEsg_02Vazao()
        self.DimensClasse=QEsg_03Dimens()
        self.SancadClasse=QEsg_20Sancad()
        self.PerfilClasse=QEsg_05Perfil()
        self.ExportaClasse=QEsg_06Export()
        self.ToolsClasse=QEsg_07Tools()
        self.ExportaXMLClasse=c3d_xml_export()
        self.EstiloClasse=Estilos()
        self.c3dClasse=c3d(iface)
        self.ForcedFlowClasse=QEsg_09ForcedFlow()
        self.ReportClasse=QEsg_10Report()
        
        #Technical Standard
        self.Std_id=0
        
    def cmbStdChange(self,Int):
        #print(Int)
        tbStd=self.dlg.tblWidStd
        frame=self.dlg.framek1k2
        if Int==0: #Brazil
            tbStd.setVisible(False)
            frame.setVisible(True)
        elif Int==1: #India
            tbStd.setVisible(True)
            frame.setVisible(False)
        self.Std_Id=Int

    # noinspection PyMethodMayBeStatic
    def chkIgualaGS_toggle(self):
        chk=self.dlg.chkIgualaGS.isChecked()
        self.dlg.chkDiamProgressivo.setChecked(True)
        self.dlg.chkDiamProgressivo.setEnabled(not chk)
        #print 'isChecked='+str(self.dlg.chkIgualaGS.isChecked())
    def btnDel_push(self):
        tableWidget=self.dlg.tableWidget
        tableWidget.removeRow(tableWidget.currentRow())
        #tableWidget.setRowCount(tableWidget.rowCount()-1)
    def btnIns_push(self):
        tableWidget=self.dlg.tableWidget
        tableWidget.insertRow(tableWidget.currentRow()+1)
    def carregaTabPopPeakFactor(self,tbMats):
        #tbMats=QEsgModel.TUBOS_MAT
        tableWidget=self.dlg.tblWidStd
        tableWidget.setRowCount(0)
        for i, tbMat in enumerate(tbMats):
            currentRowCount = tableWidget.rowCount()
            tableWidget.insertRow(currentRowCount)
            item=QTableWidgetItem("{:10.0f}".format(tbMat[0]))
            item.setTextAlignment(Qt.AlignVCenter|Qt.AlignRight)
            tableWidget.setItem(currentRowCount , 0, item)

            item=QTableWidgetItem("{:10.0f}".format(tbMat[1]))
            item.setTextAlignment(Qt.AlignVCenter|Qt.AlignRight)
            tableWidget.setItem(currentRowCount , 1, item)
            
            item=QTableWidgetItem("{:5.2f}".format(tbMat[2]))
            item.setTextAlignment(Qt.AlignVCenter|Qt.AlignRight)
            tableWidget.setItem(currentRowCount , 2, item)
    def carregaTabMats(self,tbMats):
        #tbMats=QEsgModel.TUBOS_MAT
        tableWidget=self.dlg.tableWidget
        tableWidget.setRowCount(0)
        for i, tbMat in enumerate(tbMats):
            currentRowCount = tableWidget.rowCount()
            tableWidget.insertRow(currentRowCount)
            item=QTableWidgetItem("{:7.2f}".format(tbMat[0]))
            item.setTextAlignment(Qt.AlignVCenter|Qt.AlignRight)
            tableWidget.setItem(currentRowCount , 0, item)

            item=QTableWidgetItem("{:5.3f}".format(tbMat[1]))
            item.setTextAlignment(Qt.AlignVCenter|Qt.AlignRight)
            tableWidget.setItem(currentRowCount , 1, item)
    def tableToArray(self, tblWid):
        table=tblWid
        result = []
        num_rows, num_cols = table.rowCount(), table.columnCount()
        for row in range(num_rows):
            rows = []
            for col in range(num_cols):
                item = table.item(row, col)
                rows.append(float(item.text()))#if item else ''
            result.append(rows)
        return result
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('QEsg', message)


    def add_action(
        self,
        icon_path,
        text,
        callback=None,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
        separator=False):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        if not separator:
            action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            if separator:
                menuSep=self.toolbar
                self.separator=menuSep.addSeparator()
                self.separators.append(self.separator)
                self.iface.addPluginToMenu(
                    self.menu,
                    self.separator)
            else:
                self.iface.addPluginToMenu(
                    self.menu,
                    action)

        self.actions.append(action)

        return action

    def initGui(self):
        # submenu
        self.sub_menu = QMenu(self.tr('&Exemplos'))

        itemTxt=self.tr('Inicial')
        self.sampleAction = QAction(QIcon(':/python/plugins/QEsg/icons/buttons/add.png'), itemTxt, self.iface.mainWindow())
        self.sampleAction.triggered.connect(self.openCleanSample)
        self.sub_menu.addAction(self.sampleAction)

        itemTxt=self.tr('Pronto')
        self.sampleAction = QAction(QIcon(':/python/plugins/QEsg/icons/buttons/add.png'), itemTxt, self.iface.mainWindow())
        self.sampleAction.triggered.connect(self.openFinishedSample)
        self.sub_menu.addAction(self.sampleAction)

        # Back in main menu
        self.iface.addPluginToMenu('&QEsg', self.sub_menu.menuAction())


        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/QEsg/icons/00config.png'
        self.add_action(
            icon_path,
            text=self.tr(u'00 Configurações'),
            callback=self.run,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QEsg/icons/01campos.png'
        self.add_action(
            icon_path,
            text=self.tr('01 Verifica os Campos'),
            callback=self.VerificaCampos,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QEsg/icons/00rename.png'
        self.add_action(
            icon_path,
            text=self.tr(u'02 Numerar Rede'),
            callback=self.Rename,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QEsg/icons/04crianos.png'
        self.add_action(
            icon_path,
            text=self.tr(u'03 Criar Layer de Nós'),
            callback=self.CriaNodeFile,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QEsg/icons/02campos_preenche.png'
        self.add_action(
            icon_path,
            text=self.tr(u'04 Preenche os Campos'),
            callback=self.PreencheCampos,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QEsg/icons/03vazao.png'
        self.add_action(
            icon_path,
            text=self.tr(u'05 Calcula Vazão'),
            callback=self.CalculaVazao,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QEsg/icons/05dimens.png'
        self.add_action(
            icon_path,
            text=self.tr(u'06 Dimensiona'),
            callback=self.Dimensiona,
            parent=self.iface.mainWindow())

        #Insere separador
        icon_path = ''
        self.add_action(
            icon_path,
            add_to_menu=True,
            add_to_toolbar=False,
            text='',
            parent=self.iface.mainWindow(),
            separator=True)

        icon_path = ':/plugins/QEsg/icons/06profile.svg'
        self.add_action(
            icon_path,
            add_to_menu=True,
            add_to_toolbar=True,
            text=self.tr(u'Desenha perfil'),
            callback=self.DesenhaPerfil,
            parent=self.iface.mainWindow())

        icon_path = ''
        self.add_action(
            icon_path,
            add_to_menu=True,
            add_to_toolbar=False,
            text=self.tr(u'Atualiza Nome dos PVs a partir dos nós'),
            callback=self.AtualizaPVs,
            parent=self.iface.mainWindow())

        icon_path = ''
        self.add_action(
            icon_path,
            add_to_menu=True,
            add_to_toolbar=False,
            text=self.tr(u'Apaga Nome dos Coletores'),
            callback=self.ClearPipesNames,
            parent=self.iface.mainWindow())

        icon_path = ''
        self.add_action(
            icon_path,
            add_to_menu=True,
            add_to_toolbar=False,
            text=self.tr(u'Atualiza cota do TN a partir de um MDT'),
            callback=self.AtualizaCotaTN,
            parent=self.iface.mainWindow())            

        icon_path = ''
        self.add_action(
            icon_path,
            add_to_menu=True,
            add_to_toolbar=False,
            text=self.tr(u'Cria pontos nos locais com recobrimento menor que o mínimo'),
            callback=self.CreateMinCovering_Points_Tool,
            parent=self.iface.mainWindow())               

        icon_path = ''
        self.add_action(
            icon_path,
            add_to_menu=True,
            add_to_toolbar=False,
            text=self.tr(u'Impõe a vazão na seleção'),
            callback=self.ForcedFlow_Tool,
            parent=self.iface.mainWindow())
            
        #Insere separador
        icon_path = ''
        self.add_action(
            icon_path,
            add_to_menu=True,
            add_to_toolbar=False,
            text='',
            parent=self.iface.mainWindow(),
            separator=True)
        
        #submenu Relatorio inicio
        self.sub_menuReport = QMenu('Relatório')
        
        itemTxt=self.tr('Dados do projeto')
        self.sampleAction = QAction(QIcon(''), itemTxt, self.iface.mainWindow())
        self.sampleAction.triggered.connect(self.Report_DadosGerais_update_Tool)
        self.sub_menuReport.addAction(self.sampleAction)
        
        itemTxt=self.tr('Planilha de resultados')
        self.sampleAction = QAction(QIcon(''), itemTxt, self.iface.mainWindow())
        self.sampleAction.triggered.connect(self.Report_PlanResults_update_Tool)
        self.sub_menuReport.addAction(self.sampleAction)

        # Back in main menu
        self.iface.addPluginToMenu('&QEsg', self.sub_menuReport.menuAction())
            
        #Insere separador
        icon_path = ''
        self.add_action(
            icon_path,
            add_to_menu=True,
            add_to_toolbar=False,
            text='',
            parent=self.iface.mainWindow(),
            separator=True)        
        #submenu Relatorio fim
        
        icon_path = ''
        self.add_action(
            icon_path,
            add_to_menu=True,
            add_to_toolbar=False,
            text=self.tr(u'DXF Importa (Cad ou Sancad)'),
            callback=self.ImportaSancadDXF,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QEsg/icons/07dxfout.svg'
        self.add_action(
            icon_path,
            add_to_menu=True,
            add_to_toolbar=True,
            text=self.tr(u'DXF Exporta (Cad ou Sancad)'),
            callback=self.ExportaDXF,
            parent=self.iface.mainWindow())        
        
        # submenu Civil 3D
        self.sub_menuC3D = QMenu('Autodesk Civil 3D')
        
        itemTxt=self.tr('Prepara para C3D')
        self.sampleAction = QAction(QIcon(':/plugins/QEsg/addon/c3d/icons/00c3d.svg'), itemTxt, self.iface.mainWindow())
        self.sampleAction.triggered.connect(self.c3d_prepara) #self.c3d_prepara #c3d.prepara
        self.sub_menuC3D.addAction(self.sampleAction)

        itemTxt=self.tr('Importa XML')
        self.sampleAction = QAction(QIcon(':/plugins/QEsg/addon/c3d/icons/01xml_import.svg'), itemTxt, self.iface.mainWindow())
        self.sampleAction.triggered.connect(XML_import)
        self.sub_menuC3D.addAction(self.sampleAction)

        itemTxt=self.tr('Exporta XML')
        self.sampleAction = QAction(QIcon(':/plugins/QEsg/addon/c3d/icons/02xml_export.svg'), itemTxt, self.iface.mainWindow())
        self.sampleAction.triggered.connect(self.ExportaXML)
        self.sub_menuC3D.addAction(self.sampleAction)

        # Back in main menu
        self.iface.addPluginToMenu('&QEsg', self.sub_menuC3D.menuAction())
            
        #Insere separador
        icon_path = ''
        self.add_action(
            icon_path,
            add_to_menu=True,
            add_to_toolbar=False,
            text='',
            parent=self.iface.mainWindow(),
            separator=True)

        icon_path = ':/plugins/QEsg/icons/00help.svg'
        self.add_action(
            icon_path,
            add_to_menu=True,
            add_to_toolbar=False,
            text=self.tr(u'Ajuda'),
            callback=self.CallSite,
            parent=self.iface.mainWindow())

        #Styles Combobox Label
        cmbLabel = QLabel(self.iface.mainWindow())
        cmbLabel.setText(self.tr('Mostrar:'))
        cmbLabel.setStyleSheet('color: rgb(255, 170, 0)') #font: 87 8pt "Arial Black";  #color: rgb(255, 218, 68);
        cmbLabelAction = self.toolbar.addWidget(cmbLabel)

        #Styles Combobox
        self.projCombo = QComboBox(self.iface.mainWindow())
        self.projCombo.setStyleSheet("background-color: rgb(255, 218, 68);")
        self.projComboLoad()
        self.projCombo.activated.connect(self.projComboChange) #currentIndexChanged
        projComboAction = self.toolbar.addWidget(self.projCombo)
        self.projCombo.setToolTip(self.tr("Mudar estilo"))

        self.dlg.btnLimpaSettings.clicked.connect(self.LimpaSettings)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu('&QEsg', action)
            self.iface.removeToolBarIcon(action)

        # remove Separators
        for sep in self.separators:
            self.iface.removePluginMenu(
                self.tr('&QEsg'),
                sep)
        self.iface.removePluginMenu('&QEsg', self.sub_menu.menuAction())
        self.iface.removePluginMenu('&QEsg', self.sub_menuC3D.menuAction())
        self.iface.removePluginMenu('&QEsg', self.sub_menuReport.menuAction())

        # remove the toolbar
        del self.toolbar

    def projComboLoad(self):
        estilos = QEsgModel.qSTYLES
        self.estilos = estilos
        for i, estilo in enumerate(estilos):
            self.projCombo.addItem(self.tr(estilo[0]))
    def projComboChange(self, Int):
        texto= self.estilos[Int][1]  #self.projCombo.itemText(Int).encode('utf-8')
        forma= self.estilos[Int][2]
        vLayer = self.CommonClasse.PegaQEsgLayer(forma)
        if vLayer:
            self.EstiloClasse.CarregaEstilo(vLayer, texto)
            vLayer.triggerRepaint()
        #QMessageBox.information(None,u'ComboBox Titulo','id={} \nTexto={}'.format(Int,texto))

    def CallSite(self):
        if self.locale!='pt':
            link='https://github.com/jorgealmerio/QEsg/blob/master/README_en.md'
        else:
            link='https://github.com/jorgealmerio/QEsg/blob/master/README.md'
        QDesktopServices.openUrl(QUrl(link))
    def openCleanSample(self):
        Nome='clean'
        self.iface.addProject(os.path.dirname(__file__)+'/sample/{}/{}.qgs'.format(Nome,Nome))
    def openFinishedSample(self):
        Nome='finished'
        self.iface.addProject(os.path.dirname(__file__)+'/sample/{}/{}.qgs'.format(Nome,Nome))
    def cmbMDT_onChange(self, layer):
        visivel = (layer or False) and layer.type()==QgsMapLayer.MeshLayer
        if visivel:
            mshGrps=[]
            self.dlg.cmbGrpDS.clear()
            for i in range(layer.dataProvider().datasetGroupCount()):
                meta = layer.dataProvider().datasetGroupMetadata(i)
                mshGrps.append('{0:02d}-{1}'.format(i,meta.name()))
            self.dlg.cmbGrpDS.addItems(mshGrps)
            self.dlg.cmbGrpDS.setCurrentIndex(0)
            self.cmbGrpDS_onChange(0)
            #self.dlg.cmbDS.setCurrentIndex(0)
        for i in range(0,self.dlg.hLayMalha.count()):
            obj=self.dlg.hLayMalha.itemAt(i).widget()
            obj.setVisible(visivel)
    def cmbGrpDS_onChange(self, Int):
        layer = self.dlg.cmbMDT.currentLayer()
        ds = []
        self.dlg.cmbDS.clear()
        for i in range(layer.dataProvider().datasetCount(Int)):
            meta = layer.dataProvider().datasetMetadata(QgsMeshDatasetIndex(Int, i))
            ds.append('{0:02d}-{1}'.format(i,layer.formatTime(meta.time())))
        self.dlg.cmbDS.addItems(ds)
        self.dlg.cmbDS.setCurrentIndex(0)
    def run(self):
        """Open settings Dialog"""
        self.limpaTudo()
        proj = QgsProject.instance()
        layers = proj.mapLayers().values() #self.iface.legendInterface.layers()

        layer_list = ['']
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer:
                if layer.geometryType() == QgsWkbTypes.LineGeometry:
                    layer_list.append(layer.name())
        self.dlg.cmbRede.addItems(layer_list)

        layer_list = ['']
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer:
                if layer.geometryType() == QgsWkbTypes.PointGeometry:
                    layer_list.append(layer.name())
        self.dlg.cmbVertices.addItems(layer_list)

        layer_list = ['']
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer:
                if layer.geometryType() == QgsWkbTypes.PointGeometry:
                    layer_list.append(layer.name())
        self.dlg.cmbInterf.addItems(layer_list)
        
        self.dlg.cmbMDT.setFilters(QgsMapLayerProxyModel.RasterLayer|QgsMapLayerProxyModel.MeshLayer)
        #filter out raster without info capabilities
        outList=[]
        self.dlg.cmbMDT.setExceptedLayerList(outList) #Clear ExceptedLayerList
        for i in range(0,self.dlg.cmbMDT.count()):
            lyr = self.dlg.cmbMDT.layer(i)
            if lyr!=None and (lyr.type()==QgsMapLayer.RasterLayer) and \
                not (lyr.dataProvider().capabilities() & QgsRasterDataProvider.IdentifyValue):            
                outList.append(lyr)
        self.dlg.cmbMDT.setExceptedLayerList(outList)   
        self.dlg.cmbMDT.setAllowEmptyLayer(True)

        self.leVariaveis()

        #Exibe extensoes da rede
        
        ProjVar=proj.readEntry("QEsg", 'PIPES')[0]
        if ProjVar!='':
            try:
                myLayer=proj.mapLayersByName(ProjVar)[0]
                tot1a,tot2a,geo1a,geo2a=self.CompRealGeom(myLayer)

                msgTxt=self.tr(u'<span style=" color:#0000ff;">Comprimento Geométrico:<br>Etapa 1 = {0:.2f} m<br>Etapa 2 = {1:.2f} m</span>').format(geo1a,geo2a)
                self.dlg.lbl_extGeo.setText(msgTxt)
                msgTxt=''

                if tot1a>0 or tot2a>0:
                    msgTxt=self.tr(u'Comprimento Atual:<br>Etapa 1 = {:.2f} m<br>Etapa 2 = {:.2f} m').format(tot1a,tot2a)
                self.dlg.lbl_extReal.setText(msgTxt)
                msgTxt=''

                Lini,Lfim = self.VazaoClasse.CompVirtualRede(myLayer)
                if Lini>=0 or Lfim>=0:
                    msgTxt=self.tr(u'Comprimento Virtual:<br>Etapa 1 = {:.2f} m<br>Etapa 2 = {:.2f} m').format(Lini,Lfim)
                self.dlg.lbl_extVirtual.setText(msgTxt)
            except:
                pass

#             conecta o layer da rede ao evento (signal)
#             myLayer.attributeValueChanged.connect(self.CamposClasse.OnChangeAttribute)
#             print 'conectou'

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            self.gravaVariaveis()

    def CompRealGeom(self,vLayer):
        tot1a=tot2a=0
        geo1a=geo2a=0
        for feat in vLayer.getFeatures():
            ext=feat['LENGTH']
            etapa=feat['ETAPA']
            geo=feat.geometry().length()
            if etapa==1:
                geo1a+=geo
                geo2a+=geo
                if ext!= NULL:
                    tot1a+=ext
                    tot2a+=ext
            elif etapa==2:
                geo2a+=geo
                if ext!= NULL:
                    tot2a+=ext
            else:
                geo1a+=geo
                if ext!= NULL:
                    tot1a+=ext
        return tot1a,tot2a,geo1a,geo2a

    def limpaTudo(self):
        #self.dlg.cmbBacia.clear()
        self.dlg.cmbRede.clear()
        self.dlg.cmbVertices.clear()
        self.dlg.cmbInterf.clear()
        self.iface.messageBar().findChildren(QToolButton)[0].setHidden(False)
    def LimpaSettings(self):
        proj = QgsProject.instance()
        proj.removeEntry("QEsg","")
        MsgTxt=self.tr(u'As configurações do Plugin foram removidas do Projeto')
        #listaEntry = proj.readListEntry()
        self.iface.messageBar().pushMessage("QEsg:", MsgTxt, duration=3)
        self.dlg.close()
    def leVariaveis(self):
        proj = QgsProject.instance()

        ProjVar=proj.readEntry("QEsg", "PIPES")[0]
        oInd=self.EncontraItem(self.dlg.cmbRede,ProjVar)
        self.dlg.cmbRede.setCurrentIndex(oInd)

        ProjVar=proj.readEntry("QEsg", "JUNCTIONS")[0]
        oInd=self.EncontraItem(self.dlg.cmbVertices,ProjVar)
        self.dlg.cmbVertices.setCurrentIndex(oInd)

        ProjVar=proj.readEntry("QEsg", "INTERFERENCES")[0]
        oInd=self.EncontraItem(self.dlg.cmbInterf,ProjVar)
        self.dlg.cmbInterf.setCurrentIndex(oInd)
                
        self.dlg.chkInterf.setChecked(proj.readNumEntry("QEsg", "INTERFERENCES_ON",1)[0])
        
        lyrName=proj.readEntry("QEsg", "MDT", "")[0]
        layerEntry=proj.mapLayersByName(lyrName)
        if layerEntry:
            self.dlg.cmbMDT.setLayer(layerEntry[0])
            self.dlg.cmbGrpDS.setCurrentIndex(proj.readNumEntry("QEsg", "MDT_GrpDS",0)[0])
            self.dlg.cmbDS.setCurrentIndex(proj.readNumEntry("QEsg", "MDT_DS",0)[0])
        else:
            self.dlg.cmbMDT.setLayer(None)

        self.dlg.Txt_percapita.setText(proj.readEntry("QEsg", "PERCAPTA","150")[0])
        self.dlg.Txt_k1.setText(proj.readEntry("QEsg", "K1_DIA","1.20")[0])
        self.dlg.Txt_k2.setText(proj.readEntry("QEsg", "K2_HORA","1.50")[0])
        self.dlg.Txt_CoefRet.setText(proj.readEntry("QEsg", "COEF_RET","0.80")[0])
        self.dlg.Txt_CoefInf.setText(proj.readEntry("QEsg", "COEF_INF","0.0002")[0])
        self.dlg.Txt_diametro.setText(proj.readEntry("QEsg", "DN_MIN","150")[0])
        self.dlg.Txt_qmin.setText(proj.readEntry("QEsg", "Q_MIN","1.50")[0])
#        self.dlg.Txt_manning.setText(proj.readEntry("QEsg", "MANNING","0.013")[0])
        self.dlg.Txt_rec_min.setText(proj.readEntry("QEsg", "REC_MIN","0.90")[0])
        self.dlg.Txt_y_d_max.setText(proj.readEntry("QEsg", "LAM_MAX","0.75")[0])
        self.dlg.Txt_maxForcar.setText(proj.readEntry("QEsg", "MAX_FORCAR","0.00")[0])
        self.dlg.Txt_deg_ignore.setText(proj.readEntry("QEsg", "DEG_IGNORE","0.02")[0])
        self.dlg.Txt_deg_min.setText(proj.readEntry("QEsg", "DEG_MIN","0.00")[0])
        self.dlg.Txt_deg_max.setText(proj.readEntry("QEsg", "DEG_MAX","0.60")[0])
        self.dlg.Txt_v_max.setText(proj.readEntry("QEsg", "V_MAX","5.00")[0])

        self.dlg.Txt_popini.setText(proj.readEntry("QEsg", "POPINI","0")[0])
        self.dlg.Txt_popfim.setText(proj.readEntry("QEsg", "POPFIM","0")[0])

        self.dlg.chkDiamProgressivo.setChecked(proj.readNumEntry("QEsg", "DIAM_PROGRESS",1)[0])
        self.dlg.chkPrecSancad.setChecked(proj.readNumEntry("QEsg", "PREC_SANCAD",0)[0])
        self.dlg.chkIgualaGS.setChecked(proj.readNumEntry("QEsg", "IGUALA_GS",0)[0])
        self.dlg.cmbPipeOrdem.setCurrentIndex(proj.readNumEntry("QEsg", "PIPE_ORDEM",0)[0])
        self.dlg.cmb_Imin_opt.setCurrentIndex(proj.readNumEntry("QEsg", "I_MIN_OPT",0)[0]) #0=NBR 9649;1=NBR 14486;2=MANUAL

        tubosMat=proj.readEntry("QEsg", "TUBOS_MAT","0")[0]
        if tubosMat=='0':#se nao tiver lista de materiais definidas carrega o padrao do modelo
            tubos=QEsgModel.TUBOS_MAT
        else:
            tubos=eval(tubosMat)
        self.carregaTabMats(tubos)
        
        # Restaura a norma tecnica utilizada;0=Brasil;1=India
        self.Std_id=proj.readNumEntry("QEsg", "STD",0)[0]
        self.dlg.cmbStd.setCurrentIndex(self.Std_id)
        self.cmbStdChange(self.Std_id)
        if self.Std_id==1:#if India Standard
            popTblVar=proj.readEntry("QEsg", "IN/POP_TBL","0")[0]
            if popTblVar=='0': #if there is no popul. peak table settings loads default
                popTbl=[[0.0, 20000.0, 3.0], [20000.0, 50000.0, 2.5], [50000.0, 75000.0, 2.25], [75000.0, 99999999.0, 2.0]]
            else:
                popTbl=eval(popTblVar)
            self.carregaTabPopPeakFactor(popTbl)

    def EncontraItem(self, Combo, Texto):
        for i in range(Combo.count()):
            if Combo.itemText(i)==Texto:
                return i
        return -1
    def gravaVariaveis(self):
        proj = QgsProject.instance()
        proj.removeEntry("QEsg","")#Clean all settings before save

        LyrNameSel=self.dlg.cmbRede.itemText(self.dlg.cmbRede.currentIndex())
        proj.writeEntry("QEsg", "PIPES", LyrNameSel)
        LyrNameSel=self.dlg.cmbVertices.itemText(self.dlg.cmbVertices.currentIndex())
        proj.writeEntry("QEsg", "JUNCTIONS", LyrNameSel)
        LyrNameSel=self.dlg.cmbInterf.itemText(self.dlg.cmbInterf.currentIndex())
        proj.writeEntry("QEsg", "INTERFERENCES", LyrNameSel)
        proj.writeEntry("QEsg", "INTERFERENCES_ON", self.dlg.chkInterf.isChecked())        
        
        curlyr = self.dlg.cmbMDT.currentLayer()
        LyrNameSel=curlyr.name() if curlyr else ''
        proj.writeEntry("QEsg", "MDT", LyrNameSel)
        proj.writeEntry("QEsg", "MDT_GrpDS",self.dlg.cmbGrpDS.currentIndex())
        proj.writeEntry("QEsg", "MDT_DS",self.dlg.cmbDS.currentIndex())
        

        proj.writeEntry("QEsg", "PERCAPTA", self.dlg.Txt_percapita.text())
        proj.writeEntry("QEsg", "K1_DIA", self.dlg.Txt_k1.text())
        proj.writeEntry("QEsg", "K2_HORA", self.dlg.Txt_k2.text())
        proj.writeEntry("QEsg", "COEF_RET", self.dlg.Txt_CoefRet.text())
        proj.writeEntry("QEsg", "COEF_INF", self.dlg.Txt_CoefInf.text())
        proj.writeEntry("QEsg", "DN_MIN", self.dlg.Txt_diametro.text())
        proj.writeEntry("QEsg", "Q_MIN", self.dlg.Txt_qmin.text())
#        proj.writeEntry("QEsg", "MANNING", self.dlg.Txt_manning.text())
        proj.writeEntry("QEsg", "REC_MIN", self.dlg.Txt_rec_min.text())
        proj.writeEntry("QEsg", "LAM_MAX", self.dlg.Txt_y_d_max.text())
        proj.writeEntry("QEsg", "MAX_FORCAR", self.dlg.Txt_maxForcar.text())
        proj.writeEntry("QEsg", "DEG_IGNORE", self.dlg.Txt_deg_ignore.text())
        proj.writeEntry("QEsg", "DEG_MIN", self.dlg.Txt_deg_min.text())
        proj.writeEntry("QEsg", "DEG_MAX", self.dlg.Txt_deg_max.text()) #Altura máxima de degrau, a partir de qual usa tubo de queda
        proj.writeEntry("QEsg", "V_MAX", self.dlg.Txt_v_max.text())

        proj.writeEntry("QEsg", "POPINI", self.dlg.Txt_popini.text())
        proj.writeEntry("QEsg", "POPFIM", self.dlg.Txt_popfim.text())

        proj.writeEntry("QEsg", "DIAM_PROGRESS", self.dlg.chkDiamProgressivo.isChecked())
        proj.writeEntry("QEsg", "PREC_SANCAD", self.dlg.chkPrecSancad.isChecked())
        proj.writeEntry("QEsg", "IGUALA_GS", self.dlg.chkIgualaGS.isChecked())
                
        proj.writeEntry("QEsg", "PIPE_ORDEM", self.dlg.cmbPipeOrdem.currentIndex())
        proj.writeEntry("QEsg", "I_MIN_OPT", self.dlg.cmb_Imin_opt.currentIndex())

        proj.writeEntry("QEsg", "TUBOS_MAT", str(self.tableToArray(self.dlg.tableWidget)))
        
        self.Std_id=self.dlg.cmbStd.currentIndex()
        # grava a norma tecnica utilizada;0=Brasil;1=India
        proj.writeEntry("QEsg","STD",self.Std_id)
        if self.Std_id==1:#if India Standard used, stores population Peak Factors Table
            proj.writeEntry("QEsg", "IN/POP_TBL", str(self.tableToArray(self.dlg.tblWidStd)))
    def VerificaCampos(self):
        self.CamposClasse.Verifica('Criar')
    def PreencheCampos(self):
        self.CamposClasse.Verifica('Preencher')
    def CalculaVazao(self):
        proj = QgsProject.instance()
        self.Std_id=proj.readNumEntry("QEsg", "STD",0)[0]
        if self.Std_id==1:#if India Standard
            from .stds.IN.QEsg_IN_Flow import QEsg_02Vazao
        else:
            from .QEsg_02Vazao import QEsg_02Vazao
        self.VazaoClasse=QEsg_02Vazao()
        self.VazaoClasse.CalcVazao()
    def CriaNodeFile(self):
        self.DimensClasse.CriaNos('',True)
    def Dimensiona(self):
        proj = QgsProject.instance()
        self.Std_id=proj.readNumEntry("QEsg", "STD",0)[0]
        if self.Std_id==1:#if India Standard
            from .stds.IN.QEsg_IN_Design import QEsg_03Dimens
        else:
            from .QEsg_03Dimensionamento import QEsg_03Dimens
        self.DimensClasse=QEsg_03Dimens()
        self.DimensClasse.Dimensiona()
    def AtualizaPVs(self):
        self.CamposClasse.AtualizaNomePVs()
    def AtualizaCotaTN(self):
        self.CamposClasse.AtualizaCotaTN()
    def CreateMinCovering_Points_Tool(self):
        self.ToolsClasse.CreateMinCovering_Points_Tool()
    def ImportaSancadDXF(self):
        self.SancadClasse.ImportaDXF()
    def Rename(self):
        self.RenameClasse.initGui()
    def ClearPipesNames(self):
        self.RenameClasse.LimpaNomesColetores()
    def DesenhaPerfil(self):
        self.PerfilClasse.run()
    def ExportaDXF(self):
        self.ExportaClasse.run()
    def c3d_prepara(self):
        self.c3dClasse.prepara()
    def ExportaXML(self):
        self.ExportaXMLClasse.XML_export()
    def ForcedFlow_Tool(self):
        self.ForcedFlowClasse.run()
    def Report_DadosGerais_update_Tool(self):
        self.ReportClasse.Report_DadosGerais_update()
    def Report_PlanResults_update_Tool(self):
        self.ReportClasse.Report_PlanResults_update()        
        