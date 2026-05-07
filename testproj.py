import ghost_engine.core.logger as logger
import ghost_engine.core.settings

settings = ghost_engine.core.settings.Settings()
win_width = int(settings.get_setting("window_width", 800))
win_height = int(settings.get_setting("window_height", 600))

logger.setup()
ghost_engine.set_logging_level(ghost_engine.LoggingLevels.DEBUG)
window = ghost_engine.init_window(window_width=win_width, window_height=win_height)

while not window.should_close():
    window.update()

window.terminate()

settings.save_config()