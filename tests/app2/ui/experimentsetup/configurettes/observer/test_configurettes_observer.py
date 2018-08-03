from opendrop.app2.ui.experimentsetup.configurettes.imageacquisition.image_acquisition import ObserverSpecificImAqEditorProvider


def test_specific_editor_register():
    checkpoints = []

    def my_should_edit1(observer):
        checkpoints.append(('my_should_edit1', observer))
        return False

    def my_should_edit2(observer):
        checkpoints.append(('my_should_edit2', observer))
        return True

    @ObserverSpecificImAqEditorProvider.register(my_should_edit1)
    class MySpecific1:
        def __init__(self, model):
            pass

    @ObserverSpecificImAqEditorProvider.register(my_should_edit2)
    class MySpecific2:
        def __init__(self, model):
            pass

    my_observer = object()
    my_editor = ObserverSpecificImAqEditorProvider.new_for_observer(my_observer, None)

    assert isinstance(my_editor, MySpecific2)

    checkpoints = sorted(checkpoints)  # Order is irrelevant

    assert checkpoints == [
        ('my_should_edit1', my_observer),
        ('my_should_edit2', my_observer)
    ]
