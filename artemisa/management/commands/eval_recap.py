"""Grounding eval for the AI recap: generate N real recaps and check each one.

    python manage.py eval_recap --runs 10 --out evals/recap_grounding.json

Uses the demo competition unless --competition is given. Each run is a real Claude call
(needs an API key and costs money), so N is small. The result is the share of recaps
whose every number and name is found in the standings (see artemisa/grounding.py).
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from artemisa import recap
from artemisa.grounding import grounding_issues
from artemisa.models import Competition


class Command(BaseCommand):
    help = "Generate N AI recaps for one competition and report how many pass the grounding check."

    def add_arguments(self, parser):
        parser.add_argument("--runs", type=int, default=5, help="How many recaps to generate (each is a paid API call).")
        parser.add_argument("--competition", type=int, help="Competition id (default: the demo competition).")
        parser.add_argument("--out", help="Write the full results (every recap and issue) to this JSON file.")

    def handle(self, *args, runs, competition, out, **options):
        if competition:
            target = Competition.objects.filter(pk=competition).first()
        else:
            target = Competition.objects.filter(is_demo=True).first()
        if target is None:
            raise CommandError("Competition not found (run seed_demo for the demo).")
        prompt_input = recap.recap_input(target)
        if prompt_input is None:
            raise CommandError(f"'{target.name}' has no scores yet.")

        results = []
        for run in range(1, runs + 1):
            try:
                text = recap.generate_recap(prompt_input)
            except Exception as error:  # count failed calls instead of stopping the eval
                results.append({"run": run, "error": str(error), "issues": [], "recap": None})
                self.stdout.write(f"run {run}: API error: {error}")
                continue
            issues = grounding_issues(text, prompt_input)
            results.append({"run": run, "error": None, "issues": issues, "recap": text})
            self.stdout.write(f"run {run}: {'PASS' if not issues else 'FAIL ' + '; '.join(issues)}")

        completed = [r for r in results if r["error"] is None]
        passed = [r for r in completed if not r["issues"]]
        summary = {
            "model": recap.RECAP_MODEL,
            "competition": target.name,
            "ran_at": timezone.now().isoformat(timespec="seconds"),
            "runs": runs,
            "completed": len(completed),
            "grounded": len(passed),
        }
        self.stdout.write(self.style.SUCCESS(
            f"{len(passed)}/{len(completed)} recaps grounded ({recap.RECAP_MODEL}, {target.name})"
        ))
        if out:
            path = Path(out)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({**summary, "input": prompt_input, "results": results},
                                       indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            self.stdout.write(f"Results written to {path}")
