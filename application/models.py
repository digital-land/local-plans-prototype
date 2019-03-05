import uuid

from datetime import datetime
from enum import Enum

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

    plan_documents = db.relationship('PlanDocument', back_populates='local_plan', lazy=True)

    planning_authorities = db.relationship('PlanningAuthority',
                                           secondary=planning_authority_plan,
                                           lazy=True,
                                           back_populates='local_plans')

    def is_adopted(self):
        return 'adopted' in [s[0] for s in self.states]
        
    def ordered_states(self):
        ordered = []
        for s in self.states:
            ordered.append(State(state=s[0], date=_parse_date(s[1])))
        return sorted(ordered)

    def __repr__(self):
        return f'{self.local_plan} {self.states}'

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
    name = db.Column(db.String(256))
    website = db.Column(db.String())

    local_scheme_url = db.Column(db.String())
    emerging_plan_documents = db.relationship('EmergingPlanDocument', back_populates='planning_authority', lazy=True)

    local_plans = db.relationship('LocalPlan',
                                  secondary=planning_authority_plan,
                                  lazy=True,
                                  back_populates='planning_authorities')

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

    facts = db.relationship('Fact', back_populates='plan_document', lazy=True)

    def to_dict(self):
        data = {
            'id': self.id,
            'url': self.url,
            'facts': [fact.to_dict() for fact in self.facts]
        }
        return data


class FactType(Enum):

    __order__ = 'PLAN_NAME PLAN_START_YEAR PLAN_END_YEAR HOUSING_REQUIREMENT_TOTAL HOUSING_REQUIREMENT_RANGE'

    PLAN_NAME = 'Plan name'
    PLAN_START_YEAR = 'Plan period start year'
    PLAN_END_YEAR = 'Plan period end year'
    HOUSING_REQUIREMENT_TOTAL = 'Housing requirement total'
    HOUSING_REQUIREMENT_RANGE = 'Housing requirement range'


class EmergingFactType(Enum):

    # __order__ = 'PUBLICATION_DATE PROPOSED_REG_18_DATE PROPOSED_PUBLICATION_DATE PROPOSED_' \
    #             'SUBMISSION_DATE PROPOSED_MAIN_MODIFICATIONS_DATE PROPOSED_ADOPTION_DATE ' \
    #             'HOUSING_REQUIREMENT_TOTAL HOUSING_REQUIREMENT_RANGE'

    PUBLICATION_DATE = 'Publication date'
    PROPOSED_REG_18_DATE = 'Proposed Regulation 18 date'
    PROPOSED_PUBLICATION_DATE = 'Proposed publication date'
    PROPOSED_SUBMISSION_DATE = 'Proposed submission date'
    PROPOSED_MAIN_MODIFICATIONS_DATE = 'Proposed main modifications date'
    PROPOSED_ADOPTION_DATE = 'Proposed adoption date'
    HOUSING_REQUIREMENT_TOTAL = 'Housing requirement total'
    HOUSING_REQUIREMENT_RANGE = 'Housing requirement range'



# TODO - Note with facts and emerging facts the 'fact' field can contain strings, dates, numbers or ranges
# so will put method to return right value based on fact_type

class Fact(db.Model):

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=_generate_uuid)
    notes = db.Column(db.String())
    fact = db.Column(db.String())
    fact_type = db.Column(db.String())

    plan_document_id = db.Column(UUID(as_uuid=True), db.ForeignKey('plan_document.id'), nullable=False)
    plan_document = db.relationship('PlanDocument', back_populates='facts')

    def to_dict(self):
        data = {
            'id': self.id,
            'fact': self.fact,
            'fact_type': self.fact_type.name,
            'notes': self.notes,
            'document_id': self.plan_document_id
        }
        return data


class EmergingFact(db.Model):

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=_generate_uuid)
    fact = db.Column(db.String())
    fact_type = db.Column(db.String())
    notes = db.Column(db.String())

    emerging_plan_document_id = db.Column(UUID(as_uuid=True), db.ForeignKey('emerging_plan_document.id'), nullable=False)
    emerging_plan_document = db.relationship('EmergingPlanDocument', back_populates='facts')

    def to_dict(self):
        data = {
            'id': self.id,
            'fact': self.fact,
            'fact_type': self.fact_type.name,
            'notes': self.notes,
            'document_id': self.emerging_plan_document_id
        }
        return data


class EmergingPlanDocument(db.Model):

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=_generate_uuid)
    url = db.Column(db.String())

    planning_authority_id = db.Column(db.String(64), db.ForeignKey('planning_authority.id'), nullable=False)
    planning_authority = db.relationship('PlanningAuthority', back_populates='emerging_plan_documents')

    facts = db.relationship('EmergingFact', back_populates='emerging_plan_document', lazy=True)


class State:

    def __init__(self, state, date):
        self.state = state
        self.date = date

    def __lt__(self, other):
        return self.date < other.date
