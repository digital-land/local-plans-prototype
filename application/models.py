import uuid

from datetime import datetime
from enum import Enum
from functools import total_ordering
from application.auth.utils import get_current_user
from application.extensions import db
from sqlalchemy.dialects.postgresql import UUID, JSONB


def _generate_uuid():
    return uuid.uuid4()


planning_authority_plan = db.Table(
    "planning_authority_plan",
    db.Column(
        "planning_authority_id",
        db.String(64),
        db.ForeignKey(
            "planning_authority.id",
            name="planning_authority_plan_planning_authority_id_fkey",
        ),
        primary_key=True,
    ),
    db.Column(
        "local_plan_id",
        UUID(as_uuid=True),
        db.ForeignKey(
            "local_plan.id", name="planning_authority_plan_local_plan_id_fkey"
        ),
        primary_key=True,
    ),
)


@total_ordering
class LocalPlan(db.Model):

    id = db.Column(
        UUID(as_uuid=True), default=_generate_uuid, primary_key=True, nullable=False
    )
    local_plan = db.Column(db.String())
    url = db.Column(db.String())
    title = db.Column(db.String())

    plan_start_year = db.Column(db.Date())
    plan_end_year = db.Column(db.Date())

    housing_numbers = db.Column(JSONB)

    # These are so a user can indicate they've been unable to find data
    plan_period_found = db.Column(db.Boolean)
    housing_numbers_found = db.Column(db.Boolean)

    published_date = db.Column(db.Date())
    submitted_date = db.Column(db.Date())
    sound_date = db.Column(db.Date())
    adopted_date = db.Column(db.Date())
    planning_authorities = db.relationship(
        "PlanningAuthority",
        secondary=planning_authority_plan,
        lazy=True,
        back_populates="local_plans",
        order_by="PlanningAuthority.id",
    )

    created_date = db.Column(db.DateTime(), default=datetime.utcnow)
    updated_date = db.Column(db.DateTime(), onupdate=datetime.utcnow)
    deleted = db.Column(db.Boolean, default=False)
    last_updated_by = db.Column(db.String(), onupdate=get_current_user)
    local_development_framework_number = db.Column(db.Integer)

    def __eq__(self, other):

        if self.plan_start_year is not None and other.plan_start_year is not None:
            return self.plan_start_year == other.plan_start_year
        else:
            return False

    def __lt__(self, other):

        if self.plan_start_year is not None and other.plan_start_year is not None:
            return self.plan_start_year < other.plan_start_year
        elif self.plan_start_year is not None and other.plan_start_year is None:
            return False
        else:
            return True

    def __hash__(self):
        id = f'{str(self.plan_start_year)}|{",".join([pla.id for pla in self.planning_authorities])}'
        return hash(id)

    def latest_state(self):
        return self.ordered_states()[-1]

    def is_adopted(self):
        return True if self.adopted_date is not None else False

    def is_joint_plan(self):
        return len(self.planning_authorities) > 1

    def has_joint_plan_breakdown(self):
        return (
            self.housing_numbers
            and self.housing_numbers.get("housing_number_by_planning_authority")
            is not None
        )

    def has_joint_plan_breakdown_for_authority(self, planning_authority):
        return (
            self.get_joint_plan_breakdown_for_authority(planning_authority) is not None
        )

    def get_joint_plan_breakdown_for_authority(self, planning_authority):
        if not self.is_joint_plan() and not self.has_housing_numbers:
            return None
        if self.housing_numbers.get("housing_number_by_planning_authority") is None:
            return None
        if (
            self.housing_numbers.get("housing_number_by_planning_authority").get(
                planning_authority
            )
            is None
        ):
            return None
        return self.housing_numbers.get("housing_number_by_planning_authority")[
            planning_authority
        ]["number"]

    def joint_plan_authorities(self, authority_id):
        return [
            {"name": auth.name, "id": auth.id}
            for auth in self.planning_authorities
            if authority_id != auth.id
        ]

    def has_plan_period(self):
        return self.plan_start_year is not None or self.plan_end_year is not None

    def has_housing_numbers(self):
        return self.housing_numbers is not None

    def has_pins_data(self):
        return any(
            [
                self.published_date,
                self.submitted_date,
                self.sound_date,
                self.adopted_date,
            ]
        )

    def has_missing_data(self):
        # true if period is set or user indicated can't find it
        pp = self.has_plan_period() or self.plan_period_found == False
        hn = self.has_housing_numbers() or self.housing_numbers_found == False
        if pp and hn:
            return False
        return True

    def get_correct_housing_numbers(self, planning_authority):
        if not self.is_joint_plan():
            return self.housing_numbers.get("number")
        numbers_by_authority = self.housing_numbers.get(
            "housing_number_by_planning_authority"
        )
        if numbers_by_authority is None:
            return self.housing_numbers.get("number")
        return numbers_by_authority.get(planning_authority)

    def ordered_states(self):
        states = []
        if not self.has_pins_data():
            states.append(State(state="emerging", date=self.plan_start_year))
        if self.published_date is not None:
            states.append(State(state="published", date=self.published_date))
        if self.submitted_date is not None:
            states.append(State(state="submitted", date=self.submitted_date))
        if self.sound_date is not None:
            states.append(State(state="sound", date=self.sound_date))
        if self.adopted_date is not None:
            states.append(State(state="adopted", date=self.adopted_date))
        return states

    def next_state(self):
        if self.adopted_date is not None:
            return None
        if self.sound_date is not None:
            return "adopted"
        if self.submitted_date is not None:
            return "sound"
        if self.published_date is not None:
            return "submitted"
        if self.published_date is None:
            return "published"

    def to_dict(self, authority_id):
        data = {
            "id": self.id,
            "is_adopted": self.is_adopted(),
            "title": self.title if self.title else self.local_plan,
            "joint_plan_authorities": self.joint_plan_authorities(authority_id)
            if self.is_joint_plan()
            else [],
            "url": self.url,
        }
        if self.housing_numbers:
            data["housing_numbers"] = self.housing_numbers
        else:
            data["housing_numbers_found"] = False
        if self.plan_start_year and self.plan_end_year:
            data["plan_start_year"] = self.plan_start_year.strftime("%Y")
            data["plan_end_year"] = self.plan_end_year.strftime("%Y")
        else:
            data["plan_period_found"] = False
        return data

    def is_emerging(self):
        return all(
            d is None
            for d in [
                self.published_date,
                self.submitted_date,
                self.sound_date,
                self.adopted_date,
            ]
        )

    def covers_years(self, from_, to):
        dates = [s.date for s in self.ordered_states()]
        if dates:
            return from_ >= dates[0] or to <= dates[-1]
        return False

    def id_to_str(self):
        return str(self.id)


class PlanningAuthority(db.Model):

    id = db.Column(db.String(64), primary_key=True)
    ons_code = db.Column(db.String(9))
    name = db.Column(db.String(256))
    website = db.Column(db.String())
    local_plans = db.relationship(
        "LocalPlan",
        secondary=planning_authority_plan,
        lazy="dynamic",
        back_populates="planning_authorities",
    )

    def sorted_plans(self, reverse=False, deleted=False):
        plans = self.local_plans.filter(LocalPlan.deleted == deleted).all()
        return sorted(plans, reverse=reverse)

    def get_earliest_plan_start_year(self):
        try:
            first = next(
                p for p in self.sorted_plans() if p.plan_start_year is not None
            )
            if first is not None:
                return first.plan_start_year.year
            else:
                return None
        except StopIteration:
            return None

    def get_latest_plan_end_year(self):
        try:
            first = next(
                p
                for p in self.sorted_plans(reverse=True)
                if p.plan_end_year is not None
            )
            if first is not None:
                return first.plan_end_year.year
            else:
                return None
        except StopIteration:
            return None

    def code(self):
        return self.id.split(":")[-1]

    def to_dict(self):
        data = {
            "id": self.id,
            "name": self.name,
            "ons_code": self.ons_code,
            "plans": [plan.to_dict(self.id) for plan in self.local_plans],
        }
        return data


class HousingNumberType(Enum):

    HOUSING_REQUIREMENT_TOTAL = "Housing requirement total"
    HOUSING_REQUIREMENT_RANGE = "Housing requirement range"
    HOUSING_REQUIREMENT_YEARLY_AVERAGE = "Housing requirement yearly average"
    HOUSING_REQUIREMENT_YEARLY_RANGE = "Housing requirement yearly range"


class State:
    def __init__(self, state, date):
        self.state = state
        self.date = date

    def to_dict(self):
        return {
            "state": self.state,
            "date": self.date.strftime("%Y") if self.date else None,
        }

    def __lt__(self, other):
        return self.date < other.date

    def __eq__(self, other):
        return self.state == other.state and self.date == other.date
