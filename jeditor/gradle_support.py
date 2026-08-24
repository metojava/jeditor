import os
import subprocess
import re
from typing import Optional, List

GRADLE_WRAPPER_SCRIPTS = ["gradlew", "gradlew.bat", "gradlew.cmd"]


def is_gradle_project(project_dir: str) -> bool:
    return (os.path.isfile(os.path.join(project_dir, "build.gradle")) or
            os.path.isfile(os.path.join(project_dir, "build.gradle.kts")))


def has_gradle_wrapper(project_dir: str) -> bool:
    for script in GRADLE_WRAPPER_SCRIPTS:
        if os.path.isfile(os.path.join(project_dir, script)):
            return True
    return False


def find_gradle_command() -> Optional[str]:
    for cmd in ["gradle", "gradle.bat", "gradle.cmd"]:
        for path_dir in os.environ.get("PATH", "").split(os.pathsep):
            full = os.path.join(path_dir.strip(), cmd)
            if os.path.isfile(full):
                return full
    return None


def get_gradle_command(project_dir: str) -> Optional[str]:
    if has_gradle_wrapper(project_dir):
        for script in GRADLE_WRAPPER_SCRIPTS:
            full = os.path.join(project_dir, script)
            if os.path.isfile(full):
                return full
    return find_gradle_command()


def parse_build_gradle(project_dir: str) -> dict:
    result = {
        "group": "",
        "artifact": "",
        "version": "",
        "java_version": "",
        "plugins": [],
        "dependencies": []
    }

    for filename in ["build.gradle", "build.gradle.kts"]:
        path = os.path.join(project_dir, filename)
        if not os.path.isfile(path):
            continue

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        m = re.search(r"group\s*=\s*['\"]([^'\"]+)['\"]", content)
        if m:
            result["group"] = m.group(1)

        m = re.search(r"version\s*=\s*['\"]([^'\"]+)['\"]", content)
        if m:
            result["version"] = m.group(1)

        if filename.endswith(".kts"):
            m = re.search(r"java\s*\{[^}]*sourceCompatibility\s*=\s*JavaVersion\.VERSION_(\d+)", content)
            if m:
                result["java_version"] = m.group(1)
            m = re.search(r"sourceCompatibility\s*=\s*['\"](\d+)['\"]", content)
            if m:
                result["java_version"] = m.group(1)
        else:
            m = re.search(r"sourceCompatibility\s*=\s*['\"]?(\d+(?:\.\d+)?)['\"]?", content)
            if m:
                result["java_version"] = m.group(1)

            m = re.search(r"sourceCompatibility\s*=\s*JavaVersion\.VERSION_(\d+)", content)
            if m:
                result["java_version"] = m.group(1)

        plugin_matches = re.findall(r"id\s+['\"]([^'\"]+)['\"]", content)
        result["plugins"] = plugin_matches

        dep_matches = re.findall(r"(?:implementation|testImplementation|api|compileOnly|runtimeOnly)\s+['\"]([^:]+:[^:]+:[^'\"]+)['\"]", content)
        for dep_str in dep_matches:
            parts = dep_str.split(":")
            if len(parts) >= 3:
                result["dependencies"].append({
                    "group_id": parts[0],
                    "artifact_id": parts[1],
                    "version": parts[2]
                })
            elif len(parts) == 2:
                result["dependencies"].append({
                    "group_id": parts[0],
                    "artifact_id": parts[1],
                    "version": ""
                })

        # Extract artifact from settings or root dir name
        settings_path = os.path.join(project_dir, "settings.gradle")
        if os.path.isfile(settings_path):
            with open(settings_path, "r", encoding="utf-8") as sf:
                settings_content = sf.read()
            m = re.search(r"rootProject\.name\s*=\s*['\"]([^'\"]+)['\"]", settings_content)
            if m:
                result["artifact"] = m.group(1)

        if not result["artifact"]:
            result["artifact"] = os.path.basename(project_dir)

        break

    return result


def create_gradle_project(project_dir: str, group_id: str, artifact_id: str,
                          java_version: str = "17", use_kotlin_dsl: bool = False) -> bool:
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

    if not use_kotlin_dsl:
        build_gradle = f'''plugins {{
    id 'java'
    id 'application'
}}

group = '{group_id}'
version = '1.0-SNAPSHOT'

java {{
    sourceCompatibility = JavaVersion.VERSION_{java_version}
    targetCompatibility = JavaVersion.VERSION_{java_version}
}}

repositories {{
    mavenCentral()
}}

dependencies {{
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.0'
}}

application {{
    mainClass = '{group_id}.{artifact_id.replace("-", "").title()}'
}}

test {{
    useJUnitPlatform()
}}
'''
    else:
        build_gradle = f'''plugins {{
    java
    application
}}

group = "{group_id}"
version = "1.0-SNAPSHOT"

java {{
    sourceCompatibility = JavaVersion.VERSION_{java_version}
    targetCompatibility = JavaVersion.VERSION_{java_version}
}}

repositories {{
    mavenCentral()
}}

dependencies {{
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.0")
}}

application {{
    mainClass.set("{group_id}.{artifact_id.replace("-", "").title()}")
}}

tasks.test {{
    useJUnitPlatform()
}}
'''
    build_file = "build.gradle.kts" if use_kotlin_dsl else "build.gradle"
    with open(os.path.join(project_dir, build_file), "w", encoding="utf-8") as f:
        f.write(build_gradle)

    settings = f'''rootProject.name = '{artifact_id}'
'''
    with open(os.path.join(project_dir, "settings.gradle"), "w", encoding="utf-8") as f:
        f.write(settings)

    gradle_props = f'''org.gradle.jvmargs=-Xmx2g
'''
    with open(os.path.join(project_dir, "gradle.properties"), "w", encoding="utf-8") as f:
        f.write(gradle_props)

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


def run_gradle(project_dir: str, task: str, output_callback=None):
    gradle = get_gradle_command(project_dir)
    if not gradle:
        if output_callback:
            output_callback("Gradle not found. Install Gradle or use the wrapper.\n")
        return False
    try:
        proc = subprocess.Popen(
            [gradle, "-p", project_dir, task],
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
            output_callback(f"Error running Gradle: {e}\n")
        return False
