"""
node.py
-------
Define la clase Nodo, bloque base de todos los árboles del proyecto.
Cada nodo almacena un valor, referencias a sus hijos, y metadatos
utilizados por BST y AVL (altura, factor de balance).
"""


class Node:
    """
    Representa un nodo individual dentro de un árbol binario.

    Atributos:
        value     : valor almacenado en el nodo.
        left      : referencia al hijo izquierdo (Node | None).
        right     : referencia al hijo derecho  (Node | None).
        height    : altura del nodo dentro del árbol (usado por AVL).
        balance   : factor de balance  = altura(izq) - altura(der).
    """

    def __init__(self, value):
        self.value: int | float | str = value
        self.left:  "Node | None" = None
        self.right: "Node | None" = None
        self.height: int = 1          # todo nodo nuevo es una hoja → altura 1
        self.balance: int = 0         # diferencia de alturas izq - der

    # ------------------------------------------------------------------ #
    #  Representación                                                       #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return (
            f"Node(value={self.value!r}, "
            f"height={self.height}, "
            f"balance={self.balance})"
        )

    def __str__(self) -> str:
        return str(self.value)

    # ------------------------------------------------------------------ #
    #  Utilidades de comparación (permiten ordenar nodos directamente)     #
    # ------------------------------------------------------------------ #

    def __lt__(self, other: "Node") -> bool:
        return self.value < other.value

    def __le__(self, other: "Node") -> bool:
        return self.value <= other.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Node):
            return self.value == other.value
        return NotImplemented

    def __gt__(self, other: "Node") -> bool:
        return self.value > other.value

    def __ge__(self, other: "Node") -> bool:
        return self.value >= other.value

    # ------------------------------------------------------------------ #
    #  Helpers                                                              #
    # ------------------------------------------------------------------ #

    def is_leaf(self) -> bool:
        """Retorna True si el nodo no tiene hijos."""
        return self.left is None and self.right is None

    def has_one_child(self) -> bool:
        """Retorna True si el nodo tiene exactamente un hijo."""
        return (self.left is None) != (self.right is None)

    def has_two_children(self) -> bool:
        """Retorna True si el nodo tiene ambos hijos."""
        return self.left is not None and self.right is not None

    def to_dict(self) -> dict:
        """
        Serializa el nodo a un diccionario plano (para guardado en JSON).
        Las referencias a hijos se serializan de forma recursiva.
        """
        return {
            "value":   self.value,
            "height":  self.height,
            "balance": self.balance,
            "left":    self.left.to_dict()  if self.left  else None,
            "right":   self.right.to_dict() if self.right else None,
        }

    @staticmethod
    def from_dict(data: dict | None) -> "Node | None":
        """
        Reconstruye un nodo (y todo su subárbol) desde un diccionario.
        Retorna None si data es None.
        """
        if data is None:
            return None
        node = Node(data["value"])
        node.height  = data.get("height",  1)
        node.balance = data.get("balance", 0)
        node.left    = Node.from_dict(data.get("left"))
        node.right   = Node.from_dict(data.get("right"))
        return node