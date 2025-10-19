import sys
import xml.etree.ElementTree as ET
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import networkx as nx
import matplotlib.pyplot as plt

def get_direct_dependencies(group, artifact, version, repo_url):
    group_path = group.replace('.', '/')
    pom_url = f"{repo_url}{group_path}/{artifact}/{version}/{artifact}-{version}.pom"
    try:
        with urlopen(pom_url) as response:
            pom_data = response.read().decode('utf-8')
        ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
        root = ET.fromstring(pom_data)
        dependencies = []
        for dep in root.findall(".//maven:dependency", ns):
            dep_group = dep.find("maven:groupId", ns)
            dep_artifact = dep.find("maven:artifactId", ns)
            dep_version = dep.find("maven:version", ns)
            scope = dep.find("maven:scope", ns)
            optional = dep.find("maven:optional", ns)
            # Проверяем, что все обязательные элементы присутствуют
            if dep_group is None or dep_artifact is None:
                print(f"Warning: Skipping dependency with missing groupId or artifactId")
                continue
            # Если версия отсутствует, пропускаем
            if dep_version is None:
                print(f"Warning: Skipping dependency {dep_group.text}:{dep_artifact.text} with missing version")
                continue
            # Проверяем scope и optional
            if (scope is None or scope.text in ['compile', 'runtime', 'provided']) and (optional is None or optional.text != 'true'):
                dependencies.append(f"{dep_group.text}:{dep_artifact.text}:{dep_version.text}")
        if not dependencies:
            print("No valid dependencies found in POM.")
        return dependencies
    except (HTTPError, URLError) as e:
        print(f"Error: Failed to fetch POM from {pom_url}: {e}")
        sys.exit(1)
    except ET.ParseError:
        print("Error: Invalid POM XML.")
        sys.exit(1)
    except AttributeError as e:
        print(f"Error: Unexpected structure in POM: {e}")
        sys.exit(1)
        
def parse_test_repo(file_path):
    graph = nx.DiGraph()
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if ':' in line:
                    pkg, deps = line.strip().split(':')
                    pkg = pkg.strip()
                    graph.add_node(pkg)
                    for dep in deps.split():
                        graph.add_node(dep)
                        graph.add_edge(pkg, dep)  # край от pkg к dep (зависит от)
        return graph
    except FileNotFoundError:
        print("Error: Test repo file not found.")
        sys.exit(1)
        
def recursive_bfs(graph, current_level, visited, depth, max_depth, repo_url, test_mode):
    if depth > max_depth or not current_level:
        return
    next_level = []
    for node in current_level:
        if node not in visited:  # Проверяем, не посещён ли узел
            if test_mode == 'on':
                for child in graph.successors(node):
                    if child not in visited:
                        next_level.append(child)
            else:
                parts = node.split(':')
                if len(parts) != 3:
                    print(f"Warning: Invalid node format {node}")
                    continue
                group, artifact, version = parts
                deps = get_direct_dependencies(group, artifact, version, repo_url)
                for dep in deps:
                    graph.add_node(dep)
                    graph.add_edge(node, dep)
                    if dep not in visited:
                        next_level.append(dep)
            visited.add(node)  # Добавляем узел в visited после обработки
    recursive_bfs(graph, next_level, visited, depth + 1, max_depth, repo_url, test_mode)

def build_graph(start_node, max_depth, repo_url, test_mode, test_file=None):
    graph = nx.DiGraph()
    graph.add_node(start_node)
    visited = set()
    if test_mode == 'on' and test_file:
        graph = parse_test_repo(test_file)
    recursive_bfs(graph, [start_node], visited, 1, max_depth, repo_url, test_mode)
    return graph

def detect_cycles(graph):
    try:
        cycles = list(nx.simple_cycles(graph))
        if cycles:
            print("Cycles detected in graph:")
            for i, cycle in enumerate(cycles, 1):
                print(f"Cycle {i}: {' -> '.join(cycle)} -> ...")
            return True
        else:
            print("No cycles detected in graph.")
            return False
    except Exception as e:
        print(f"Error detecting cycles: {e}")
        return False

def get_dependency_load_order(graph, start_node):
    try:
        # Проверяем наличие цикла
        cycles = list(nx.simple_cycles(graph))
        if cycles:
            print("Cannot compute load order due to cycles in the graph:")
            for i, cycle in enumerate(cycles, 1):
                print(f"Cycle {i}: {' -> '.join(cycle)} -> ...")
            return None
        
        # Выполняем топологическую сортировку
        topological_order = list(nx.topological_sort(graph))
        
        # Для порядка загрузки зависимостей нужен обратный порядок:
        # сначала загружаются узлы без зависимостей (листья), затем те, что от них зависят
        load_order = list(reversed(topological_order))
        
        print(f"Dependency load order for {start_node}:")
        print(" -> ".join(load_order))
        return load_order
    except Exception as e:
        print(f"Error computing load order: {e}")
        return None
def main():
    if len(sys.argv) != 2:
        print("Usage: python app.py config.xml")
        sys.exit(1)

    config_file = sys.argv[1]
    try:
        tree = ET.parse(config_file)
        root = tree.getroot()

        package_name = root.find('package_name').text.strip()
        repo_url = root.find('repo_url').text.strip()
        test_mode = root.find('test_mode').text.strip()
        package_version = root.find('package_version').text.strip()
        output_file = root.find('output_file').text.strip()
        ascii_mode = root.find('ascii_mode').text.strip()
        max_depth = int(root.find('max_depth').text.strip())

        # Вывод параметров (из этапа 1)
        '''print(f"package_name: {package_name}")
        print(f"repo_url: {repo_url}")
        print(f"test_mode: {test_mode}")
        print(f"package_version: {package_version}")
        print(f"output_file: {output_file}")
        print(f"ascii_mode: {ascii_mode}")
        print(f"max_depth: {max_depth}")'''

        if test_mode == 'off':
            group, artifact = package_name.split(':')
            direct_deps = get_direct_dependencies(group, artifact, package_version, repo_url)
            print("Direct dependencies:")
            for dep in direct_deps:
                print(dep)
        else:
            print("Test mode on, skipping real dependencies fetch for this stage.")
            
        start_node = f"{package_name}:{package_version}" if test_mode == 'off' else package_name
        test_file = repo_url if test_mode == 'on' else None
        graph = build_graph(start_node, max_depth, repo_url, test_mode, test_file)
        print("Graph nodes:", list(graph.nodes))
        print("Graph edges:", list(graph.edges))
        detect_cycles(graph)
        get_dependency_load_order(graph, start_node)
        

    except FileNotFoundError:
        print("Error: Config file not found.")
        sys.exit(1)
    except ET.ParseError:
        print("Error: Invalid XML format.")
        sys.exit(1)
    except (AttributeError, ValueError):
        print("Error: Missing or invalid parameter in config (e.g., missing element or non-integer max_depth).")
        sys.exit(1)

if __name__ == "__main__":
    main()