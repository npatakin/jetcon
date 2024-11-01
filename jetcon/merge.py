from jetcon.node import JetNode


def merge(
    dst: JetNode,
    src: JetNode
) -> JetNode:
    insect = src.keys() & dst.keys()

    for k in insect:
        if isinstance(src[k], JetNode) and isinstance(dst[k], JetNode):
            merge(dst[k], src[k])
        else:
            dst[k] = src[k]

    diff = src.keys() - dst.keys()

    for k in diff:
        dst[k] = src[k]

    return dst
