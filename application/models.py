import uuid

from datetime import datetime
from enum import Enum
from functools import total_ordering

from geoalchemy2 import Geometry
from sqlalchemy import func

from application.extensions import db
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSON


def _generate_uuid():
    return uuid.uuid4()


planning_authority_plan = db.Table('planning_authority_plan',
    db.Column('planning_authority_id', db.String(64), db.ForeignKey('planning_authority.id', name='planning_authority_plan_planning_authority_id_fkey'), primary_key=True),
    db.Column('local_plan_id_old', db.String),
    db.Column('local_plan_id', UUID(as_uuid=True), db.ForeignKey('local_plan.id', name='planning_authority_plan_local_plan_id_fkey'), primary_key=True)
)


@total_ordering
class LocalPlan(db.Model):

    id = db.Column(UUID(as_uuid=True), default=_generate_uuid, primary_key=True, nullable=False)
    local_plan = db.Column(db.String())
    url = db.Column(db.String())
    title = db.Column(db.String())

    plan_start_year = db.Column(db.Date())
    plan_end_year = db.Column(db.Date())

    housing_numbers = db.Column(JSON)

    # These are so a user can indicate they've been unable to find data
    plan_period_found = db.Column(db.Boolean)
    housing_numbers_found = db.Column(db.Boolean)

    published_date = db.Column(db.Date())
    submitted_date = db.Column(db.Date())
    sound_date = db.Column(db.Date())
    adopted_date = db.Column(db.Date())
    planning_authorities = db.relationship('PlanningAuthority',
                                           secondary=planning_authority_plan,
                                           lazy=True,
                                           back_populates='local_plans')

    plan_documents = db.relationship('PlanDocument', back_populates='local_plan', lazy=True, order_by='PlanDocument.created_date')

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

    def latest_state(self):
        return self.ordered_states()[-1]

    def is_adopted(self):
        return True if self.adopted_date is not None else False

    def is_joint_plan(self):
        return len(self.planning_authorities) > 1

    def joint_plan_authorities(self, authority_id):
        return [{'name': auth.name, 'id':auth.id} for auth in self.planning_authorities if authority_id != auth.id]

    def has_plan_period(self):
        return self.plan_start_year is not None or self.plan_end_year is not None

    def has_housing_numbers(self):
        return self.housing_numbers is not None

    def has_plan_documents(self):
        return len(self.plan_documents) > 0

    def has_pins_data(self):
        return any([self.published_date, self.submitted_date, self.sound_date, self.adopted_date])

    def has_missing_data(self):
        # true if period is set or user indicated can't find it
        pp = (self.has_plan_period() or self.plan_period_found == False)
        hn = (self.has_housing_numbers() or self.housing_numbers_found == False) 
        if pp and hn:
            return False
        return True

    def ordered_states(self):
        states = []
        if not self.has_pins_data():
            date = self.plan_start_year if self.plan_start_year else None
            states.append(State(state='emerging', date=date))
        if self.published_date is not None:
            states.append(State(state='published', date=self.published_date))
        if self.submitted_date is not None:
            states.append(State(state='submitted', date=self.submitted_date))
        if self.sound_date is not None:
            states.append(State(state='sound', date=self.sound_date))
        if self.adopted_date is not None:
            states.append(State(state='adopted', date=self.adopted_date))
        return states

    def to_dict(self, authority_id):
        title = self.title if self.title else self.local_plan
        data = {
            'id': self.id,
            'is_adopted': self.is_adopted(),
            'title': title,
            'plan_start_year': self.plan_start_year.strftime('%Y') if self.plan_start_year else None,
            'plan_end_year': self.plan_end_year.strftime('%Y') if self.plan_end_year else None,
            'joint_plan_authorities': self.joint_plan_authorities(authority_id) if self.is_joint_plan() else None,
            'url': self.url,
            'housing_numbers': self.housing_numbers,
            'plan_period_found': self.plan_period_found,
            'housing_numbers_found': self.housing_numbers_found
        }
        return data

    def is_emerging(self):
        return all(d is None for d in [self.published_date, self.submitted_date, self.sound_date, self.adopted_date])

    def covers_years(self, from_, to):
        dates = [s.date for s in self.ordered_states()]
        return from_ >= dates[0] or to <= dates[-1]


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
    geometry = db.Column(Geometry(srid=4326))

    def sorted_hdt(self, reverse=False):
        return sorted(self.housing_delivery_tests, reverse=reverse)

    def sorted_plans(self, reverse=False):
        if len(self.local_plans) == 1:
            return self.local_plans
        return sorted(self.local_plans, reverse=reverse)

    def get_local_scheme_documents(self):
        # TODO add a subtype on other documents to filter on rather than title
        docs = [doc for doc in self.other_documents if doc.title is not None and 'local development scheme' == doc.title.lower()]
        return docs

    def gather_facts(self, as_dict=False):

        facts = []
        for doc in self.other_documents:
            for fact in doc.facts:
                if as_dict:
                    facts.append(fact.to_dict())
                else:
                    facts.append(fact)

        for plan in self.local_plans:
            for doc in plan.plan_documents:
                for fact in doc.facts:
                    if as_dict:
                        facts.append(fact.to_dict())
                    else:
                        facts.append(fact)

        return facts

    def code(self):
        return self.id.split(':')[-1]

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'plans': [plan.to_dict(self.id) for plan in self.local_plans]
        }
        return data


def _parse_date(datestr):
    return datetime.strptime(datestr, '%Y-%m-%d')


class FactType(Enum):

    HOUSING_REQUIREMENT_TOTAL = 'Housing requirement total'
    HOUSING_REQUIREMENT_RANGE = 'Housing requirement range'
    HOUSING_REQUIREMENT_YEARLY_AVERAGE = 'Housing requirement yearly average'
    HOUSING_REQUIREMENT_YEARLY_RANGE = 'Housing requirement yearly range'


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

    def get_housing_average_for_plan(self):
        housing_average = {'housing': '???', 'source': None}
        for plan in self.planning_authority.local_plans:
            if plan.covers_years(self.from_year, self.to_year):
                for doc in plan.plan_documents:
                    for fact in doc.facts:
                        if fact.fact_type == 'HOUSING_REQUIREMENT_YEARLY_AVERAGE':
                            housing_average = {'housing': fact.fact, 'source': doc.url}
        return housing_average


class State:
    def __init__(self, state, date):
        self.state = state
        self.date = date

    def to_dict(self):
        return {'state': self.state, 'date': self.date.strftime('%Y')}

    def __lt__(self, other):
        return self.date < other.date

    def __eq__(self, other):
        return self.state == other. state and self.date == other.date


class Document(db.Model):

    __tablename__ = 'document'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=_generate_uuid)
    url = db.Column(db.String())
    title = db.Column(db.String())
    type = db.Column(db.String(64))

    facts = db.relationship('Fact',
                            back_populates='document',
                            lazy=True,
                            cascade='all, delete, delete-orphan',
                            order_by='Fact.created_date')

    created_date = db.Column(db.DateTime(), default=datetime.utcnow)

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

    local_plan_id = db.Column(UUID(as_uuid=True), db.ForeignKey('local_plan.id', name='document_local_plan_id_fkey'))
    local_plan_id_old = db.Column(db.String(64))
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
    from_ = db.Column(db.String())
    to = db.Column(db.String())

    created_date = db.Column(db.DateTime(), default=datetime.utcnow)
    image_url = db.Column(db.String())

    document_id = db.Column(UUID(as_uuid=True), db.ForeignKey('document.id'), nullable=False)
    document = db.relationship('Document', back_populates='facts')

    def get_fact_type(self):
        if self.fact_type in FactType.__members__:
            return FactType[self.fact_type]
        elif self.fact_type in EmergingFactType.__members__:
            return EmergingFactType[self.fact_type]
        return None

    def to_dict(self):
        data = {
            'id': str(self.id),
            'fact': self.fact,
            'fact_type': self.fact_type,
            'fact_type_display': self.get_fact_type().value if self.get_fact_type() else self.fact_type,
            'notes': self.notes,
            'document': str(self.document_id),
            'document_url': self.document.url,
            'created_date': self.created_date.date(),
            'from': self.from_,
            'to': self.to,
            'screenshot': self.image_url
        }

        if isinstance(self.document, OtherDocument):
            data['planning_authority'] = self.document.planning_authority.id
        else:
            data['planning_authority'] = None

        if isinstance(self.document, PlanDocument):
            data['plan'] = self.document.local_plan.local_plan
            if len(self.document.local_plan.planning_authorities) > 1:
                data['planning_authority'] = [pla.id for pla in self.document.local_plan.planning_authorities]
            else:
                data['planning_authority'] = self.document.local_plan.planning_authorities[0].id
        else:
            data['plan'] = None

        return data
