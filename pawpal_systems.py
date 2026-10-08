from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta

# Days until the next occurrence of a recurring task
FREQUENCY_DAYS = {"daily": 1, "weekly": 7}


@dataclass
class Task:
    description: str
    duration: int
    deadline: date
    priority: int  # 1 is the most urgent
    pet: Pet  # each task depends on a pet (Task "many" -> "1" Pet)
    completed: bool = False
    frequency: str = "once"  # "once", "daily" or "weekly"
    start_time: datetime | None = None  # optional; only timed tasks can conflict

    def __post_init__(self) -> None:
        """Reject frequencies other than once, daily or weekly."""
        if self.frequency != "once" and self.frequency not in FREQUENCY_DAYS:
            raise ValueError(f"Unknown frequency: {self.frequency}")

    @property
    def end_time(self) -> datetime | None:
        """When the task finishes (start_time plus duration), or None if untimed."""
        if self.start_time is None:
            return None
        return self.start_time + timedelta(minutes=self.duration)

    def complete(self) -> Task | None:
        """Mark done; for a recurring task, return the next occurrence (else None).

        Completing an already-completed task does nothing, so it can't spawn duplicates.
        The next occurrence is due today plus one period (1 day daily, 7 days weekly),
        however early or late this one was completed.
        """
        if self.completed:
            return None
        self.completed = True
        if self.frequency == "once":
            return None
        shift = timedelta(days=FREQUENCY_DAYS[self.frequency])
        next_deadline = date.today() + shift
        next_start = (
            self.start_time + (next_deadline - self.deadline) if self.start_time else None
        )
        return replace(self, deadline=next_deadline, start_time=next_start, completed=False)


def _priority_key(task: Task) -> tuple:
    """Sort key for urgency: lower tuples come first.

    1. completed: incomplete tasks first, completed tasks last
    2. priority: ascending, since 1 is the most urgent
    3. deadline: earliest first, to break priority ties
    4. duration: shortest first, to break deadline ties
    """
    return (task.completed, task.priority, task.deadline, task.duration)


def _overlaps(a: Task, b: Task) -> bool:
    """True if two timed tasks' [start, end) ranges intersect."""
    return a.start_time < b.end_time and b.start_time < a.end_time


@dataclass
class Scheduler:
    # Scheduler "1" -> "1" Owner; excluded from repr/eq to avoid infinite recursion
    owner: Owner = field(repr=False, compare=False)
    tasks: list[Task] = field(default_factory=list)  # Scheduler "1" -> "many" Task

    def display_list(self) -> None:
        """Print the tasks as a numbered list with status, pet, priority and timing."""
        if not self.tasks:
            print("No tasks.")
            return
        for i, task in enumerate(self.tasks, start=1):
            mark = "x" if task.completed else " "
            print(
                f"{i}. [{mark}] {task.description} ({task.pet.name}) - "
                f"priority {task.priority}, due {task.deadline}, "
                f"{task.duration} min, {task.frequency}"
                + (f", starts {task.start_time:%Y-%m-%d %H:%M}" if task.start_time else "")
            )

    def prioritize(self) -> None:
        """Sort the tasks in place: incomplete first, then priority, deadline, duration."""
        self.tasks.sort(key=_priority_key)

    def sort_by_time(self) -> list[Task]:
        """Return the tasks ordered by start_time, untimed last, ties broken by priority."""
        return sorted(
            self.tasks,
            key=lambda t: (t.start_time is None, t.start_time or datetime.max, _priority_key(t)),
        )

    def filter_tasks(
        self,
        pet: Pet | None = None,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Return the tasks matching the pet, pet name (case-insensitive) and completion status (None = any)."""
        return [
            t
            for t in self.tasks
            if (pet is None or t.pet is pet)
            and (pet_name is None or t.pet.name.lower() == pet_name.lower())
            and (completed is None or t.completed == completed)
        ]

    def complete_task(self, task: Task) -> Task | None:
        """Complete a task and queue its next occurrence if it recurs."""
        next_task = task.complete()
        if next_task is not None:
            self.tasks.append(next_task)
        return next_task

    def _plan(self) -> tuple[list[Task], list[tuple[Task, Task]]]:
        """Greedy plan in urgency order; also returns (skipped, blocker) conflict pairs.

        A task is skipped if it doesn't fit the remaining time, or if it is timed and
        overlaps a timed task already in the plan.
        """
        plan: list[Task] = []
        conflicts: list[tuple[Task, Task]] = []
        remaining = self.owner.available_time
        for task in sorted(self.filter_tasks(completed=False), key=_priority_key):
            if task.duration > remaining:
                continue
            blocker = next(
                (p for p in plan if task.start_time and p.start_time and _overlaps(task, p)),
                None,
            )
            if blocker:
                conflicts.append((task, blocker))
                continue
            plan.append(task)
            remaining -= task.duration
        return plan, conflicts

    def fit_to_time(self) -> list[Task]:
        """Pick incomplete tasks, most urgent first, that fit in available_time without overlapping.

        Greedy: it never backtracks, so an early large task can crowd out several smaller ones.
        """
        return self._plan()[0]

    def conflicting_tasks(self) -> list[tuple[Task, Task]]:
        """(task, blocker) pairs: tasks dropped from the plan because they overlap a planned one."""
        return self._plan()[1]

    def next_free_slot(
        self, duration: int, after: datetime, exclude: Task | None = None
    ) -> datetime:
        """Earliest start at or after `after` where `duration` minutes clear every timed task.

        Sweeps the incomplete timed tasks in start order, pushing the candidate start to
        the end of any task it would collide with, until a gap fits. `exclude` ignores one
        task (the one being moved). Back-to-back is allowed (ranges are [start, end)).
        """
        busy = sorted(
            (t for t in self.filter_tasks(completed=False) if t.start_time and t is not exclude),
            key=lambda t: t.start_time,
        )
        candidate = after
        length = timedelta(minutes=duration)
        for t in busy:
            if t.end_time <= candidate:
                continue
            if candidate + length <= t.start_time:
                break
            candidate = t.end_time
        return candidate

    def unscheduled(self) -> list[Task]:
        """Incomplete tasks that fit_to_time() leaves out (no time left, or a conflict)."""
        planned = {id(t) for t in self.fit_to_time()}
        return [
            t
            for t in sorted(self.filter_tasks(completed=False), key=_priority_key)
            if id(t) not in planned
        ]

    def find_conflicts(self) -> list[tuple[Task, Task]]:
        """Pairs of incomplete timed tasks whose time ranges overlap, across all pets.

        Compares every pair once (O(n^2)); each pair is returned in list order.
        """
        timed = [t for t in self.filter_tasks(completed=False) if t.start_time]
        return [
            (a, b)
            for i, a in enumerate(timed)
            for b in timed[i + 1 :]
            if _overlaps(a, b)
        ]


    def conflict_warnings(self) -> list[str]:
        """Warning messages for overlapping timed tasks; never raises.

        Each pair is checked on its own, so a task with bad timing data (e.g. mixed
        naive/aware datetimes) yields a warning about itself instead of crashing.
        """
        warnings: list[str] = []
        timed = [t for t in self.tasks if not t.completed and t.start_time]
        for i, a in enumerate(timed):
            for b in timed[i + 1 :]:
                try:
                    if not _overlaps(a, b):
                        continue
                    who = (
                        f"for {a.pet.name}"
                        if a.pet is b.pet
                        else f"for {a.pet.name} and {b.pet.name}"
                    )
                    message = (
                        f"Warning: '{a.description}' ({a.start_time:%H:%M}-{a.end_time:%H:%M}) "
                        f"overlaps '{b.description}' ({b.start_time:%H:%M}-{b.end_time:%H:%M}) "
                        f"{who}."
                    )
                    try:
                        slot = self.next_free_slot(b.duration, b.start_time, exclude=b)
                        message += f" Next free slot for '{b.description}': {slot:%H:%M}."
                    except Exception:
                        pass  # the warning is still useful without a suggestion
                    warnings.append(message)
                except Exception:
                    warnings.append(
                        f"Warning: couldn't check '{a.description}' against "
                        f"'{b.description}' (invalid time data)."
                    )
        return warnings


@dataclass
class Food:
    food_type: str
    serving_size: float
    quantity: int = 0  # units in stock, updated by purchase() and feed()

    def purchase(self, quantity: int = 1) -> None:
        """Add units to the food stock; the quantity must be positive."""
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self.quantity += quantity

    def feed(self, pet: Pet) -> None:
        """Use one unit of stock to feed the pet; raise ValueError if none is left."""
        if self.quantity <= 0:
            raise ValueError(f"No {self.food_type} left to feed {pet.name}")
        self.quantity -= 1
        pet.eat(self)


@dataclass
class Pet:
    name: str
    species: str
    birthday: date
    weight: float
    gender: str
    color: str
    foods: list[Food] = field(default_factory=list)  # Pet "1" -> "many" Food

    @property
    def age(self) -> int:
        """The pet's age in whole years, computed from its birthday."""
        today = date.today()
        had_birthday = (today.month, today.day) >= (self.birthday.month, self.birthday.day)
        return today.year - self.birthday.year - (not had_birthday)

    def eat(self, food: Food) -> str:
        """Return a message describing the pet eating the given food."""
        return f"{self.name} ate {food.serving_size} of {food.food_type}"

    def walk(self) -> str:
        """Return a message describing the pet going for a walk."""
        return f"{self.name} went for a walk"

    def make_sound(self) -> str:
        """Return the sound the pet makes, based on its species."""
        sounds = {"dog": "Woof!", "cat": "Meow!", "bird": "Tweet!"}
        return f"{self.name}: {sounds.get(self.species.lower(), '...')}"

    def sleep(self) -> str:
        """Return a message describing the pet sleeping."""
        return f"{self.name} is sleeping"

    def play(self) -> str:
        """Return a message describing the pet playing."""
        return f"{self.name} is playing"


@dataclass
class Owner:
    name: str
    available_time: int = 0  # minutes available per day, same unit as Task.duration
    pets: list[Pet] = field(default_factory=list)  # Owner "1" -> "many" Pet
    schedule: Scheduler = field(init=False)  # Owner "1" -> "1" Scheduler, holds the tasks

    def __post_init__(self) -> None:
        """Create the owner's Scheduler, linked back to this owner."""
        self.schedule = Scheduler(owner=self)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def add_task(self, task: Task) -> None:
        """Add a task to the schedule; its pet must belong to this owner."""
        if not any(task.pet is p for p in self.pets):
            raise ValueError(f"{task.pet.name} does not belong to {self.name}")
        self.schedule.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from the schedule; raise ValueError if it isn't there."""
        self.schedule.tasks.remove(task)

    def tasks_for(self, pet: Pet) -> list[Task]:
        """Return the scheduled tasks that belong to the given pet."""
        return [t for t in self.schedule.tasks if t.pet is pet]
