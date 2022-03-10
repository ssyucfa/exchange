import typing


if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    from .views import ListGameView, GameWinnerView

    app.router.add_view("/admin.fetch_games", ListGameView)
    app.router.add_view("/admin.fetch_game_stats", GameWinnerView)
