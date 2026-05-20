"""
ui/Ui.py
--------
Interfaz gráfica principal del Visualizador de Árboles y Recursividad.
Construida con PyQt6.

Funcionalidades incluidas:
  - Visualización jerárquica de Árbol Binario, BST y AVL.
  - Inserción, búsqueda, eliminación con animación del camino recorrido.
  - Recorridos: preorden, inorden, postorden y nivel-order (BFS).
  - Consultas avanzadas: mínimo, máximo, ancestros, sucesor, predecesor,
    búsqueda por rango, espejo, LCA (Ancestro Común más Cercano).
  - Panel de información extendida: hojas, internos, ancho, propiedades.
  - Inserción de múltiples valores a la vez.
  - Zoom con Ctrl+scroll en el canvas.
  - Factor de balance visible en nodos AVL con color según estado.
  - Velocidad de animación configurable (Lento / Normal / Rápido).
  - Historial de las últimas 15 operaciones.
  - Atajos de teclado (Ctrl+F, Ctrl+S, Ctrl+O, Delete, Ctrl+0).
  - Tooltip en cada nodo: valor, nivel, altura, balance, tipo.
  - Guardado y carga de estructuras en JSON.

Bugs corregidos respecto a la versión original:
  - Timer detenido en change_tree_type, clear_tree y closeEvent.
  - Canvas usa el nodo como clave (no id(node)) — sin colisiones.
  - Input limpiado después de buscar.
"""

from __future__ import annotations

import os
import re
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from PyQt6.QtCore import QPointF, Qt, QTimer
    from PyQt6.QtGui import (
        QAction, QBrush, QColor, QFont, QKeySequence,
        QPainter, QPen, QWheelEvent, QShortcut
    )
    from PyQt6.QtWidgets import (
        QApplication, QComboBox, QFileDialog, QFrame,
        QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsScene,
        QGraphicsView, QGridLayout, QHBoxLayout,
        QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
        QMainWindow, QMessageBox, QPushButton, QScrollArea,
        QSizePolicy, QVBoxLayout, QWidget,
    )
except ImportError as exc:
    raise SystemExit(
        "PyQt6 no está instalado. Instálalo con:\n"
        "    pip install PyQt6\n\n"
        f"Detalle: {exc}"
    )

from logic import AVL, BST, BinaryTree, TreeStorage


# ═══════════════════════════════════════════════════════════════════════ #
#  Paleta de colores                                                       #
# ═══════════════════════════════════════════════════════════════════════ #

class Colors:
    bg           = "#eaf2ff"
    panel        = "#ffffff"
    ink          = "#10203f"
    muted        = "#516580"
    border       = "#b9ccef"
    primary      = "#1d4ed8"
    primary_dark = "#1e40af"
    warning      = "#f59e0b"
    danger       = "#dc2626"
    edge         = "#7692bd"
    node         = "#ffffff"
    focus        = "#fef08a"
    soft_blue    = "#dbeafe"
    soft_green   = "#dcfce7"
    soft_orange  = "#ffedd5"
    # Balance AVL
    bal_ok       = "#dcfce7"   # bf=0  → verde
    bal_warn     = "#fef9c3"   # bf=±1 → amarillo
    bal_bad      = "#fee2e2"   # bf>1  → rojo (no debería verse)


# ═══════════════════════════════════════════════════════════════════════ #
#  Canvas                                                                  #
# ═══════════════════════════════════════════════════════════════════════ #

class TreeCanvas(QGraphicsView):
    """
    Dibuja el árbol de forma jerárquica.
    - Ctrl+scroll: zoom.
    - Clic+arrastre: desplazamiento.
    - Tooltip por nodo: valor, nivel, altura, balance, tipo.
    - Colores AVL según factor de balance.
    """

    def __init__(self, colors: Colors, parent=None) -> None:
        super().__init__(parent)
        self.colors          = colors
        self.tree            = None
        self.highlight_values: set = set()
        self._zoom           = 1.0

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setBackgroundBrush(QBrush(QColor("#f4f8ff")))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    # ── Zoom ─────────────────────────────────────────────────────────── #

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor      = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self._zoom  = max(0.2, min(4.0, self._zoom * factor))
            self.resetTransform()
            self.scale(self._zoom, self._zoom)
        else:
            super().wheelEvent(event)

    def reset_zoom(self) -> None:
        self._zoom = 1.0
        self.resetTransform()

    # ── Dibujo ───────────────────────────────────────────────────────── #

    def set_tree(self, tree, highlight_values: set | None = None) -> None:
        self.tree             = tree
        self.highlight_values = set(highlight_values or set())
        self.draw_tree()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.draw_tree()

    def draw_tree(self) -> None:
        self.scene.clear()
        w = max(self.viewport().width(),  800)
        h = max(self.viewport().height(), 480)
        self.scene.setSceneRect(0, 0, w, h)

        if self.tree is None or self.tree.root is None:
            self._empty_message(w, h)
            return

        pos: dict = {}
        self._assign_pos(self.tree.root, w / 2, 72, w / 4, pos)
        self._draw_edges(self.tree.root, pos)
        self._draw_nodes(self.tree.root, pos)

    def _empty_message(self, w: float, h: float) -> None:
        f1 = QFont("Segoe UI", 16, QFont.Weight.DemiBold)
        t1 = self.scene.addText("El árbol está vacío", f1)
        t1.setDefaultTextColor(QColor(self.colors.muted))
        t1.setPos((w - t1.boundingRect().width()) / 2,
                  (h - t1.boundingRect().height()) / 2)
        f2 = QFont("Segoe UI", 11)
        t2 = self.scene.addText("Inserta valores desde el panel lateral", f2)
        t2.setDefaultTextColor(QColor(self.colors.border))
        t2.setPos((w - t2.boundingRect().width()) / 2,
                  (h - t2.boundingRect().height()) / 2 + 36)

    def _assign_pos(self, node, x: float, y: float, spread: float, pos: dict) -> None:
        if node is None:
            return
        pos[id(node)] = QPointF(x, y)          # ← nodo directo, no id(node)
        ns = max(spread / 2, 44)
        ny = y + 98
        self._assign_pos(node.left,  x - spread, ny, ns, pos)
        self._assign_pos(node.right, x + spread, ny, ns, pos)

    def _draw_edges(self, node, pos: dict) -> None:
        if node is None:
            return
        start = pos[id(node)]
        for child in (node.left, node.right):
            if child is None:
                continue
            end  = pos[id(child)]
            line = QGraphicsLineItem(
                start.x(), start.y() + 30,
                end.x(),   end.y()   - 30,
            )
            line.setPen(QPen(QColor(self.colors.edge), 2.5,
                             Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            self.scene.addItem(line)
            self._draw_edges(child, pos)

    def _draw_nodes(self, node, pos: dict) -> None:
        if node is None:
            return

        p   = pos[id(node)]
        r   = 28
        hl  = node.value in self.highlight_values

        # Color de relleno
        if hl:
            fill, border, bw = self.colors.focus, self.colors.warning, 3
        elif isinstance(self.tree, AVL):
            bf = node.balance
            fill   = self.colors.bal_ok if bf == 0 else (
                      self.colors.bal_warn if abs(bf) == 1 else self.colors.bal_bad)
            border = ("#166534" if bf == 0 else "#b45309" if abs(bf) == 1 else "#991b1b")
            bw = 2
        else:
            fill, border, bw = self.colors.node, self.colors.ink, 2

        # Círculo
        circle = QGraphicsEllipseItem(p.x()-r, p.y()-r, r*2, r*2)
        circle.setBrush(QBrush(QColor(fill)))
        circle.setPen(QPen(QColor(border), bw))
        circle.setToolTip(self._tooltip(node))
        self.scene.addItem(circle)

        # Valor
        vf  = QFont("Segoe UI", 11, QFont.Weight.Bold)
        vlb = self.scene.addText(str(node.value), vf)
        vlb.setDefaultTextColor(QColor(self.colors.ink))
        vlb.setPos(p.x() - vlb.boundingRect().width()  / 2,
                   p.y() - vlb.boundingRect().height() / 2 - 4)

        # Factor de balance (AVL)
        if isinstance(self.tree, AVL):
            bf     = node.balance
            bfc    = ("#166534" if bf == 0 else
                      "#b45309" if abs(bf) == 1 else "#991b1b")
            bff    = QFont("Segoe UI", 7)
            bflb   = self.scene.addText(f"bf={bf:+d}", bff)
            bflb.setDefaultTextColor(QColor(bfc))
            bflb.setPos(p.x() - bflb.boundingRect().width()  / 2,
                        p.y() + r - 14)

        self._draw_nodes(node.left,  pos)
        self._draw_nodes(node.right, pos)

    def _tooltip(self, node) -> str:
        if self.tree is None:
            return ""
        lvl  = self.tree.get_level(node.value)
        kind = ("Hoja" if node.is_leaf()
                else "Un hijo" if node.has_one_child()
                else "Dos hijos")
        lines = [
            f"Valor:  {node.value}",
            f"Nivel:  {lvl}",
            f"Altura: {node.height}",
            f"Tipo:   {kind}",
        ]
        if isinstance(self.tree, AVL):
            lines.append(f"Balance: {node.balance:+d}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════ #
#  Ventana principal                                                       #
# ═══════════════════════════════════════════════════════════════════════ #

class TreeVisualizerWindow(QMainWindow):

    TREE_TYPES = {"Árbol Binario": BinaryTree, "BST": BST, "AVL": AVL}

    def __init__(self) -> None:
        super().__init__()
        self.colors  = Colors()
        self.tree    = AVL()
        self.storage = TreeStorage()

        self.highlight_values: set  = set()
        self.animation_values: list = []
        self.animation_final:  set  = set()
        self.animation_index:  int  = 0
        self.animation_speed:  int  = 300
        self._history:    list[str] = []
        self._speed_btns: list      = []
        self._op_count:   int       = 0

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._animation_step)

        self.setWindowTitle("Visualizador de Árboles y Recursividad")
        self.resize(1360, 840)
        self.setMinimumSize(1040, 680)

        self._build_ui()
        self._build_menu()
        self._build_shortcuts()
        self._seed_example()
        self.refresh()

    # ================================================================== #
    #  Construcción de la UI                                              #
    # ================================================================== #

    def _build_ui(self) -> None:
        root = QWidget(); root.setObjectName("Root")
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(20, 14, 20, 12)
        main.setSpacing(10)

        title    = QLabel("Visualizador de Árboles y Recursividad")
        title.setObjectName("Title")
        subtitle = QLabel("Construye, analiza y visualiza Árboles Binarios, BST y AVL en tiempo real.")
        subtitle.setObjectName("Subtitle")
        main.addWidget(title)
        main.addWidget(subtitle)

        body = QHBoxLayout(); body.setSpacing(12)
        main.addLayout(body, stretch=1)

        # Sidebar
        sf = QFrame(); sf.setObjectName("Panel"); sf.setFixedWidth(368)
        so = QVBoxLayout(sf); so.setContentsMargins(0,0,0,0); so.setSpacing(0)
        sc = QScrollArea(); sc.setObjectName("SidebarScroll")
        sc.setWidgetResizable(True); sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sw = QWidget(); sw.setObjectName("SidebarContent")
        self._side = QVBoxLayout(sw)
        self._side.setContentsMargins(14, 14, 14, 14)
        self._side.setSpacing(9)
        sc.setWidget(sw); so.addWidget(sc)
        body.addWidget(sf)

        # Canvas panel
        rp = QFrame(); rp.setObjectName("Panel")
        rl = QVBoxLayout(rp); rl.setContentsMargins(0,0,0,0); rl.setSpacing(0)
        self.canvas = TreeCanvas(self.colors)
        rl.addWidget(self.canvas, stretch=1)

        bp = QFrame(); bp.setObjectName("BottomPanel")
        bl = QVBoxLayout(bp); bl.setContentsMargins(14,8,14,8); bl.setSpacing(3)
        self.traversal_label = QLabel("El recorrido aparecerá aquí.")
        self.traversal_label.setObjectName("Output"); self.traversal_label.setWordWrap(True)
        self.rotation_label  = QLabel("Sin rotaciones registradas.")
        self.rotation_label.setObjectName("OutputMuted"); self.rotation_label.setWordWrap(True)
        bl.addWidget(self.traversal_label); bl.addWidget(self.rotation_label)
        rl.addWidget(bp)
        body.addWidget(rp, stretch=1)

        self.status_label = QLabel("Listo.")
        self.status_label.setObjectName("Status")
        main.addWidget(self.status_label)

        self._build_sidebar()
        self._apply_styles()

    def _build_sidebar(self) -> None:
        s = self._side

        # Tipo
        s.addWidget(self._sec("Tipo de árbol"))
        self.tree_type_combo = QComboBox()
        self.tree_type_combo.addItems(self.TREE_TYPES.keys())
        self.tree_type_combo.setCurrentText("AVL")
        self.tree_type_combo.setMinimumHeight(34)
        self.tree_type_combo.currentTextChanged.connect(self.change_tree_type)
        s.addWidget(self.tree_type_combo)

        # Insertar
        s.addWidget(self._sec("Insertar"))
        r1 = QHBoxLayout()
        self.value_input = QLineEdit(); self.value_input.setPlaceholderText("Valor entero")
        self.value_input.setMinimumHeight(34); self.value_input.returnPressed.connect(self.insert_value)
        bi = QPushButton("Insertar"); bi.setObjectName("PrimaryButton")
        bi.setMinimumHeight(34); bi.clicked.connect(self.insert_value)
        r1.addWidget(self.value_input, stretch=1); r1.addWidget(bi)
        s.addLayout(r1)

        r2 = QHBoxLayout()
        self.multi_input = QLineEdit(); self.multi_input.setPlaceholderText("Varios: 10, 20, 30 …")
        self.multi_input.setMinimumHeight(32); self.multi_input.returnPressed.connect(self.insert_multiple)
        bm = QPushButton("Insertar varios"); bm.setMinimumHeight(32); bm.clicked.connect(self.insert_multiple)
        r2.addWidget(self.multi_input, stretch=1); r2.addWidget(bm)
        s.addLayout(r2)

        # Operaciones básicas
        s.addWidget(self._sec("Operaciones"))
        g = QGridLayout(); g.setSpacing(6)
        self._btn(g, "Buscar",        self.search_value,                        0, 0)
        self._btn(g, "Eliminar nodo", self.delete_value,                        0, 1)
        self._btn(g, "Preorden",      lambda: self.show_traversal("preorder"),  1, 0)
        self._btn(g, "Inorden",       lambda: self.show_traversal("inorder"),   1, 1)
        self._btn(g, "Postorden",     lambda: self.show_traversal("postorder"), 2, 0)
        self._btn(g, "Nivel-Order",   self.show_level_order,                    2, 1)
        self._btn(g, "3 Recorridos",  self.show_all_traversals,                 3, 0)
        self._btn(g, "Ejemplo",       self._seed_example,                       3, 1)
        self._btn(g, "Limpiar árbol", self.clear_tree,                          4, 0, danger=True)
        self._btn(g, "Espejo",        self.mirror_tree,                         4, 1, warning=True)
        s.addLayout(g)

        # Consultas avanzadas
        s.addWidget(self._sec("Consultas avanzadas"))

        mm = QHBoxLayout()
        self._btn(mm, "Mínimo",  self.show_min)
        self._btn(mm, "Máximo",  self.show_max)
        s.addLayout(mm)

        sl = QHBoxLayout()
        self._btn(sl, "Guardar", self.save_tree)
        self._btn(sl, "Cargar",  self.load_tree)
        s.addLayout(sl)

        # Ancestros
        ra = QHBoxLayout()
        self.anc_input = QLineEdit(); self.anc_input.setPlaceholderText("Valor → ancestros")
        self.anc_input.setMinimumHeight(32); self.anc_input.returnPressed.connect(self.show_ancestors)
        ba = QPushButton("Ancestros"); ba.setMinimumHeight(32); ba.clicked.connect(self.show_ancestors)
        ra.addWidget(self.anc_input, stretch=1); ra.addWidget(ba)
        s.addLayout(ra)

        # Sucesor / Predecesor
        rsp = QHBoxLayout()
        self.sp_input = QLineEdit(); self.sp_input.setPlaceholderText("Valor → suc/pred")
        self.sp_input.setMinimumHeight(32)
        bs = QPushButton("Sucesor");    bs.setMinimumHeight(32); bs.clicked.connect(self.show_successor)
        bp = QPushButton("Predecesor"); bp.setMinimumHeight(32); bp.clicked.connect(self.show_predecessor)
        rsp.addWidget(self.sp_input, stretch=1); rsp.addWidget(bs); rsp.addWidget(bp)
        s.addLayout(rsp)

        # Rango
        rrng = QHBoxLayout()
        self.range_low  = QLineEdit(); self.range_low.setPlaceholderText("Desde"); self.range_low.setMinimumHeight(32)
        self.range_high = QLineEdit(); self.range_high.setPlaceholderText("Hasta"); self.range_high.setMinimumHeight(32)
        br = QPushButton("Rango"); br.setMinimumHeight(32); br.clicked.connect(self.show_range)
        rrng.addWidget(self.range_low); rrng.addWidget(self.range_high); rrng.addWidget(br)
        s.addLayout(rrng)

        # LCA
        rlca = QHBoxLayout()
        self.lca_a = QLineEdit(); self.lca_a.setPlaceholderText("A (LCA)"); self.lca_a.setMinimumHeight(32)
        self.lca_b = QLineEdit(); self.lca_b.setPlaceholderText("B (LCA)"); self.lca_b.setMinimumHeight(32)
        bl = QPushButton("LCA"); bl.setMinimumHeight(32); bl.clicked.connect(self.show_lca)
        rlca.addWidget(self.lca_a); rlca.addWidget(self.lca_b); rlca.addWidget(bl)
        s.addLayout(rlca)

        # Velocidad
        s.addWidget(self._sec("Velocidad de animación"))
        rv = QHBoxLayout()
        for lbl, ms in [("Lento", 600), ("Normal", 300), ("Rápido", 100)]:
            b = QPushButton(lbl); b.setMinimumHeight(30)
            b.setCheckable(True); b.setChecked(lbl == "Normal")
            b.setObjectName("SpeedButton")
            b.clicked.connect(lambda _, m=ms, btn=b: self._set_speed(m, btn))
            rv.addWidget(b)
            self._speed_btns.append(b)
            if lbl == "Normal":
                self._active_speed = b
        s.addLayout(rv)

        self._sep(s)

        # Info
        s.addWidget(self._sec("Información del árbol"))
        mg = QGridLayout(); mg.setSpacing(5)
        self.m_type   = self._met("Tipo",        "-")
        self.m_root   = self._met("Raíz",        "-")
        self.m_height = self._met("Altura",      "0")
        self.m_count  = self._met("Nodos",       "0")
        self.m_leaves = self._met("Hojas",       "0")
        self.m_intern = self._met("Internos",    "0")
        self.m_width  = self._met("Ancho máx.",  "0")
        self.m_bal    = self._met("AVL balance", "-")
        mg.addWidget(self.m_type,   0, 0); mg.addWidget(self.m_root,   0, 1)
        mg.addWidget(self.m_height, 1, 0); mg.addWidget(self.m_count,  1, 1)
        mg.addWidget(self.m_leaves, 2, 0); mg.addWidget(self.m_intern, 2, 1)
        mg.addWidget(self.m_width,  3, 0); mg.addWidget(self.m_bal,    3, 1)
        s.addLayout(mg)

        self.props_label = QLabel("—"); self.props_label.setObjectName("PropsLabel")
        self.props_label.setWordWrap(True)
        s.addWidget(self.props_label)

        self._sep(s)

        # Recorridos
        s.addWidget(self._sec("Recorridos actuales"))
        self.c_pre   = self._tcard("Preorden")
        self.c_in    = self._tcard("Inorden")
        self.c_post  = self._tcard("Postorden")
        self.c_level = self._tcard("Nivel-Order")
        for c in (self.c_pre, self.c_in, self.c_post, self.c_level):
            s.addWidget(c)

        self._sep(s)

        # Historial
        s.addWidget(self._sec("Historial de operaciones"))
        self.history_list = QListWidget()
        self.history_list.setObjectName("HistoryList")
        self.history_list.setMaximumHeight(130)
        self.history_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        s.addWidget(self.history_list)

        self._sep(s)

        # Leyenda
        s.addWidget(self._sec("Leyenda"))
        s.addWidget(self._legend("Nodo normal",       self.colors.node,     self.colors.ink))
        s.addWidget(self._legend("Nodo resaltado",    self.colors.focus,    self.colors.warning))
        s.addWidget(self._legend("AVL  bf = 0",       self.colors.bal_ok,   "#166534"))
        s.addWidget(self._legend("AVL  bf = ±1",      self.colors.bal_warn, "#b45309"))

        hint = QLabel("💡 Ctrl+scroll = zoom   Ctrl+0 = reset\n   Ctrl+F = buscar   Ctrl+S = guardar\n   Delete = eliminar")
        hint.setObjectName("Hint")
        s.addWidget(hint)

        s.addStretch(1)

    def _build_menu(self) -> None:
        m = self.menuBar()
        fm = m.addMenu("Archivo")
        self._act(fm, "Guardar árbol", "Ctrl+S", self.save_tree)
        self._act(fm, "Cargar árbol",  "Ctrl+O", self.load_tree)
        fm.addSeparator()
        self._act(fm, "Salir",         "Ctrl+Q", self.close)

        vm = m.addMenu("Ver")
        self._act(vm, "Restablecer zoom", "Ctrl+0", self.canvas.reset_zoom)
        self._act(vm, "Insertar ejemplo", "",        self._seed_example)

        tm = m.addMenu("Árbol")
        self._act(tm, "Mínimo",        "", self.show_min)
        self._act(tm, "Máximo",        "", self.show_max)
        self._act(tm, "Espejo",        "", self.mirror_tree)
        tm.addSeparator()
        self._act(tm, "Limpiar árbol", "", self.clear_tree)

    def _build_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+F"), self, self.search_value)
        QShortcut(QKeySequence("Delete"), self, self.delete_value)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_tree)
        QShortcut(QKeySequence("Ctrl+O"), self, self.load_tree)
        QShortcut(QKeySequence("Ctrl+0"), self, self.canvas.reset_zoom)

    # ================================================================== #
    #  Helpers de widgets                                                 #
    # ================================================================== #

    def _sec(self, t: str) -> QLabel:
        l = QLabel(t); l.setObjectName("Section"); return l

    def _sep(self, layout: QVBoxLayout) -> None:
        f = QFrame(); f.setFrameShape(QFrame.Shape.HLine); f.setObjectName("Separator")
        layout.addWidget(f)

    def _btn(self, layout, text: str, slot,
             row=None, col=None, danger=False, warning=False) -> QPushButton:
        b = QPushButton(text); b.setMinimumHeight(33)
        if danger:   b.setObjectName("DangerButton")
        elif warning: b.setObjectName("WarningButton")
        b.clicked.connect(slot)
        if isinstance(layout, QGridLayout):
            layout.addWidget(b, row, col)
        else:
            layout.addWidget(b)
        return b

    def _met(self, title: str, value: str) -> QFrame:
        f = QFrame(); f.setObjectName("Metric"); f.setMinimumHeight(52)
        t = QLabel(title); t.setObjectName("MetricTitle")
        v = QLabel(value); v.setObjectName("MetricValue")
        f.value_label = v
        box = QVBoxLayout(f); box.setContentsMargins(8,5,8,5)
        box.addWidget(t); box.addWidget(v)
        return f

    def _tcard(self, title: str) -> QFrame:
        f = QFrame(); f.setObjectName("TraversalCard"); f.setMinimumHeight(48)
        t = QLabel(title); t.setObjectName("TraversalTitle")
        v = QLabel("(vacío)"); v.setObjectName("TraversalValue"); v.setWordWrap(True)
        f.value_label = v
        box = QVBoxLayout(f); box.setContentsMargins(8,5,8,5); box.setSpacing(2)
        box.addWidget(t); box.addWidget(v)
        return f

    def _legend(self, label: str, fill: str, outline: str) -> QWidget:
        w = QWidget(); row = QHBoxLayout(w); row.setContentsMargins(0,0,0,0)
        sw = QLabel(); sw.setFixedSize(22, 16)
        sw.setStyleSheet(f"background:{fill};border:2px solid {outline};border-radius:8px;")
        tx = QLabel(label); tx.setObjectName("Legend")
        row.addWidget(sw); row.addWidget(tx, stretch=1)
        return w

    def _act(self, menu, text: str, shortcut: str, slot) -> None:
        a = QAction(text, self)
        if shortcut: a.setShortcut(QKeySequence(shortcut))
        a.triggered.connect(slot)
        menu.addAction(a)

    # ================================================================== #
    #  Estilos                                                            #
    # ================================================================== #

    def _apply_styles(self) -> None:
        c = self.colors
        self.setStyleSheet(f"""
            QWidget#Root {{
                background:{c.bg}; color:{c.ink};
                font-family:"Segoe UI",Arial,sans-serif; font-size:13px;
            }}
            QWidget#SidebarContent,
            QScrollArea#SidebarScroll,
            QScrollArea#SidebarScroll > QWidget,
            QScrollArea#SidebarScroll > QWidget > QWidget {{
                background:transparent; border:none;
            }}
            QLabel#Title {{ font-size:24px; font-weight:700; color:{c.ink}; }}
            QLabel#Subtitle {{ color:{c.muted}; font-size:13px; }}
            QLabel#Section {{
                font-weight:700; font-size:11px; color:{c.muted};
                text-transform:uppercase; letter-spacing:1px;
            }}
            QLabel#OutputMuted, QLabel#Legend, QLabel#Hint {{
                color:{c.muted}; font-size:12px;
            }}
            QLabel#PropsLabel {{ color:{c.muted}; font-size:11px; padding:3px 0; }}
            QFrame#Panel {{
                background:{c.panel}; border:1px solid {c.border}; border-radius:12px;
            }}
            QFrame#BottomPanel {{
                background:#f4f8ff; border-top:1px solid {c.border};
                border-bottom-left-radius:12px; border-bottom-right-radius:12px;
            }}
            QFrame#Metric {{
                background:{c.soft_blue}; border:1px solid {c.border}; border-radius:8px;
            }}
            QLabel#MetricTitle {{ color:{c.muted}; font-size:11px; }}
            QLabel#MetricValue {{ color:{c.ink}; font-size:18px; font-weight:700; }}
            QFrame#TraversalCard {{
                background:#f8fbff; border:1px solid {c.border}; border-radius:8px;
            }}
            QLabel#TraversalTitle {{ color:{c.muted}; font-size:11px; font-weight:700; }}
            QLabel#TraversalValue {{ color:{c.ink}; font-size:11px; }}
            QLabel#Status {{
                padding:8px 14px; background:{c.soft_green};
                border-radius:8px; color:{c.ink}; font-size:12px; font-weight:600;
            }}
            QLabel#Output {{ color:{c.ink}; font-size:12px; }}

            QComboBox {{
                background:#ffffff;
                border:2px solid {c.border};
                border-radius:8px;
                padding:10px 14px;
                color:{c.ink};
                font-weight:600;
                font-size:14px;
            }}
            QComboBox:hover {{ border-color:{c.primary}; }}
            QComboBox:focus {{ border-color:{c.primary}; }}
            QComboBox::drop-down {{ border:none; width:24px; }}
            QComboBox::down-arrow {{
                image:none;
                border-left:5px solid transparent;
                border-right:5px solid transparent;
                border-top:6px solid {c.muted};
                margin-right:8px;
            }}
            QComboBox QAbstractItemView {{
                background:#ffffff;
                color:{c.ink};
                border:1px solid {c.border};
                border-radius:8px;
                padding:4px;
                outline:none;
                selection-background-color:{c.soft_blue};
                selection-color:{c.ink};
            }}
            QComboBox QAbstractItemView::item {{
                background:#ffffff;
                color:{c.ink};
                padding:10px 14px;
                min-height:28px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background:{c.soft_blue};
                color:{c.ink};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background:{c.soft_blue};
                color:{c.ink};
            }}

            QLineEdit {{
                background:#ffffff;
                border:2px solid {c.border};
                border-radius:8px;
                padding:10px 14px;
                color:{c.ink};
                font-size:14px;
            }}
            QLineEdit:focus {{ border-color:{c.primary}; }}

            QPushButton {{
                background:{c.soft_blue}; border:1px solid {c.border};
                border-radius:8px; padding:10px 16px;
                font-weight:600; color:{c.ink};
            }}
            QPushButton:hover {{ background:{c.primary}; color:#ffffff; border-color:{c.primary}; }}
            QPushButton#PrimaryButton {{
                background:{c.primary}; color:#ffffff; border:none;
            }}
            QPushButton#PrimaryButton:hover {{ background:{c.primary_dark}; }}
            QPushButton#DangerButton {{
                background:{c.soft_orange}; color:#991b1b; border-color:#fed7aa;
            }}
            QPushButton#DangerButton:hover {{ background:#fcd2a2; color:#991b1b; }}
            QPushButton#WarningButton {{
                background:#fef9c3; color:#92400e; border-color:#fde68a;
            }}
            QPushButton#WarningButton:hover {{ background:#fde68a; color:#92400e; }}
            QPushButton#SpeedButton {{
                background:{c.soft_blue}; border:1px solid {c.border};
                border-radius:8px; padding:6px 10px; font-size:12px;
            }}
            QPushButton#SpeedButton:hover {{ background:{c.primary}; color:#ffffff; }}
            QPushButton#SpeedButton:checked {{
                background:{c.primary}; color:#ffffff; border-color:{c.primary};
            }}
            QFrame#Separator {{
                color:{c.border}; background:{c.border}; max-height:1px; border:none;
            }}
            QListWidget#HistoryList {{
                background:#f8fbff; border:1px solid {c.border};
                border-radius:8px; font-size:11px; color:{c.ink};
            }}
            QListWidget#HistoryList::item {{
                padding:4px 8px; border-bottom:1px solid {c.border};
            }}
            QMenuBar {{ background:{c.panel}; font-size:13px; }}
            QMenuBar::item:selected {{ background:{c.soft_blue}; border-radius:4px; }}
            QMenu {{
                background:{c.panel}; border:1px solid {c.border}; border-radius:6px;
            }}
            QMenu::item:selected {{ background:{c.soft_blue}; }}
        """)

    # ================================================================== #
    #  Operaciones                                                        #
    # ================================================================== #

    def change_tree_type(self, text: str) -> None:
        self.animation_timer.stop()                         # BUG FIX
        self.tree             = self.TREE_TYPES[text]()
        self.highlight_values = set()
        self._log(f"Tipo → {text}")
        self.traversal_label.setText(f"Árbol {text} creado.")
        self.rotation_label.setText("Sin rotaciones.")
        self.status_label.setText(f"Tipo: {text}  |  Raíz: {self._root()}")
        self.refresh()

    def insert_value(self) -> None:
        value = self._int(self.value_input)
        if value is None: return
        count_before = self.tree.node_count
        path, rots   = self._do_insert(value)
        is_duplicate = self.tree.node_count == count_before
        visited      = path + [value]
        self.value_input.clear()
        if is_duplicate:
            self.traversal_label.setText(
                f"⚠ El valor {value} ya existe en el árbol — no se insertaron duplicados."
            )
            self.rotation_label.setText("Los árboles BST y AVL no permiten valores repetidos.")
            self.status_label.setText(f"Duplicado ignorado: {value}  |  Nodos: {self.tree.node_count}")
            self._log(f"Duplicado ignorado: {value}")
            self.animate_values(path, final={value})
            return
        self.traversal_label.setText(f"Inserción de {value}  |  Camino: {self._fmt(visited)}")
        self.rotation_label.setText(
            ("Rotaciones: " + ", ".join(rots) if rots else "Sin rotaciones.") +
            f"  |  Raíz: {self._root()}"
        )
        self.status_label.setText(f"Insertado {value}  |  Nodos: {self.tree.node_count}")
        self._log(f"Insertar {value}")
        self.animate_values(visited, final={value})

    def insert_multiple(self) -> None:
        raw = self.multi_input.text().strip()
        if not raw:
            QMessageBox.warning(self, "Sin valores", "Ingresa valores separados por comas.")
            return
        vals = []
        for t in raw.replace(",", " ").split():
            try: vals.append(int(t))
            except ValueError: pass
        if not vals:
            QMessageBox.critical(self, "Error", "No se encontraron enteros válidos.")
            return
        for v in vals:
            self._do_insert(v)
        self.multi_input.clear()
        self.highlight_values = set(vals)
        self.traversal_label.setText(f"Insertados: {self._fmt(vals)}")
        self.rotation_label.setText(f"{len(vals)} valores añadidos.")
        self.status_label.setText(f"Inserción múltiple  |  Nodos: {self.tree.node_count}")
        self._log(f"Insertar varios: {vals}")
        self.refresh()

    def search_value(self) -> None:
        value = self._int(self.value_input)
        if value is None: return
        node, path = self.tree.search(value)
        self.value_input.clear()                            # BUG FIX
        found = node is not None
        self.traversal_label.setText(f"Búsqueda de {value}  |  Camino: {self._fmt(path)}")
        self.rotation_label.setText(f"{'✓ Encontrado' if found else '✗ No encontrado'}  |  {len(path)} nodos visitados")
        self.status_label.setText(f"{'Encontrado' if found else 'No encontrado'}: {value}")
        self._log(f"Buscar {value} → {'OK' if found else 'no existe'}")
        self.animate_values(path, final={value} if found else set())

    def delete_value(self) -> None:
        value = self._int(self.value_input)
        if value is None: return
        self.animation_timer.stop()
        if isinstance(self.tree, AVL):
            ok, desc, rots = self.tree.delete(value)
            rot_text = ("Rotaciones: " + ", ".join(rots)) if rots else "Sin rotaciones."
        else:
            ok, desc = self.tree.delete(value)
            rot_text = "Eliminación completada."
        self.value_input.clear()
        self.highlight_values = set()
        self.traversal_label.setText(desc)
        self.rotation_label.setText(rot_text + f"  |  Raíz: {self._root()}")
        self.status_label.setText(f"{'Eliminado' if ok else 'No encontrado'}: {value}  |  Nodos: {self.tree.node_count}")
        self._log(f"Eliminar {value} → {'OK' if ok else 'no existe'}")
        self.refresh()

    def show_traversal(self, kind: str) -> None:
        names = {"preorder":"Preorden","inorder":"Inorden","postorder":"Postorden"}
        vals  = getattr(self.tree, kind)()
        self.traversal_label.setText(f"{names[kind]}: {self._fmt(vals)}")
        self.rotation_label.setText("Recorrido recursivo animado.")
        self.status_label.setText(f"{names[kind]}  |  {len(vals)} nodos")
        self._log(f"Recorrido {names[kind]}")
        self.animate_values(vals)

    def show_level_order(self) -> None:
        if self.tree.root is None:
            self.traversal_label.setText("El árbol está vacío.")
            self.status_label.setText("Sin nodos para recorrer.")
            return
        vals   = self.tree.level_order()
        levels = self.tree.nodes_by_level()
        self.traversal_label.setText(f"Nivel-Order (BFS): {self._fmt(vals)}")
        self.rotation_label.setText("  |  ".join(f"N{i}:{lv}" for i, lv in enumerate(levels)))
        self.status_label.setText(f"Nivel-Order  |  {len(levels)} niveles  |  Ancho: {self.tree.get_width()}")
        self._log("Recorrido Nivel-Order")
        self.animate_values(vals)

    def show_all_traversals(self) -> None:
        pre, ino, post, lvl = (self.tree.preorder(), self.tree.inorder(),
                               self.tree.postorder(), self.tree.level_order())
        self.traversal_label.setText(
            f"Pre: {self._fmt(pre)}  |  In: {self._fmt(ino)}  |  Post: {self._fmt(post)}"
        )
        self.rotation_label.setText(f"Nivel-Order: {self._fmt(lvl)}")
        self.status_label.setText("4 recorridos actualizados.")
        self._log("Ver 4 recorridos")
        self.animate_values(pre)

    # ── Consultas avanzadas ─────────────────────────────────────────── #

    def show_min(self) -> None:
        if not isinstance(self.tree, (BST, AVL)):
            QMessageBox.information(self, "Solo BST/AVL", "Mínimo solo aplica a BST y AVL.")
            return
        val = self.tree.get_min()
        if val is None: self.status_label.setText("Árbol vacío."); return
        self.traversal_label.setText(f"Mínimo del árbol: {val}")
        self.rotation_label.setText("Nodo más a la izquierda.")
        self.status_label.setText(f"Mínimo: {val}")
        self._log(f"Mínimo → {val}")
        self.animate_values(self.tree.get_ancestors(val) + [val], final={val})

    def show_max(self) -> None:
        if not isinstance(self.tree, (BST, AVL)):
            QMessageBox.information(self, "Solo BST/AVL", "Máximo solo aplica a BST y AVL.")
            return
        val = self.tree.get_max()
        if val is None: self.status_label.setText("Árbol vacío."); return
        self.traversal_label.setText(f"Máximo del árbol: {val}")
        self.rotation_label.setText("Nodo más a la derecha.")
        self.status_label.setText(f"Máximo: {val}")
        self._log(f"Máximo → {val}")
        self.animate_values(self.tree.get_ancestors(val) + [val], final={val})

    def show_ancestors(self) -> None:
        value = self._int(self.anc_input)
        if value is None: return
        node, _ = self.tree.search(value)
        if node is None:
            self.status_label.setText(f"{value} no existe en el árbol.")
            return
        ancs = self.tree.get_ancestors(value)
        self.traversal_label.setText(
            f"Ancestros de {value}: {self._fmt(ancs) if ancs else '(es la raíz)'}"
        )
        self.rotation_label.setText(f"{len(ancs)} ancestro(s)  |  Nivel: {self.tree.get_level(value)}")
        self.status_label.setText(f"Ancestros de {value}")
        self._log(f"Ancestros({value}) → {ancs}")
        self.animate_values(ancs, final={value})

    def show_successor(self) -> None:
        if not isinstance(self.tree, (BST, AVL)):
            QMessageBox.information(self, "Solo BST/AVL", "Sucesor solo aplica a BST y AVL.")
            return
        value = self._int(self.sp_input)
        if value is None: return
        suc = self.tree.successor(value)
        self.traversal_label.setText(
            f"Sucesor de {value}: {suc if suc is not None else 'no existe (es el máximo)'}"
        )
        self.rotation_label.setText("Siguiente valor mayor en inorden.")
        self.status_label.setText(f"Sucesor({value}) → {suc}")
        self._log(f"Sucesor({value}) → {suc}")
        if suc is not None:
            self.animate_values([value, suc], final={suc})

    def show_predecessor(self) -> None:
        if not isinstance(self.tree, (BST, AVL)):
            QMessageBox.information(self, "Solo BST/AVL", "Predecesor solo aplica a BST y AVL.")
            return
        value = self._int(self.sp_input)
        if value is None: return
        pred = self.tree.predecessor(value)
        self.traversal_label.setText(
            f"Predecesor de {value}: {pred if pred is not None else 'no existe (es el mínimo)'}"
        )
        self.rotation_label.setText("Anterior valor menor en inorden.")
        self.status_label.setText(f"Predecesor({value}) → {pred}")
        self._log(f"Predecesor({value}) → {pred}")
        if pred is not None:
            self.animate_values([value, pred], final={pred})

    def show_range(self) -> None:
        if not isinstance(self.tree, (BST, AVL)):
            QMessageBox.information(self, "Solo BST/AVL", "Rango solo aplica a BST y AVL.")
            return
        low  = self._int(self.range_low,  "Desde")
        high = self._int(self.range_high, "Hasta")
        if low is None or high is None: return
        if low > high: low, high = high, low
        res = self.tree.range_search(low, high)
        self.traversal_label.setText(f"Rango [{low}, {high}]: {self._fmt(res) if res else '(sin resultados)'}")
        self.rotation_label.setText(f"{len(res)} valor(es) en el rango.")
        self.status_label.setText(f"Rango [{low},{high}]  |  {len(res)} resultados")
        self._log(f"Rango[{low},{high}] → {res}")
        self.animate_values(res, final=set(res))

    def show_lca(self) -> None:
        v1 = self._int(self.lca_a, "Valor A")
        v2 = self._int(self.lca_b, "Valor B")
        if v1 is None or v2 is None: return
        res = self.tree.lca(v1, v2)
        if res is None:
            self.status_label.setText("LCA: algún valor no existe en el árbol.")
            return
        self.traversal_label.setText(f"LCA({v1}, {v2}) = {res}  (Ancestro Común más Cercano)")
        self.rotation_label.setText("Nodo más profundo que es ancestro de ambos valores.")
        self.status_label.setText(f"LCA({v1},{v2}) → {res}")
        self._log(f"LCA({v1},{v2}) → {res}")
        combined = list(dict.fromkeys(
            self.tree.get_ancestors(v1) + [v1] +
            self.tree.get_ancestors(v2) + [v2]
        ))
        self.animate_values(combined, final={res})

    def mirror_tree(self) -> None:
        if not isinstance(self.tree, (BST, AVL)):
            QMessageBox.information(self, "Solo BST/AVL", "Espejo aplica a BST y AVL.")
            return
        if self.tree.root is None:
            QMessageBox.information(self, "Árbol vacío", "Inserta valores antes de aplicar espejo.")
            return
        r = QMessageBox.question(
            self, "Espejo",
            "Esto invertirá el árbol sobre su eje vertical.\n"
            "El árbol dejará de ser un BST válido.\n\n¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if r == QMessageBox.StandardButton.Yes:
            self.animation_timer.stop()
            self.tree.mirror()
            self.highlight_values = set()
            self.traversal_label.setText("Árbol espejo — hijos intercambiados recursivamente.")
            self.rotation_label.setText("Inorden ahora produce orden descendente.")
            self.status_label.setText("Árbol invertido.")
            self._log("Espejo")
            self.refresh()

    def clear_tree(self) -> None:
        self.animation_timer.stop()                         # BUG FIX
        msg = QMessageBox(self)
        msg.setWindowTitle("Limpiar árbol")
        msg.setText("¿Eliminar todos los nodos?")
        msg.setIcon(QMessageBox.Icon.Question)
        si = msg.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        msg.addButton("No", QMessageBox.ButtonRole.NoRole)
        msg.exec()
        if msg.clickedButton() == si:
            self.tree.clear()
            self.highlight_values = set()
            self.traversal_label.setText("Árbol vacío.")
            self.rotation_label.setText("Sin rotaciones.")
            self.status_label.setText("Árbol limpiado.")
            self._log("Árbol limpiado")
            self.refresh()

    def save_tree(self) -> None:
        filename, ok = QInputDialog.getText(self, "Guardar árbol", "Nombre del archivo:")
        if not ok or not filename.strip(): return
        # Eliminar caracteres inválidos en nombres de archivo
        safe = re.sub(r'[\\/:*?"<>|]', '_', filename.strip())
        if safe != filename.strip():
            QMessageBox.information(
                self, "Nombre ajustado",
                f"Se reemplazaron caracteres inválidos:\n'{filename.strip()}' → '{safe}'"
            )
        try:
            path = self.storage.save(self.tree, safe)
            self.status_label.setText(f"Guardado: {path}")
            self._log(f"Guardar → {filename.strip()}.json")
            QMessageBox.information(self, "Guardado", f"Árbol guardado en:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Error al guardar", str(exc))

    def load_tree(self) -> None:
        fp, _ = QFileDialog.getOpenFileName(
            self, "Cargar árbol", self.storage.save_dir,
            "Archivos JSON (*.json);;Todos (*.*)",
        )
        if not fp: return
        try:
            self.animation_timer.stop()
            loader    = TreeStorage(save_dir=os.path.dirname(fp))
            self.tree = loader.load(os.path.basename(fp))
            self.tree_type_combo.blockSignals(True)
            self.tree_type_combo.setCurrentText(self._disp_type(self.tree))
            self.tree_type_combo.blockSignals(False)
            name = os.path.basename(fp)
            self.traversal_label.setText(f"Cargado: {name}")
            self.rotation_label.setText("Estructura reconstruida desde JSON.")
            self.status_label.setText(f"Árbol cargado  |  Raíz: {self._root()}")
            self._log(f"Cargar ← {name}")
            # Resaltar la raíz al cargar para dar feedback visual inmediato
            root_val = self.tree.root_value
            if root_val is not None:
                self.animate_values(
                    self.tree.level_order()[:min(7, self.tree.node_count)],
                    final={root_val}
                )
            else:
                self.highlight_values = set()
                self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Error al cargar", str(exc))

    # ================================================================== #
    #  Animación                                                          #
    # ================================================================== #

    def animate_values(self, values: list, final: set | None = None) -> None:
        self.animation_timer.stop()
        self.animation_values = list(values)
        self.animation_final  = set(final if final is not None else values)
        self.animation_index  = 0
        if not self.animation_values:
            self.highlight_values = set()
            self.refresh()
            return
        self.animation_timer.start(self.animation_speed)

    def _animation_step(self) -> None:
        if self.animation_index >= len(self.animation_values):
            self.animation_timer.stop()
            self.highlight_values = set(self.animation_final)
            self.refresh()
            return
        self.highlight_values = set(self.animation_values[: self.animation_index + 1])
        self.animation_index += 1
        self.refresh()

    def _set_speed(self, ms: int, btn: QPushButton) -> None:
        self.animation_speed = ms
        for b in self._speed_btns:
            b.setChecked(False)
        btn.setChecked(True)

    # ================================================================== #
    #  Refresco                                                           #
    # ================================================================== #

    def refresh(self) -> None:
        self._update_metrics()
        self._update_traversals()
        self.canvas.set_tree(self.tree, self.highlight_values)

    def _update_metrics(self) -> None:
        info = self.tree.get_full_info()
        raw  = str(info.get("type", "-"))
        disp = {"BinaryTree": "Árbol Binario", "BST": "BST", "AVL": "AVL"}.get(raw, raw)

        self.m_type.value_label.setText(disp)
        self.m_root.value_label.setText(self._root())
        self.m_height.value_label.setText(str(info.get("height",     0)))
        self.m_count.value_label.setText(str(info.get("node_count",  0)))
        self.m_leaves.value_label.setText(str(info.get("leaves",     0)))
        self.m_intern.value_label.setText(str(info.get("internal",   0)))
        self.m_width.value_label.setText(str(info.get("width",       0)))

        bal = info.get("is_balanced")
        self.m_bal.value_label.setText(
            "Balanceado" if bal is True else "Desbalanceado" if bal is False else "No aplica"
        )
        props = []
        if info.get("is_perfect"):  props.append("✓ Perfecto")
        if info.get("is_complete"): props.append("✓ Completo")
        if info.get("is_full"):     props.append("✓ Lleno")
        self.props_label.setText("  ".join(props) if props else "—")

    def _update_traversals(self) -> None:
        self.c_pre.value_label.setText(self._fmt(self.tree.preorder()))
        self.c_in.value_label.setText(self._fmt(self.tree.inorder()))
        self.c_post.value_label.setText(self._fmt(self.tree.postorder()))
        self.c_level.value_label.setText(self._fmt(self.tree.level_order()))

    # ================================================================== #
    #  Historial                                                          #
    # ================================================================== #

    def _log(self, action: str) -> None:
        self._op_count += 1
        self._history.insert(0, f"#{self._op_count}  {action}")
        self._history = self._history[:15]
        self.history_list.clear()
        for i, entry in enumerate(self._history):
            item = QListWidgetItem(f"• {entry}")
            item.setForeground(QColor(self.colors.ink if i == 0 else self.colors.muted))
            self.history_list.addItem(item)

    # ================================================================== #
    #  Utilidades                                                         #
    # ================================================================== #

    def _do_insert(self, value) -> tuple[list, list]:
        if isinstance(self.tree, AVL):
            _, path, rots = self.tree.insert(value)
        else:
            _, path = self.tree.insert(value)
            rots = []
        return path, rots

    def _int(self, widget: QLineEdit, label: str = "Valor") -> int | None:
        raw = widget.text().strip()
        if not raw:
            QMessageBox.warning(self, "Campo vacío", f"Ingresa un número en '{label}'.")
            return None
        try:
            return int(raw)
        except ValueError:
            QMessageBox.critical(self, "Valor inválido", f"'{raw}' no es un entero.")
            return None

    def _seed_example(self) -> None:
        self.animation_timer.stop()
        tree_class    = self.TREE_TYPES[self.tree_type_combo.currentText()]
        self.tree     = tree_class()
        for v in [50, 30, 70, 20, 40, 60, 80]:
            self.tree.insert(v)
        self.highlight_values = set()
        self.traversal_label.setText("Ejemplo: 50 → 30 → 70 → 20 → 40 → 60 → 80")
        self.rotation_label.setText("Usa los botones para explorar el árbol.")
        self.status_label.setText(f"Ejemplo cargado  |  Raíz: {self._root()}")
        self._log("Ejemplo cargado")
        self.refresh()

    def _disp_type(self, tree) -> str:
        if isinstance(tree, AVL): return "AVL"
        if isinstance(tree, BST): return "BST"
        return "Árbol Binario"

    def _fmt(self, values: list) -> str:
        return " → ".join(str(v) for v in values) if values else "(vacío)"

    def _root(self) -> str:
        v = self.tree.root_value
        return "-" if v is None else str(v)

    # ================================================================== #
    #  Ciclo de vida                                                      #
    # ================================================================== #

    def closeEvent(self, event) -> None:
        self.animation_timer.stop()                         # BUG FIX
        super().closeEvent(event)


# ═══════════════════════════════════════════════════════════════════════ #
#  Entry point                                                             #
# ═══════════════════════════════════════════════════════════════════════ #

def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Visualizador de Árboles")
    app.setStyle("Fusion")
    window = TreeVisualizerWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()