from dataclasses import dataclass


@dataclass
class SM2Result:
    repetitions: int
    ease_factor: float
    interval_days: int


def sm2_update(
    quality: int,
    repetitions: int,
    ease_factor: float,
    interval_days: int,
) -> SM2Result:
    """Update SM-2 spaced repetition parameters.

    quality: 0-5 where 0 is complete blackout and 5 is perfect recall.
    """
    q = max(0, min(5, quality))
    if q < 3:
        return SM2Result(repetitions=0, ease_factor=ease_factor, interval_days=1)

    new_ef = ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ef = max(1.3, new_ef)

    if repetitions == 0:
        new_interval = 1
    elif repetitions == 1:
        new_interval = 6
    else:
        new_interval = max(1, round(interval_days * new_ef))

    return SM2Result(
        repetitions=repetitions + 1,
        ease_factor=round(new_ef, 2),
        interval_days=new_interval,
    )
