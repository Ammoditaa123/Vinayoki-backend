import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Content, Interaction, User, UserSkill
from app.routes.feed import get_personalized_feed
from app.routes.interactions import create_interaction
from app.schemas import InteractionCreate


class BuildStateTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.user = User(
            name="Build Test Learner",
            goal="Career Skills",
            level="Intermediate",
            learning_style="Build",
        )
        self.db.add(self.user)
        self.db.flush()
        self.content = Content(
            title="Portfolio Artifact",
            topic="career",
            skill="portfolio_skill",
            type="build",
            difficulty=2,
            duration=5,
            description="Create a small portfolio artifact.",
            progress_value=10,
        )
        self.db.add(self.content)
        self.db.commit()
        self.db.refresh(self.user)
        self.db.refresh(self.content)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def build_payload(self, idempotency_key="build-once"):
        return InteractionCreate(
            user_id=self.user.id,
            content_id=self.content.id,
            action="build",
            completed=True,
            time_spent=60,
            idempotency_key=idempotency_key,
        )

    def test_successful_build_updates_related_skill_signals(self):
        result = create_interaction(self.build_payload(), self.db)
        skill = self.db.query(UserSkill).filter_by(
            user_id=self.user.id,
            skill=self.content.skill,
        ).one()

        self.assertEqual(result.action, "build")
        self.assertEqual(result.progress_earned, self.content.progress_value)
        self.assertAlmostEqual(skill.completion_rate, 0.2)
        self.assertAlmostEqual(skill.skill_score, 0.33)
        self.assertAlmostEqual(skill.interest_score, 0.52)

    def test_idempotent_retry_does_not_apply_build_state_twice(self):
        first = create_interaction(self.build_payload("same-build-key"), self.db)
        first_state = self.db.query(UserSkill).filter_by(
            user_id=self.user.id,
            skill=self.content.skill,
        ).one()
        first_values = (
            first_state.completion_rate,
            first_state.skill_score,
            first_state.interest_score,
        )

        retry = create_interaction(self.build_payload("same-build-key"), self.db)
        self.db.expire_all()
        retry_state = self.db.query(UserSkill).filter_by(
            user_id=self.user.id,
            skill=self.content.skill,
        ).one()

        self.assertEqual(retry.id, first.id)
        self.assertEqual(
            self.db.query(Interaction).filter_by(idempotency_key="same-build-key").count(),
            1,
        )
        self.assertEqual(
            (
                retry_state.completion_rate,
                retry_state.skill_score,
                retry_state.interest_score,
            ),
            first_values,
        )

    def test_build_signals_remain_within_zero_and_one(self):
        skill = UserSkill(
            user_id=self.user.id,
            skill=self.content.skill,
            interest_score=0.99,
            skill_score=0.99,
            completion_rate=0.99,
            skip_rate=0.75,
        )
        self.db.add(skill)
        self.db.commit()

        create_interaction(self.build_payload("bounded-build-key"), self.db)
        self.db.refresh(skill)

        for value in (skill.interest_score, skill.skill_score, skill.completion_rate, skill.skip_rate):
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
        self.assertEqual(skill.interest_score, 1.0)
        self.assertEqual(skill.skill_score, 1.0)
        self.assertAlmostEqual(skill.completion_rate, 0.992)

    def test_personalized_feed_uses_updated_build_skill_state(self):
        skill = UserSkill(
            user_id=self.user.id,
            skill=self.content.skill,
            interest_score=0.59,
            skill_score=0.49,
            completion_rate=0.2,
            skip_rate=0.0,
        )
        self.db.add(skill)
        self.db.commit()

        before = get_personalized_feed(self.user.id, self.db)
        before_activity = next(item for item in before["activities"] if item["id"] == self.content.id)

        create_interaction(self.build_payload("feed-build-key"), self.db)
        after = get_personalized_feed(self.user.id, self.db)
        after_activity = next(item for item in after["activities"] if item["id"] == self.content.id)

        self.assertEqual(after["user_id"], self.user.id)
        self.assertEqual(after["count"], 1)
        self.assertGreater(
            after_activity["recommendation_score"],
            before_activity["recommendation_score"],
        )
        self.assertIn("Builds on a skill you've already demonstrated", after_activity["why_this"])
        self.assertIn("Matches your portfolio skill interest", after_activity["why_this"])
        self.assertNotIn("Builds on a skill you've already demonstrated", before_activity["why_this"])
        self.assertNotIn("Matches your portfolio skill interest", before_activity["why_this"])


if __name__ == "__main__":
    unittest.main()
