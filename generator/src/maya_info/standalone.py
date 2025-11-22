import maya.standalone


class MayaStandalone:
    def __enter__(self):
        try:
            maya.standalone.initialize()
        except RuntimeError:
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            maya.standalone.uninitialize()
        except RuntimeError:
            pass
