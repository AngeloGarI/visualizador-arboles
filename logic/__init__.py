"""
logic/__init__.py
-----------------
Paquete con toda la lógica de árboles.
Exporta las clases principales para uso cómodo:

    from logic import Node, BinaryTree, BST, AVL, TreeStorage
"""

from .node         import Node
from .binary_tree  import BinaryTree
from .bst          import BST
from .avl          import AVL
from .tree_storage import TreeStorage

__all__ = [
    "Node",
    "BinaryTree",
    "BST",
    "AVL",
    "TreeStorage",
]