from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    description: str
    duration: int
    deadline: date
    priority: int  # 1 is the most urgent
    pet: Pet  # each task depends on a pet (Task "many" -> "1" Pet)
    completed: bool = False

    def complete(self) -> None:
        pass


@dataclass
class TodoList:
    tasks: list[Task] = field(default_factory=list)

    def display_list(self) -> None:
        pass

    def prioritize(self) -> None:
        # Sort self.tasks in place by these keys, in order:
        #   1. completed: incomplete tasks first, completed tasks last
        #   2. priority: ascending, since 1 is the most urgent
        #   3. deadline: earliest first, to break priority ties
        #   4. duration: shortest first, to break deadline ties
        pass


@dataclass
class Food:
    food_type: str
    serving_size: float
    quantity: int = 0  # units in stock, updated by purchase() and feed()

    def purchase(self) -> None:
        pass

    def feed(self, pet: Pet) -> None:
        pass


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
        today = date.today()
        had_birthday = (today.month, today.day) >= (self.birthday.month, self.birthday.day)
        return today.year - self.birthday.year - (not had_birthday)

    def eat(self) -> None:
        pass

    def walk(self) -> None:
        pass

    def make_sound(self) -> None:
        pass

    def sleep(self) -> None:
        pass

    def play(self) -> None:
        pass


@dataclass
class Owner:
    name: str
    available_time: int = 0  # minutes available per day, same unit as Task.duration
    schedule: TodoList = field(default_factory=TodoList)  # Owner "1" -> "many" Task
    pets: list[Pet] = field(default_factory=list)  # Owner "1" -> "many" Pet

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task: Task) -> None:
        pass

    def tasks_for(self, pet: Pet) -> list[Task]:
        pass
