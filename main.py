from datetime import date, datetime, time

from pawpal_systems import Owner, Pet, Task


def at(hour: int, minute: int = 0) -> datetime:
    """Return today's date at the given hour and minute."""
    return datetime.combine(date.today(), time(hour, minute))


def show(tasks: list[Task]) -> None:
    """Print each task on one line with status, start time, pet, duration and priority."""
    if not tasks:
        print("  (none)")
    for t in tasks:
        when = f"{t.start_time:%I:%M %p}" if t.start_time else "  --   "
        mark = "x" if t.completed else " "
        print(f"  [{mark}] {when}  {t.description:<16} {t.pet.name:<9} {t.duration:>3} min  (priority {t.priority})")


def main() -> None:
    """Demo the Scheduler: sorting, filtering, recurring tasks and conflict warnings."""
    owner = Owner("Saniya", available_time=120)

    Sparky = Pet("Sparky", "dog", date(2021, 3, 14), 22.5, "M", "brown")
    Garfield = Pet("Garfield", "cat", date(2019, 8, 2), 4.2, "F", "white")
    owner.pets.extend([Sparky, Garfield])

    today = date.today()
    # Added deliberately out of time order, with one untimed task
    owner.add_task(Task("Brush fur", 15, today, 3, Garfield, start_time=at(18, 30)))
    owner.add_task(Task("Vet check-up", 45, today, 2, Sparky, start_time=at(14, 0)))
    owner.add_task(Task("Buy cat food", 20, today, 2, Garfield))
    owner.add_task(Task("Morning walk", 30, today, 1, Sparky, frequency="daily", start_time=at(7, 30)))
    owner.add_task(Task("Feed breakfast", 10, today, 1, Garfield, frequency="daily", start_time=at(8, 15)))

    scheduler = owner.schedule
    vet = next(t for t in scheduler.tasks if t.description == "Vet check-up")
    scheduler.complete_task(vet)  # one-off task, so no repeat is queued

    print("Added order (unsorted)")
    show(scheduler.tasks)

    print(f"\nToday's Schedule for {owner.name} ({today:%A, %B %d}) - sort_by_time()")
    show(scheduler.sort_by_time())

    print("\nSparky's tasks - filter_tasks(pet_name='sparky')")
    show(scheduler.filter_tasks(pet_name="sparky"))

    print("\nGarfield's pending tasks - filter_tasks(pet_name='Garfield', completed=False)")
    show(scheduler.filter_tasks(pet_name="Garfield", completed=False))

    print("\nCompleted tasks - filter_tasks(completed=True)")
    show(scheduler.filter_tasks(completed=True))

    print("\nUnknown pet - filter_tasks(pet_name='Nobody')")
    show(scheduler.filter_tasks(pet_name="Nobody"))

    # Two tasks for different pets at the exact same time
    owner.add_task(Task("Grooming", 30, today, 2, Garfield, start_time=at(7, 30)))

    print("\nConflict check - conflict_warnings()")
    warnings = scheduler.conflict_warnings()
    for message in warnings:
        print(f"  {message}")
    if not warnings:
        print("  (no conflicts)")


if __name__ == "__main__":
    main()
