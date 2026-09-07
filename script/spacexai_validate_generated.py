"""Validate generated SpaceXAI wiring in a disposable native Core checkout."""

from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


def run_command(name: str, command: list[str]) -> None:
    """Run one native validator and preserve its complete output."""
    print(f"Running {name}: {' '.join(command)}", flush=True)
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    output = result.stdout + result.stderr
    Path(f"generated-{name}.txt").write_text(output)
    print(output, end="", flush=True)
    if result.returncode:
        raise RuntimeError(f"{name} failed with exit code {result.returncode}")


def validate_integration(root: Path) -> dict[str, Any]:
    """Accept only a clean result or the exact unpublished-dependency finding."""
    sys.path.insert(0, str(root))
    from script.hassfest import __main__ as hassfest  # noqa: PLC0415
    from script.hassfest.model import Config, Integration  # noqa: PLC0415

    reports: list[dict[str, Any]] = []
    original_report = hassfest.print_integrations_status

    def record_report(
        config: Config,
        integrations: list[Integration],
        *,
        show_fixable_errors: bool = True,
    ) -> None:
        """Capture all findings, including fixable findings hidden by the CLI."""
        reports.append(
            {
                "general_errors": [asdict(error) for error in config.errors],
                "integrations": [
                    {
                        "domain": integration.domain,
                        "errors": [asdict(error) for error in integration.errors],
                        "warnings": [
                            asdict(warning) for warning in integration.warnings
                        ],
                    }
                    for integration in integrations
                ],
            }
        )
        original_report(config, integrations, show_fixable_errors=True)

    original_argv = sys.argv
    hassfest.print_integrations_status = record_report
    sys.argv = [
        "hassfest",
        "--action",
        "validate",
        "--integration-path",
        "homeassistant/components/spacexai",
    ]
    try:
        exit_code = hassfest.main()
    finally:
        hassfest.print_integrations_status = original_report
        sys.argv = original_argv

    expected = [
        {
            "general_errors": [],
            "integrations": [
                {
                    "domain": "spacexai",
                    "errors": [
                        {
                            "plugin": "quality_scale",
                            "error": (
                                "Quality scale tier bronze requires quality scale rules "
                                "to be met:\n  dependency-transparency: todo"
                            ),
                            "fixable": False,
                        }
                    ],
                    "warnings": [],
                }
            ],
        }
    ]
    result = {"exit_code": exit_code, "reports": reports}
    Path("generated-hassfest-findings.json").write_text(json.dumps(result, indent=2))
    if exit_code == 0 and reports == [{"general_errors": [], "integrations": []}]:
        return {**result, "status": "passed"}
    if exit_code == 1 and reports == expected:
        return {**result, "status": "blocked_only_on_dependency_publication"}
    raise RuntimeError(
        "Hassfest reported unexpected findings; inspect the JSON evidence"
    )


def main() -> None:
    """Regenerate native metadata and require an unchanged tracked checkout."""
    root = Path.cwd()
    if not (root / "homeassistant/components/spacexai/manifest.json").is_file():
        raise RuntimeError("Run from the disposable Core checkout being validated")
    run_command("tracked-before", ["git", "diff", "--exit-code", "HEAD", "--"])
    run_command(
        "requirements-generation", [sys.executable, "-m", "script.gen_requirements_all"]
    )
    run_command(
        "hassfest-generation",
        [
            sys.executable,
            "-m",
            "script.hassfest",
            "--action",
            "generate",
            "--plugins",
            "translations,codeowners,config_flow,mypy_config",
        ],
    )
    run_command("tracked-after", ["git", "diff", "--exit-code", "HEAD", "--"])
    run_command(
        "requirements-validation",
        [sys.executable, "-m", "script.gen_requirements_all", "validate"],
    )
    result = validate_integration(root)
    run_command("tracked-final", ["git", "diff", "--exit-code", "HEAD", "--"])
    Path("generated-validation.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
