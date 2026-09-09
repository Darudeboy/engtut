from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    language = State()
    level_test = State()
    goal = State()
    reminder = State()


class ReadingStates(StatesGroup):
    answering = State()


class VocabularyStates(StatesGroup):
    reviewing = State()


class GrammarStates(StatesGroup):
    answering = State()


class WritingStates(StatesGroup):
    answering = State()


class DialogueStates(StatesGroup):
    chatting = State()


class ListeningStates(StatesGroup):
    answering = State()


class DailyStates(StatesGroup):
    in_session = State()


class ExamStates(StatesGroup):
    answering = State()
