def remove_duplicates(lst):
    """removes duplicates without compromising order"""
    seen = set()
    res = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            res.append(item)
    return res