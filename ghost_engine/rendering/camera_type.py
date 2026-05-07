from ..core.logger import Logger

class CamType:
    def get_view_mat(self):
        Logger.log_fatal("CamType.get_view_mat must be overridden!")
    
    def get_projection_mat(self):
        Logger.log_fatal("CamType.get_projection_mat must be overridden!")
    
    def get_view_pos(self):
        Logger.log_fatal("CamType.get_view_pos must be overridden!")
        