from typing import Generator, List, TypeVar

T = TypeVar("T")


def chunkList(lst: List[T], n: int) -> Generator[List[T], None, None]:
    for i in range(0, len(lst), n):
        yield lst[i : i + n]
