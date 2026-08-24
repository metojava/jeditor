import os
import re
import subprocess
import platform
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class JavaInstallation:
    path: str
    version: str
    is_jdk: bool
    vendor: str = "unknown"

    def major_version(self) -> int:
        match = re.search(r'(\d+)', self.version)
        return int(match.group(1)) if match else 0

    def display_name(self) -> str:
        jdk_str = "JDK" if self.is_jdk else "JRE"
        return f"Java {self.version} ({jdk_str}) - {self.path}"


class JavaFinder:
    def find_all(self) -> List[JavaInstallation]:
        found: List[JavaInstallation] = []
        seen = set()

        for candidate in self._get_candidates():
            normalized = os.path.normpath(candidate)
            if normalized in seen:
                continue
            seen.add(normalized)
            inst = self._inspect(candidate)
            if inst:
                found.append(inst)

        found.sort(key=lambda x: x.major_version(), reverse=True)
        return found

    def recommend(self, found: Optional[List[JavaInstallation]] = None) -> Optional[JavaInstallation]:
        if found is None:
            found = self.find_all()

        jdks = [j for j in found if j.is_jdk]
        if jdks:
            lts_versions = {8, 11, 17, 21}
            for jdk in jdks:
                if jdk.major_version() in lts_versions:
                    return jdk
            return jdks[0]

        if found:
            return found[0]
        return None

    def _get_candidates(self) -> List[str]:
        candidates = []

        java_home = os.environ.get("JAVA_HOME", "").strip()
        if java_home and os.path.isdir(java_home):
            candidates.append(java_home)
            candidates.append(os.path.join(java_home, "bin"))

        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        for d in path_dirs:
            d = d.strip()
            if not d:
                continue
            java_exe = os.path.join(d, "java")
            if os.path.isfile(java_exe) or os.path.isfile(java_exe + ".exe"):
                candidates.append(d)
            java_exe2 = os.path.join(d, "java.exe")
            if os.path.isfile(java_exe2):
                candidates.append(d)

        if platform.system() == "Windows":
            for base in [os.environ.get("ProgramFiles", "C:\\Program Files"),
                         os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")]:
                java_dir = os.path.join(base, "Java")
                if os.path.isdir(java_dir):
                    for entry in os.listdir(java_dir):
                        full = os.path.join(java_dir, entry)
                        if os.path.isdir(full):
                            candidates.append(full)
                            candidates.append(os.path.join(full, "bin"))

            try:
                import winreg
                for key_path in [
                    r"SOFTWARE\JavaSoft\Java Development Kit",
                    r"SOFTWARE\JavaSoft\Java Runtime Environment",
                    r"SOFTWARE\JavaSoft\JDK",
                    r"SOFTWARE\JavaSoft\JRE",
                ]:
                    try:
                        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                        try:
                            i = 0
                            while True:
                                subkey_name = winreg.EnumKey(key, i)
                                subkey = winreg.OpenKey(key, subkey_name)
                                try:
                                    java_home_val, _ = winreg.QueryValueEx(subkey, "JavaHome")
                                    if java_home_val and os.path.isdir(java_home_val):
                                        candidates.append(java_home_val)
                                except FileNotFoundError:
                                    pass
                                winreg.CloseKey(subkey)
                                i += 1
                        except OSError:
                            pass
                        winreg.CloseKey(key)
                    except FileNotFoundError:
                        pass
            except ImportError:
                pass

            for home in [os.environ.get("USERPROFILE"), os.environ.get("HOMEDRIVE") + "\\"]:
                if home:
                    for entry in [".jdks", ".sdkman", "sdkman"]:
                        sdk_dir = os.path.join(home, entry)
                        if os.path.isdir(sdk_dir):
                            candidates.append(sdk_dir)

        return candidates

    def _inspect(self, candidate: str) -> Optional[JavaInstallation]:
        java_exe = self._find_java_exe(candidate)
        if not java_exe:
            return None

        try:
            result = subprocess.run(
                [java_exe, "-version"],
                capture_output=True, text=True, timeout=10
            )
            version_output = result.stderr or result.stdout
        except (subprocess.TimeoutExpired, OSError):
            return None

        version = self._parse_version(version_output)
        if not version:
            return None

        is_jdk = False
        if version_output:
            is_jdk = ("openjdk" in version_output.lower() or
                      " hotspot" in version_output.lower() or
                      "jdk" in candidate.lower() or
                      "jdk" in version.lower() or
                      "(build" in version_output)

        vendor = "unknown"
        if "temurin" in version_output.lower() or "adoptium" in version_output.lower():
            vendor = "Eclipse Temurin"
        elif "amazon" in version_output.lower() or "corretto" in version_output.lower():
            vendor = "Amazon Corretto"
        elif "zulu" in version_output.lower():
            vendor = "Azul Zulu"
        elif "graalvm" in version_output.lower() or "graal" in version_output.lower():
            vendor = "GraalVM"
        elif "openjdk" in version_output.lower():
            vendor = "OpenJDK"
        elif "oracle" in version_output.lower():
            vendor = "Oracle"
        elif "ibm" in version_output.lower():
            vendor = "IBM"
        elif "sapmachine" in version_output.lower():
            vendor = "SAPMachine"
        elif "microsoft" in version_output.lower():
            vendor = "Microsoft"

        return JavaInstallation(
            path=os.path.dirname(java_exe),
            version=version,
            is_jdk=True,
            vendor=vendor
        )

    def _find_java_exe(self, candidate: str) -> Optional[str]:
        if os.path.isfile(candidate):
            return candidate
        if os.path.isdir(candidate):
            for name in ["java", "java.exe"]:
                full = os.path.join(candidate, name)
                if os.path.isfile(full):
                    return full
            for name in ["java", "java.exe"]:
                full = os.path.join(candidate, "bin", name)
                if os.path.isfile(full):
                    return full
        return None

    def _parse_version(self, output: str) -> Optional[str]:
        if not output:
            return None
        patterns = [
            r'(?:openjdk|java|jdk)\s+version\s+"?([\d._]+-?[^"\s]*)"?',
            r'(\d+\.\d+\.\d+[\d._]*)',
            r'(\d+)',
        ]
        for pat in patterns:
            match = re.search(pat, output, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
