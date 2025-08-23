# -*- coding: utf-8 -*-
from builtins import object
#
# This file is part of QEsg
#
# QEsg_Model.py - Encapsulates QEsg_Model model stucture and logic
#
# Copyright 2016
#
# QEsg is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2, or (at your option) any later version.
#
# QEsg is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with program; see the file COPYING. If not,
# write to the Free Software Foundation, Inc., 59 Temple Place
# - Suite 330, Boston, MA 02111-1307, USA.
#

# Describe the model structure

from qgis.PyQt.QtCore import *

class QEsgModel(object):
    def tr(self, message):
        QCoreApplication.translate('QEsg',message)
    TUBOS_MAT=[[150.,.013],
                [200.,.013],
                [250.,.013],
                [300.,.013],
                [350.,.013],
                [400.,.013],
                [450.,.013],
                [500.,.013],
                [600.,.013],
                [700.,.013],
                [800.,.013],
                [900.,.013],
                [1000.,.013],
                [1100.,.013],
                [1200.,.013],
                [1300.,.013],
                [1400.,.013],
                [1500.,.013],
                [1600.,.013],
                [1700.,.013],
                [1800.,.013],
                [1900.,.013],
                [2000.,.013],
                [2100.,.013]]
    GIS_SHAPES = ['PIPES','JUNCTIONS','INTERFERENCES' ] #'BACIAS'
    COLUMNS = {'BACIAS': ['DC_ID','POPINI','POPFIM','PERCAPTA','K1_DIA','K2_HORA','COEF_RET','COEF_INF'],
               'PIPES': ['Coletor','Trecho','DC_ID', 'PVM', 'PVJ', 'LENGTH','CTM', 'CTJ','CCM','CCJ','NA_MON','NA_JUS','PRFM','PRFJ', 'DIAMETER',
                         'DECL','DECL_MIN','Q_CONC_INI', 'Q_CONC_FIM', 'Q_INI','Q_FIM','VEL_INI','VEL_FIM','VEL_CRI','TRATIVA','LAM_INI','LAM_FIM','OBS',
                          'MANNING','LAM_MAX','REC_MIN','CONTR_LADO','ETAPA','PONTA_SECA'],
               'JUNCTIONS': ['DC_ID', 'COTA_TN'],
               'INTERFERENCES': ['DC_ID', 'TIPO_INT','CS','CI','DIAMETER','CGI','INTERNAL']}
#                'RESERVOIRS': ['DC_ID', 'HEAD', 'PATTERN'],
#                'TANKS': ['DC_ID', 'COTA_TN', 'INITIALLEV', 'MINIMUMLEV', 'MAXIMUMLEV', 'DIAMETER', 'MINIMUMVOL', 'VOLUMECURV'],
#                'PUMPS': ['COTA_TN', 'DC_ID', 'PROPERTIES'],
#                'VALVES': ['COTA_TN', 'DC_ID', 'DIAMETER', 'TYPE', 'SETTING', 'MINORLOSS'],}

    INDIA_COLUMNS = {'BACIAS': ['DC_ID','POPINI','POPFIM','PERCAPTA','K1_DIA','K2_HORA','COEF_RET','COEF_INF'],
               'PIPES': ['Coletor','Trecho','DC_ID', 'PVM', 'PVJ', 'LENGTH','CTM', 'CTJ','CCM','CCJ','NA_MON','NA_JUS','PRFM','PRFJ', 'DIAMETER','DECL',
                           'Q_CONC_INI', 'Q_CONC_FIM', 'Q_INI','Q_FIM','VEL_INI','VEL_FIM','VEL_CRI','VEL_PROJ','TRATIVA','LAM_INI','LAM_FIM','OBS',
                          'MANNING','LAM_MAX','REC_MIN','CONTR_LADO','ETAPA','PONTA_SECA'],
               'JUNCTIONS': ['DC_ID', 'COTA_TN'],
               'INTERFERENCES': ['DC_ID', 'TIPO_INT','CS','CI','DIAMETER','CGI','INTERNAL']}

    #COLUMNS E CAMPOSDEF poderiam ser apenas um dicionario, o problema e que os dicionarios nao sao armazenados na ordem em que foram criados,
    #                    assim os campos seriam criados na tabela em ordem diferente
    #CAMPOSDEF ={'CAMPO': [COLUMN_TYPE,COLUMN_TYPENAME,COLUMN_SYZE,COLUMN_PREC]}
    CAMPOSDEF = {   'Coletor': [QVariant.Int,'integer',6,0],
                    'Trecho': [QVariant.Int,'integer',6,0],
                    'DC_ID': [QVariant.String,'String',20,0],
                    'POPINI': [QVariant.Double,'Real',10,1],
                    'POPFIM': [QVariant.Double,'Real',10,1],
                    'PERCAPTA': [QVariant.Double,'Real',10,1],
                    'K1_DIA': [QVariant.Double,'Real',10,2],
                    'K2_HORA': [QVariant.Double,'Real',10,2],
                    'COEF_RET': [QVariant.Double,'Real',10,2],
                    'COEF_INF': [QVariant.Double,'Real',10,5],
                    'PVM': [QVariant.String,'String',20,0],
                    'PVJ': [QVariant.String,'String',20,0],
                    'LENGTH': [QVariant.Double,'Real',10,3],
                    'CTM': [QVariant.Double,'Real',10,3],
                    'CTJ': [QVariant.Double,'Real',10,3],
                    'CCM': [QVariant.Double,'Real',15,5],
                    'CCJ': [QVariant.Double,'Real',15,5],
                    'NA_MON': [QVariant.Double,'Real',10,3],
                    'NA_JUS': [QVariant.Double,'Real',10,3],
                    'PRFM': [QVariant.Double,'Real',10,3],
                    'PRFJ': [QVariant.Double,'Real',10,3],
                    'DIAMETER': [QVariant.Double,'Real',10,1], #mm
                    'DN_FIXO': [QVariant.String,'String',1,0],
                    'DECL': [QVariant.Double,'Real',10,5],
                    'DECL_MIN': [QVariant.Double,'Real',10,5],
                    'Q_CONC_INI': [QVariant.Double,'Real',10,3],
                    'Q_CONC_FIM': [QVariant.Double,'Real',10,3],
                    'Q_INI': [QVariant.Double,'Real',10,3],
                    'Q_FIM': [QVariant.Double,'Real',10,3],
                    'VEL_INI': [QVariant.Double,'Real',10,2],
                    'VEL_FIM': [QVariant.Double,'Real',10,2],
                    'VEL_CRI': [QVariant.Double,'Real',10,2],
                    'VEL_PROJ': [QVariant.Double,'Real',10,2],#India Proj Speed
                    'TRATIVA': [QVariant.Double,'Real',10,3],
                    'LAM_INI': [QVariant.Double,'Real',10,4], #h/d
                    'LAM_FIM': [QVariant.Double,'Real',10,4], #h/d
                    'OBS': [QVariant.String,'String',50,0],
                    'MANNING': [QVariant.Double,'Real',10,3],
                    'LAM_MAX': [QVariant.Double,'Real',10,2], #h/d
                    'REC_MIN': [QVariant.Double,'Real',10,3],
                    'CONTR_LADO':[QVariant.Int,'integer',1,0],
                    'ETAPA': [QVariant.Int,'integer',1,0],
                    'PONTA_SECA': [QVariant.String,'String',1,0],

                    'COTA_TN': [QVariant.Double,'Real',10,3],
                    'TIPO_INT':[QVariant.String,'String',2,0],
                    'CS': [QVariant.Double,'Real',10,3],
                    'CI': [QVariant.Double,'Real',10,3],
                    'CGI': [QVariant.Double,'Real',10,3],
                    'INTERNAL':[QVariant.Int,'integer',1,0]}

    # Link sections share common ID namespace
    LINK_SECTIONS = ['PIPES','PUMPS','VALVES']
    # GIS nodes are different, see GHydraulicsModel.NODE_SECTIONS
    NODE_SECTIONS = ['JUNCTIONS', 'RESERVOIRS', 'TANKS']

    # List of units where length is in feet
    FEET_UNITS = ['CFS', 'GPM', 'MGD', 'IMGD', 'AFD']

    NODE_FIELDS = ['PVM', 'PVJ']

    # List of Styles
    qSTYLES = [ [QCoreApplication.translate('QEsg','Nós-ID'),'nos_nomes.qml','JUNCTIONS'],
                [QCoreApplication.translate('QEsg','Rede-Nomes'),'rede_nomes.qml','PIPES'],
                [QCoreApplication.translate('QEsg','Rede-CTM e CTJ'),'rede_ctm_ctj.qml','PIPES'],
                [QCoreApplication.translate('QEsg','Rede-CCM e CCJ'),'rede_ccm_ccj.qml','PIPES'],
                [QCoreApplication.translate('QEsg','Rede-PRFM e PRFJ'),'rede_prfm_prfj.qml','PIPES'],
                [QCoreApplication.translate('QEsg','Rede-Dimensionamento'),'rede_dimensionamento.qml','PIPES'],
                [QCoreApplication.translate('QEsg','Rede-Vazão'),'rede_vazao.qml','PIPES'],
                [QCoreApplication.translate('QEsg','Rede-Dados Completos'),'rede_completo.qml','PIPES'],
                [QCoreApplication.translate('QEsg','Rede-Tubo de Queda'),'rede_tubo_queda.qml','PIPES'],
                [QCoreApplication.translate('QEsg','Rede-Degrau ou TQ'),'rede_degrau.qml','PIPES'],
                [QCoreApplication.translate('QEsg','Rede-Ponta Seca'),'rede_ponta_seca.qml','PIPES'],
                [QCoreApplication.translate('QEsg','Rede-Contribuição pontual'),'rede_contrib_pontual.qml','PIPES'],
                [QCoreApplication.translate('QEsg','Rede-Tipo de contribuição'),'rede_tipo_contribuicao.qml','PIPES'],
                [QCoreApplication.translate('QEsg','Interferência-Padrão'),'interf_default.qml','INTERFERENCES']]
