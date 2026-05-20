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

    # ================================================================== #
    #  Recorrido por niveles (BFS / Level-Order)                          #
    # ================================================================== #

    def nodes_by_level(self) -> list[list]:
        """
        Recorrido por niveles (BFS / Level-Order).
        Es el 4to recorrido clásico además de pre/in/postorden.

        Retorna una lista de listas, donde cada sublista contiene
        los valores de los nodos en ese nivel:
            [[raíz], [hijos], [nietos], ...]

        Ejemplo para árbol con raíz 1, hijos 2 y 3:
            [[1], [2, 3], [4, 5, 6, 7]]
        """
        if self.root is None:
            return []

        result: list[list] = []
        queue = deque([self.root])

        while queue:
            level_size  = len(queue)
            level_vals: list = []

            for _ in range(level_size):
                node = queue.popleft()
                level_vals.append(node.value)
                if node.left:
                    queue.append(node.left)
                if node.right:
                    queue.append(node.right)

            result.append(level_vals)

        return result

    def level_order(self) -> list:
        """
        Versión plana del recorrido por niveles.
        Retorna todos los valores en orden BFS en una sola lista.
        Útil para mostrar como secuencia (igual que pre/in/postorden).
        """
        return [val for level in self.nodes_by_level() for val in level]

    # ================================================================== #
    #  Nivel / profundidad de un nodo                                     #
    # ================================================================== #

    def get_level(self, value) -> int:
        """
        Retorna el nivel (profundidad) del nodo con el valor dado.
        La raíz está en nivel 0.
        Retorna -1 si el valor no existe en el árbol.
        """
        return self._get_level_recursive(self.root, value, 0)

    def _get_level_recursive(self, node: Node | None, value, current_level: int) -> int:
        """Búsqueda recursiva del nivel de un nodo."""
        if node is None:
            return -1
        if node.value == value:
            return current_level

        # Buscar en subárbol izquierdo
        left_result = self._get_level_recursive(node.left, value, current_level + 1)
        if left_result != -1:
            return left_result

        # Buscar en subárbol derecho
        return self._get_level_recursive(node.right, value, current_level + 1)

    # ================================================================== #
    #  Ancestros de un nodo                                               #
    # ================================================================== #

    def get_ancestors(self, value) -> list:
        """
        Retorna la lista de valores ancestros del nodo con el valor dado,
        desde la raíz hasta el padre directo del nodo (excluyendo el nodo mismo).
        Implementado recursivamente.

        Retorna lista vacía si el valor no existe o si es la raíz.

        Ejemplo: para el nodo 20 en un árbol con raíz 50, hijo 30, nieto 20:
            get_ancestors(20) → [50, 30]
        """
        ancestors: list = []
        self._find_ancestors_recursive(self.root, value, ancestors)
        return ancestors

    def _find_ancestors_recursive(
        self,
        node:      Node | None,
        value,
        ancestors: list,
    ) -> bool:
        """
        Recorre el árbol recursivamente acumulando ancestros.
        Retorna True si encontró el valor (para que los llamadores
        sepan si deben conservar el nodo en la lista de ancestros).
        """
        if node is None:
            return False
        if node.value == value:
            return True

        # Intentar encontrar en subárbol izquierdo o derecho
        if (self._find_ancestors_recursive(node.left,  value, ancestors) or
                self._find_ancestors_recursive(node.right, value, ancestors)):
            ancestors.insert(0, node.value)   # insertar al frente → orden raíz→padre
            return True

        return False

    # ================================================================== #
    #  Ancestro Común más Cercano — LCA                                   #
    # ================================================================== #

    def lca(self, val1, val2):
        """
        Lowest Common Ancestor (Ancestro Común más Cercano).
        Encuentra el nodo más profundo que es ancestro de ambos valores.

        Algoritmo recursivo:
          - Si el nodo actual es alguno de los dos valores → es el LCA.
          - Si val1 está en el subárbol izquierdo y val2 en el derecho
            (o viceversa) → el nodo actual es el LCA.
          - Si ambos están en el mismo subárbol → bajar recursivamente.

        Retorna el valor del LCA, o None si alguno de los valores
        no existe en el árbol.

        Ejemplo: lca(20, 40) en árbol con raíz 50 → retorna 30
        """
        # Verificar que ambos valores existen
        node1, _ = self.search(val1)
        node2, _ = self.search(val2)
        if node1 is None or node2 is None:
            return None

        result = self._lca_recursive(self.root, val1, val2)
        return result.value if result else None

    def _lca_recursive(self, node: Node | None, val1, val2) -> Node | None:
        """
        Núcleo recursivo del algoritmo LCA.
        Retorna el nodo LCA o None.
        """
        if node is None:
            return None

        # Si el nodo actual es uno de los valores buscados, él mismo es el LCA
        if node.value == val1 or node.value == val2:
            return node

        # Buscar en ambos subárboles
        left_lca  = self._lca_recursive(node.left,  val1, val2)
        right_lca = self._lca_recursive(node.right, val1, val2)

        # Si encontramos uno en cada subárbol → este nodo es el LCA
        if left_lca and right_lca:
            return node

        # Si solo está en un lado, retornar ese lado
        return left_lca if left_lca else right_lca

    # ================================================================== #
    #  Propiedades estructurales del árbol                                #
    # ================================================================== #

    def is_full(self) -> bool:
        """
        Árbol lleno: todo nodo tiene exactamente 0 o 2 hijos (nunca 1).
        También llamado 'strictly binary tree'.
        """
        return self._is_full_recursive(self.root)

    def _is_full_recursive(self, node: Node | None) -> bool:
        if node is None:
            return True
        if node.is_leaf():
            return True
        if node.has_one_child():
            return False   # viola la propiedad
        return (self._is_full_recursive(node.left) and
                self._is_full_recursive(node.right))

    def is_perfect(self) -> bool:
        """
        Árbol perfecto: todos los niveles están completamente llenos.
        Un árbol perfecto de altura h tiene exactamente 2^h - 1 nodos.
        """
        h = self.height
        expected_nodes = (2 ** h) - 1
        return self._node_count == expected_nodes

    def is_complete(self) -> bool:
        """
        Árbol completo: todos los niveles están llenos excepto
        posiblemente el último, que se llena de izquierda a derecha.
        Verificación mediante BFS: no puede haber un nodo después
        de un hueco en el recorrido por niveles.
        """
        if self.root is None:
            return True

        queue     = deque([self.root])
        found_gap = False   # ¿encontramos un hijo None?

        while queue:
            node = queue.popleft()

            for child in (node.left, node.right):
                if child is None:
                    found_gap = True
                else:
                    if found_gap:
                        return False   # nodo después de un hueco → no es completo
                    queue.append(child)

        return True

    # ================================================================== #
    #  Conteo de hojas y nodos internos                                   #
    # ================================================================== #

    def count_leaves(self) -> int:
        """
        Cuenta los nodos hoja (sin hijos) de forma recursiva.
        Propiedad interesante: en un árbol lleno, leaves = internal_nodes + 1.
        """
        return self._count_leaves_recursive(self.root)

    def _count_leaves_recursive(self, node: Node | None) -> int:
        if node is None:
            return 0
        if node.is_leaf():
            return 1
        return (self._count_leaves_recursive(node.left) +
                self._count_leaves_recursive(node.right))

    def count_internal(self) -> int:
        """
        Cuenta los nodos internos (con al menos un hijo).
        count_internal() + count_leaves() == node_count.
        """
        return self._node_count - self.count_leaves()

    # ================================================================== #
    #  Ancho máximo del árbol                                             #
    # ================================================================== #

    def get_width(self) -> int:
        """
        Retorna el ancho máximo del árbol: el mayor número de nodos
        que hay en un mismo nivel.
        Un árbol con un solo nodo tiene ancho 1.
        Útil para la GUI: saber cuánto espacio horizontal necesita el canvas.
        """
        levels = self.nodes_by_level()
        if not levels:
            return 0
        return max(len(level) for level in levels)

    def get_width_per_level(self) -> list[int]:
        """
        Retorna una lista con el ancho de cada nivel.
        Índice 0 = raíz (siempre 1), índice 1 = hijos, etc.
        """
        return [len(level) for level in self.nodes_by_level()]

    # ================================================================== #
    #  get_info extendido                                                 #
    # ================================================================== #

    def get_full_info(self) -> dict:
        """
        Versión extendida de get_info() con todas las métricas.
        Ideal para mostrar en un panel de información detallado en la GUI.
        """
        return {
            **self.get_info(),
            "leaves":      self.count_leaves(),
            "internal":    self.count_internal(),
            "width":       self.get_width(),
            "is_full":     self.is_full(),
            "is_complete": self.is_complete(),
            "is_perfect":  self.is_perfect(),
        }