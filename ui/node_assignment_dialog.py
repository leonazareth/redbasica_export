# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox


class NodeAssignmentDialog(QDialog):
    """Dialog to select attributes for Node Assignment."""
    
    def __init__(self, fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Assign Nodes & Attributes")
        
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QVBoxLayout.SetFixedSize)  # Minimize size to content
        
        # ID Field
        layout.addWidget(QLabel("Node ID Field (Required):"))
        self.id_combo = QComboBox()
        self.id_combo.addItems(fields)
        self._set_default(self.id_combo, ["id_nodo_(n", "node_id", "id"])
        layout.addWidget(self.id_combo)
        
        # Ground Elevation Field (CT - Cota do Terreno)
        layout.addWidget(QLabel("Ground Elevation Field (CT):"))
        self.ground_elev_combo = QComboBox()
        self.ground_elev_combo.addItem(" - Skip - ", None)
        self.ground_elev_combo.addItems(fields)
        self._set_default(self.ground_elev_combo, ["ct_(n)", "ground_elev", "cota_terreno", "elev"])
        layout.addWidget(self.ground_elev_combo)
        
        # Invert Elevation Field (CF - Cota de Fundo)
        layout.addWidget(QLabel("Invert Elevation Field (CF):"))
        self.invert_elev_combo = QComboBox()
        self.invert_elev_combo.addItem(" - Skip - ", None)
        self.invert_elev_combo.addItems(fields)
        self._set_default(self.invert_elev_combo, ["cf_nodo", "invert_elev", "cota_fundo", "cf"])
        layout.addWidget(self.invert_elev_combo)
        
        # Depth Field (Profundidade - optional, pode ser calculado)
        layout.addWidget(QLabel("Depth Field (h) [optional]:"))
        self.depth_combo = QComboBox()
        self.depth_combo.addItem(" - Skip - ", None)
        self.depth_combo.addItems(fields)
        self._set_default(self.depth_combo, ["h_nodo_nt", "depth", "profundidade"])
        layout.addWidget(self.depth_combo)
        

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def _set_default(self, combo, candidates):
        """Select first matching candidate based on priority. Exact match first, then partial."""
        # First pass: exact match (case insensitive)
        for cand in candidates:
            cand_lower = cand.lower()
            for i in range(combo.count()):
                text = combo.itemText(i).lower()
                if cand_lower == text:  # Exact match
                    combo.setCurrentIndex(i)
                    return
        
        # Second pass: partial match (contains)
        for cand in candidates:
            cand_lower = cand.lower()
            for i in range(combo.count()):
                text = combo.itemText(i).lower()
                if cand_lower in text:  # Partial match
                    combo.setCurrentIndex(i)
                    return

    def get_selected_fields(self):
        """Return (id_field, depth_field, ground_elev_field, invert_elev_field)."""
        id_f = self.id_combo.currentText()
        
        depth_f = self.depth_combo.currentText()
        if depth_f == " - Skip - ": depth_f = None
        
        ground_elev_f = self.ground_elev_combo.currentText()
        if ground_elev_f == " - Skip - ": ground_elev_f = None
        
        invert_elev_f = self.invert_elev_combo.currentText()
        if invert_elev_f == " - Skip - ": invert_elev_f = None
        
        return id_f, depth_f, ground_elev_f, invert_elev_f
