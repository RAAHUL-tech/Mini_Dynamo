from vector_clock import compare, VCComparison

def deduplicate_versions(versions):
    seen = set()
    unique = []

    for v in versions:
        key = (v["value"], frozenset(v["vector_clock"].items()))
        if key not in seen:
            seen.add(key)
            unique.append(v)

    return unique


def resolve_versions(versions):
    survivors = []

    for v in versions:
        dominated = False
        for other in versions:
            if v == other:
                continue
            if compare(v["vector_clock"], other["vector_clock"]) == VCComparison.IS_DOMINATED:
                dominated = True
                break
        if not dominated:
            survivors.append(v)

    return deduplicate_versions(survivors)
