import os
from typing import Optional, Callable
from . import maven_support
from . import gradle_support


class ProjectManager:
    PLAIN = "plain"
    MAVEN = "maven"
    GRADLE = "gradle"

    def __init__(self, output_callback: Optional[Callable] = None):
        self.project_dir: Optional[str] = None
        self.project_type: Optional[str] = None
        self.output_callback = output_callback

    def set_output_callback(self, callback: Callable):
        self.output_callback = callback

    def open_project(self, directory: str) -> str:
        self.project_dir = directory
        self.project_type = self.detect_type(directory)
        return self.project_type

    def detect_type(self, directory: str) -> str:
        if maven_support.is_maven_project(directory):
            return self.MAVEN
        elif gradle_support.is_gradle_project(directory):
            return self.GRADLE
        return self.PLAIN

    def get_project_info(self) -> dict:
        if not self.project_dir:
            return {"type": self.PLAIN, "name": "", "java_version": ""}
        info = {"type": self.project_type, "name": os.path.basename(self.project_dir), "java_version": ""}
        if self.project_type == self.MAVEN:
            pom = maven_support.parse_pom(os.path.join(self.project_dir, "pom.xml"))
            info["artifact"] = pom.get("artifact_id", "")
            info["group"] = pom.get("group_id", "")
            info["version"] = pom.get("version", "")
            info["java_version"] = pom.get("java_version", "")
        elif self.project_type == self.GRADLE:
            ginfo = gradle_support.parse_build_gradle(self.project_dir)
            info["artifact"] = ginfo.get("artifact", "")
            info["group"] = ginfo.get("group", "")
            info["version"] = ginfo.get("version", "")
            info["java_version"] = ginfo.get("java_version", "")
        return info

    def build_project(self):
        if not self.project_dir:
            return
        if self.project_type == self.MAVEN:
            maven_support.run_maven(self.project_dir, "compile", self.output_callback)
        elif self.project_type == self.GRADLE:
            gradle_support.run_gradle(self.project_dir, "compileJava", self.output_callback)

    def run_project(self):
        if not self.project_dir:
            return
        if self.project_type == self.MAVEN:
            maven_support.run_maven(self.project_dir, "exec:java", self.output_callback)
        elif self.project_type == self.GRADLE:
            gradle_support.run_gradle(self.project_dir, "run", self.output_callback)

    def test_project(self):
        if not self.project_dir:
            return
        if self.project_type == self.MAVEN:
            maven_support.run_maven(self.project_dir, "test", self.output_callback)
        elif self.project_type == self.GRADLE:
            gradle_support.run_gradle(self.project_dir, "test", self.output_callback)

    def clean_project(self):
        if not self.project_dir:
            return
        if self.project_type == self.MAVEN:
            maven_support.run_maven(self.project_dir, "clean", self.output_callback)
        elif self.project_type == self.GRADLE:
            gradle_support.run_gradle(self.project_dir, "clean", self.output_callback)

    def package_project(self):
        if not self.project_dir:
            return
        if self.project_type == self.MAVEN:
            maven_support.run_maven(self.project_dir, "package", self.output_callback)
        elif self.project_type == self.GRADLE:
            gradle_support.run_gradle(self.project_dir, "build", self.output_callback)

    def create_maven_project(self, directory: str, group_id: str,
                              artifact_id: str, java_version: str) -> bool:
        ok = maven_support.create_maven_project(directory, group_id, artifact_id, java_version)
        if ok:
            self.open_project(directory)
        return ok

    def create_gradle_project(self, directory: str, group_id: str,
                               artifact_id: str, java_version: str,
                               use_kotlin_dsl: bool = False) -> bool:
        ok = gradle_support.create_gradle_project(directory, group_id, artifact_id,
                                                   java_version, use_kotlin_dsl)
        if ok:
            self.open_project(directory)
        return ok

    def get_source_folders(self) -> list:
        if not self.project_dir:
            return []
        folders = []

        if self.project_type == self.MAVEN:
            candidates = [
                os.path.join(self.project_dir, "src", "main", "java"),
                os.path.join(self.project_dir, "src", "test", "java"),
                os.path.join(self.project_dir, "src", "main", "resources"),
            ]
        elif self.project_type == self.GRADLE:
            candidates = [
                os.path.join(self.project_dir, "src", "main", "java"),
                os.path.join(self.project_dir, "src", "test", "java"),
                os.path.join(self.project_dir, "src", "main", "resources"),
                os.path.join(self.project_dir, "src", "main", "kotlin"),
                os.path.join(self.project_dir, "src", "main", "groovy"),
            ]
        else:
            candidates = [self.project_dir]

        for c in candidates:
            if os.path.isdir(c):
                folders.append(c)

        if not folders:
            folders.append(self.project_dir)

        return folders
