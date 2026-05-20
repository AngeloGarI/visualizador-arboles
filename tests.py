"""
test_trees.py
-------------
Pruebas unitarias para BinaryTree, BST y AVL.
Ejecutar con:  python test_trees.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from logic import BinaryTree, BST, AVL, TreeStorage


# ═══════════════════════════════════════════════════════════════════════ #
#  Colores para terminal                                                   #
# ═══════════════════════════════════════════════════════════════════════ #

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

passed = 0
failed = 0


def check(description: str, condition: bool) -> None:
    global passed, failed
    if condition:
        print(f"  {GREEN}✓{RESET}  {description}")
        passed += 1
    else:
        print(f"  {RED}✗{RESET}  {description}")
        failed += 1


def section(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{'─'*55}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*55}{RESET}")


# ═══════════════════════════════════════════════════════════════════════ #
#  Pruebas BinaryTree                                                      #
# ═══════════════════════════════════════════════════════════════════════ #

def test_binary_tree() -> None:
    section("ÁRBOL BINARIO GENERAL")
    bt = BinaryTree()

    # Inserción
    for v in [1, 2, 3, 4, 5, 6, 7]:
        bt.insert(v)

    check("Nodos insertados correctamente (7)", bt.node_count == 7)
    check("Altura del árbol completo de 7 nodos = 3", bt.height == 3)
    check("Raíz es 1", bt.root_value == 1)

    # Recorridos
    check("Preorden [1,2,4,5,3,6,7]", bt.preorder()  == [1, 2, 4, 5, 3, 6, 7])
    check("Inorden  [4,2,5,1,6,3,7]", bt.inorder()   == [4, 2, 5, 1, 6, 3, 7])
    check("Postorden[4,5,2,6,7,3,1]", bt.postorder() == [4, 5, 2, 6, 7, 3, 1])

    # Búsqueda
    node, path = bt.search(5)
    check("Búsqueda de 5: encontrado",      node is not None and node.value == 5)
    check("Búsqueda de 5: camino no vacío", len(path) > 0)

    node_none, _ = bt.search(99)
    check("Búsqueda de 99: no encontrado",  node_none is None)

    # Eliminación
    ok, msg = bt.delete(4)
    check("Eliminación de nodo hoja (4): éxito", ok)
    check("Nodos después de eliminar: 6", bt.node_count == 6)

    ok2, _ = bt.delete(999)
    check("Eliminar valor inexistente retorna False", not ok2)

    # Info general
    info = bt.get_info()
    check("get_info contiene 'height'",     "height"     in info)
    check("get_info contiene 'node_count'", "node_count" in info)


# ═══════════════════════════════════════════════════════════════════════ #
#  Pruebas BST                                                             #
# ═══════════════════════════════════════════════════════════════════════ #

def test_bst() -> None:
    section("ÁRBOL BINARIO DE BÚSQUEDA (BST)")
    bst = BST()

    values = [50, 30, 70, 20, 40, 60, 80]
    for v in values:
        bst.insert(v)

    check("Nodos insertados (7)",         bst.node_count == 7)
    check("Raíz es 50",                   bst.root_value == 50)
    check("Es un BST válido",             bst.is_valid_bst())
    check("Inorden produce orden ascend.", bst.inorder() == sorted(values))

    # Búsqueda BST
    node, path = bst.search(40)
    check("Búsqueda de 40: encontrado",   node is not None)
    check("Camino de búsqueda de 40",     50 in path and 30 in path)

    # Inserción de duplicado
    bst.insert(50)
    check("Duplicados no se insertan",    bst.node_count == 7)

    # Eliminación – caso hoja
    ok, desc = bst.delete(20)
    check("Eliminar hoja 20: éxito",      ok)
    check("Descripción menciona 'hoja'",  "hoja" in desc.lower())
    check("Nodos = 6 tras eliminar 20",   bst.node_count == 6)
    check("Sigue siendo BST válido",      bst.is_valid_bst())

    # Eliminación – un hijo
    bst2 = BST()
    for v in [10, 5, 15, 3]:
        bst2.insert(v)
    ok2, desc2 = bst2.delete(5)
    check("Eliminar nodo con un hijo (5): éxito", ok2)
    check("Sigue siendo BST válido tras eliminar con 1 hijo", bst2.is_valid_bst())

    # Eliminación – dos hijos (usar árbol fresco para garantizar 2 hijos)
    bst3 = BST()
    for v in [50, 30, 70, 20, 40]:
        bst3.insert(v)
    ok3, desc3 = bst3.delete(30)
    check("Eliminar nodo con dos hijos (30): éxito", ok3)
    check("Descripción menciona 'sucesor'", "sucesor" in desc3.lower())
    check("Sigue siendo BST válido",         bst.is_valid_bst())


# ═══════════════════════════════════════════════════════════════════════ #
#  Pruebas AVL                                                             #
# ═══════════════════════════════════════════════════════════════════════ #

def test_avl() -> None:
    section("ÁRBOL AVL")
    avl = AVL()

    # Rotación simple derecha: insertar 30, 20, 10 → desbalance en 30
    avl.insert(30)
    avl.insert(20)
    _, _, rotations = avl.insert(10)
    check("Rotación simple derecha detectada", len(rotations) > 0)
    check("AVL balanceado tras rotación derecha", avl._is_balanced(avl.root))

    avl.clear()

    # Rotación simple izquierda: insertar 10, 20, 30 → desbalance en 10
    avl.insert(10)
    avl.insert(20)
    _, _, rotations = avl.insert(30)
    check("Rotación simple izquierda detectada", len(rotations) > 0)
    check("AVL balanceado tras rotación izquierda", avl._is_balanced(avl.root))

    avl.clear()

    # Rotación doble izquierda-derecha: 30, 10, 20
    avl.insert(30)
    avl.insert(10)
    _, _, rotations = avl.insert(20)
    check("Rotación doble izq-der detectada", len(rotations) > 0)
    check("AVL balanceado tras rotación doble izq-der", avl._is_balanced(avl.root))

    avl.clear()

    # Rotación doble derecha-izquierda: 10, 30, 20
    avl.insert(10)
    avl.insert(30)
    _, _, rotations = avl.insert(20)
    check("Rotación doble der-izq detectada", len(rotations) > 0)
    check("AVL balanceado tras rotación doble der-izq", avl._is_balanced(avl.root))

    avl.clear()

    # Inserción masiva y balance continuo
    for v in [40, 20, 60, 10, 30, 50, 70, 5, 15, 25, 35]:
        avl.insert(v)
    check("AVL balanceado con 11 nodos", avl._is_balanced(avl.root))
    check("Es BST válido con 11 nodos",  avl.is_valid_bst())

    # Eliminación y rebalanceo
    ok, desc, rots = avl.delete(10)
    check("Eliminación en AVL: éxito", ok)
    check("AVL sigue balanceado tras eliminación", avl._is_balanced(avl.root))

    # Factores de balance
    factors = avl.get_balance_factors()
    check("get_balance_factors retorna dict no vacío", len(factors) > 0)
    check("Todos los factores en [-1, 0, 1]",
          all(abs(b) <= 1 for b in factors.values()))


# ═══════════════════════════════════════════════════════════════════════ #
#  Pruebas TreeStorage                                                     #
# ═══════════════════════════════════════════════════════════════════════ #

def test_storage() -> None:
    section("GUARDADO Y CARGA (TreeStorage)")
    storage = TreeStorage(save_dir="data/test_temp")

    # Guardar AVL
    avl = AVL()
    for v in [50, 25, 75, 10, 30]:
        avl.insert(v)

    path = storage.save(avl, "test_avl")
    check("Archivo guardado existe",   os.path.isfile(path))

    # Cargar
    loaded = storage.load("test_avl")
    check("Árbol cargado es AVL",             isinstance(loaded, AVL))
    check("Nodos cargados correctamente (5)", loaded.node_count == 5)
    check("Raíz cargada correctamente",       loaded.root_value == avl.root_value)
    check("Inorden preservado",               loaded.inorder() == avl.inorder())

    # Guardar BST
    bst = BST()
    for v in [15, 10, 20]:
        bst.insert(v)
    storage.save(bst, "test_bst")

    loaded_bst = storage.load("test_bst")
    check("Árbol cargado es BST", isinstance(loaded_bst, BST))

    # Listar archivos
    files = storage.list_saved_files()
    names = [f["filename"] for f in files]
    check("test_avl.json en la lista", "test_avl.json" in names)
    check("test_bst.json en la lista", "test_bst.json" in names)

    # Archivo inexistente
    try:
        storage.load("no_existe")
        check("FileNotFoundError lanzado", False)
    except FileNotFoundError:
        check("FileNotFoundError lanzado correctamente", True)

    # Limpiar archivos temporales
    storage.delete_file("test_avl")
    storage.delete_file("test_bst")
    try:
        os.rmdir("data/test_temp")
    except OSError:
        pass


# ═══════════════════════════════════════════════════════════════════════ #
#  Resumen                                                                 #
# ═══════════════════════════════════════════════════════════════════════ #

if __name__ == "__main__":
    print(f"\n{BOLD}{'═'*55}")
    print("  SUITE DE PRUEBAS – VISUALIZADOR DE ÁRBOLES")
    print(f"{'═'*55}{RESET}")

    test_binary_tree()
    test_bst()
    test_avl()
    test_storage()

    total = passed + failed
    print(f"\n{BOLD}{'═'*55}{RESET}")
    print(f"  Resultados: {GREEN}{passed} pasadas{RESET} / {RED}{failed} fallidas{RESET} / {total} total")
    print(f"{BOLD}{'═'*55}{RESET}\n")

    sys.exit(0 if failed == 0 else 1)