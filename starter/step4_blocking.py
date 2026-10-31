"""Шаг 4 (дополнительный). Блокировка event loop.

Ниже готовый асинхронный сервер из шага 3б. Но теперь клиент "bob"
прислал не запрос в базу, а задачу на тяжёлые вычисления: функция
heavy_compute. Она синхронная и работает 1-3 секунды в зависимости от машины.

Задание 4а:
  В handle_request для клиента "bob" вызовите heavy_compute()
  вместо await asyncio.sleep(duration). Остальные клиенты по-прежнему
  ждут через asyncio.sleep. Запустите.
  Что произошло с остальными клиентами? Почему, ведь всё написано на async?

Задание 4б:
  Исправьте так, чтобы остальные клиенты не ждали bob. Два инструмента:
    await asyncio.to_thread(heavy_compute)
    await loop.run_in_executor(pool, heavy_compute)
  где loop = asyncio.get_running_loop(), а pool — это ProcessPoolExecutor
  из concurrent.futures, открытый через with в main.
  Попробуйте оба. Порядок строк в выводе должен стать как в шаге 3б,
  время bob зависит от машины.

Задание 4в (если осталось время):
  Сделайте тяжёлыми трёх клиентов: bob, dave и eve. Сравните общее время
  для to_thread и для пула процессов. Почему оно отличается? Вспомните GIL.
"""

import argparse
import asyncio
from concurrent.futures import ProcessPoolExecutor

from timer import log, print_time

CLIENTS = [
    ("alice", 0.5),
    ("bob", 5.0),
    ("carol", 0.5),
    ("dave", 0.5),
    ("eve", 0.5),
]


def heavy_compute() -> int:
    """Синхронные тяжёлые вычисления, 1-3 секунды."""
    h = 0
    for i in range(30_000_000):
        h = (h * 31 + i) & 0xFFFFFFFF
    return h


async def handle_request(
    client: str,
    duration: float,
    *,
    mode: str,
    heavy_clients: set[str],
    pool: ProcessPoolExecutor | None = None,
) -> None:
    log(f"{client}: запрос принят")

    if client not in heavy_clients:
        await asyncio.sleep(duration)
    elif mode == "blocked":
        heavy_compute()
    elif mode == "thread":
        await asyncio.to_thread(heavy_compute)
    elif mode == "process":
        if pool is None:
            raise ValueError("Для режима process нужен ProcessPoolExecutor")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(pool, heavy_compute)
    else:
        raise ValueError(f"Неизвестный режим: {mode}")

    log(f"{client}: ответ отправлен")


async def serve(
    mode: str,
    heavy_clients: set[str],
    pool: ProcessPoolExecutor | None = None,
) -> None:
    await asyncio.gather(
        *(
            handle_request(
                client,
                duration,
                mode=mode,
                heavy_clients=heavy_clients,
                pool=pool,
            )
            for client, duration in CLIENTS
        )
    )


async def main(
    mode: str = "blocked",
    heavy_clients: set[str] | None = None,
) -> None:
    selected_heavy_clients = {"bob"} if heavy_clients is None else heavy_clients

    if mode == "process":
        with ProcessPoolExecutor() as pool:
            await serve(mode, selected_heavy_clients, pool)
    else:
        await serve(mode, selected_heavy_clients)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Показать блокировку event loop и способы вынести вычисления."
    )
    parser.add_argument(
        "--mode",
        choices=("blocked", "thread", "process"),
        default="blocked",
        help="blocked — считать в event loop; thread/process — вынести вычисления",
    )
    parser.add_argument(
        "--heavy",
        default="bob",
        help="список клиентов с тяжёлыми вычислениями через запятую (по умолчанию: bob)",
    )
    args = parser.parse_args()

    known_clients = {client for client, _ in CLIENTS}
    heavy_clients = {name.strip() for name in args.heavy.split(",") if name.strip()}
    unknown_clients = heavy_clients - known_clients
    if unknown_clients:
        parser.error(f"неизвестные клиенты: {', '.join(sorted(unknown_clients))}")

    with print_time():
        asyncio.run(main(mode=args.mode, heavy_clients=heavy_clients))
