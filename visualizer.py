import argparse
import urllib.request
import urllib.error
import json
import sys
from collections import deque

sys.stdout.reconfigure(encoding='utf-8')


def print_config(args):
    print("=== Этап 1: Настраиваемые параметры ===")
    for key, value in vars(args).items():
        print(f"{key}: {value}")
    print("=======================================\n")


def get_npm_deps(package, version):
    url = f"https://registry.npmjs.org/{package}/{version}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data.get('dependencies', {})
    except urllib.error.URLError:
        return {}
    except Exception as e:
        print(f"Ошибка при получении пакета {package}: {e}")
        return {}


def get_test_deps(filepath, package):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get(package, {})
    except FileNotFoundError:
        print(f"Ошибка: Файл '{filepath}' не найден.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Ошибка: Некорректный JSON в '{filepath}'.")
        sys.exit(1)


def build_graph(pkg, ver, url, is_test, max_d):
    graph = {}
    load_order = []
    visited = set()
    queue = deque([(pkg, ver, 0)])

    while queue:
        cur_pkg, cur_ver, depth = queue.popleft()

        if cur_pkg in visited:
            continue

        visited.add(cur_pkg)
        load_order.append(cur_pkg)

        if depth >= max_d:
            if cur_pkg not in graph:
                graph[cur_pkg] = {}
            continue

        if is_test:
            deps = get_test_deps(url, cur_pkg)
        else:
            deps = get_npm_deps(cur_pkg, cur_ver)

        graph[cur_pkg] = deps

        for d_pkg, d_ver in deps.items():
            cln_v = d_ver.strip('^~><=') if isinstance(d_ver, str) else d_ver
            queue.append((d_pkg, cln_v, depth + 1))

    return graph, load_order


def print_ascii(graph, node, max_d, cur_d=0, pref="", is_last=True, vis=None):
    if vis is None:
        vis = set()

    marker = "└── " if is_last else "├── "
    print(f"{pref}{marker}{node}")

    if node in vis or cur_d >= max_d:
        return

    vis.add(node)
    children = list(graph.get(node, {}).keys())

    for i, child in enumerate(children):
        last_child = (i == len(children) - 1)
        new_pref = pref + (" " if is_last else "│ ")
        print_ascii(
            graph, child, max_d, cur_d + 1, new_pref, last_child, vis.copy()
        )


def print_d2(graph):
    for parent, children in graph.items():
        if not children:
            print(f"{parent}")
        for child in children:
            print(f"{parent} -> {child}")


def parse_args():
    p = argparse.ArgumentParser(description="Анализатор графа")
    p.add_argument("--package", required=True, help="Имя пакета")
    p.add_argument("--url", required=True, help="URL или путь к файлу")
    p.add_argument("--test-mode", action="store_true", help="Тест режим")
    p.add_argument("--version", default="latest", help="Версия пакета")
    p.add_argument("--ascii", action="store_true", help="Вывод ASCII")
    p.add_argument("--max-depth", type=int, default=3, help="Глубина")

    try:
        return p.parse_args()
    except SystemExit:
        print("Ошибка: Отсутствуют обязательные параметры.")
        sys.exit(1)


def print_results(args, graph, load_order):
    print("=== Этап 2: Прямые зависимости ===")
    dir_deps = list(graph.get(args.package, {}).keys())
    res = dir_deps if dir_deps else 'Нет зависимостей'
    print(f"Прямые зависимости для {args.package}: {res}\n")

    print("=== Этап 4: Порядок загрузки зависимостей ===")
    print(" -> ".join(load_order) + "\n")

    print("=== Этап 5: Визуализация (D2) ===")
    print_d2(graph)
    print("\n")

    if args.ascii:
        print("=== Этап 5: Визуализация (ASCII-дерево) ===")
        print_ascii(graph, args.package, args.max_depth)
        print("\n")


def main():
    args = parse_args()

    if args.max_depth < 0:
        print("Ошибка: Глубина должна быть >= 0.")
        sys.exit(1)

    print_config(args)

    graph, load_order = build_graph(
        args.package, args.version, args.url, args.test_mode, args.max_depth
    )

    print_results(args, graph, load_order)


if __name__ == "__main__":
    main()