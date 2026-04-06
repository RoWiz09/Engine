from ..core.exceptions import OverrideError

class CamType:
    def get_view_mat(self):
        raise OverrideError("This function needs to be overridden!")
    
    def get_projection_mat(self):
        raise OverrideError("This function needs to be overridden!")
    
    def get_view_pos(self):
        raise OverrideError("This function needs to be overridden!")
        