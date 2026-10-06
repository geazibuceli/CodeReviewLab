def collect(value, items=[]):
    items.append(value)
    return items


def indexed_total(items):
    total = 0
    for index in range(len(items) + 1):
        total += items[index]
    return total


async def safe_first(items):
    return items[0] if items else None
