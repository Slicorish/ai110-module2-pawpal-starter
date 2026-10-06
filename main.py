from datetime import date, datetime, time

from pawpal_systems import Owner, Pet, Task


def at(hour: int, minute: int = 0) -> datetime:
    return datetime.combine(date.today(), time(hour, minute))


def main() -> None:
    owner = Owner("Saniya", available_time=120)

    Sparky = Pet("Sparky", "dog", date(2021, 3, 14), 22.5, "M", "brown")
    Garfield = Pet("Garfield", "cat", date(2019, 8, 2), 4.2, "F", "white")
    owner.pets.extend([Sparky, Garfield])

    today = date.today()
    owner.add_task(Task("Morning walk", 30, today, 1, Sparky, frequency="daily", start_time=at(7, 30)))
    owner.add_task(Task("Feed breakfast", 10, today, 1, Garfield, frequency="daily", start_time=at(8, 15)))
    owner.add_task(Task("Vet check-up", 45, today, 2, Sparky, start_time=at(14, 0)))
    owner.add_task(Task("Brush fur", 15, today, 3, Garfield, start_time=at(18, 30)))

    print(f"Today's Schedule for {owner.name} ({today:%A, %B %d})")
    print("-" * 50)
    for task in sorted(owner.schedule.tasks, key=lambda t: t.start_time):
        print(
            f"{task.start_time:%I:%M %p}  {task.description:<16} "
            f"{task.pet.name:<6} {task.duration:>3} min  (priority {task.priority})"
        )


if __name__ == "__main__":
    main()
