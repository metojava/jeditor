import os
import subprocess
import xml.etree.ElementTree as ET
from typing import Optional

MAVEN_WRAPPER_SCRIPTS = ["mvnw", "mvnw.bat", "mvnw.cmd"]


def is_maven_project(project_dir: str) -> bool:
    return os.path.isfile(os.path.join(project_dir, "pom.xml"))


def has_maven_wrapper(project_dir: str) -> bool:
    for script in MAVEN_WRAPPER_SCRIPTS:
        if os.path.isfile(os.path.join(project_dir, script)):
            return True
    return False


def find_maven_command() -> Optional[str]:
    for cmd in ["mvn", "mvn.cmd", "mvn.bat"]:
        for path_dir in os.environ.get("PATH", "").split(os.pathsep):
            full = os.path.join(path_dir.strip(), cmd)
            if os.path.isfile(full):
                return full
    m2_home = os.environ.get("M2_HOME", "")
    if m2_home:
        for cmd in ["mvn", "mvn.bat"]:
            full = os.path.join(m2_home, "bin", cmd)
            if os.path.isfile(full):
                return full
    return None


def get_maven_command(project_dir: str) -> Optional[str]:
    if has_maven_wrapper(project_dir):
        for script in MAVEN_WRAPPER_SCRIPTS:
            full = os.path.join(project_dir, script)
            if os.path.isfile(full):
                return full
    return find_maven_command()


def parse_pom(pom_path: str) -> dict:
    result = {
        "group_id": "",
        "artifact_id": "",
        "version": "",
        "packaging": "jar",
        "java_version": "",
        "dependencies": []
    }
    if not os.path.isfile(pom_path):
        return result
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
        ns = {"m": "http://maven.apache.org/POM/4.0.0"}
        ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")

        def child_text(parent, tag):
            el = parent.find(f"m:{tag}", ns)
            return el.text.strip() if el is not None and el.text else ""

        result["group_id"] = child_text(root, "groupId")
        result["artifact_id"] = child_text(root, "artifactId")
        result["version"] = child_text(root, "version")
        result["packaging"] = child_text(root, "packaging") or "jar"

        props = root.find("m:properties", ns)
        if props is not None:
            for prop in ["maven.compiler.source", "maven.compiler.target",
                         "java.version", "jdk.version"]:
                val = child_text(props, prop)
                if val:
                    result["java_version"] = val
                    break

        deps = root.find("m:dependencies", ns)
        if deps is not None:
            for dep in deps.findall("m:dependency", ns):
                result["dependencies"].append({
                    "group_id": child_text(dep, "groupId"),
                    "artifact_id": child_text(dep, "artifactId"),
                    "version": child_text(dep, "version"),
                    "scope": child_text(dep, "scope") or "compile"
                })
    except ET.ParseError:
        pass
    return result


def create_maven_project(project_dir: str, group_id: str, artifact_id: str,
                         java_version: str = "17") -> bool:
    src_main_java = os.path.join(project_dir, "src", "main", "java")
    src_main_resources = os.path.join(project_dir, "src", "main", "resources")
    src_test_java = os.path.join(project_dir, "src", "test", "java")
    os.makedirs(src_main_java, exist_ok=True)
    os.makedirs(src_main_resources, exist_ok=True)
    os.makedirs(src_test_java, exist_ok=True)

    package_path = group_id.replace(".", os.sep)
    main_class_dir = os.path.join(src_main_java, package_path)
    os.makedirs(main_class_dir, exist_ok=True)
    test_class_dir = os.path.join(src_test_java, package_path)
    os.makedirs(test_class_dir, exist_ok=True)

    if "." in java_version:
        raw_version = java_version
    else:
        raw_version = java_version

    pom_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>{group_id}</groupId>
    <artifactId>{artifact_id}</artifactId>
    <version>1.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <maven.compiler.source>{raw_version}</maven.compiler.source>
        <maven.compiler.target>{raw_version}</maven.compiler.target>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.10.0</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>{raw_version}</source>
                    <target>{raw_version}</target>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
'''
    with open(os.path.join(project_dir, "pom.xml"), "w", encoding="utf-8") as f:
        f.write(pom_xml)

    class_name = "".join(word.capitalize() for word in artifact_id.split("-"))
    app_java = f'''package {group_id};

public class {class_name} {{
    public static void main(String[] args) {{
        System.out.println("Hello from {artifact_id}!");
    }}
}}
'''
    with open(os.path.join(main_class_dir, f"{class_name}.java"), "w", encoding="utf-8") as f:
        f.write(app_java)

    test_java = f'''package {group_id};

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class {class_name}Test {{
    @Test
    public void testApp() {{
        assertTrue(true);
    }}
}}
'''
    with open(os.path.join(test_class_dir, f"{class_name}Test.java"), "w", encoding="utf-8") as f:
        f.write(test_java)

    return True


def run_maven(project_dir: str, goal: str, output_callback=None):
    mvn = get_maven_command(project_dir)
    if not mvn:
        if output_callback:
            output_callback("Maven not found. Install Maven or use the wrapper.\n")
        return False
    try:
        proc = subprocess.Popen(
            [mvn, "-f", project_dir, goal],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, cwd=project_dir
        )
        for line in proc.stdout:
            if output_callback:
                output_callback(line)
        proc.wait()
        return proc.returncode == 0
    except Exception as e:
        if output_callback:
            output_callback(f"Error running Maven: {e}\n")
        return False
