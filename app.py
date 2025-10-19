import sys
import xml.etree.ElementTree as ET
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

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