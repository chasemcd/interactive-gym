from server import remote_game


class GameCallback:
    def on_episode_start(self, remote_game: remote_game.RemoteGame):
        pass

    def on_episode_end(self, remote_game: remote_game.RemoteGame):
        pass

    def on_game_tick(self, remote_game: remote_game.RemoteGame):
        pass

    def on_graphics_start(self, remote_game: remote_game.RemoteGame):
        pass

    def on_graphics_end(self, remote_game: remote_game.RemoteGame):
        pass

    def on_waitroom_start(self, remote_game: remote_game.RemoteGame):
        pass

    def on_waitroom_join(self, remote_game: remote_game.RemoteGame):
        pass

    def on_waitroom_end(self, remote_game: remote_game.RemoteGame):
        pass

    def on_waitroom_timeout(self, remote_game: remote_game.RemoteGame):
        pass

    def on_game_end(self, remote_game: remote_game.RemoteGame):
        pass
