"""
main.py
-------
Interfaz de consola interactiva para el Visualizador de Árboles.
Permite probar toda la lógica (BinaryTree, BST, AVL) mientras
la interfaz gráfica (PyQt) está en desarrollo.

Ejecutar:
    python main.py
"""

import os
import sys
import time

from logic import BinaryTree, BST, AVL, TreeStorage

# ═══════════════════════════════════════════════════════════════════════ #
#  Colores ANSI                                                            #
# ═══════════════════════════════════════════════════════════════════════ #

GREEN   = "\033[92m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
MAGENTA = "\033[95m"
BLUE    = "\033[94m"
WHITE   = "\033[97m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"

def c(color: str, text: str) -> str:
    """Envuelve texto con color ANSI."""
    return f"{color}{text}{RESET}"

# ═══════════════════════════════════════════════════════════════════════ #
#  Utilidades de pantalla                                                  #
# ═══════════════════════════════════════════════════════════════════════ #

def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")

def pause() -> None:
    input(f"\n  {DIM}Presiona Enter para continuar...{RESET}")

def header(title: str) -> None:
    width = 60
    print(f"\n{BOLD}{CYAN}{'═' * width}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'═' * width}{RESET}\n")

def section(title: str) -> None:
    print(f"\n{BOLD}{BLUE}  ── {title} ──{RESET}")

def ok(msg: str) -> None:
    print(f"  {GREEN}✓{RESET}  {msg}")

def err(msg: str) -> None:
    print(f"  {RED}✗{RESET}  {msg}")

def info(msg: str) -> None:
    print(f"  {CYAN}ℹ{RESET}  {msg}")

def warn(msg: str) -> None:
    print(f"  {YELLOW}⚠{RESET}  {msg}")

def ask(prompt: str) -> str:
    return input(f"  {YELLOW}▶{RESET}  {prompt}: ").strip()

# ═══════════════════════════════════════════════════════════════════════ #
#  Visualización del árbol en consola                                     #
# ═══════════════════════════════════════════════════════════════════════ #

def print_tree(tree, highlight: list = None) -> None:
    """
    Dibuja el árbol en consola de forma jerárquica.
    Los nodos en 'highlight' se resaltan en amarillo.
    """
    from logic.node import Node

    if tree.root is None:
        warn("El árbol está vacío.")
        return

    highlight_set = set(highlight) if highlight else set()

    def _draw(node, prefix: str, is_left: bool, is_root: bool = False):
        if node is None:
            return

        if is_root:
            connector = ""
            new_prefix = ""
        else:
            connector = "├── " if is_left else "└── "
            new_prefix = prefix + ("│   " if is_left else "    ")

        # Color del nodo
        val_str = str(node.value)
        if node.value in highlight_set:
            val_str = c(YELLOW + BOLD, f"[{node.value}]")
        else:
            val_str = c(WHITE + BOLD, str(node.value))

        # Info extra (altura y balance para AVL)
        extra = ""
        if isinstance(tree, AVL):
            bf = node.balance
            bf_color = GREEN if bf == 0 else (YELLOW if abs(bf) == 1 else RED)
            extra = c(DIM, f"  h={node.height} bf=") + c(bf_color, str(bf))

        print(f"  {prefix}{connector}{val_str}{extra}")

        # Calcular prefijo para hijos
        child_prefix = prefix if is_root else new_prefix
        if node.left or node.right:
            _draw(node.left,  child_prefix, True)
            _draw(node.right, child_prefix, False)

    print()
    _draw(tree.root, "", False, is_root=True)
    print()

def print_tree_info(tree) -> None:
    """Muestra el panel de información del árbol."""
    info_dict = tree.get_info()
    print(f"\n  {BOLD}{'─'*40}{RESET}")
    print(f"  {BOLD}Tipo   :{RESET}  {c(MAGENTA, info_dict['type'])}")
    print(f"  {BOLD}Raíz   :{RESET}  {c(WHITE, str(info_dict['root']))}")
    print(f"  {BOLD}Altura :{RESET}  {c(CYAN, str(info_dict['height']))}")
    print(f"  {BOLD}Nodos  :{RESET}  {c(CYAN, str(info_dict['node_count']))}")
    if "is_balanced" in info_dict:
        bal = c(GREEN, "Sí") if info_dict["is_balanced"] else c(RED, "No")
        print(f"  {BOLD}Balance:{RESET}  {bal}")
    print(f"  {BOLD}{'─'*40}{RESET}")

def animate_path(path: list, label: str = "Recorrido") -> None:
    """Muestra el camino recorrido paso a paso."""
    if not path:
        return
    print(f"\n  {DIM}{label}:{RESET}", end="  ")
    for i, val in enumerate(path):
        time.sleep(0.08)
        arrow = " → " if i < len(path) - 1 else ""
        print(c(YELLOW, str(val)) + c(DIM, arrow), end="", flush=True)
    print()

def animate_traversal(values: list, name: str) -> None:
    """Muestra el recorrido animado con numeración."""
    print(f"\n  {BOLD}{name}:{RESET}")
    print("  ", end="")
    for i, val in enumerate(values):
        time.sleep(0.1)
        print(c(CYAN, f"{i+1}.") + c(WHITE, f"{val}  "), end="", flush=True)
    print()

# ═══════════════════════════════════════════════════════════════════════ #
#  Menús                                                                   #
# ═══════════════════════════════════════════════════════════════════════ #

def menu_seleccionar_tipo() -> str:
    """Menú inicial para elegir tipo de árbol."""
    clear()
    header("VISUALIZADOR DE ÁRBOLES Y RECURSIVIDAD")
    print(f"  {BOLD}Selecciona el tipo de árbol:{RESET}\n")
    print(f"  {c(CYAN, '1')}  Árbol Binario General")
    print(f"  {c(CYAN, '2')}  Árbol Binario de Búsqueda (BST)")
    print(f"  {c(CYAN, '3')}  Árbol AVL")
    print(f"  {c(CYAN, '4')}  Cargar árbol desde archivo")
    print(f"  {c(RED,  '0')}  Salir\n")
    return ask("Opción")

def menu_principal(tree) -> str:
    """Menú principal de operaciones sobre el árbol activo."""
    clear()
    header(f"ÁRBOL ACTIVO: {tree.TREE_TYPE}")
    print_tree(tree)
    print_tree_info(tree)
    print(f"\n  {BOLD}Operaciones disponibles:{RESET}\n")
    print(f"  {c(CYAN,  '1')}  Insertar valor")
    print(f"  {c(CYAN,  '2')}  Buscar valor")
    print(f"  {c(CYAN,  '3')}  Eliminar valor")
    print(f"  {c(CYAN,  '4')}  Recorridos (preorden / inorden / postorden)")
    print(f"  {c(CYAN,  '5')}  Insertar múltiples valores")
    print(f"  {c(CYAN,  '6')}  Guardar árbol")
    print(f"  {c(CYAN,  '7')}  Ver información detallada de nodos")
    print(f"  {c(YELLOW,'8')}  Limpiar árbol")
    print(f"  {c(RED,   '0')}  Volver al menú principal\n")
    return ask("Opción")

# ═══════════════════════════════════════════════════════════════════════ #
#  Operaciones                                                             #
# ═══════════════════════════════════════════════════════════════════════ #

def op_insertar(tree) -> None:
    clear()
    header("INSERTAR VALOR")
    print_tree(tree)

    raw = ask("Valor a insertar (entero)")
    if not raw:
        return

    try:
        value = int(raw)
    except ValueError:
        err("Ingresa un número entero válido.")
        pause()
        return

    # Llamada según tipo (AVL retorna 3 valores)
    if isinstance(tree, AVL):
        node, path, rotations = tree.insert(value)
        clear()
        header("INSERTAR VALOR")
        animate_path(path, "Camino recorrido")
        print_tree(tree, highlight=path + [value])
        if rotations:
            print(f"\n  {BOLD}{YELLOW}Rotaciones aplicadas:{RESET}")
            for r in rotations:
                print(f"    {c(YELLOW, '↻')}  {r}")
        else:
            info("No se requirieron rotaciones.")
    else:
        node, path = tree.insert(value)
        clear()
        header("INSERTAR VALOR")
        animate_path(path, "Camino recorrido")
        print_tree(tree, highlight=path + [value])

    ok(f"Valor {c(WHITE+BOLD, str(value))} insertado correctamente.")
    pause()


def op_buscar(tree) -> None:
    clear()
    header("BUSCAR VALOR")
    print_tree(tree)

    raw = ask("Valor a buscar")
    if not raw:
        return

    try:
        value = int(raw)
    except ValueError:
        err("Ingresa un número entero válido.")
        pause()
        return

    node, path = tree.search(value)

    clear()
    header("BUSCAR VALOR")
    animate_path(path, "Camino recorrido")
    print_tree(tree, highlight=path)

    if node:
        ok(f"Valor {c(WHITE+BOLD, str(value))} {c(GREEN, 'ENCONTRADO')} "
           f"tras visitar {len(path)} nodo(s).")
    else:
        err(f"Valor {c(WHITE+BOLD, str(value))} {c(RED, 'NO ENCONTRADO')} "
            f"en el árbol.")
    pause()


def op_eliminar(tree) -> None:
    clear()
    header("ELIMINAR VALOR")
    print_tree(tree)

    raw = ask("Valor a eliminar")
    if not raw:
        return

    try:
        value = int(raw)
    except ValueError:
        err("Ingresa un número entero válido.")
        pause()
        return

    # Llamada según tipo
    if isinstance(tree, AVL):
        success, description, rotations = tree.delete(value)
    else:
        success, description = tree.delete(value)
        rotations = []

    clear()
    header("ELIMINAR VALOR")

    if success:
        print_tree(tree)
        ok(f"Valor {c(WHITE+BOLD, str(value))} eliminado correctamente.")
        info(f"Caso: {description}")
        if rotations:
            print(f"\n  {BOLD}{YELLOW}Rotaciones de rebalanceo:{RESET}")
            for r in rotations:
                print(f"    {c(YELLOW, '↻')}  {r}")
    else:
        print_tree(tree)
        err(description)

    pause()


def op_recorridos(tree) -> None:
    while True:
        clear()
        header("RECORRIDOS")
        print_tree(tree)

        print(f"  {c(CYAN,'1')}  Preorden   (raíz → izquierda → derecha)")
        print(f"  {c(CYAN,'2')}  Inorden    (izquierda → raíz → derecha)")
        print(f"  {c(CYAN,'3')}  Postorden  (izquierda → derecha → raíz)")
        print(f"  {c(CYAN,'4')}  Ver los tres recorridos")
        print(f"  {c(RED, '0')}  Volver\n")

        opcion = ask("Opción")

        if opcion == "0":
            break
        elif opcion == "1":
            vals = tree.preorder()
            clear()
            header("PREORDEN  —  raíz → izquierda → derecha")
            print_tree(tree)
            animate_traversal(vals, "Preorden")
            info(f"Secuencia completa: {c(CYAN, str(vals))}")
            pause()
        elif opcion == "2":
            vals = tree.inorder()
            clear()
            header("INORDEN  —  izquierda → raíz → derecha")
            print_tree(tree)
            animate_traversal(vals, "Inorden")
            info(f"Secuencia completa: {c(CYAN, str(vals))}")
            if isinstance(tree, (BST, AVL)):
                info("(En BST/AVL el inorden produce valores en orden ascendente)")
            pause()
        elif opcion == "3":
            vals = tree.postorder()
            clear()
            header("POSTORDEN  —  izquierda → derecha → raíz")
            print_tree(tree)
            animate_traversal(vals, "Postorden")
            info(f"Secuencia completa: {c(CYAN, str(vals))}")
            pause()
        elif opcion == "4":
            clear()
            header("LOS TRES RECORRIDOS")
            print_tree(tree)
            animate_traversal(tree.preorder(),  "Preorden ")
            animate_traversal(tree.inorder(),   "Inorden  ")
            animate_traversal(tree.postorder(), "Postorden")
            pause()
        else:
            warn("Opción inválida.")
            pause()


def op_insertar_multiples(tree) -> None:
    clear()
    header("INSERTAR MÚLTIPLES VALORES")
    info("Ingresa los valores separados por comas o espacios.")
    info("Ejemplo:  10, 5, 20, 3, 7\n")

    raw = ask("Valores")
    if not raw:
        return

    # Separar por coma o espacio
    tokens = raw.replace(",", " ").split()
    valores = []
    invalidos = []

    for t in tokens:
        try:
            valores.append(int(t))
        except ValueError:
            invalidos.append(t)

    if invalidos:
        warn(f"Se ignoraron los valores no numéricos: {invalidos}")

    if not valores:
        err("No se ingresó ningún valor válido.")
        pause()
        return

    print()
    for v in valores:
        if isinstance(tree, AVL):
            node, path, rotations = tree.insert(v)
            msg = f"Insertado {c(WHITE+BOLD, str(v))}"
            if rotations:
                msg += f"  {c(YELLOW, '↻ ' + rotations[-1])}"
        else:
            node, path = tree.insert(v)
            msg = f"Insertado {c(WHITE+BOLD, str(v))}"
        ok(msg)
        time.sleep(0.05)

    clear()
    header("INSERTAR MÚLTIPLES VALORES")
    print_tree(tree, highlight=valores)
    ok(f"{len(valores)} valores insertados.")
    print_tree_info(tree)
    pause()


def op_guardar(tree, storage: TreeStorage) -> None:
    clear()
    header("GUARDAR ÁRBOL")

    # Listar archivos existentes
    files = storage.list_saved_files()
    if files:
        section("Archivos guardados actualmente")
        for f in files:
            print(f"  {c(DIM,'•')}  {f['filename']}  "
                  f"{c(CYAN, f['tree_type'])}  "
                  f"{c(DIM, f['saved_at'])}")
        print()

    nombre = ask("Nombre del archivo (sin extensión)")
    if not nombre:
        warn("Operación cancelada.")
        pause()
        return

    try:
        filepath = storage.save(tree, nombre)
        ok(f"Árbol guardado en:  {c(CYAN, filepath)}")
    except Exception as e:
        err(f"Error al guardar: {e}")

    pause()


def op_cargar(storage: TreeStorage):
    """Carga un árbol desde archivo. Retorna el árbol o None."""
    clear()
    header("CARGAR ÁRBOL")

    files = storage.list_saved_files()
    if not files:
        warn("No hay archivos guardados en el directorio 'data/'.")
        pause()
        return None

    section("Archivos disponibles")
    for i, f in enumerate(files, 1):
        print(f"  {c(CYAN, str(i))}  {f['filename']:<30} "
              f"{c(MAGENTA, f['tree_type']):<12} "
              f"nodos={c(WHITE, str(f['node_count']))}  "
              f"{c(DIM, f['saved_at'])}")

    print(f"  {c(RED,'0')}  Cancelar\n")
    raw = ask("Número de archivo")

    if raw == "0" or not raw:
        return None

    try:
        idx = int(raw) - 1
        if idx < 0 or idx >= len(files):
            err("Número fuera de rango.")
            pause()
            return None
        filename = files[idx]["filename"]
        tree = storage.load(filename)
        clear()
        header("CARGAR ÁRBOL")
        print_tree(tree)
        ok(f"Árbol '{c(CYAN, filename)}' cargado correctamente.")
        print_tree_info(tree)
        pause()
        return tree
    except (FileNotFoundError, ValueError) as e:
        err(str(e))
        pause()
        return None


def op_info_nodos(tree) -> None:
    """Muestra altura y factor de balance de cada nodo."""
    clear()
    header("INFORMACIÓN DETALLADA DE NODOS")
    print_tree(tree)

    from collections import deque
    if tree.root is None:
        warn("El árbol está vacío.")
        pause()
        return

    print(f"  {BOLD}{'Valor':<10} {'Altura':<10} {'Balance':<10} {'Tipo de nodo'}{RESET}")
    print(f"  {'─'*50}")

    queue = deque([tree.root])
    while queue:
        node = queue.popleft()
        if node.is_leaf():
            tipo = c(GREEN, "Hoja")
        elif node.has_one_child():
            tipo = c(YELLOW, "Un hijo")
        else:
            tipo = c(CYAN, "Dos hijos")

        bf = node.balance
        bf_color = GREEN if bf == 0 else (YELLOW if abs(bf) == 1 else RED)
        print(f"  {c(WHITE+BOLD, str(node.value)):<10} "
              f"{str(node.height):<10} "
              f"{c(bf_color, str(bf)):<10} "
              f"{tipo}")

        if node.left:  queue.append(node.left)
        if node.right: queue.append(node.right)

    pause()


def op_limpiar(tree) -> None:
    clear()
    header("LIMPIAR ÁRBOL")
    warn("Esto eliminará todos los nodos del árbol actual.")
    confirm = ask("¿Confirmar? (s/n)")
    if confirm.lower() == "s":
        tree.clear()
        ok("Árbol vaciado.")
    else:
        info("Operación cancelada.")
    pause()


# ═══════════════════════════════════════════════════════════════════════ #
#  Flujo principal                                                         #
# ═══════════════════════════════════════════════════════════════════════ #

def crear_arbol(tipo: str) -> BinaryTree | None:
    """Instancia el árbol según la opción seleccionada."""
    if tipo == "1":
        return BinaryTree()
    elif tipo == "2":
        return BST()
    elif tipo == "3":
        return AVL()
    return None


def main() -> None:
    storage = TreeStorage()
    tree: BinaryTree | None = None

    while True:
        opcion = menu_seleccionar_tipo()

        if opcion == "0":
            clear()
            print(f"\n  {c(CYAN, 'Hasta luego.')}\n")
            sys.exit(0)

        elif opcion in ("1", "2", "3"):
            tree = crear_arbol(opcion)
            nombres = {"1": "Árbol Binario", "2": "BST", "3": "AVL"}
            ok(f"{nombres[opcion]} creado.")
            time.sleep(0.4)

        elif opcion == "4":
            cargado = op_cargar(storage)
            if cargado:
                tree = cargado
            else:
                continue
        else:
            warn("Opción inválida.")
            time.sleep(0.5)
            continue

        # ── Bucle de operaciones sobre el árbol activo ──────────────── #
        while tree is not None:
            op = menu_principal(tree)

            if op == "0":
                tree = None
                break
            elif op == "1":
                op_insertar(tree)
            elif op == "2":
                op_buscar(tree)
            elif op == "3":
                op_eliminar(tree)
            elif op == "4":
                op_recorridos(tree)
            elif op == "5":
                op_insertar_multiples(tree)
            elif op == "6":
                op_guardar(tree, storage)
            elif op == "7":
                op_info_nodos(tree)
            elif op == "8":
                op_limpiar(tree)
            else:
                warn("Opción inválida.")
                time.sleep(0.5)


if __name__ == "__main__":
    main()