"""Шаг 2б: десять задач ждут конкурентно."""

import asyncio

from timer import print_time


async def work(n: int) -> None:
    print(f"start {n}")
    await asyncio.sleep(1)
    print(f"done {n}")


async def main() -> None:
    coroutines = []
    for n in range(1, 11):
        coroutines.append(work(n))

    # gather планирует корутины и ждёт завершения всех десяти.
    await asyncio.gather(*coroutines)


if __name__ == "__main__":
    with print_time():
        asyncio.run(main())
