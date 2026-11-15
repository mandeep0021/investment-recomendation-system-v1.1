from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DeploymentConfigTests(unittest.TestCase):
    def test_dockerfile_runs_as_non_root_and_has_healthcheck(self):
        dockerfile = (ROOT / "Dockerfile1").read_text(encoding="utf-8")
        self.assertIn("USER app", dockerfile)
        self.assertIn("HEALTHCHECK", dockerfile)
        self.assertIn("--server.address=0.0.0.0", dockerfile)

    def test_compose_binds_only_to_loopback_and_hardens_container(self):
        compose = (ROOT / "Docker-compose1.yml").read_text(encoding="utf-8")
        self.assertIn('"127.0.0.1:8501:8501"', compose)
        self.assertIn("read_only: true", compose)
        self.assertIn("no-new-privileges:true", compose)
        self.assertIn("cap_drop:", compose)

    def test_dockerignore_excludes_secrets_and_git_history(self):
        dockerignore = (ROOT / ".Dockerignore1").read_text(encoding="utf-8")
        self.assertIn(".git", dockerignore)
        self.assertIn(".env", dockerignore)
        self.assertIn(".streamlit/secrets.toml", dockerignore)


if __name__ == "__main__":
    unittest.main()
