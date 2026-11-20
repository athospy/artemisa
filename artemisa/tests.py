import io
import json
from types import SimpleNamespace
from unittest import mock

from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from mcp.server.mcpserver.exceptions import ToolError

from . import mcp_tools, recap
from .grounding import grounding_issues
from .management.commands.seed_demo import DEMO_RECAP_FILE
from .management.commands.mcp import build_server
from .models import Archer, Category, Competition, Registration, Score, validate_score


def make_competition(name, is_demo=False):
    return Competition.objects.create(
        name=name, description="", event_date=timezone.now(), location="Range",
        code=name.upper(), is_demo=is_demo,
    )


def register_with_arrows(competition, category, archer_name, arrows):
    archer = Archer.objects.create(name=archer_name, club_name="Club", email=f"{archer_name}@example.com")
    registration = Registration.objects.create(competition=competition, category=category, archer=archer)
    for i, arrow in enumerate(arrows):
        Score.objects.create(registration=registration, end_number=i // 6 + 1, shoot_number=i % 6 + 1, score=arrow)
    return registration


class PublicDemoAccessTests(TestCase):
    """Visitors can see the demo competition (results, timer) and nothing else."""

    def setUp(self):
        self.category = Category.objects.create(name="Recurve Bow Women", code="RW")
        self.demo = make_competition("Demo", is_demo=True)
        self.real = make_competition("Real event")
        register_with_arrows(self.demo, self.category, "Demo Archer", ["X", "9", "8", "M", "10", "7"])
        register_with_arrows(self.real, self.category, "Real Archer", ["10", "10", "10", "10", "10", "10"])
        self.user = User.objects.create_user("organizer", password="test-pass-123")

    def leaderboard(self, body):
        return self.client.post(reverse("result_category"), json.dumps(body), content_type="application/json")

    # --- pages -----------------------------------------------------------------

    def test_demo_page_is_public_and_read_only(self):
        response = self.client.get(reverse("demo"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demo")
        self.assertContains(response, reverse("result_screen", args=[self.demo.id]))
        self.assertContains(response, reverse("shoot_timer", args=[self.demo.id]))
        self.assertContains(response, reverse("match_recap", args=[self.demo.id]))
        self.assertNotContains(response, reverse("compete", args=[self.demo.id]))

    def test_demo_page_404_when_no_demo_exists(self):
        self.demo.delete()
        self.assertEqual(self.client.get(reverse("demo")).status_code, 404)

    def test_demo_page_does_not_change_the_scorers_session(self):
        # select_competition stores the competition scores are saved into; the demo
        # page must not switch it, or a scorer would save into the demo by mistake.
        self.client.force_login(self.user)
        self.client.get(reverse("select_competition", args=[self.real.id]))
        before = self.client.session["current_competition"]
        self.client.get(reverse("demo"))
        self.assertEqual(self.client.session["current_competition"], before)

    def test_visitor_can_open_demo_results_timer_and_recap(self):
        for name in ("result_screen", "shoot_timer", "match_recap"):
            response = self.client.get(reverse(name, args=[self.demo.id]))
            self.assertEqual(response.status_code, 200, name)

    def test_visitor_is_sent_to_login_for_real_competition_pages(self):
        for name in ("result_screen", "shoot_timer", "compete", "match_recap"):
            response = self.client.get(reverse(name, args=[self.real.id]))
            self.assertRedirects(response, f"{reverse('login')}?next={reverse(name, args=[self.real.id])}",
                                 fetch_redirect_response=False, msg_prefix=name)

    def test_scoring_stays_private_even_for_the_demo(self):
        response = self.client.get(reverse("compete", args=[self.demo.id]))
        self.assertEqual(response.status_code, 302)

    def test_visitor_cannot_get_a_real_competition_recap(self):
        response = self.client.post(reverse("generate_match_recap", args=[self.real.id]))
        self.assertEqual(response.status_code, 403)

    def test_logged_in_user_still_opens_real_competition_pages(self):
        self.client.force_login(self.user)
        for name in ("result_screen", "shoot_timer"):
            self.assertEqual(self.client.get(reverse(name, args=[self.real.id])).status_code, 200, name)

    # --- leaderboard data ------------------------------------------------------

    def test_visitor_gets_demo_leaderboard(self):
        response = self.leaderboard({"competition_id": self.demo.id, "category_id": self.category.id})
        self.assertEqual(response.status_code, 200)
        rows = json.loads(response.json()["data"])
        # X=10, 9, 8, M=0, 10, 7
        self.assertEqual(rows, [{"name": "Demo Archer", "score": 44, "tens": 2, "xs": 1, "last_end_total": 44}])

    def test_visitor_cannot_read_real_leaderboard(self):
        response = self.leaderboard({"competition_id": self.real.id, "category_id": self.category.id})
        self.assertEqual(response.status_code, 403)

    def test_leaderboard_needs_a_competition(self):
        response = self.leaderboard({"category_id": self.category.id})
        self.assertEqual(response.status_code, 400)

    def test_leaderboard_rejects_a_non_numeric_competition(self):
        response = self.leaderboard({"competition_id": "abc", "category_id": self.category.id})
        self.assertEqual(response.status_code, 400)

    def test_leaderboard_uses_the_page_competition_not_the_session(self):
        # Bug fixed here: the session said "demo" but the page asked for the real event.
        self.client.force_login(self.user)
        self.client.get(reverse("select_competition", args=[self.demo.id]))
        response = self.leaderboard({"competition_id": self.real.id, "category_id": self.category.id})
        self.assertEqual(json.loads(response.json()["data"])[0]["name"], "Real Archer")

    def test_leaderboard_falls_back_to_session_for_old_clients(self):
        self.client.force_login(self.user)
        self.client.get(reverse("select_competition", args=[self.real.id]))
        response = self.leaderboard({"category_id": self.category.id})
        self.assertEqual(json.loads(response.json()["data"])[0]["name"], "Real Archer")

    # --- home, sign-up ------------------------------------------------------------

    def test_home_shows_demo_button_to_visitors(self):
        response = self.client.get(reverse("index"))
        self.assertContains(response, "Try the live demo")

    def test_home_hides_demo_button_when_there_is_no_demo(self):
        self.demo.delete()
        self.assertNotContains(self.client.get(reverse("index")), "Try the live demo")

    def test_home_shows_organizer_buttons_when_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("index"))
        self.assertContains(response, "View Competitions")
        self.assertNotContains(response, "Try the live demo")

    def test_public_sign_up_is_closed(self):
        self.assertEqual(self.client.get("/register/").status_code, 404)
        self.assertNotContains(self.client.get(reverse("login")), "Register here")


def fake_claude_response(text="Lucía wins on tens.", stop_reason="end_turn"):
    return SimpleNamespace(stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=text)])


@mock.patch("artemisa.recap.anthropic.Anthropic")
class SavedRecapTests(TestCase):
    """The AI recap is saved and reused; visitors never cause an API call."""

    def setUp(self):
        self.category = Category.objects.create(name="Recurve Bow Women", code="RW")
        self.demo = make_competition("Demo", is_demo=True)
        self.real = make_competition("Real event")
        self.registration = register_with_arrows(self.real, self.category, "Real Archer", ["10", "9", "X", "8", "7", "M"])
        register_with_arrows(self.demo, self.category, "Demo Archer", ["9"] * 6)
        self.user = User.objects.create_user("organizer", password="test-pass-123")

    def generate(self, competition):
        return self.client.post(reverse("generate_match_recap", args=[competition.id]))

    def test_first_request_calls_claude_and_saves_the_recap(self, client_class):
        create = client_class.return_value.beta.messages.create
        create.return_value = fake_claude_response("A great day.")
        self.client.force_login(self.user)

        response = self.generate(self.real)

        self.assertEqual(response.json(), {"recap": "A great day."})
        self.real.refresh_from_db()
        self.assertEqual(self.real.ai_recap, "A great day.")
        self.assertEqual(self.real.ai_recap_input, recap.recap_input(self.real))
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs["model"], "claude-opus-5-5")
        self.assertEqual(kwargs["fallbacks"], "default")
        self.assertIn("Real Archer (44 pts, 2 tens, 1 Xs)", kwargs["messages"][0]["content"])

    def test_unchanged_standings_reuse_the_saved_recap(self, client_class):
        create = client_class.return_value.beta.messages.create
        create.return_value = fake_claude_response("First.")
        self.client.force_login(self.user)
        self.generate(self.real)
        create.return_value = fake_claude_response("Second.")

        self.assertEqual(self.generate(self.real).json(), {"recap": "First."})
        self.assertEqual(create.call_count, 1)

    def test_changed_scores_make_a_new_recap(self, client_class):
        create = client_class.return_value.beta.messages.create
        create.return_value = fake_claude_response("First.")
        self.client.force_login(self.user)
        self.generate(self.real)
        Score.objects.filter(registration=self.registration, shoot_number=6).update(score="10")
        create.return_value = fake_claude_response("Second.")

        self.assertEqual(self.generate(self.real).json(), {"recap": "Second."})
        self.assertEqual(create.call_count, 2)

    def test_visitor_gets_the_saved_demo_recap_without_an_api_call(self, client_class):
        self.demo.ai_recap = "Saved demo recap."
        self.demo.ai_recap_input = recap.recap_input(self.demo)
        self.demo.save()

        self.assertEqual(self.generate(self.demo).json(), {"recap": "Saved demo recap."})
        page = self.client.get(reverse("match_recap", args=[self.demo.id]))
        self.assertContains(page, "Saved demo recap.")
        self.assertNotContains(page, "generate_recap_btn")
        client_class.assert_not_called()

    def test_visitor_never_triggers_generation(self, client_class):
        response = self.generate(self.demo)  # no saved recap yet
        self.assertEqual(response.status_code, 404)
        self.assertContains(self.client.get(reverse("match_recap", args=[self.demo.id])),
                            "No AI recap has been written")
        client_class.assert_not_called()

    def test_stale_saved_recap_is_not_shown_to_visitors(self, client_class):
        self.demo.ai_recap = "Old recap."
        self.demo.ai_recap_input = "standings that no longer match"
        self.demo.save()
        self.assertEqual(self.generate(self.demo).status_code, 404)
        self.assertNotContains(self.client.get(reverse("match_recap", args=[self.demo.id])), "Old recap.")

    def test_logged_in_user_sees_the_button_until_a_recap_is_saved(self, client_class):
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse("match_recap", args=[self.real.id])), "generate_recap_btn")

    def test_api_error_returns_502_and_saves_nothing(self, client_class):
        client_class.return_value.beta.messages.create.side_effect = RuntimeError("network down")
        self.client.force_login(self.user)
        with self.assertLogs("artemisa.views", level="ERROR"):
            response = self.generate(self.real)
        self.assertEqual(response.status_code, 502)
        self.real.refresh_from_db()
        self.assertEqual(self.real.ai_recap, "")

    def test_refusal_returns_502_and_saves_nothing(self, client_class):
        client_class.return_value.beta.messages.create.return_value = fake_claude_response("", stop_reason="refusal")
        self.client.force_login(self.user)
        with self.assertLogs("artemisa.views", level="ERROR"):
            self.assertEqual(self.generate(self.real).status_code, 502)
        self.real.refresh_from_db()
        self.assertEqual(self.real.ai_recap, "")

    def test_no_scores_returns_400_without_an_api_call(self, client_class):
        empty = make_competition("Empty")
        self.client.force_login(self.user)
        self.assertEqual(self.generate(empty).status_code, 400)
        client_class.assert_not_called()


class SeedDemoTests(TestCase):
    def setUp(self):
        self.real = make_competition("Real event")
        self.category = Category.objects.create(name="Recurve Bow Women", code="RW")
        register_with_arrows(self.real, self.category, "Real Archer", ["9"] * 6)

    def test_creates_the_demo_and_reuses_existing_categories(self):
        call_command("seed_demo", stdout=open("/dev/null", "w"))
        demo = Competition.objects.get(is_demo=True)
        self.assertEqual(Registration.objects.filter(competition=demo).count(), 16)
        self.assertEqual(Score.objects.filter(registration__competition=demo).count(), 16 * 36)
        self.assertEqual(Category.objects.filter(code="RW").count(), 1)  # reused, not duplicated

    def test_rerun_resets_only_the_demo(self):
        call_command("seed_demo", stdout=open("/dev/null", "w"))
        call_command("seed_demo", stdout=open("/dev/null", "w"))
        self.assertEqual(Competition.objects.filter(is_demo=True).count(), 1)
        self.assertEqual(Score.objects.filter(registration__competition__is_demo=True).count(), 16 * 36)
        self.assertEqual(Score.objects.filter(registration__competition=self.real).count(), 6)

    def test_every_arrow_is_a_valid_score(self):
        call_command("seed_demo", stdout=open("/dev/null", "w"))
        for value in Score.objects.values_list("score", flat=True).distinct():
            validate_score(value)  # raises ValidationError if not 0-10, X or M

    def test_demo_gets_the_committed_ai_recap(self):
        # Fails if the demo data changes without rerunning `seed_demo --refresh-recap`.
        call_command("seed_demo", stdout=open("/dev/null", "w"))
        demo = Competition.objects.get(is_demo=True)
        self.assertTrue(demo.ai_recap)
        self.assertEqual(recap.saved_recap(demo, recap.recap_input(demo)), demo.ai_recap)

    def test_recurve_women_top_two_tie_and_the_leader_wins_on_tens(self):
        call_command("seed_demo", stdout=open("/dev/null", "w"))
        demo = Competition.objects.get(is_demo=True)
        response = self.client.post(
            reverse("result_category"),
            json.dumps({"competition_id": demo.id, "category_id": self.category.id}),
            content_type="application/json",
        )
        first, second = json.loads(response.json()["data"])[:2]
        self.assertEqual(first["score"], second["score"])
        self.assertGreater(first["tens"], second["tens"])


class McpToolsTests(TestCase):
    """The read-only tools behind `manage.py mcp` (called directly, no MCP client)."""

    def setUp(self):
        self.recurve = Category.objects.create(name="Recurve Bow Women", code="RW")
        self.compound = Category.objects.create(name="Compound Bow Men", code="CM")
        self.event = make_competition("Spring Open")
        # Tie on 50 points and on last end; Ana wins on 10s (5 vs 2) even though
        # "Abril" sorts first by name, so the test fails if the 10s tiebreak is lost.
        self.ana = register_with_arrows(self.event, self.recurve, "Ana Ruiz", ["10", "X", "10", "M", "10", "10"])
        register_with_arrows(self.event, self.recurve, "Abril Sosa", ["10", "10", "9", "9", "6", "6"])
        register_with_arrows(self.event, self.compound, "Carlos Paz", ["9"] * 6 + ["8"] * 6)

    def test_list_competitions_has_categories_and_no_emails(self):
        [competition] = mcp_tools.list_competitions()
        self.assertEqual(competition["name"], "Spring Open")
        self.assertEqual(competition["categories"], [
            {"name": "Compound Bow Men", "code": "CM", "archers": 1},
            {"name": "Recurve Bow Women", "code": "RW", "archers": 2},
        ])
        self.assertNotIn("@", json.dumps(mcp_tools.list_competitions()))

    def test_leaderboard_uses_the_tiebreaker_and_matches_the_results_screen(self):
        board = mcp_tools.get_leaderboard(self.event.id, "rw")
        ranking = board["categories"][0]["ranking"]
        self.assertEqual([(r["rank"], r["name"], r["score"], r["tens"]) for r in ranking],
                         [(1, "Ana Ruiz", 50, 5), (2, "Abril Sosa", 50, 2)])
        self.client.force_login(User.objects.create_user("u", password="test-pass-123"))
        screen = self.client.post(reverse("result_category"),
                                  json.dumps({"competition_id": self.event.id, "category_id": self.recurve.id}),
                                  content_type="application/json")
        self.assertEqual([a["name"] for a in json.loads(screen.json()["data"])], ["Ana Ruiz", "Abril Sosa"])

    def test_leaderboard_without_category_returns_all(self):
        board = mcp_tools.get_leaderboard(self.event.id)
        self.assertEqual([c["code"] for c in board["categories"]], ["CM", "RW"])

    def test_scorecard_has_ends_and_running_totals(self):
        card = mcp_tools.get_archer_scorecard(self.event.id, "carlos")
        [scorecard] = card["scorecards"]
        self.assertEqual(scorecard["ends"], [
            {"end": 1, "arrows": ["9"] * 6, "end_total": 54, "running_total": 54},
            {"end": 2, "arrows": ["8"] * 6, "end_total": 48, "running_total": 102},
        ])
        self.assertEqual((scorecard["rank"], scorecard["of"], scorecard["total"]), (1, 1, 102))

    def test_errors_are_messages_for_the_model(self):
        cases = [
            (lambda: mcp_tools.get_leaderboard(9999), "No competition with id 9999"),
            (lambda: mcp_tools.get_leaderboard(self.event.id, "longbow"), "No category 'longbow'"),
            (lambda: mcp_tools.get_archer_scorecard(self.event.id, "zoe"), "No archer matching 'zoe'"),
            (lambda: mcp_tools.get_archer_scorecard(self.event.id, "s"), "matches several archers"),
        ]
        for call, message in cases:
            with self.assertRaisesMessage(ToolError, message):
                call()

    def test_match_recap_never_calls_the_api(self):
        with mock.patch("artemisa.recap.anthropic.Anthropic") as client_class:
            self.assertIsNone(mcp_tools.get_match_recap(self.event.id)["recap"])
            self.event.ai_recap = "Saved."
            self.event.ai_recap_input = recap.recap_input(self.event)
            self.event.save()
            self.assertEqual(mcp_tools.get_match_recap(self.event.id)["recap"], "Saved.")
            client_class.assert_not_called()

    def test_server_exposes_four_read_only_tools(self):
        tools = async_to_sync(build_server().list_tools)()
        self.assertEqual(sorted(t.name for t in tools),
                         ["get_archer_scorecard", "get_leaderboard", "get_match_recap", "list_competitions"])
        self.assertTrue(all(t.annotations.read_only_hint for t in tools))


class GroundingCheckTests(TestCase):
    """The AI recap may only state facts that are in its input."""

    INPUT = (
        "Competition: Spring Open 2026\n\nFinal standings by category:\n"
        "Recurve Bow Women: Ana Ruiz (297 pts, 5 tens, 4 Xs), Abril Sosa (290 pts, 2 tens, 1 Xs)\n"
        "Compound Bow Men: Carlos Paz (310 pts, 9 tens, 3 Xs)"
    )

    def test_accepts_facts_margins_and_names_from_the_input(self):
        text = ("What a Spring Open 2026! Ana Ruiz won Recurve Bow Women with 297 points and 5 tens, "
                "7 points clear of Abril Sosa. Carlos Paz's 310 topped Compound Bow Men. In Recurve, "
                "Ana's 4 Xs stood out.")
        self.assertEqual(grounding_issues(text, self.INPUT), [])

    def test_accepts_possessives(self):
        # Found by the first real eval run: "Abril Sosa' 290" was flagged as an unknown name.
        self.assertEqual(grounding_issues("Ana Ruiz's 297 beat Abril Sosa' 290.", self.INPUT), [])

    def test_flags_an_invented_number(self):
        self.assertEqual(grounding_issues("Ana Ruiz shot 299.", self.INPUT),
                         ["number not in the standings: 299"])

    def test_flags_an_invented_archer(self):
        self.assertEqual(grounding_issues("Juan Gómez was close behind.", self.INPUT),
                         ["name not in the standings: Juan Gómez"])

    def test_committed_demo_recap_is_grounded(self):
        saved = json.loads(DEMO_RECAP_FILE.read_text(encoding="utf-8"))
        self.assertEqual(grounding_issues(saved["recap"], saved["input"]), [])

    @mock.patch("artemisa.recap.anthropic.Anthropic")
    def test_seed_demo_refuses_an_ungrounded_recap(self, client_class):
        client_class.return_value.beta.messages.create.return_value = fake_claude_response("Someone shot 999.")
        before = DEMO_RECAP_FILE.read_text(encoding="utf-8")
        with self.assertRaisesMessage(CommandError, "failed the grounding check"):
            call_command("seed_demo", "--refresh-recap", stdout=open("/dev/null", "w"))
        self.assertEqual(DEMO_RECAP_FILE.read_text(encoding="utf-8"), before)

    @mock.patch("artemisa.recap.anthropic.Anthropic")
    def test_live_generation_logs_an_ungrounded_recap_but_keeps_it(self, client_class):
        client_class.return_value.beta.messages.create.return_value = fake_claude_response("Ana shot 999.")
        category = Category.objects.create(name="Recurve Bow Women", code="RW")
        event = make_competition("Event")
        register_with_arrows(event, category, "Ana Ruiz", ["9"] * 6)
        self.client.force_login(User.objects.create_user("u", password="test-pass-123"))
        with self.assertLogs("artemisa.views", level="WARNING") as logs:
            response = self.client.post(reverse("generate_match_recap", args=[event.id]))
        self.assertEqual(response.json(), {"recap": "Ana shot 999."})
        self.assertIn("number not in the standings: 999", logs.output[0])


@mock.patch("artemisa.recap.anthropic.Anthropic")
class EvalRecapCommandTests(TestCase):
    def test_reports_how_many_recaps_are_grounded(self, client_class):
        call_command("seed_demo", stdout=open("/dev/null", "w"))
        saved = json.loads(DEMO_RECAP_FILE.read_text(encoding="utf-8"))
        client_class.return_value.beta.messages.create.side_effect = [
            fake_claude_response(saved["recap"]),            # grounded
            fake_claude_response("Someone shot 999."),       # invented score
            RuntimeError("network down"),                   # failed call
        ]
        out = io.StringIO()
        call_command("eval_recap", "--runs", "3", stdout=out)
        self.assertIn("run 2: FAIL number not in the standings: 999", out.getvalue())
        self.assertIn("1/2 recaps grounded", out.getvalue())


class DatabaseConstraintTests(TestCase):
    """Migration 0007: the database itself rejects duplicates, not only the forms."""

    def setUp(self):
        self.category = Category.objects.create(name="Recurve Bow Women", code="RW")
        self.competition = make_competition("Event")
        self.registration = register_with_arrows(self.competition, self.category, "Ana Ruiz", ["9"])

    def test_one_score_per_arrow(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Score.objects.create(registration=self.registration, end_number=1, shoot_number=1, score="10")

    def test_one_registration_per_archer_category_and_competition(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Registration.objects.create(competition=self.competition, category=self.category,
                                        archer=self.registration.archer)
