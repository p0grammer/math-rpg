"""
Mathpal — Level Progression Engine & JSON Parser
=================================================
Parses `data/levels.json` to configure the 50-level campaign with procedural
fallback and topic-to-generator routing.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Callable, List, Tuple, Optional

from logic.equation_generator import EquationGenerator, MathProblem

LEVELS_JSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "levels.json"
)


@dataclass
class LevelDefinition:
    level_number: int
    name: str
    chapter_id: int
    topic: str
    is_boss: bool
    enemy_id: str
    enemy_name: str
    enemy_type: str
    enemy_max_hp: int
    hp_per_hit: int
    formula_display: str
    story_messages: List[Tuple[str, str]]
    tutorial_messages: List[Tuple[str, str]]
    victory_messages: List[Tuple[str, str]]

    def generate_problem(self, difficulty: int = 1) -> MathProblem:
        """Generate an algorithmic problem matching this level's topic."""
        return EquationGenerator.generate(self.topic, difficulty)


class LevelManager:
    """Singleton / class manager for levels loaded from JSON with procedural fallback."""

    _LEVELS: dict[int, LevelDefinition] = {}
    _INITIALIZED = False

    @classmethod
    def initialize(cls):
        if cls._INITIALIZED:
            return
        cls._INITIALIZED = True
        cls.load_from_json()

    @classmethod
    def load_from_json(cls, filepath=LEVELS_JSON_PATH):
        if not os.path.isfile(filepath):
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                levels_list = data.get("levels", [])
                for item in levels_list:
                    enemy = item.get("enemy", {})
                    lvl = LevelDefinition(
                        level_number=item["level_number"],
                        name=item["name"],
                        chapter_id=item.get("chapter_id", (item["level_number"] - 1) // 5 + 1),
                        topic=item.get("topic", "POWER_RULE"),
                        is_boss=item.get("is_boss", False),
                        enemy_id=enemy.get("id", "beast"),
                        enemy_name=enemy.get("name", "ENEMY"),
                        enemy_type=enemy.get("sprite_type", "beast"),
                        enemy_max_hp=enemy.get("max_hp", 100),
                        hp_per_hit=enemy.get("hp_per_hit", 25),
                        formula_display=item.get("formula_display", "d/dx( f )"),
                        story_messages=[(m[0], m[1]) for m in item.get("story_messages", [])],
                        tutorial_messages=[(m[0], m[1]) for m in item.get("tutorial_messages", [])],
                        victory_messages=[(m[0], m[1]) for m in item.get("victory_messages", [])],
                    )
                    cls._LEVELS[lvl.level_number] = lvl
        except Exception:
            pass

    @classmethod
    def get_level(cls, level_id: int) -> LevelDefinition:
        cls.initialize()
        if level_id in cls._LEVELS:
            return cls._LEVELS[level_id]

        # Procedural fallback for levels 1..50 if not in JSON
        is_boss = (level_id % 5 == 0)
        chapter_id = (level_id - 1) // 5 + 1

        topic_cycle = [
            "POWER_RULE", "PRODUCT_RULE", "QUOTIENT_RULE", "TRIG_DERIVATIVES", "CHAIN_RULE",
            "EXP_LOG_DERIVATIVES", "CHAIN_RULE", "BASIC_INTEGRALS", "BASIC_INTEGRALS", "U_SUBSTITUTION"
        ]
        topic = topic_cycle[(level_id - 1) % len(topic_cycle)]

        sprite_pool = ["slime", "crystal", "skull", "beast"]
        sprite_type = "golem" if is_boss else sprite_pool[(level_id) % len(sprite_pool)]
        enemy_name = f"BOSS: ARCH-ENTITY {level_id}" if is_boss else f"CALCULUS GUARDIAN {level_id}"

        return LevelDefinition(
            level_number=level_id,
            name=f"Level {level_id}: Calculus Trial" if not is_boss else f"Level {level_id}: Boss Confrontation",
            chapter_id=chapter_id,
            topic=topic,
            is_boss=is_boss,
            enemy_id=f"enemy_{level_id}",
            enemy_name=enemy_name,
            enemy_type=sprite_type,
            enemy_max_hp=120 if is_boss else 80,
            hp_per_hit=24 if is_boss else 20,
            formula_display=f"Topic: {topic}",
            story_messages=[("MASTER LEIBNIZ", f"Level {level_id} awaits! Focus your mind!")],
            tutorial_messages=[("MASTER LEIBNIZ", f"Channel the power of {topic.replace('_', ' ')}!")],
            victory_messages=[("", f"Level {level_id} successfully cleared!")],
        )

    @classmethod
    def max_level(cls) -> int:
        cls.initialize()
        return 50


LevelManager.initialize()
