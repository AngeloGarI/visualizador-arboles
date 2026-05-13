"""
tree_storage.py
---------------
Módulo de guardado y carga de árboles en formato JSON.
Permite al usuario guardar su trabajo y retomarlo más tarde.

Formato del archivo JSON:
{
    "tree_type": "AVL" | "BST" | "BinaryTree",
    "saved_at":  "2025-...",
    "node_count": N,
    "root": { ... nodo serializado recursivamente ... }
}
"""

import json
import os
from datetime import datetime

from .node        import Node
from .binary_tree import BinaryTree
from .bst         import BST
from .avl         import AVL


# Mapa de nombre → clase para la carga dinámica
_TREE_CLASSES: dict[str, type] = {
    "BinaryTree": BinaryTree,
    "BST":        BST,
    "AVL":        AVL,
}

# Directorio por defecto donde se guardan los archivos
DEFAULT_SAVE_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


class TreeStorage:
    """
    Gestiona el guardado y la carga de árboles binarios en disco (JSON).
    """

    def __init__(self, save_dir: str = DEFAULT_SAVE_DIR):
        self.save_dir = os.path.abspath(save_dir)
        os.makedirs(self.save_dir, exist_ok=True)

    # ================================================================== #
    #  Guardado                                                            #
    # ================================================================== #

    def save(self, tree: BinaryTree, filename: str) -> str:
        """
        Serializa el árbol a JSON y lo guarda en disco.

        Parámetros:
            tree     : instancia de BinaryTree, BST o AVL.
            filename : nombre del archivo (se añade .json si no lo tiene).

        Retorna:
            Ruta absoluta del archivo guardado.
        """
        if not filename.endswith(".json"):
            filename += ".json"

        filepath = os.path.join(self.save_dir, filename)

        data = tree.to_dict()
        data["saved_at"] = datetime.now().isoformat(timespec="seconds")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return filepath

    # ================================================================== #
    #  Carga                                                               #
    # ================================================================== #

    def load(self, filename: str) -> BinaryTree:
        """
        Lee un archivo JSON y reconstruye el árbol correspondiente.

        Parámetros:
            filename : nombre del archivo (se añade .json si no lo tiene).

        Retorna:
            Instancia de BinaryTree, BST o AVL reconstruida.

        Lanza:
            FileNotFoundError si el archivo no existe.
            ValueError        si el tipo de árbol no es reconocido.
        """
        if not filename.endswith(".json"):
            filename += ".json"

        filepath = os.path.join(self.save_dir, filename)

        if not os.path.isfile(filepath):
            raise FileNotFoundError(
                f"No se encontró el archivo '{filepath}'."
            )

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        tree_type_name = data.get("tree_type", "BinaryTree")
        tree_class     = _TREE_CLASSES.get(tree_type_name)

        if tree_class is None:
            raise ValueError(
                f"Tipo de árbol desconocido: '{tree_type_name}'. "
                f"Los tipos válidos son: {list(_TREE_CLASSES.keys())}"
            )

        tree = tree_class()
        tree.from_dict(data)
        return tree

    # ================================================================== #
    #  Listado de archivos                                                 #
    # ================================================================== #

    def list_saved_files(self) -> list[dict]:
        """
        Lista todos los archivos JSON guardados en el directorio de datos.

        Retorna:
            Lista de diccionarios con keys: filename, tree_type, saved_at, node_count.
        """
        files: list[dict] = []

        for fname in os.listdir(self.save_dir):
            if not fname.endswith(".json"):
                continue

            fpath = os.path.join(self.save_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                files.append({
                    "filename":   fname,
                    "tree_type":  meta.get("tree_type",  "?"),
                    "saved_at":   meta.get("saved_at",   "?"),
                    "node_count": meta.get("node_count", "?"),
                })
            except (json.JSONDecodeError, KeyError):
                files.append({
                    "filename":  fname,
                    "tree_type": "error al leer",
                    "saved_at":  "?",
                    "node_count": "?",
                })

        return sorted(files, key=lambda x: x["saved_at"], reverse=True)

    # ================================================================== #
    #  Eliminación de archivo                                              #
    # ================================================================== #

    def delete_file(self, filename: str) -> bool:
        """
        Elimina un archivo guardado.

        Retorna True si se eliminó correctamente, False si no existía.
        """
        if not filename.endswith(".json"):
            filename += ".json"

        filepath = os.path.join(self.save_dir, filename)

        if os.path.isfile(filepath):
            os.remove(filepath)
            return True
        return False