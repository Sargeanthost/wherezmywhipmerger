from itertools import permutations, combinations


def generate_partitions(objects):
    n = len(objects)
    result = []

    def helper(curr, rest):
        if not rest:
            result.append(curr)
            return
        for i in range(1, len(rest) + 1):
            helper(curr + [rest[:i]], rest[i:])

    helper([], objects)
    return result


objects = ["A", "B", "C", "D", "E"]
partitions = generate_partitions(objects)
all_permutations = []

for partition in partitions:
    perms = [set(permutations(group)) for group in partition]
    print(perms)
    all_permutations.append(perms)


# print(f"Total partitions: {len(partitions)}")
count = 0
for p in partitions:
    # print(p)
    count += len(p)
# print(f"Total permutations: {count}")
