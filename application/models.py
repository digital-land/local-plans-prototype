import uuid

from datetime import datetime
from enum import Enum
from functools import total_ordering

from sqlalchemy.ext.mutable import Mutable
from application.extensions import db
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSON


def _generate_uuid():
    return uuid.uuid4()


class MutableList(Mutable, list):

    def __setitem__(self, key, value):
        list.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        list.__delitem__(self, key)
        self.changed()

    def append(self, value):
        list.append(self, value)
        self.changed()

    def pop(self, index=0):
        value = list.pop(self, index)
        self.changed()
        return value

    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, MutableList):
            if isinstance(value, list):
                return MutableList(value)
            return Mutable.coerce(key, value)
        else:
            return value


planning_authority_plan = db.Table('planning_authority_plan',
    db.Column('planning_authority_id', db.String(64), db.ForeignKey('planning_authority.id'), primary_key=True),
    db.Column('local_plan_id', db.String, db.ForeignKey('local_plan.local_plan'), primary_key=True)
)


class LocalPlan(db.Model):

    local_plan = db.Column(db.String(), primary_key=True)
    url = db.Column(db.String())
    title = db.Column(db.String())
    states = db.Column(MutableList.as_mutable(ARRAY(db.String())), server_default='{}')
    published_date = db.Column(db.Date())
    submitted_date = db.Column(db.Date())
    sound_date = db.Column(db.Date())
    adopted_date = db.Column(db.Date())
    plan_documents = db.relationship('PlanDocument', back_populates='local_plan', lazy=True)
    planning_authorities = db.relationship('PlanningAuthority',
                                           secondary=planning_authority_plan,
                                           lazy=True,
                                           back_populates='local_plans')

    def latest_state(self):
        return self.ordered_states()[-1]

    def is_adopted(self):
        return True if self.adopted_date is not None else False
        
    def ordered_states(self):
        states = []
        if self.published_date is not None:
            states.append(State(state='published', date=self.published_date))
        if self.submitted_date is not None:
            states.append(State(state='submitted', date=self.submitted_date))
        if self.sound_date is not None:
            states.append(State(state='sound', date=self.sound_date))
        if self.adopted_date is not None:
            states.append(State(state='adopted', date=self.adopted_date))
        return states

    def to_dict(self):
        data = {
            'id': self.local_plan,
            'is_adopted': self.is_adopted(),
            'title': self.title,
            'planning_authorities': [{'name': authority.name, 'id':authority.id} for authority in self.planning_authorities]
        }
        return data


class PlanningAuthority(db.Model):

    id = db.Column(db.String(64), primary_key=True)
    ons_code = db.Column(db.String(9))
    name = db.Column(db.String(256))
    website = db.Column(db.String())
    local_scheme_url = db.Column(db.String())
    emerging_plan_documents = db.relationship('EmergingPlanDocument', back_populates='planning_authority', lazy=True)
    local_plans = db.relationship('LocalPlan',
                                  secondary=planning_authority_plan,
                                  lazy=True,
                                  back_populates='planning_authorities')

    housing_delivery_tests = db.relationship('HousingDeliveryTest',
                                             lazy=True,
                                             back_populates='planning_authority')

    def sorted_hdt(self, reverse=False):
        return sorted(self.housing_delivery_tests, reverse=reverse)

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'plans': [plan.to_dict() for plan in self.local_plans]
        }
        return data


def _parse_date(datestr):
    return datetime.strptime(datestr, '%Y-%m-%d')


class PlanDocument(db.Model):

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=_generate_uuid)
    plan_document_type = db.Column(db.String)
    url = db.Column(db.String())
    local_plan_id = db.Column(db.String(64), db.ForeignKey('local_plan.local_plan'), nullable=False)
    local_plan = db.relationship('LocalPlan', back_populates='plan_documents')
    facts = db.relationship('Fact', back_populates='plan_document', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        data = {
            'id': self.id,
            'url': self.url,
            'facts': [fact.to_dict() for fact in self.facts],
            'type': "plan_document"
        }
        return data


class FactType(Enum):

    PLAN_NAME = 'Plan name'
    PLAN_START_YEAR = 'Plan period start year'
    PLAN_END_YEAR = 'Plan period end year'
    HOUSING_REQUIREMENT_TOTAL = 'Housing requirement total'
    HOUSING_REQUIREMENT_RANGE = 'Housing requirement range'
    OTHER = 'Other'


class EmergingFactType(Enum):

    PUBLICATION_DATE = 'Publication date'
    PROPOSED_REG_18_DATE = 'Proposed Regulation 18 date'
    PROPOSED_PUBLICATION_DATE = 'Proposed publication date'
    PROPOSED_SUBMISSION_DATE = 'Proposed submission date'
    PROPOSED_MAIN_MODIFICATIONS_DATE = 'Proposed main modifications date'
    PROPOSED_ADOPTION_DATE = 'Proposed adoption date'
    HOUSING_REQUIREMENT_TOTAL = 'Housing requirement total'
    HOUSING_REQUIREMENT_RANGE = 'Housing requirement range'
    OTHER = 'Other'


# TODO - Note with facts and emerging facts the 'fact' field can contain strings, dates, numbers or ranges
# so will put method to return right value based on fact_type

class Fact(db.Model):

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=_generate_uuid)
    fact = db.Column(db.String())
    fact_type = db.Column(db.String())
    notes = db.Column(db.String())
    plan_document_id = db.Column(UUID(as_uuid=True), db.ForeignKey('plan_document.id'), nullable=False)
    plan_document = db.relationship('PlanDocument', back_populates='facts')
    created_date = db.Column(db.DateTime(), default=datetime.utcnow)

    def to_dict(self):
        data = {
            'id': self.id,
            'fact': self.fact,
            'fact_type': self.fact_type,
            'fact_type_display': FactType[self.fact_type].value,
            'notes': self.notes,
            'document_id': self.plan_document_id
        }
        return data


class EmergingFact(db.Model):

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=_generate_uuid)
    fact = db.Column(db.String())
    fact_type = db.Column(db.String())
    notes = db.Column(db.String())
    emerging_plan_document_id = db.Column(UUID(as_uuid=True),
                                          db.ForeignKey('emerging_plan_document.id'),
                                          nullable=False)
    emerging_plan_document = db.relationship('EmergingPlanDocument', back_populates='facts')
    created_date = db.Column(db.DateTime(), default=datetime.utcnow)

    def to_dict(self):
        data = {
            'id': self.id,
            'fact': self.fact,
            'fact_type': self.fact_type,
            'fact_type_display': EmergingFactType[self.fact_type].value,
            'notes': self.notes,
            'document_id': self.emerging_plan_document_id
        }
        return data


class EmergingPlanDocument(db.Model):

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=_generate_uuid)
    url = db.Column(db.String())
    planning_authority_id = db.Column(db.String(64), db.ForeignKey('planning_authority.id'), nullable=False)
    planning_authority = db.relationship('PlanningAuthority', back_populates='emerging_plan_documents')
    facts = db.relationship('EmergingFact',
                            back_populates='emerging_plan_document',
                            lazy=True,
                            cascade="all, delete-orphan")

    def to_dict(self):
        data = {
            'id': self.id,
            'url': self.url,
            'facts': [fact.to_dict() for fact in self.facts],
            'type': "emerging_plan_document"
        }
        return data


@total_ordering
class HousingDeliveryTest(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=_generate_uuid)
    from_year = db.Column(db.Date())
    to_year = db.Column(db.Date())
    homes_required = db.Column(db.Integer())
    homes_delivered = db.Column(db.Integer())

    planning_authority_id = db.Column(db.String(64), db.ForeignKey('planning_authority.id'), nullable=False)
    planning_authority = db.relationship('PlanningAuthority', back_populates='housing_delivery_tests')

    def __eq__(self, other):
        return self.planning_authority_id == other.planning_authority_id and (self.from_year, self.to_year) == (other.from_year, other.to_year)

    def __lt__(self, other):
        return self.planning_authority_id == other.planning_authority_id and (self.from_year < other.from_year) and (self.to_year < other.to_year)

    def percent_delivered(self):
        return (self.homes_delivered / self.homes_required) * 100.0


class State:

    def __init__(self, state, date):
        self.state = state
        self.date = date

    def __lt__(self, other):
        return self.date < other.date
