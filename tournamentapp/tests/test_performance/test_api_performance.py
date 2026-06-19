import time
from django.test import TestCase, Client
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from tournamentapp.models import (
    Tournament, Team, Player, Match, MatchEvent, Field
)
from accounts.models import AppUser
from django.utils import timezone
from datetime import timedelta


class LeaderboardPerformanceTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = AppUser.objects.create_user(
            email="testuser@abv.bg",
            password="password1234"
        )

        self.client.force_login(self.user)

        self.tournament = Tournament.objects.create(
            name="Perf Tournament",
            owner=self.user,
        )

        self.teams = []
        for i in range(10):
            self.teams.append(
                Team.objects.create(
                    name=f"Team {i}",
                    tournament=self.tournament,
                    tournament_points=i,
                )
            )

        self.field = Field.objects.create(
            name="Field A",
            tournament=self.tournament,
            owner=self.user
        )

        self.match = Match.objects.create(
            home_team=self.teams[0],
            away_team=self.teams[1],
            start_time=timezone.now() - timedelta(days=1),
            is_finished=True,
            field=self.field,
            tournament=self.tournament,
        )

        self.player = Player.objects.create(
            name="Star Player",
            team=self.teams[0]
        )

        # simulate scoring pressure
        for _ in range(20):
            MatchEvent.objects.create(
                match=self.match,
                event_type="goal",
                team=self.teams[0],
                player=self.player
            )

    def test_leaderboard_query_count(self):
        url = reverse("leaderboard", args=[self.tournament.id])

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        print("\nLeaderboard queries:", len(ctx))

        for q in ctx.captured_queries:
            print(q["sql"])

        self.assertLessEqual(
            len(ctx),
            15,
            "Leaderboard is too heavy (N+1 or inefficient loops)"
        )

    def test_leaderboard_response_time(self):
        url = reverse("leaderboard", args=[self.tournament.id])

        start = time.perf_counter()
        response = self.client.get(url)
        elapsed = time.perf_counter() - start

        self.assertEqual(response.status_code, 200)

        print("\nLeaderboard time:", elapsed)

        self.assertLess(
            elapsed,
            0.5,
            "Leaderboard too slow for production load"
        )

# small_count = ...
# large_count = ...

# self.assertLessEqual(
#     large_count - small_count,
#     3,
#     "Queries scale with data size (possible N+1)"
# )