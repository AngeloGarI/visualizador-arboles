"""
avl.py
------
Árbol AVL (Adelson-Velsky and Landis).
Hereda de BST y añade rebalanceo automático tras cada inserción y eliminación.

Propiedad AVL:
    Para todo nodo N:  |altura(izq) - altura(der)| <= 1
    Si se viola, se aplica la rotación correspondiente.

Rotaciones implementadas:
    - Rotación simple derecha   (caso izquierda-izquierda)
    - Rotación simple izquierda (caso derecha-derecha)
    - Rotación doble izq-der    (caso izquierda-derecha)
    - Rotación doble der-izq    (caso derecha-izquierda)
"""

from .node import Node
from .bst  import BST


class AVL(BST):
    """
    Árbol AVL con balance automático.
    Todas las operaciones mantienen la propiedad de balance en O(log n).
    """

    TREE_TYPE = "AVL"

    # ================================================================== #
    #  Altura y factor de balance                                          #
    # ================================================================== #

    def _get_height(self, node: Node | None) -> int:
        """Retorna la altura almacenada en el nodo (0 si es None)."""
        return node.height if node else 0

    def _get_balance(self, node: Node | None) -> int:
        """
        Calcula el factor de balance:
            balance = altura(subárbol_izquierdo) - altura(subárbol_derecho)
        Valores fuera de [-1, 1] indican desbalance.
        """
        if node is None:
            return 0
        return self._get_height(node.left) - self._get_height(node.right)

    def _update_height_and_balance(self, node: Node) -> None:
        """Actualiza la altura y el factor de balance de un nodo."""
        node.height  = 1 + max(self._get_height(node.left),
                               self._get_height(node.right))
        node.balance = self._get_balance(node)

    # ================================================================== #
    #  Rotaciones                                                          #
    # ================================================================== #

    def _rotate_right(self, z: Node) -> Node:
        """
        Rotación simple derecha (caso izquierda-izquierda).

            z                y
           / \\             /  \\
          y   T4    →     x    z
         / \\                  / \\
        x   T3               T3  T4
        """
        y  = z.left
        T3 = y.right

        # Realizar la rotación
        y.right = z
        z.left  = T3

        # Actualizar alturas (primero z porque ahora es hijo de y)
        self._update_height_and_balance(z)
        self._update_height_and_balance(y)

        return y  # nueva raíz del subárbol

    def _rotate_left(self, z: Node) -> Node:
        """
        Rotación simple izquierda (caso derecha-derecha).

          z                  y
         / \\               /  \\
        T1   y    →        z    x
            / \\          / \\
           T2   x        T1  T2
        """
        y  = z.right
        T2 = y.left

        # Realizar la rotación
        y.left  = z
        z.right = T2

        # Actualizar alturas
        self._update_height_and_balance(z)
        self._update_height_and_balance(y)

        return y  # nueva raíz del subárbol

    def _rotate_left_right(self, z: Node) -> Node:
        """
        Rotación doble izquierda-derecha (caso izquierda-derecha).
        Paso 1: rotación izquierda sobre el hijo izquierdo.
        Paso 2: rotación derecha sobre z.
        """
        z.left = self._rotate_left(z.left)
        return self._rotate_right(z)

    def _rotate_right_left(self, z: Node) -> Node:
        """
        Rotación doble derecha-izquierda (caso derecha-izquierda).
        Paso 1: rotación derecha sobre el hijo derecho.
        Paso 2: rotación izquierda sobre z.
        """
        z.right = self._rotate_right(z.right)
        return self._rotate_left(z)

    # ================================================================== #
    #  Rebalanceo                                                          #
    # ================================================================== #

    def _rebalance(self, node: Node, value=None) -> tuple[Node, str]:
        """
        Evalúa el factor de balance y aplica la rotación necesaria.

        Retorna:
            (nodo_posiblemente_rotado, descripción_de_la_rotación)
        """
        balance = self._get_balance(node)
        rotation_done = ""

        # ── Caso Izquierda-Izquierda (balance > 1, valor va a izquierda) ──
        if balance > 1 and (value is None or value < node.left.value):
            rotation_done = f"Rotación simple derecha en nodo {node.value}"
            return self._rotate_right(node), rotation_done

        # ── Caso Derecha-Derecha (balance < -1, valor va a derecha) ──────
        if balance < -1 and (value is None or value > node.right.value):
            rotation_done = f"Rotación simple izquierda en nodo {node.value}"
            return self._rotate_left(node), rotation_done

        # ── Caso Izquierda-Derecha (balance > 1, valor va a derecha) ─────
        if balance > 1 and (value is None or value > node.left.value):
            rotation_done = f"Rotación doble izquierda-derecha en nodo {node.value}"
            return self._rotate_left_right(node), rotation_done

        # ── Caso Derecha-Izquierda (balance < -1, valor va a izquierda) ──
        if balance < -1 and (value is None or value < node.right.value):
            rotation_done = f"Rotación doble derecha-izquierda en nodo {node.value}"
            return self._rotate_right_left(node), rotation_done

        return node, rotation_done

    # ================================================================== #
    #  Inserción AVL                                                       #
    # ================================================================== #

    def insert(self, value) -> tuple[Node, list, list]:
        """
        Inserta un valor y rebalancea el árbol si es necesario.

        Retorna:
            (nuevo_nodo, camino_recorrido, lista_de_rotaciones_aplicadas)
        """
        path:      list = []
        rotations: list = []
        wrapper:   list[Node | None] = [None]

        self.root = self._insert_avl(self.root, value, path, wrapper, rotations)
        self._node_count += 1
        return wrapper[0], path, rotations

    def _insert_avl(
        self,
        node:      Node | None,
        value,
        path:      list,
        wrapper:   list,
        rotations: list,
    ) -> Node:
        # ── Paso 1: Inserción BST estándar ─────────────────────────────
        if node is None:
            new_node   = Node(value)
            wrapper[0] = new_node
            return new_node

        path.append(node.value)

        if value < node.value:
            node.left  = self._insert_avl(node.left,  value, path, wrapper, rotations)
        elif value > node.value:
            node.right = self._insert_avl(node.right, value, path, wrapper, rotations)
        else:
            # Duplicado: no insertar
            self._node_count -= 1  # compensar el +1 del método público
            return node

        # ── Paso 2: Actualizar altura y balance ────────────────────────
        self._update_height_and_balance(node)

        # ── Paso 3: Rebalancear si es necesario ────────────────────────
        node, rotation_desc = self._rebalance(node, value)
        if rotation_desc:
            rotations.append(rotation_desc)

        return node

    # ================================================================== #
    #  Eliminación AVL                                                     #
    # ================================================================== #

    def delete(self, value) -> tuple[bool, str, list]:
        """
        Elimina el nodo y rebalancea el árbol automáticamente.

        Retorna:
            (éxito: bool, descripción_del_caso: str, rotaciones_aplicadas: list)
        """
        if self.root is None:
            return False, "El árbol está vacío.", []

        found, _ = self.search(value)
        if found is None:
            return False, f"El valor {value!r} no existe en el árbol.", []

        case_description: list[str] = [""]
        rotations:        list      = []

        self.root = self._delete_avl(self.root, value, case_description, rotations)
        self._node_count -= 1
        return True, case_description[0], rotations

    def _delete_avl(
        self,
        node:  Node | None,
        value,
        case:  list[str],
        rotations: list,
    ) -> Node | None:
        # ── Paso 1: Eliminación BST estándar ───────────────────────────
        if node is None:
            return None

        if value < node.value:
            node.left  = self._delete_avl(node.left,  value, case, rotations)
        elif value > node.value:
            node.right = self._delete_avl(node.right, value, case, rotations)
        else:
            # Nodo encontrado
            if node.is_leaf():
                case[0] = "Nodo hoja eliminado directamente."
                return None
            elif node.has_one_child():
                case[0] = "Nodo con un hijo: el hijo ocupa su lugar."
                return node.right if node.left is None else node.left
            else:
                case[0] = (
                    "Nodo con dos hijos: reemplazado por el sucesor inorden "
                    "(mínimo del subárbol derecho)."
                )
                successor  = self._min_node(node.right)
                node.value = successor.value
                node.right = self._delete_avl(
                    node.right, successor.value, [""], rotations
                )

        # ── Paso 2: Actualizar altura y balance ────────────────────────
        self._update_height_and_balance(node)

        # ── Paso 3: Rebalancear ────────────────────────────────────────
        node, rotation_desc = self._rebalance(node)
        if rotation_desc:
            rotations.append(rotation_desc)

        return node

    # ================================================================== #
    #  Info AVL adicional (para la GUI)                                    #
    # ================================================================== #

    def get_info(self) -> dict:
        info = super().get_info()
        info["is_balanced"] = self._is_balanced(self.root)
        return info

    def _is_balanced(self, node: Node | None) -> bool:
        """Verifica que todo el árbol esté balanceado (para pruebas)."""
        if node is None:
            return True
        balance = abs(self._get_balance(node))
        if balance > 1:
            return False
        return self._is_balanced(node.left) and self._is_balanced(node.right)

    def get_balance_factors(self) -> dict:
        """
        Retorna un diccionario {valor_nodo: factor_de_balance}
        para toda la estructura. Útil para visualizar en la GUI.
        """
        factors: dict = {}
        self._collect_balance_factors(self.root, factors)
        return factors

    def _collect_balance_factors(
        self,
        node:    Node | None,
        factors: dict,
    ) -> None:
        if node is None:
            return
        factors[node.value] = node.balance
        self._collect_balance_factors(node.left,  factors)
        self._collect_balance_factors(node.right, factors)