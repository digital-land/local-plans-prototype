import uuid

from datetime import datetime
from enum import Enum
from functools import total_ordering

from sqlalchemy.ext.mutable import Mutable
from application.extensions import db
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSON


def _generate_uuid():
    return uuid.uuid4()


planning_authority_plan = db.Table('planning_authority_plan',
    db.Column('planning_authority_id', db.String(64), db.ForeignKey('planning_authority.id'), primary_key=True),
    db.Column('local_plan_id', db.String, db.ForeignKey('local_plan.local_plan'), primary_key=True)
)


class LocalPlan(db.Model):

    local_plan = db.Column(db.String(), primary_key=True)
    url = db.Column(db.String())
    title = db.Column(db.String())
    published_date = db.Column(db.Date())
    submitted_date = db.Column(db.Date())
    sound_date = db.Column(db.Date())
    adopted_date = db.Column(db.Date())
    planning_authorities = db.relationship('PlanningAuthority',
                                           secondary=planning_authority_plan,
                                           lazy=True,
                                           back_populates='local_plans')

    plan_documents = db.relationship('PlanDocument', back_populates='local_plan', lazy=True)

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
    local_plans = db.relationship('LocalPlan',
                                  secondary=planning_authority_plan,
                                  lazy=True,
                                  back_populates='planning_authorities')

    housing_delivery_tests = db.relationship('HousingDeliveryTest',
                                             lazy=True,
                                             back_populates='planning_authority')

    other_documents = db.relationship('OtherDocument', back_populates="planning_authority")

    def sorted_hdt(self, reverse=False):
        return sorted(self.housing_delivery_tests, reverse=reverse)

    def get_local_scheme_documents(self):
        # TODO add a subtype on other documents to filter on rather than title
        docs = [doc for doc in self.other_documents if doc.title is not None and 'local development scheme' == doc.title.lower()]
        return docs

    def gather_facts(self, filters=[]):

        facts = []
        for doc in self.other_documents:
            for fact in doc.facts:
                if filters:
                    if fact.fact_type in filters:
                        facts.append(fact)
                else:
                    facts.append(fact)

        for plan in self.local_plans:
            for doc in plan.plan_documents:
                for fact in doc.facts:
                    if filters:
                        if fact.fact_type in filters:
                            facts.append(fact)
                    else:
                        facts.append(fact)

        return facts

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'plans': [plan.to_dict() for plan in self.local_plans]
        }
        return data


def _parse_date(datestr):
    return datetime.strptime(datestr, '%Y-%m-%d')


class FactType(Enum):

    PLAN_NAME = 'Plan name'
    PLAN_PERIOD = 'Plan period'
    PLAN_START_YEAR = 'Plan period start year'
    PLAN_END_YEAR = 'Plan period end year'
    HOUSING_REQUIREMENT_TOTAL = 'Housing requirement total'
    HOUSING_REQUIREMENT_RANGE = 'Housing requirement range'
    HOUSING_REQUIREMENT_YEARLY_AVERAGE = 'Housing requirement yearly average'
    HOUSING_REQUIREMENT_YEARLY_RANGE = 'Housing requirement yearly range'
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


class Document(db.Model):

    __tablename__ = 'document'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=_generate_uuid)
    url = db.Column(db.String())
    title = db.Column(db.String())
    type = db.Column(db.String(64))

    facts = db.relationship('Fact', back_populates='document',lazy=True, cascade='all, delete, delete-orphan')

    __mapper_args__ = {
        'polymorphic_on':type,
        'polymorphic_identity':'document'
    }

    def to_dict(self):
        data = {
            'id': self.id,
            'url': self.url,
            'facts': [fact.to_dict() for fact in self.facts],
            'type': self.type
        }
        return data



class PlanDocument(Document):

    __mapper_args__ = {
        'polymorphic_identity':'plan_document'
    }

    local_plan_id = db.Column(db.String(64), db.ForeignKey('local_plan.local_plan'))
    local_plan = db.relationship('LocalPlan', back_populates='plan_documents')

    def to_dict(self):
        data = {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'facts': [fact.to_dict() for fact in self.facts],
            'type': "plan_document"
        }
        return data


class OtherDocument(Document):

    __mapper_args__ = {
        'polymorphic_identity':'other_document'
    }

    planning_authority_id = db.Column(db.String(64), db.ForeignKey('planning_authority.id'))
    planning_authority = db.relationship('PlanningAuthority', back_populates='other_documents')

    def to_dict(self):
        data = {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'facts': [fact.to_dict() for fact in self.facts],
            'type': "emerging_plan_document"
        }
        # TODO remove these over rides and use base to_dict method. this is only here as some code
        # expects emerging_plan_document so once updated then base object method does the right thing.
        return data


class Fact(db.Model):

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=_generate_uuid)
    fact = db.Column(db.String())
    fact_type = db.Column(db.String())
    notes = db.Column(db.String())
    from_year = db.Column(db.Date())
    to_year = db.Column(db.Date())

    created_date = db.Column(db.DateTime(), default=datetime.utcnow)
    image_url = db.Column(db.String())

    document_id = db.Column(UUID(as_uuid=True), db.ForeignKey('document.id'), nullable=False)
    document = db.relationship('Document', back_populates='facts')


    def get_fact_type(self):
        if self.fact_type in FactType.__members__:
            return FactType[self.fact_type]
        elif self.fact_type in EmergingFactType.__members__:
            return EmergingFactType[self.fact_type]


    def to_dict(self):
        data = {
            'id': str(self.id),
            'fact': self.fact,
            'fact_type': self.fact_type,
            'fact_type_display': self.get_fact_type().value,
            'notes': self.notes,
            'document_id': str(self.document_id)
        }
        return data
