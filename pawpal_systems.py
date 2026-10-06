from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    description: str
    duration: int
    deadline: date
    priority: int

    def create(self) -> None:
        pass

    def delete(self) -> None:
        pass

    def complete(self) -> None:
        pass


@dataclass
class TodoList:
    tasks: list[Task] = field(default_factory=list)

    def add(self, task: Task) -> None:
        pass

    def remove(self, task: Task) -> None:
        pass

    def print(self) -> None:
        pass

    def prioritize(self) -> None:
        pass


@dataclass
class Food:
    type: str
    serving_size: float

    def purchase(self) -> None:
        pass

    def feed(self) -> None:
        pass


@dataclass
class Pet:
    name: str
    age: int
    birthday: date
    weight: float
    gender: str
    color: str
    foods: list[Food] = field(default_factory=list)  # Pet "1" -> "many" Food
    todo_list: TodoList = field(default_factory=TodoList)  # Pet "1" -> "1" TodoList

    def eat(self) -> None:
        pass

    def walk(self) -> None:
        pass

    def bark(self) -> None:
        pass

    def sleep(self) -> None:
        pass

    def play(self) -> None:
        pass


@dataclass
class Owner:
    name: str
    schedule: TodoList = field(default_factory=TodoList)
    pets: list[Pet] = field(default_factory=list)  # Owner "1" -> "many" Pet

    def create_schedule(self) -> None:
        pass

    def edit_schedule(self) -> None:
        pass
