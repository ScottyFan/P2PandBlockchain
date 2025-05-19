import subprocess
import tempfile
import os
import json
import logging
from typing import Dict, Any, List
from urllib.parse import urlparse
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskExecutor:
    def __init__(self):
        self.supported_languages = {
            "python": {
                "extensions": [".py"],
                "analyzers": {
                    "pylint": self._run_pylint,
                    "flake8": self._run_flake8,
                    "mypy": self._run_mypy
                }
            },
            "javascript": {
                "extensions": [".js", ".jsx"],
                "analyzers": {
                    "eslint": self._run_eslint,
                    "jshint": self._run_jshint
                }
            }
        }
    
    def execute_analysis(self, task_id: str, code_url: str, 
                        analysis_type: str) -> Dict[str, Any]:
        logger.info(f"Starting analysis for task {task_id}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                code_path = self._download_code(code_url, temp_dir)
                
                language = self._detect_language(code_path)
                
                results = self._run_analysis(
                    code_path, 
                    language, 
                    analysis_type
                )
                
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "language": language,
                    "analysis_type": analysis_type,
                    "results": results
                }
                
            except Exception as e:
                logger.error(f"Analysis failed: {e}")
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": str(e)
                }
    
    def _download_code(self, code_url: str, target_dir: str) -> str:
        parsed_url = urlparse(code_url)
        
        if "github.com" in parsed_url.netloc:
            repo_path = os.path.join(target_dir, "repo")
            cmd = ["git", "clone", "--depth", "1", code_url, repo_path]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                logger.info(f"Cloned repository from {code_url}")
                return repo_path
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to clone repository: {e}")
                raise
        else:
            raise ValueError(f"Unsupported code URL: {code_url}")
    
    def _detect_language(self, code_path: str) -> str:
        file_counts = {}
        
        for root, dirs, files in os.walk(code_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                _, ext = os.path.splitext(file)
                if ext:
                    file_counts[ext] = file_counts.get(ext, 0) + 1
        
        for language, info in self.supported_languages.items():
            language_count = sum(
                file_counts.get(ext, 0) 
                for ext in info["extensions"]
            )
            if language_count > 0:
                return language
        
        return "unknown"
    
    def _run_analysis(self, code_path: str, language: str, 
                     analysis_type: str) -> Dict[str, Any]:
        if language not in self.supported_languages:
            return {"error": f"Unsupported language: {language}"}
        
        analyzers = self.supported_languages[language]["analyzers"]
        results = {}
        
        if analysis_type == "all":
            for analyzer_name, analyzer_func in analyzers.items():
                results[analyzer_name] = analyzer_func(code_path)
        elif analysis_type in analyzers:
            results[analysis_type] = analyzers[analysis_type](code_path)
        else:
            results["error"] = f"Unknown analysis type: {analysis_type}"
        
        return results
    
    def _run_pylint(self, code_path: str) -> Dict[str, Any]:
        try:
            cmd = ["pylint", "--output-format=json", code_path]
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=300  
            )
            
            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                    return {
                        "tool": "pylint",
                        "issue_count": len(issues),
                        "issues": issues[:10]  # Limit to first 10 issues
                    }
                except json.JSONDecodeError:
                    return {
                        "tool": "pylint",
                        "error": "Failed to parse output",
                        "raw_output": result.stdout[:500]
                    }
            else:
                return {
                    "tool": "pylint",
                    "issue_count": 0,
                    "issues": []
                }
                
        except subprocess.TimeoutExpired:
            return {"tool": "pylint", "error": "Analysis timeout"}
        except Exception as e:
            return {"tool": "pylint", "error": str(e)}
    
    def _run_flake8(self, code_path: str) -> Dict[str, Any]:
        try:
            cmd = ["flake8", "--format=json", code_path]
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=300
            )
            
            if result.stdout:
                try:
                    lines = result.stdout.strip().split('\n')
                    issues = []
                    for line in lines[:10]:  # Limit to first 10
                        if line:
                            parts = line.split(':')
                            if len(parts) >= 4:
                                issues.append({
                                    "file": parts[0],
                                    "line": parts[1],
                                    "column": parts[2],
                                    "message": ':'.join(parts[3:])
                                })
                    
                    return {
                        "tool": "flake8",
                        "issue_count": len(lines),
                        "issues": issues
                    }
                except Exception:
                    return {
                        "tool": "flake8",
                        "error": "Failed to parse output"
                    }
            else:
                return {
                    "tool": "flake8",
                    "issue_count": 0,
                    "issues": []
                }
                
        except subprocess.TimeoutExpired:
            return {"tool": "flake8", "error": "Analysis timeout"}
        except Exception as e:
            return {"tool": "flake8", "error": str(e)}
    
    def _run_mypy(self, code_path: str) -> Dict[str, Any]:
        try:
            cmd = ["mypy", "--json-report", "-", code_path]
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=300
            )
            if result.stderr:
                lines = result.stderr.strip().split('\n')
                issues = []
                for line in lines[:10]: 
                    if line and ':' in line:
                        issues.append({"message": line})
                
                return {
                    "tool": "mypy",
                    "issue_count": len(lines),
                    "issues": issues
                }
            else:
                return {
                    "tool": "mypy",
                    "issue_count": 0,
                    "issues": []
                }
                
        except subprocess.TimeoutExpired:
            return {"tool": "mypy", "error": "Analysis timeout"}
        except Exception as e:
            return {"tool": "mypy", "error": str(e)}
    
    def _run_eslint(self, code_path: str) -> Dict[str, Any]:
        return {
            "tool": "eslint",
            "error": "ESLint not implemented yet"
        }
    
    def _run_jshint(self, code_path: str) -> Dict[str, Any]:
        return {
            "tool": "jshint",
            "error": "JSHint not implemented yet"
        }
