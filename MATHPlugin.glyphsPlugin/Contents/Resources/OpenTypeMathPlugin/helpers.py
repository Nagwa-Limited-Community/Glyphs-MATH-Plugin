def _getMetrics(layer):
    size = layer.bounds.size
    return size.width, size.height


def _bboxWidth(layer):
    return layer.bounds.size.width


def _bboxHeight(layer):
    return layer.bounds.size.height
