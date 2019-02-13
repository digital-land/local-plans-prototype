import uuid

from sqlalchemy import ForeignKeyConstraint

from application.extensions import db
from sqlalchemy.dialects.postgresql import UUID


def _generate_uuid():
    return uuid.uuid4()


class PlanningAuthority(db.Model):

    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256))

    local_plans = db.relationship('LocalPlan', back_populates='planning_authority', lazy=True)


class LocalPlan(db.Model):

    local_plan = db.Column(db.String(), primary_key=True)
    status = db.Column(db.String(), primary_key=True)

    entry_id = db.Integer()
    planning_policy_url = db.Column(db.String())

    planning_authority_id = db.Column(db.String(64), db.ForeignKey('planning_authority.id'), nullable=False)
    planning_authority = db.relationship('PlanningAuthority', back_populates='local_plans')

    date = db.Column(db.Date)

    # plan_documents = db.relationship('PlanDocument', back_populates='local_plan', lazy=True)

    def __repr__(self):
        return f'{self.local_plan} {self.status} {self.date}'


class PlanDocument(db.Model):

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=_generate_uuid)
    plan_document_type = db.Column(db.String)
    url = db.Column(db.String())

    local_plan_id = db.Column(db.String(), nullable=False)
    local_plan_status = db.Column(db.String(), nullable=False)

    local_plan = db.relationship('LocalPlan',
        foreign_keys=[local_plan_id, local_plan_status],
        remote_side=[LocalPlan.local_plan, LocalPlan.status],
        backref=db.backref('plan_documents'),
    )


    __table_args__ = (
        ForeignKeyConstraint(
            ['local_plan_id', 'local_plan_status'],
            ['local_plan.local_plan', 'local_plan.status'],
        ),
    )

