"""
bst.py
------
Árbol Binario de Búsqueda (BST).
Hereda de BinaryTree y sobreescribe inserción, búsqueda y eliminación
con lógica ordenada recursiva.

Invariante BST:
    Para todo nodo N:
        - todos los valores en su subárbol izquierdo < N.value
        - todos los valores en su subárbol derecho   > N.value
"""

from .node import Node
from .binary_tree import BinaryTree


class BST(BinaryTree):
    """
    Árbol Binario de Búsqueda.
    Inserción, búsqueda y eliminación son O(h) donde h = altura.
    """

    TREE_TYPE = "BST"

    # ================================================================== #
    #  Inserción recursiva                                                 #
    # ================================================================== #

    def insert(self, value) -> tuple[Node, list]:
        """
        Inserta un valor respetando la propiedad BST.

        Retorna:
            (nuevo_nodo, camino_recorrido)
        """
        path: list = []
        inserted_node_wrapper: list[Node | None] = [None]  # workaround closure

        self.root = self._insert_recursive(
            self.root, value, path, inserted_node_wrapper
        )
        self._node_count += 1
        return inserted_node_wrapper[0], path

    def _insert_recursive(
        self,
        node:    Node | None,
        value,
        path:    list,
        wrapper: list,
    ) -> Node:
        """
        Recorre el árbol comparando valores y ubica el nuevo nodo
        en la posición correcta.
        """
        # Caso base: posición encontrada
        if node is None:
            new_node    = Node(value)
            wrapper[0]  = new_node
            return new_node

        path.append(node.value)  # registrar nodo visitado

        if value < node.value:
            node.left  = self._insert_recursive(node.left,  value, path, wrapper)
        elif value > node.value:
            node.right = self._insert_recursive(node.right, value, path, wrapper)
        else:
            # Duplicado: no insertar; deshacer el +1 del metodo publico
            self._node_count -= 1
            wrapper[0] = node

        return node

    # ================================================================== #
    #  Búsqueda recursiva ordenada                                         #
    # ================================================================== #

    def search(self, value) -> tuple[Node | None, list]:
        """
        Busca un valor aprovechando el orden BST (descarta ramas enteras).

        Retorna:
            (nodo_encontrado_o_None, camino_de_nodos_visitados)
        """
        path: list = []
        result = self._search_bst(self.root, value, path)
        return result, path

    def _search_bst(self, node: Node | None, value, path: list) -> Node | None:
        """Búsqueda recursiva BST: O(h)."""
        if node is None:
            return None

        path.append(node.value)

        if value == node.value:
            return node
        elif value < node.value:
            return self._search_bst(node.left,  value, path)
        else:
            return self._search_bst(node.right, value, path)

    # ================================================================== #
    #  Eliminación recursiva (3 casos)                                    #
    # ================================================================== #

    def delete(self, value) -> tuple[bool, str]:
        """
        Elimina el nodo con el valor indicado respetando la propiedad BST.

        Casos manejados:
            1. Nodo hoja        → se elimina directamente.
            2. Un solo hijo     → el hijo sube a ocupar su lugar.
            3. Dos hijos        → se reemplaza con el sucesor inorden
                                  (mínimo del subárbol derecho).

        Retorna:
            (éxito: bool, descripción_del_caso: str)
        """
        if self.root is None:
            return False, "El árbol está vacío."

        # Verificar existencia antes de eliminar
        found, _ = self.search(value)
        if found is None:
            return False, f"El valor {value!r} no existe en el árbol."

        case_description: list[str] = [""]  # closure mutable
        self.root = self._delete_recursive(self.root, value, case_description)
        self._node_count -= 1
        return True, case_description[0]

    def _delete_recursive(
        self,
        node:  Node | None,
        value,
        case:  list[str],
    ) -> Node | None:
        """Elimina recursivamente manteniendo la invariante BST."""
        if node is None:
            return None

        if value < node.value:
            node.left  = self._delete_recursive(node.left,  value, case)

        elif value > node.value:
            node.right = self._delete_recursive(node.right, value, case)

        else:
            # ─── Nodo encontrado ───────────────────────────────────── #

            # Caso 1: Nodo hoja
            if node.is_leaf():
                case[0] = "Nodo hoja eliminado directamente."
                return None

            # Caso 2: Un solo hijo
            elif node.has_one_child():
                case[0] = "Nodo con un hijo: el hijo ocupa su lugar."
                return node.right if node.left is None else node.left

            # Caso 3: Dos hijos → reemplazar con sucesor inorden
            else:
                case[0] = (
                    "Nodo con dos hijos: reemplazado por el sucesor "
                    "inorden (mínimo del subárbol derecho)."
                )
                successor        = self._min_node(node.right)
                node.value       = successor.value
                node.right       = self._delete_recursive(
                    node.right, successor.value, [""]
                )

        return node

    def _min_node(self, node: Node) -> Node:
        """Retorna el nodo con el valor mínimo en el subárbol dado."""
        current = node
        while current.left is not None:
            current = current.left
        return current

    def _max_node(self, node: Node) -> Node:
        """Retorna el nodo con el valor máximo en el subárbol dado."""
        current = node
        while current.right is not None:
            current = current.right
        return current

    # ================================================================== #
    #  Utilidades BST                                                      #
    # ================================================================== #

    def get_sorted_values(self) -> list:
        """Retorna todos los valores en orden ascendente (inorden)."""
        return self.inorder()

    def is_valid_bst(self) -> bool:
        """Verifica que el árbol cumple la propiedad BST (para pruebas)."""
        return self._validate(self.root, None, None)

    def _validate(
        self,
        node: Node | None,
        min_val,
        max_val,
    ) -> bool:
        if node is None:
            return True
        if min_val is not None and node.value <= min_val:
            return False
        if max_val is not None and node.value >= max_val:
            return False
        return (
            self._validate(node.left,  min_val,    node.value) and
            self._validate(node.right, node.value, max_val)
        )