from __future__ import annotations

import os
import sys
from dataclasses import dataclass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from PyQt6.QtCore import QPointF, QTimer, Qt
    from PyQt6.QtGui import QAction, QBrush, QColor, QFont, QPainter, QPen
    from PyQt6.QtWidgets import (
        QApplication,
        QComboBox,
        QFileDialog,
        QFrame,
        QGraphicsEllipseItem,
        QGraphicsLineItem,
        QGraphicsScene,
        QGraphicsView,
        QGridLayout,
        QHBoxLayout,
        QInputDialog,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:
    raise SystemExit(
        "PyQt6 no esta instalado. Instala la dependencia con:\n"
        "    pip install PyQt6\n\n"
        f"Detalle: {exc}"
    )

from logic import AVL, BST, BinaryTree, TreeStorage


@dataclass
class Colors:
    bg: str = "#eef3f8"
    panel: str = "#ffffff"
    ink: str = "#172033"
    muted: str = "#64748b"
    border: str = "#d7e1ee"
    primary: str = "#2563eb"
    primary_dark: str = "#1d4ed8"
    warning: str = "#d97706"
    danger: str = "#dc2626"
    edge: str = "#91a4bc"
    node: str = "#ffffff"
    focus: str = "#fde68a"


class TreeCanvas(QGraphicsView):
    def __init__(self, colors: Colors, parent=None) -> None:
        super().__init__(parent)
        self.colors = colors
        self.tree = None
        self.highlight_values: set[int] = set()

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setBackgroundBrush(QBrush(QColor("#fbfdff")))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_tree(self, tree, highlight_values: set[int] | None = None) -> None:
        self.tree = tree
        self.highlight_values = set(highlight_values or set())
        self.draw_tree()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.draw_tree()

    def draw_tree(self) -> None:
        self.scene.clear()

        width = max(self.viewport().width(), 760)
        height = max(self.viewport().height(), 430)
        self.scene.setSceneRect(0, 0, width, height)

        if self.tree is None or self.tree.root is None:
            text = self.scene.addText(
                "El arbol esta vacio",
                QFont("Segoe UI", 18, QFont.Weight.DemiBold),
            )
            text.setDefaultTextColor(QColor(self.colors.muted))
            text.setPos((width - text.boundingRect().width()) / 2, height / 2 - 30)
            return

        positions: dict[int, QPointF] = {}
        self._assign_positions(self.tree.root, width / 2, 70, width / 4, positions)
        self._draw_edges(self.tree.root, positions)
        self._draw_nodes(self.tree.root, positions)

    def _assign_positions(self, node, x: float, y: float, spread: float, positions: dict[int, QPointF]) -> None:
        if node is None:
            return

        positions[id(node)] = QPointF(x, y)

        next_spread = max(spread / 2, 46)
        next_y = y + 96

        self._assign_positions(node.left, x - spread, next_y, next_spread, positions)
        self._assign_positions(node.right, x + spread, next_y, next_spread, positions)

    def _draw_edges(self, node, positions: dict[int, QPointF]) -> None:
        if node is None:
            return

        start = positions[id(node)]

        for child in (node.left, node.right):
            if child is None:
                continue

            end = positions[id(child)]
            line = QGraphicsLineItem(start.x(), start.y() + 28, end.x(), end.y() - 28)
            line.setPen(
                QPen(
                    QColor(self.colors.edge),
                    3,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            self.scene.addItem(line)
            self._draw_edges(child, positions)

    def _draw_nodes(self, node, positions: dict[int, QPointF]) -> None:
        if node is None:
            return

        pos = positions[id(node)]
        radius = 29

        highlighted = node.value in self.highlight_values
        fill = self.colors.focus if highlighted else self.colors.node
        border = self.colors.warning if highlighted else self.colors.ink

        circle = QGraphicsEllipseItem(
            pos.x() - radius,
            pos.y() - radius,
            radius * 2,
            radius * 2,
        )
        circle.setBrush(QBrush(QColor(fill)))
        circle.setPen(QPen(QColor(border), 3))
        self.scene.addItem(circle)

        label = self.scene.addText(
            str(node.value),
            QFont("Segoe UI", 12, QFont.Weight.DemiBold),
        )
        label.setDefaultTextColor(QColor(self.colors.ink))
        label.setPos(pos.x() - label.boundingRect().width() / 2, pos.y() - 17)

        self._draw_nodes(node.left, positions)
        self._draw_nodes(node.right, positions)


class TreeVisualizerWindow(QMainWindow):
    TREE_TYPES = {
        "Arbol Binario": BinaryTree,
        "BST": BST,
        "AVL": AVL,
    }

    def __init__(self) -> None:
        super().__init__()

        self.colors = Colors()
        self.tree = AVL()
        self.storage = TreeStorage()

        self.highlight_values: set[int] = set()
        self.animation_values: list[int] = []
        self.animation_final: set[int] = set()
        self.animation_index = 0

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._animation_step)

        self.setWindowTitle("Visualizador de Arboles y Recursividad")
        self.resize(1220, 760)
        self.setMinimumSize(980, 640)

        self._build_ui()
        self._build_menu()
        self._seed_example()
        self.refresh()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(24, 20, 24, 16)
        main_layout.setSpacing(14)

        title = QLabel("Visualizador de Arboles y Recursividad")
        title.setObjectName("Title")

        subtitle = QLabel(
            "Interfaz PyQt6 para insertar, buscar, eliminar, recorrer, animar, guardar y cargar estructuras."
        )
        subtitle.setObjectName("Subtitle")

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        content = QHBoxLayout()
        content.setSpacing(16)
        main_layout.addLayout(content, stretch=1)

        sidebar = QFrame()
        sidebar.setObjectName("Panel")
        sidebar.setFixedWidth(340)

        sidebar_outer = QVBoxLayout(sidebar)
        sidebar_outer.setContentsMargins(0, 0, 0, 0)
        sidebar_outer.setSpacing(0)

        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setObjectName("SidebarScroll")
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        sidebar_content = QWidget()
        sidebar_content.setObjectName("SidebarContent")

        side_layout = QVBoxLayout(sidebar_content)
        side_layout.setContentsMargins(18, 18, 18, 18)
        side_layout.setSpacing(12)

        self.sidebar_scroll.setWidget(sidebar_content)
        sidebar_outer.addWidget(self.sidebar_scroll)

        content.addWidget(sidebar)

        canvas_panel = QFrame()
        canvas_panel.setObjectName("Panel")

        canvas_layout = QVBoxLayout(canvas_panel)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(0)

        content.addWidget(canvas_panel, stretch=1)

        self.canvas = TreeCanvas(self.colors)
        canvas_layout.addWidget(self.canvas, stretch=1)

        output_panel = QFrame()
        output_panel.setObjectName("BottomPanel")

        output_layout = QVBoxLayout(output_panel)
        output_layout.setContentsMargins(16, 12, 16, 12)
        output_layout.setSpacing(5)

        self.traversal_label = QLabel("El recorrido aparecera aqui.")
        self.traversal_label.setObjectName("Output")
        self.traversal_label.setWordWrap(True)

        self.rotation_label = QLabel("Sin rotaciones registradas.")
        self.rotation_label.setObjectName("OutputMuted")
        self.rotation_label.setWordWrap(True)

        output_layout.addWidget(self.traversal_label)
        output_layout.addWidget(self.rotation_label)

        canvas_layout.addWidget(output_panel)

        self.status_label = QLabel("Listo para construir y visualizar arboles.")
        self.status_label.setObjectName("Status")
        main_layout.addWidget(self.status_label)

        self._build_sidebar(side_layout)
        self._apply_styles()

    def _build_sidebar(self, layout: QVBoxLayout) -> None:
        layout.addWidget(self._section_label("Tipo de arbol"))

        self.tree_type_combo = QComboBox()
        self.tree_type_combo.addItems(self.TREE_TYPES.keys())
        self.tree_type_combo.setCurrentText("AVL")
        self.tree_type_combo.setMinimumHeight(34)
        self.tree_type_combo.currentTextChanged.connect(self.change_tree_type)
        layout.addWidget(self.tree_type_combo)

        input_row = QHBoxLayout()

        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Valor entero")
        self.value_input.setMinimumHeight(34)
        self.value_input.returnPressed.connect(self.insert_value)

        insert_button = QPushButton("Insertar")
        insert_button.setObjectName("PrimaryButton")
        insert_button.setMinimumHeight(34)
        insert_button.clicked.connect(self.insert_value)

        input_row.addWidget(self.value_input, stretch=1)
        input_row.addWidget(insert_button)

        layout.addLayout(input_row)

        actions = QGridLayout()
        actions.setSpacing(8)

        self._button(actions, "Buscar", self.search_value, 0, 0)
        self._button(actions, "Eliminar nodo", self.delete_value, 0, 1)
        self._button(actions, "Preorden", lambda: self.show_traversal("preorder"), 1, 0)
        self._button(actions, "Inorden", lambda: self.show_traversal("inorder"), 1, 1)
        self._button(actions, "Postorden", lambda: self.show_traversal("postorder"), 2, 0)
        self._button(actions, "Tres recorridos", self.show_all_traversals, 2, 1)
        self._button(actions, "Eliminar arbol", self.clear_tree, 3, 0, danger=True)
        self._button(actions, "Guardar", self.save_tree, 3, 1)
        self._button(actions, "Cargar", self.load_tree, 4, 0)

        layout.addLayout(actions)

        example_button = QPushButton("Insertar ejemplo")
        example_button.clicked.connect(self._seed_example)
        layout.addWidget(example_button)

        self._separator(layout)

        layout.addWidget(self._section_label("Informacion general"))

        metrics = QGridLayout()
        metrics.setSpacing(8)

        self.type_metric = self._metric_card("Tipo", "-")
        self.root_metric = self._metric_card("Raiz", "-")
        self.height_metric = self._metric_card("Altura", "0")
        self.count_metric = self._metric_card("Nodos", "0")
        self.balance_metric = self._metric_card("Balance AVL", "-")

        metrics.addWidget(self.type_metric, 0, 0)
        metrics.addWidget(self.root_metric, 0, 1)
        metrics.addWidget(self.height_metric, 1, 0)
        metrics.addWidget(self.count_metric, 1, 1)
        metrics.addWidget(self.balance_metric, 2, 0, 1, 2)

        layout.addLayout(metrics)

        self._separator(layout)

        layout.addWidget(self._section_label("Recorridos actuales"))
        self.preorder_card = self._traversal_card("Preorden")
        self.inorder_card = self._traversal_card("Inorden")
        self.postorder_card = self._traversal_card("Postorden")
        layout.addWidget(self.preorder_card)
        layout.addWidget(self.inorder_card)
        layout.addWidget(self.postorder_card)

        self._separator(layout)

        layout.addWidget(self._section_label("Leyenda visual"))
        layout.addWidget(self._legend_row("Nodo normal", self.colors.node, self.colors.ink))
        layout.addWidget(self._legend_row("Visitado / resultado", self.colors.focus, self.colors.warning))

        layout.addStretch(1)

    def _build_menu(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("Archivo")

        save_action = QAction("Guardar arbol", self)
        save_action.triggered.connect(self.save_tree)
        file_menu.addAction(save_action)

        load_action = QAction("Cargar arbol", self)
        load_action.triggered.connect(self.load_tree)
        file_menu.addAction(load_action)

        file_menu.addSeparator()

        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _button(self, layout: QGridLayout, text: str, slot, row: int, column: int, danger: bool = False) -> None:
        button = QPushButton(text)
        button.setMinimumHeight(34)
        if danger:
            button.setObjectName("DangerButton")

        button.clicked.connect(slot)
        layout.addWidget(button, row, column)

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("Section")
        return label

    def _separator(self, layout: QVBoxLayout) -> None:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("Separator")
        layout.addWidget(line)

    def _metric_card(self, title: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Metric")
        card.setMinimumHeight(58)

        title_label = QLabel(title)
        title_label.setObjectName("MetricTitle")

        value_label = QLabel(value)
        value_label.setObjectName("MetricValue")

        card.value_label = value_label

        box = QVBoxLayout(card)
        box.setContentsMargins(10, 8, 10, 8)
        box.addWidget(title_label)
        box.addWidget(value_label)

        return card

    def _traversal_card(self, title: str) -> QFrame:
        card = QFrame()
        card.setObjectName("TraversalCard")
        card.setMinimumHeight(54)

        title_label = QLabel(title)
        title_label.setObjectName("TraversalTitle")

        value_label = QLabel("(vacio)")
        value_label.setObjectName("TraversalValue")
        value_label.setWordWrap(True)

        card.value_label = value_label

        box = QVBoxLayout(card)
        box.setContentsMargins(10, 7, 10, 7)
        box.setSpacing(2)
        box.addWidget(title_label)
        box.addWidget(value_label)

        return card

    def _legend_row(self, label: str, fill: str, outline: str) -> QWidget:
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)

        swatch = QLabel()
        swatch.setFixedSize(28, 20)
        swatch.setStyleSheet(
            f"background:{fill}; border:2px solid {outline}; border-radius:10px;"
        )

        text = QLabel(label)
        text.setObjectName("Legend")

        row_layout.addWidget(swatch)
        row_layout.addWidget(text, stretch=1)

        return row

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget#Root {{
                background: {self.colors.bg};
                color: {self.colors.ink};
                font-family: Segoe UI, Arial;
                font-size: 14px;
            }}

            QWidget#SidebarContent,
            QScrollArea#SidebarScroll,
            QScrollArea#SidebarScroll > QWidget,
            QScrollArea#SidebarScroll > QWidget > QWidget {{
                background: transparent;
                border: none;
            }}

            QLabel#Title {{
                font-size: 26px;
                font-weight: 700;
                color: {self.colors.ink};
            }}

            QLabel#Subtitle,
            QLabel#OutputMuted,
            QLabel#Legend {{
                color: {self.colors.muted};
            }}

            QLabel#Section {{
                font-weight: 700;
                color: {self.colors.ink};
            }}

            QFrame#Panel {{
                background: {self.colors.panel};
                border: 1px solid {self.colors.border};
                border-radius: 8px;
            }}

            QFrame#BottomPanel {{
                background: {self.colors.panel};
                border-top: 1px solid {self.colors.border};
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }}

            QFrame#Metric {{
                background: #fbfdff;
                border: 1px solid {self.colors.border};
                border-radius: 8px;
            }}

            QLabel#MetricTitle {{
                color: {self.colors.muted};
                font-size: 12px;
            }}

            QLabel#MetricValue {{
                color: {self.colors.ink};
                font-size: 20px;
                font-weight: 700;
            }}

            QFrame#TraversalCard {{
                background: #fbfdff;
                border: 1px solid {self.colors.border};
                border-radius: 8px;
            }}

            QLabel#TraversalTitle {{
                color: {self.colors.muted};
                font-size: 12px;
                font-weight: 700;
            }}

            QLabel#TraversalValue {{
                color: {self.colors.ink};
                font-size: 12px;
            }}

            QLabel#Status {{
                padding: 8px 12px;
                background: #dde8f7;
                border-radius: 8px;
                color: {self.colors.ink};
            }}

            QLineEdit,
            QComboBox {{
                background: #fbfdff;
                border: 1px solid {self.colors.border};
                border-radius: 8px;
                padding: 9px 10px;
                color: {self.colors.ink};
                min-height: 20px;
            }}

            QLineEdit:focus,
            QComboBox:focus {{
                border: 1px solid {self.colors.primary};
            }}

            QPushButton {{
                background: #f8fafc;
                border: 1px solid {self.colors.border};
                border-radius: 8px;
                padding: 9px 10px;
                font-weight: 600;
                color: {self.colors.ink};
                min-height: 20px;
            }}

            QPushButton:hover {{
                background: #eef4ff;
                border-color: {self.colors.primary};
            }}

            QPushButton#PrimaryButton {{
                background: {self.colors.primary};
                color: white;
                border-color: {self.colors.primary};
            }}

            QPushButton#PrimaryButton:hover {{
                background: {self.colors.primary_dark};
            }}

            QPushButton#DangerButton {{
                background: #fff5f5;
                color: {self.colors.danger};
                border-color: #fecaca;
            }}

            QPushButton#DangerButton:hover {{
                background: #fee2e2;
            }}

            QFrame#Separator {{
                color: {self.colors.border};
                background: {self.colors.border};
                max-height: 1px;
                border: none;
            }}

            QMenuBar {{
                background: {self.colors.panel};
            }}
            """
        )

    def change_tree_type(self, text: str) -> None:
        tree_class = self.TREE_TYPES[text]
        self.tree = tree_class()

        self.highlight_values = set()
        self.traversal_label.setText("Arbol nuevo. Inserta valores para empezar.")
        self.rotation_label.setText("Sin rotaciones registradas.")
        self.status_label.setText(f"Tipo cambiado a {text}. Raiz actual: {self._root_text()}.")

        self.refresh()

    def _seed_example(self) -> None:
        tree_class = self.TREE_TYPES[self.tree_type_combo.currentText()]
        self.tree = tree_class()

        for value in [50, 30, 70, 20, 40, 60, 80]:
            self.tree.insert(value)

        self.highlight_values = set()
        self.traversal_label.setText("Ejemplo cargado: 50 -> 30 -> 70 -> 20 -> 40 -> 60 -> 80")
        self.rotation_label.setText("Usa los botones para animar recorridos, busquedas e inserciones.")
        self.status_label.setText(f"Arbol de ejemplo insertado. Raiz actual: {self._root_text()}.")

        self.refresh()

    def _read_int(self) -> int | None:
        raw = self.value_input.text().strip()

        if not raw:
            QMessageBox.warning(self, "Valor requerido", "Ingresa un numero entero.")
            return None

        try:
            return int(raw)
        except ValueError:
            QMessageBox.critical(self, "Valor invalido", "Solo se aceptan numeros enteros.")
            return None

    def insert_value(self) -> None:
        value = self._read_int()
        if value is None:
            return

        if isinstance(self.tree, AVL):
            _node, path, rotations = self.tree.insert(value)
            if rotations:
                self.rotation_label.setText(
                    "Rotaciones: "
                    + ", ".join(rotations)
                    + f" | Raiz actual: {self._root_text()}"
                )
            else:
                self.rotation_label.setText(f"No se requirieron rotaciones. Raiz actual: {self._root_text()}.")
        else:
            _node, path = self.tree.insert(value)
            self.rotation_label.setText(f"Insercion realizada sin rotaciones. Raiz actual: {self._root_text()}.")

        visited = path + [value]

        self.value_input.clear()
        self.traversal_label.setText(f"Insercion de {value}. Camino: {self._format_path(visited)}")
        self.status_label.setText(f"Valor {value} insertado. Raiz actual: {self._root_text()}.")

        self.animate_values(visited, final={value})

    def search_value(self) -> None:
        value = self._read_int()
        if value is None:
            return

        node, path = self.tree.search(value)

        self.traversal_label.setText(f"Busqueda de {value}. Camino: {self._format_path(path)}")
        self.rotation_label.setText("Busqueda recursiva resaltada en el lienzo.")
        self.status_label.setText(
            ("Valor encontrado." if node else "Valor no encontrado.")
            + f" Raiz actual: {self._root_text()}."
        )

        self.animate_values(path, final={value} if node else set())

    def delete_value(self) -> None:
        value = self._read_int()
        if value is None:
            return

        if isinstance(self.tree, AVL):
            ok, description, rotations = self.tree.delete(value)
            if rotations:
                self.rotation_label.setText(
                    "Rotaciones: "
                    + ", ".join(rotations)
                    + f" | Raiz actual: {self._root_text()}"
                )
            else:
                self.rotation_label.setText(f"Sin rotaciones de rebalanceo. Raiz actual: {self._root_text()}.")
        else:
            ok, description = self.tree.delete(value)
            self.rotation_label.setText(f"Eliminacion realizada. Raiz actual: {self._root_text()}.")

        self.value_input.clear()
        self.highlight_values = set()

        self.traversal_label.setText(description)
        self.status_label.setText(
            f"Valor {value} eliminado. Raiz actual: {self._root_text()}."
            if ok
            else description
        )

        self.refresh()

    def show_traversal(self, kind: str) -> None:
        names = {
            "preorder": "Preorden",
            "inorder": "Inorden",
            "postorder": "Postorden",
        }

        values = getattr(self.tree, kind)()

        self.traversal_label.setText(f"{names[kind]}: {self._format_path(values)}")
        self.rotation_label.setText("Recorrido recursivo animado paso a paso.")
        self.status_label.setText(f"Mostrando recorrido {names[kind].lower()}. Raiz actual: {self._root_text()}.")

        self.animate_values(values)

    def show_all_traversals(self) -> None:
        preorder = self.tree.preorder()
        inorder = self.tree.inorder()
        postorder = self.tree.postorder()

        self.traversal_label.setText(
            "Preorden: "
            + self._format_path(preorder)
            + " | Inorden: "
            + self._format_path(inorder)
            + " | Postorden: "
            + self._format_path(postorder)
        )
        self.rotation_label.setText("Los tres recorridos estan visibles en el panel lateral.")
        self.status_label.setText(f"Recorridos actualizados. Raiz actual: {self._root_text()}.")
        self.animate_values(preorder)

    def clear_tree(self) -> None:
        answer = QMessageBox.question(
            self,
            "Eliminar arbol",
            "Deseas borrar todos los nodos para construir otro arbol?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if answer == QMessageBox.StandardButton.Yes:
            self.tree.clear()
            self.highlight_values = set()

            self.traversal_label.setText("Arbol vacio.")
            self.rotation_label.setText("Sin rotaciones registradas.")
            self.status_label.setText("Arbol eliminado. Puedes construir uno nuevo.")

            self.refresh()

    def save_tree(self) -> None:
        filename, ok = QInputDialog.getText(self, "Guardar arbol", "Nombre del archivo:")

        if not ok or not filename.strip():
            return

        try:
            path = self.storage.save(self.tree, filename.strip())
            self.status_label.setText(f"Arbol guardado en {path}")
            QMessageBox.information(self, "Guardado", f"Arbol guardado correctamente:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Error al guardar", str(exc))

    def load_tree(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Cargar arbol",
            self.storage.save_dir,
            "Archivos JSON (*.json);;Todos los archivos (*.*)",
        )

        if not file_path:
            return

        try:
            loader = TreeStorage(save_dir=os.path.dirname(file_path))
            self.tree = loader.load(os.path.basename(file_path))

            self.tree_type_combo.blockSignals(True)
            self.tree_type_combo.setCurrentText(self._display_type(self.tree))
            self.tree_type_combo.blockSignals(False)

            self.highlight_values = set()

            self.traversal_label.setText(f"Cargado: {os.path.basename(file_path)}")
            self.rotation_label.setText("Estructura reconstruida desde JSON.")
            self.status_label.setText(f"Arbol cargado correctamente. Raiz actual: {self._root_text()}.")

            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Error al cargar", str(exc))

    def animate_values(self, values: list[int], final: set[int] | None = None) -> None:
        self.animation_timer.stop()

        self.animation_values = list(values)
        self.animation_final = set(final or values)
        self.animation_index = 0

        if not self.animation_values:
            self.highlight_values = set()
            self.refresh()
            return

        self.animation_timer.start(300)

    def _animation_step(self) -> None:
        if self.animation_index >= len(self.animation_values):
            self.animation_timer.stop()
            self.highlight_values = set(self.animation_final)
            self.refresh()
            return

        self.highlight_values = set(self.animation_values[: self.animation_index + 1])
        self.animation_index += 1

        self.refresh()

    def refresh(self) -> None:
        self._update_metrics()
        self._update_traversal_panel()
        self.canvas.set_tree(self.tree, self.highlight_values)

    def _update_metrics(self) -> None:
        info = self.tree.get_info()

        self.type_metric.value_label.setText(str(info.get("type", "-")))
        self.root_metric.value_label.setText(self._root_text())
        self.height_metric.value_label.setText(str(info.get("height", 0)))
        self.count_metric.value_label.setText(str(info.get("node_count", 0)))

        balanced = info.get("is_balanced")
        if balanced is True:
            text = "Si"
        elif balanced is False:
            text = "No"
        else:
            text = "No aplica"

        self.balance_metric.value_label.setText(text)

    def _update_traversal_panel(self) -> None:
        self.preorder_card.value_label.setText(self._format_path(self.tree.preorder()))
        self.inorder_card.value_label.setText(self._format_path(self.tree.inorder()))
        self.postorder_card.value_label.setText(self._format_path(self.tree.postorder()))

    def _display_type(self, tree) -> str:
        if isinstance(tree, AVL):
            return "AVL"
        if isinstance(tree, BST):
            return "BST"
        return "Arbol Binario"

    def _format_path(self, values: list[int]) -> str:
        if not values:
            return "(sin nodos visitados)"
        return " -> ".join(str(value) for value in values)

    def _root_text(self) -> str:
        root = self.tree.root_value
        return "-" if root is None else str(root)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Visualizador de Arboles")
    app.setStyle("Fusion")

    window = TreeVisualizerWindow()
    window.show()
    window.raise_()
    window.activateWindow()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
