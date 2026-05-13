"""
binary_tree.py
--------------
Implementación del Árbol Binario general (no ordenado).
Los nodos se insertan completando nivel por nivel (inserción BFS).
Contiene:
  - Inserción (BFS, no recursiva por naturaleza del árbol general).
  - Eliminación de nodos (hoja, un hijo, dos hijos).
  - Búsqueda recursiva.
  - Recorridos recursivos: preorden, inorden, postorden.
  - Cálculo de altura y conteo de nodos.
  - Serialización / deserialización JSON.
"""

from collections import deque
from .node import Node


class BinaryTree:
    """
    Árbol Binario general.
    La inserción llena el árbol nivel por nivel (izquierda → derecha).
    """

    TREE_TYPE = "BinaryTree"

    def __init__(self):
        self.root: Node | None = None
        self._node_count: int = 0

    # ================================================================== #
    #  Propiedades                                                         #
    # ================================================================== #

    @property
    def node_count(self) -> int:
        return self._node_count

    @property
    def height(self) -> int:
        return self._height(self.root)

    @property
    def root_value(self):
        return self.root.value if self.root else None

    # ================================================================== #
    #  Inserción                                                           #
    # ================================================================== #

    def insert(self, value) -> tuple[Node, list]:
        """
        Inserta un valor completando el árbol nivel por nivel.

        Retorna:
            (nuevo_nodo, camino_recorrido)
            El camino es la lista de valores visitados hasta insertar.
        """
        new_node = Node(value)
        path: list = []

        if self.root is None:
            self.root = new_node
            self._node_count += 1
            return new_node, path

        # BFS para encontrar el primer hueco disponible
        queue = deque([self.root])
        while queue:
            current = queue.popleft()
            path.append(current.value)

            if current.left is None:
                current.left = new_node
                self._node_count += 1
                return new_node, path
            else:
                queue.append(current.left)

            if current.right is None:
                current.right = new_node
                self._node_count += 1
                return new_node, path
            else:
                queue.append(current.right)

        return new_node, path  # nunca debería llegar aquí

    # ================================================================== #
    #  Búsqueda recursiva                                                  #
    # ================================================================== #

    def search(self, value) -> tuple[Node | None, list]:
        """
        Busca un valor en el árbol de forma recursiva.

        Retorna:
            (nodo_encontrado_o_None, camino_de_nodos_visitados)
        """
        path: list = []
        result = self._search_recursive(self.root, value, path)
        return result, path

    def _search_recursive(self, node: Node | None, value, path: list) -> Node | None:
        """Búsqueda recursiva genérica (recorrido preorden)."""
        if node is None:
            return None

        path.append(node.value)

        if node.value == value:
            return node

        # Buscar en subárbol izquierdo
        found = self._search_recursive(node.left, value, path)
        if found:
            return found

        # Buscar en subárbol derecho
        return self._search_recursive(node.right, value, path)

    # ================================================================== #
    #  Eliminación                                                         #
    # ================================================================== #

    def delete(self, value) -> tuple[bool, str]:
        """
        Elimina el nodo con el valor indicado.
        En el árbol binario general se reemplaza por el nodo más
        profundo/derecho (estrategia estándar para no romper la forma).

        Retorna:
            (éxito: bool, descripción_del_caso: str)
        """
        if self.root is None:
            return False, "El árbol está vacío."

        # Encontrar el nodo a eliminar y el último nodo (más profundo)
        target_node = None
        last_node   = None
        last_parent = None
        is_right_child = False

        queue = deque([(self.root, None, False)])
        while queue:
            node, parent, is_right = queue.popleft()

            if node.value == value:
                target_node = node

            last_node   = node
            last_parent = parent
            is_right_child = is_right

            if node.left:
                queue.append((node.left, node, False))
            if node.right:
                queue.append((node.right, node, True))

        if target_node is None:
            return False, f"El valor {value!r} no existe en el árbol."

        # Determinar el caso de eliminación para el informe
        if target_node.is_leaf():
            case_description = "Nodo hoja eliminado directamente."
        elif target_node.has_one_child():
            case_description = "Nodo con un hijo: el hijo ocupa su lugar."
        else:
            case_description = "Nodo con dos hijos: reemplazado por el nodo más profundo."

        # Reemplazar el valor del target con el del último nodo
        target_node.value = last_node.value

        # Eliminar el último nodo del árbol
        if last_parent is None:
            # El árbol solo tenía un nodo (la raíz)
            self.root = None
        elif is_right_child:
            last_parent.right = None
        else:
            last_parent.left = None

        self._node_count -= 1
        return True, case_description

    # ================================================================== #
    #  Recorridos recursivos                                               #
    # ================================================================== #

    def preorder(self) -> list:
        """
        Recorrido preorden: raíz → izquierda → derecha.
        Retorna lista de valores en el orden visitado.
        """
        result: list = []
        self._preorder_recursive(self.root, result)
        return result

    def _preorder_recursive(self, node: Node | None, result: list) -> None:
        if node is None:
            return
        result.append(node.value)                    # visitar raíz
        self._preorder_recursive(node.left,  result) # subárbol izquierdo
        self._preorder_recursive(node.right, result) # subárbol derecho

    def inorder(self) -> list:
        """
        Recorrido inorden: izquierda → raíz → derecha.
        En un BST este recorrido produce los valores en orden ascendente.
        """
        result: list = []
        self._inorder_recursive(self.root, result)
        return result

    def _inorder_recursive(self, node: Node | None, result: list) -> None:
        if node is None:
            return
        self._inorder_recursive(node.left,  result) # subárbol izquierdo
        result.append(node.value)                    # visitar raíz
        self._inorder_recursive(node.right, result) # subárbol derecho

    def postorder(self) -> list:
        """
        Recorrido postorden: izquierda → derecha → raíz.
        """
        result: list = []
        self._postorder_recursive(self.root, result)
        return result

    def _postorder_recursive(self, node: Node | None, result: list) -> None:
        if node is None:
            return
        self._postorder_recursive(node.left,  result) # subárbol izquierdo
        self._postorder_recursive(node.right, result) # subárbol derecho
        result.append(node.value)                     # visitar raíz

    # ================================================================== #
    #  Altura y conteo                                                     #
    # ================================================================== #

    def _height(self, node: Node | None) -> int:
        """Calcula la altura de un subárbol de forma recursiva."""
        if node is None:
            return 0
        return 1 + max(self._height(node.left), self._height(node.right))

    def count_nodes(self) -> int:
        """Cuenta todos los nodos de forma recursiva (verificación)."""
        return self._count_recursive(self.root)

    def _count_recursive(self, node: Node | None) -> int:
        if node is None:
            return 0
        return 1 + self._count_recursive(node.left) + self._count_recursive(node.right)

    # ================================================================== #
    #  Info general (para la GUI)                                          #
    # ================================================================== #

    def get_info(self) -> dict:
        """
        Devuelve un diccionario con información general del árbol.
        Útil para que la GUI muestre los metadatos en pantalla.
        """
        return {
            "type":        self.TREE_TYPE,
            "root":        self.root_value,
            "height":      self.height,
            "node_count":  self.node_count,
        }

    # ================================================================== #
    #  Serialización                                                       #
    # ================================================================== #

    def to_dict(self) -> dict:
        return {
            "tree_type":  self.TREE_TYPE,
            "node_count": self._node_count,
            "root":       self.root.to_dict() if self.root else None,
        }

    def from_dict(self, data: dict) -> None:
        """Reconstruye el árbol desde un diccionario (cargado desde JSON)."""
        self.root         = Node.from_dict(data.get("root"))
        self._node_count  = data.get("node_count", self.count_nodes())

    def clear(self) -> None:
        """Vacía el árbol completamente."""
        self.root        = None
        self._node_count = 0

    # ================================================================== #
    #  Representación                                                      #
    # ================================================================== #

    def __repr__(self) -> str:
        return f"{self.TREE_TYPE}(nodes={self.node_count}, height={self.height})"

    def __str__(self) -> str:
        """Representación en texto del árbol (útil para depuración)."""
        lines: list[str] = []
        self._print_tree(self.root, "", False, lines)
        return "\n".join(lines) if lines else "(árbol vacío)"

    def _print_tree(self, node: Node | None, prefix: str, is_left: bool, lines: list) -> None:
        if node is None:
            return
        connector = "├── " if is_left else "└── "
        lines.append(f"{prefix}{connector}{node.value}")
        extension = "│   " if is_left else "    "
        self._print_tree(node.left,  prefix + extension, True,  lines)
        self._print_tree(node.right, prefix + extension, False, lines)